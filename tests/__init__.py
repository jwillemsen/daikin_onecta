"""Tests for daikin_onecta integration."""

# TODO:
# - Test rate limits
# - Test various sensors, provide test json for various devices
# - Test commands to devices with cache updates
from __future__ import annotations

import json
import logging
from typing import Any
from unittest.mock import Mock
from unittest.mock import patch

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.daikin_onecta import DOMAIN


TEST_CONFIG_ENTRY_ID = "77889900af"


def load_fixture_json(name):
    with open(f"tests/fixtures/{name}.json") as json_file:
        data = json.load(json_file)
        return data


def create_mock_daikin_onecta_config_entry(
    hass: HomeAssistant,
    data: dict[str, Any] | None = None,
    options: dict[str, Any] | None = None,
) -> ConfigEntry:
    """Add a test config entry."""
    config_entry: MockConfigEntry = MockConfigEntry(
        entry_id=TEST_CONFIG_ENTRY_ID,
        domain=DOMAIN,
        data=data or "",
        title="",
        options=options or {},
    )
    config_entry.add_to_hass(hass)
    return config_entry


async def setup_mock_daikin_onecta_config_entry(
    hass: HomeAssistant,
    data: dict[str, Any] | None = None,
    config_entry: ConfigEntry | None = None,
    client: Mock | None = None,
) -> ConfigEntry:
    log = logging.getLogger()
    log.setLevel(logging.DEBUG)
    client_data = "altherma"
    # if data is not None:
    data = load_fixture_json("altherma")
    #    client_data = data.get("client_data", "client")
    """Add a mock sunspec config entry to hass."""
    config_entry = config_entry or create_mock_daikin_onecta_config_entry(hass, data)
    """Mock data from client.fetch_data()"""
    with patch(
        "custom_components.daikin_onecta.DaikinApi.getCloudDeviceDetails",
        return_value=load_fixture_json("altherma"),
    ):
        await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()
    return config_entry
