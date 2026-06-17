"""Unit tests for DaikinOnectaDevice silent-revert detection."""
import logging
from datetime import datetime
from datetime import timedelta
from unittest.mock import AsyncMock

import pytest

from custom_components.daikin_onecta.device import _MISSING
from custom_components.daikin_onecta.device import _PendingWrite
from custom_components.daikin_onecta.device import DaikinOnectaDevice
from custom_components.daikin_onecta.device import REVERT_CHECK_TTL


def _make_device(operation_mode="auto", fan_current_mode="auto"):
    api = AsyncMock()
    api.doBearerRequest = AsyncMock(return_value=True)
    json_data = {
        "id": "dev-1",
        "deviceModel": "dx23",
        "isCloudConnectionUp": {"value": True},
        "managementPoints": [
            {
                "embeddedId": "climateControl",
                "managementPointType": "climateControl",
                "name": {"value": "Woonkamer"},
                "operationMode": {"settable": True, "values": ["auto", "cooling"], "value": operation_mode},
                "fanControl": {
                    "value": {
                        "operationModes": {
                            "auto": {
                                "fanSpeed": {
                                    "currentMode": {"settable": True, "value": fan_current_mode, "values": ["auto", "fixed"]},
                                },
                            },
                        },
                    },
                },
            }
        ],
    }
    return DaikinOnectaDevice(json_data, api), api


def _new_payload(operation_mode_value, fan_current_mode_value=None, drop_fan=False):
    fan_block = {} if drop_fan else {
        "fanControl": {
            "value": {
                "operationModes": {
                    "auto": {
                        "fanSpeed": {
                            "currentMode": {"value": fan_current_mode_value, "values": ["auto", "fixed"]},
                        },
                    },
                },
            },
        },
    }
    return {
        "id": "dev-1",
        "deviceModel": "dx23",
        "isCloudConnectionUp": {"value": True},
        "managementPoints": [
            {
                "embeddedId": "climateControl",
                "managementPointType": "climateControl",
                "name": {"value": "Woonkamer"},
                "operationMode": {"value": operation_mode_value},
                **fan_block,
            }
        ],
    }


def test_read_value_top_level_and_nested():
    device, _ = _make_device(operation_mode="auto", fan_current_mode="fixed")
    assert device._read_value("climateControl", "operationMode", "") == "auto"
    assert device._read_value("climateControl", "fanControl", "/operationModes/auto/fanSpeed/currentMode") == "fixed"


def test_read_value_returns_missing_for_unknown_paths():
    device, _ = _make_device()
    assert device._read_value("does-not-exist", "operationMode", "") is _MISSING
    assert device._read_value("climateControl", "doesNotExist", "") is _MISSING
    assert device._read_value("climateControl", "fanControl", "/operationModes/unknown/fanSpeed/currentMode") is _MISSING


def test_read_value_distinguishes_missing_from_explicit_none():
    device, _ = _make_device()
    # Replace value with explicit None
    device.daikin_data["managementPoints"][0]["operationMode"] = {"value": None}
    assert device._read_value("climateControl", "operationMode", "") is None
    # Drop the "value" key entirely -> missing
    device.daikin_data["managementPoints"][0]["operationMode"] = {}
    assert device._read_value("climateControl", "operationMode", "") is _MISSING


@pytest.mark.asyncio
async def test_successful_patch_records_pending_write():
    device, _ = _make_device()
    await device.patch("dev-1", "climateControl", "operationMode", "", "auto")
    assert ("climateControl", "operationMode", "") in device._pending_writes


@pytest.mark.asyncio
async def test_failed_patch_does_not_record_pending_write():
    device, api = _make_device()
    api.doBearerRequest = AsyncMock(return_value=False)
    await device.patch("dev-1", "climateControl", "operationMode", "", "auto")
    assert device._pending_writes == {}


@pytest.mark.asyncio
async def test_matching_refresh_clears_pending_write_silently(caplog):
    device, _ = _make_device()
    await device.patch("dev-1", "climateControl", "operationMode", "", "auto")
    caplog.clear()
    with caplog.at_level(logging.WARNING, logger="custom_components.daikin_onecta.device"):
        device.setJsonData(_new_payload("auto", fan_current_mode_value="auto"))
    assert device._pending_writes == {}
    assert "reverted" not in caplog.text


@pytest.mark.asyncio
async def test_mismatching_refresh_warns_and_drops_pending_write(caplog):
    device, _ = _make_device()
    await device.patch("dev-1", "climateControl", "operationMode", "", "auto")
    with caplog.at_level(logging.WARNING, logger="custom_components.daikin_onecta.device"):
        device.setJsonData(_new_payload("cooling", fan_current_mode_value="auto"))
    assert device._pending_writes == {}
    assert "was set to 'auto'" in caplog.text
    assert "now reports 'cooling'" in caplog.text


@pytest.mark.asyncio
async def test_missing_characteristic_keeps_pending_write(caplog):
    device, _ = _make_device()
    await device.patch(
        "dev-1", "climateControl", "fanControl", "/operationModes/auto/fanSpeed/currentMode", "auto"
    )
    with caplog.at_level(logging.WARNING, logger="custom_components.daikin_onecta.device"):
        device.setJsonData(_new_payload("auto", drop_fan=True))
    # No fanControl in the new payload -> keep watching, no warning yet.
    assert ("climateControl", "fanControl", "/operationModes/auto/fanSpeed/currentMode") in device._pending_writes
    assert "reverted" not in caplog.text


@pytest.mark.asyncio
async def test_second_patch_supersedes_previous_pending_write(caplog):
    device, _ = _make_device()
    await device.patch("dev-1", "climateControl", "operationMode", "", "auto")
    await device.patch("dev-1", "climateControl", "operationMode", "", "cooling")
    assert len(device._pending_writes) == 1
    pending = next(iter(device._pending_writes.values()))
    assert pending.value == "cooling"
    # Cloud confirms the latest value -> no warning, no leftover entries.
    with caplog.at_level(logging.WARNING, logger="custom_components.daikin_onecta.device"):
        device.setJsonData(_new_payload("cooling", fan_current_mode_value="auto"))
    assert device._pending_writes == {}
    assert "reverted" not in caplog.text


def test_expired_pending_write_is_dropped_silently(caplog):
    device, _ = _make_device()
    device._pending_writes[("climateControl", "operationMode", "")] = _PendingWrite(
        embedded_id="climateControl",
        data_point="operationMode",
        data_point_path="",
        value="auto",
        set_at=datetime.now() - REVERT_CHECK_TTL - timedelta(seconds=1),
    )
    with caplog.at_level(logging.WARNING, logger="custom_components.daikin_onecta.device"):
        device.setJsonData(_new_payload("cooling", fan_current_mode_value="auto"))
    assert device._pending_writes == {}
    assert "reverted" not in caplog.text
