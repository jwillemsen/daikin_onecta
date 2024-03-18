# """Global fixtures for myenergi integration."""
from typing import Any
from unittest.mock import patch
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry
from homeassistant.const import Platform
import homeassistant.helpers.entity_registry as er
from syrupy import SnapshotAssertion
from unittest.mock import AsyncMock, patch
from contextlib import contextmanager

import pytest

from . import load_fixture_json

pytest_plugins = "pytest_homeassistant_custom_component"


@pytest.fixture(name="auto_enable_custom_integrations", autouse=True)
def auto_enable_custom_integrations(hass: Any, enable_custom_integrations: Any) -> None:  # noqa: F811
    """Enable custom integrations defined in the test dir."""


# This fixture is used to prevent HomeAssistant from attempting to create and dismiss persistent
# notifications. These calls would fail without this fixture since the persistent_notification
# integration is never loaded during a test.
@pytest.fixture(name="skip_notifications", autouse=True)
def skip_notifications_fixture():
    """Skip notification calls."""
    with patch("homeassistant.components.persistent_notification.async_create"), patch(
        "homeassistant.components.persistent_notification.async_dismiss"
    ):
        yield


# This fixture, when used, will result in calls to async_get_data to return None. To have the call
# return a value, we would add the `return_value=<VALUE_TO_RETURN>` parameter to the patch call.
@pytest.fixture(name="bypass_get_data")
def bypass_get_data_fixture():
    # """Mock data from client.fetch_data()"""
    # with patch(
    #     "pymyenergi.client.MyenergiClient.fetch_data",
    #     return_value=load_fixture_json("client"),
    # ), patch(
    #     "pymyenergi.zappi.Zappi.fetch_history_data",
    #     return_value=load_fixture_json("history_zappi"),
    # ), patch(
    #     "pymyenergi.eddi.Eddi.fetch_history_data",
    #     return_value=load_fixture_json("history_eddi"),
    # ):
    yield


# In this fixture, we are forcing calls to async_get_data to raise an Exception. This is useful
# for exception handling.
@pytest.fixture(name="error_on_get_data")
def error_get_data_fixture():
    """Simulate error when retrieving data from API."""
    with patch(
        "pymyenergi.client.MyenergiClient.refresh",
        side_effect=Exception,
    ):
        yield


# In this fixture, we are forcing calls to async_get_data to raise an Exception. This is useful
# for exception handling.
@pytest.fixture(name="auth_error_on_get_data")
def auth_error_get_data_fixture():
    """Simulate authentication error when retrieving data from API."""
    with patch(
        "pymyenergi.client.MyenergiClient.refresh",
        side_effect=WrongCredentials,
    ):
        yield


# In this fixture, we are forcing calls to async_get_data to raise an Exception. This is useful
# for exception handling.
@pytest.fixture(name="timeout_error_on_get_data")
def timeout_error_get_data_fixture():
    """Simulate authentication error when retrieving data from API."""
    with patch(
        "pymyenergi.client.MyenergiClient.refresh",
        side_effect=TimeoutException,
    ):
        yield


async def snapshot_platform_entities(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    platform: Platform,
    entity_registry: er.EntityRegistry,
    snapshot: SnapshotAssertion,
) -> None:
    """Snapshot entities and their states."""
    with selected_platforms([platform]):
        assert await hass.config_entries.async_setup(config_entry.entry_id)

        await hass.async_block_till_done()
    # with selected_platforms([platform]):
    entity_entries = er.async_entries_for_config_entry(entity_registry, config_entry.entry_id)

    assert entity_entries
    for entity_entry in entity_entries:
        assert entity_entry == snapshot(name=f"{entity_entry.entity_id}-entry")
        assert hass.states.get(entity_entry.entity_id) == snapshot(name=f"{entity_entry.entity_id}-state")


@contextmanager
def selected_platforms(platforms: list[Platform]) -> AsyncMock:
    """Restrict loaded platforms to list given."""
    with patch(
        "homeassistant.helpers.config_entry_oauth2_flow.async_get_config_entry_implementation",
    ), patch(
        "custom_components.daikin_onecta.DaikinApi.getCloudDeviceDetails",
        return_value=load_fixture_json("altherma"),
    ):
        yield


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
        options={
            "weather_areas": {
                "Home avg": {
                    "lat_ne": 32.2345678,
                    "lon_ne": -117.1234567,
                    "lat_sw": 32.1234567,
                    "lon_sw": -117.2345678,
                    "show_on_map": False,
                    "area_name": "Home avg",
                    "mode": "avg",
                },
                "Home max": {
                    "lat_ne": 32.2345678,
                    "lon_ne": -117.1234567,
                    "lat_sw": 32.1234567,
                    "lon_sw": -117.2345678,
                    "show_on_map": True,
                    "area_name": "Home max",
                    "mode": "max",
                },
            }
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


# @pytest.fixture(name="access_token")
# def async_get_access_token() -> AsyncMock:
#     """Restrict loaded platforms to list given."""
#
#     with patch(
#         "custom_components.daikin_onecta.DaikinApi.async_get_access_token",
#         return_value="aa",
#     ):
#         yield
