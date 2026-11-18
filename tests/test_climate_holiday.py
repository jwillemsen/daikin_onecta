"""Tests for the Daikin holiday mode service and climate attributes."""

from datetime import date, timedelta
from unittest.mock import AsyncMock, patch

from homeassistant.const import ATTR_ENTITY_ID, STATE_UNAVAILABLE
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ServiceValidationError
from homeassistant.util import dt as dt_util
import pytest
from pytest_homeassistant.test_util.aiohttp import AiohttpClientMocker

from custom_components.daikin_onecta.climate import SERVICE_SET_HOLIDAY_MODE, DaikinClimate
from custom_components.daikin_onecta.const import DAIKIN_API_URL, DOMAIN

from .conftest import FAKE_ACCESS_TOKEN, SnapshotTestContext, load_fixture_json

CLIMATE = "climate.altherma_leaving_water_temperature"
HOLIDAY_URL = DAIKIN_API_URL + "/v1/gateway-devices/1ece521b-5401-4a42-acce-6f76fba246aa/management-points/climateControlMainZone/holiday-mode"
DAYS_BY_DEFAULT = 60
START_SENSOR = "sensor.altherma_climatecontrol_holiday_start_date"
END_SENSOR = "sensor.altherma_climatecontrol_holiday_end_date"


def _in_days(days: int) -> str:
    """Return the ISO date that many days from the current day."""
    return (dt_util.now().date() + timedelta(days=days)).isoformat()


async def _setup_altherma(snapshot_context: SnapshotTestContext) -> tuple[HomeAssistant, AiohttpClientMocker]:
    """Set up the Altherma fixture and mock the holiday mode endpoint."""
    hass = snapshot_context.hass
    aioclient_mock = snapshot_context.aioclient_mock
    aioclient_mock.get(
        DAIKIN_API_URL + "/v1/gateway-devices",
        status=200,
        json=load_fixture_json("altherma"),
        headers={
            "X-RateLimit-Limit-minute": "0",
            "X-RateLimit-Limit-day": "0",
            "X-RateLimit-Remaining-day": "0",
        },
    )
    aioclient_mock.post(HOLIDAY_URL, status=204)
    with patch("homeassistant.helpers.config_entry_oauth2_flow.async_get_config_entry_implementation"):
        assert await hass.config_entries.async_setup(snapshot_context.config_entry.entry_id)
        await hass.async_block_till_done()
    return hass, aioclient_mock


def _holiday_calls(aioclient_mock: AiohttpClientMocker) -> list:
    """Return the body of every holiday mode request made so far."""
    return [call[2] for call in aioclient_mock.mock_calls if call[0] == "POST" and str(call[1]) == HOLIDAY_URL]


@pytest.mark.asyncio
async def test_holiday_attributes_and_away_preset(
    onecta_auth: AsyncMock,
    snapshot_context: SnapshotTestContext,
) -> None:
    """Expose the stored holiday period and keep the Away preset working."""
    hass, aioclient_mock = await _setup_altherma(snapshot_context)

    state = hass.states.get(CLIMATE)
    assert state.attributes["holiday_start_date"] == "2017-01-01"
    assert state.attributes["holiday_end_date"] == "2017-01-01"
    assert state.attributes["preset_mode"] == "none"

    with patch("custom_components.daikin_onecta.DaikinApi.async_get_access_token", return_value=FAKE_ACCESS_TOKEN):
        await hass.services.async_call("climate", "set_preset_mode", {ATTR_ENTITY_ID: CLIMATE, "preset_mode": "away"}, blocking=True)
        await hass.async_block_till_done()

        assert _holiday_calls(aioclient_mock) == [{"enabled": True, "startDate": _in_days(0), "endDate": _in_days(DAYS_BY_DEFAULT)}]
        state = hass.states.get(CLIMATE)
        assert state.attributes["preset_mode"] == "away"
        assert state.attributes["holiday_start_date"] == _in_days(0)
        assert state.attributes["holiday_end_date"] == _in_days(DAYS_BY_DEFAULT)

        await hass.services.async_call("climate", "set_preset_mode", {ATTR_ENTITY_ID: CLIMATE, "preset_mode": "none"}, blocking=True)
        await hass.async_block_till_done()

        assert _holiday_calls(aioclient_mock)[-1] == {"enabled": False}
        assert hass.states.get(CLIMATE).attributes["preset_mode"] == "none"


@pytest.mark.parametrize(
    ("data", "expected"),
    [
        (
            {"enabled": True, "start_date": "2026-12-20", "end_date": "2027-01-06"},
            {"enabled": True, "startDate": "2026-12-20", "endDate": "2027-01-06"},
        ),
        (
            {"enabled": True, "duration_days": 7},
            {"enabled": True, "startDate": "today+0", "endDate": "today+7"},
        ),
        (
            {"enabled": True, "start_date": "2026-12-20", "duration_days": 3},
            {"enabled": True, "startDate": "2026-12-20", "endDate": "2026-12-23"},
        ),
        (
            {"enabled": True},
            {"enabled": True, "startDate": "today+0", "endDate": f"today+{DAYS_BY_DEFAULT}"},
        ),
        ({"enabled": False}, {"enabled": False}),
    ],
)
@pytest.mark.asyncio
async def test_set_holiday_mode_service(
    onecta_auth: AsyncMock,
    snapshot_context: SnapshotTestContext,
    data: dict,
    expected: dict,
) -> None:
    """The service sends the requested holiday period to the right management point."""
    hass, aioclient_mock = await _setup_altherma(snapshot_context)
    # Expected dates written as "today+N" are relative to the current test day
    expected = {key: _in_days(int(value.removeprefix("today+"))) if str(value).startswith("today+") else value for key, value in expected.items()}

    with patch("custom_components.daikin_onecta.DaikinApi.async_get_access_token", return_value=FAKE_ACCESS_TOKEN):
        await hass.services.async_call(
            DOMAIN,
            SERVICE_SET_HOLIDAY_MODE,
            {ATTR_ENTITY_ID: CLIMATE, **data},
            blocking=True,
        )
        await hass.async_block_till_done()

    assert _holiday_calls(aioclient_mock) == [expected]
    state = hass.states.get(CLIMATE)
    assert state.attributes["preset_mode"] == ("away" if data["enabled"] else "none")
    if data["enabled"]:
        assert state.attributes["holiday_start_date"] == expected["startDate"]
        assert state.attributes["holiday_end_date"] == expected["endDate"]


@pytest.mark.asyncio
async def test_set_holiday_mode_service_rejects_end_before_start(
    onecta_auth: AsyncMock,
    snapshot_context: SnapshotTestContext,
) -> None:
    """An end date before the start date is rejected without calling Daikin."""
    hass, aioclient_mock = await _setup_altherma(snapshot_context)

    with (
        patch("custom_components.daikin_onecta.DaikinApi.async_get_access_token", return_value=FAKE_ACCESS_TOKEN),
        pytest.raises(ServiceValidationError),
    ):
        await hass.services.async_call(
            DOMAIN,
            SERVICE_SET_HOLIDAY_MODE,
            {
                ATTR_ENTITY_ID: CLIMATE,
                "enabled": True,
                "start_date": date(2026, 12, 20),
                "end_date": date(2026, 12, 1),
            },
            blocking=True,
        )

    assert _holiday_calls(aioclient_mock) == []
    assert hass.states.get(CLIMATE).attributes["preset_mode"] == "none"


@pytest.mark.asyncio
async def test_set_holiday_mode_service_unsupported(
    onecta_auth: AsyncMock,
    snapshot_context: SnapshotTestContext,
) -> None:
    """Reject the service when the management point has no holiday mode."""
    hass, aioclient_mock = await _setup_altherma(snapshot_context)

    with (
        patch("custom_components.daikin_onecta.DaikinApi.async_get_access_token", return_value=FAKE_ACCESS_TOKEN),
        patch.object(DaikinClimate, "preset_characteristic", return_value=None),
        pytest.raises(ServiceValidationError),
    ):
        await hass.services.async_call(DOMAIN, SERVICE_SET_HOLIDAY_MODE, {ATTR_ENTITY_ID: CLIMATE, "enabled": True}, blocking=True)

    assert _holiday_calls(aioclient_mock) == []


@pytest.mark.asyncio
async def test_holiday_date_sensors(
    onecta_auth: AsyncMock,
    snapshot_context: SnapshotTestContext,
) -> None:
    """The date sensors are unavailable for Daikin's placeholder and follow the configured period."""
    hass, _ = await _setup_altherma(snapshot_context)

    # The fixture carries Daikin's 2017-01-01 placeholder for both dates
    assert hass.states.get(START_SENSOR).state == STATE_UNAVAILABLE
    assert hass.states.get(END_SENSOR).state == STATE_UNAVAILABLE

    with patch("custom_components.daikin_onecta.DaikinApi.async_get_access_token", return_value=FAKE_ACCESS_TOKEN):
        await hass.services.async_call(
            DOMAIN,
            SERVICE_SET_HOLIDAY_MODE,
            {ATTR_ENTITY_ID: CLIMATE, "enabled": True, "start_date": "2026-12-20", "end_date": "2027-01-06"},
            blocking=True,
        )
        await hass.async_block_till_done()

    start = hass.states.get(START_SENSOR)
    end = hass.states.get(END_SENSOR)
    assert (start.state, start.attributes["device_class"]) == ("2026-12-20", "date")
    assert (end.state, end.attributes["device_class"]) == ("2027-01-06", "date")
