# """Global fixtures for myenergi integration."""
from typing import Any
from unittest.mock import AsyncMock
from unittest.mock import patch

import homeassistant.helpers.entity_registry as er
import pytest
from _pytest.assertion import truncate
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry
from syrupy import SnapshotAssertion

from . import load_fixture_json

truncate.DEFAULT_MAX_LINES = 9999
truncate.DEFAULT_MAX_CHARS = 9999


@pytest.fixture(name="auto_enable_custom_integrations", autouse=True)
def auto_enable_custom_integrations(hass: Any, enable_custom_integrations: Any) -> None:  # noqa: F811
    """Enable custom integrations defined in the test dir."""


async def snapshot_platform_entities(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    platform: Platform,
    entity_registry: er.EntityRegistry,
    snapshot: SnapshotAssertion,
    fixture_device_json,
) -> None:
    """Snapshot entities and their states."""
    with patch(
        "homeassistant.helpers.config_entry_oauth2_flow.async_get_config_entry_implementation",
    ), patch(
        "custom_components.daikin_onecta.DaikinApi.getCloudDeviceDetails",
        return_value=load_fixture_json(fixture_device_json),
    ), patch(
        "custom_components.daikin_onecta.DaikinApi.async_get_access_token",
        return_value="XXXXXX",
    ):
        assert await hass.config_entries.async_setup(config_entry.entry_id)

        await hass.async_block_till_done()

    entity_entries = er.async_entries_for_config_entry(entity_registry, config_entry.entry_id)

    assert entity_entries
    for entity_entry in entity_entries:
        entity_entry == snapshot(name=f"{entity_entry.entity_id}-entry")  # todo add assert back
        hass.states.get(entity_entry.entity_id) == snapshot(name=f"{entity_entry.entity_id}-state")  # todo add assert back


@pytest.fixture(name="config_entry")
def mock_config_entry_fixture(hass: HomeAssistant) -> MockConfigEntry:
    """Mock a config entry."""
    mock_entry = MockConfigEntry(
        domain="daikin_onecta",
        data={
            "auth_implementation": "cloud",
            "token": {
                "refresh_token": "mock-refresh-token",
                "access_token": "mock-access-token",
                "type": "Bearer",
                "expires_in": 60,
                "expires_at": 1000,
                "scope": 1,
            },
        },
    )
    mock_entry.add_to_hass(hass)

    return mock_entry


@pytest.fixture(name="onecta_auth")
def onecta_auth() -> AsyncMock:
    """Restrict loaded platforms to list given."""
    yield


@pytest.fixture(name="access_token")
def async_get_access_token() -> AsyncMock:
    """Restrict loaded platforms to list given."""

    with patch(
        "custom_components.daikin_onecta.DaikinApi.async_get_access_token",
        return_value="aa",
    ):
        yield
