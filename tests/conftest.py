# """Global fixtures for myenergi integration."""
from __future__ import annotations

import json
import time
from typing import Any
from unittest.mock import AsyncMock
from unittest.mock import MagicMock
from unittest.mock import patch

import homeassistant.helpers.entity_registry as er
import pytest
from _pytest.assertion import truncate
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry
from pytest_homeassistant_custom_component.test_util.aiohttp import AiohttpClientMocker
from syrupy import SnapshotAssertion

from custom_components.daikin_onecta.const import DAIKIN_API_URL
from custom_components.daikin_onecta.const import DOMAIN
from custom_components.daikin_onecta.coordinator import OnectaRuntimeData

truncate.DEFAULT_MAX_LINES = 9999
truncate.DEFAULT_MAX_CHARS = 9999

FAKE_REFRESH_TOKEN = "some-refresh-token"
FAKE_ACCESS_TOKEN = (
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"
    ".eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ"
    ".SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"
)
FAKE_AUTH_IMPL = "conftest-imported-cred"


def load_fixture_json(name):
    with open(f"tests/fixtures/{name}.json") as json_file:
        data = json.load(json_file)
        return data


@pytest.fixture(name="auto_enable_custom_integrations", autouse=True)
def auto_enable_custom_integrations(hass: Any, enable_custom_integrations: Any) -> None:  # noqa: F811
    """Enable custom integrations defined in the test dir."""


async def snapshot_platform_entities(
    hass: HomeAssistant,
    aioclient_mock: AiohttpClientMocker,
    config_entry: MockConfigEntry,
    platform: Platform,
    entity_registry: er.EntityRegistry,
    snapshot: SnapshotAssertion,
    fixture_device_json,
) -> None:
    config_entry.runtime_data = OnectaRuntimeData(daikin_api=MagicMock(), coordinator=MagicMock(), devices={})
    """Snapshot entities and their states."""
    with patch(
        "homeassistant.helpers.config_entry_oauth2_flow.async_get_config_entry_implementation",
    ), patch(
        "homeassistant.helpers.config_entry_oauth2_flow.OAuth2Session.valid_token",
        False,
    ), patch(
        "homeassistant.helpers.config_entry_oauth2_flow.OAuth2Session.async_ensure_token_valid",
    ), patch(
        "homeassistant.helpers.config_entry_oauth2_flow.OAuth2Session.token",
        {"access_token": FAKE_ACCESS_TOKEN},
    ):
        aioclient_mock.get(DAIKIN_API_URL + "/v1/gateway-devices", status=200, json=load_fixture_json(fixture_device_json))
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
                "access_token": FAKE_ACCESS_TOKEN,
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
        return_value=FAKE_ACCESS_TOKEN,
    ):
        yield


@pytest.fixture(name="token_expiration_time")
def mock_token_expiration_time() -> float:
    """Fixture for expiration time of the config entry auth token."""
    return time.time() + 86400


@pytest.fixture(name="token_entry")
def mock_token_entry(token_expiration_time: float) -> dict[str, Any]:
    """Fixture for OAuth 'token' data for a ConfigEntry."""
    return {
        "refresh_token": FAKE_REFRESH_TOKEN,
        "access_token": FAKE_ACCESS_TOKEN,
        "type": "Bearer",
        "expires_at": token_expiration_time,
    }


@pytest.fixture(name="config_entry_v1_1")
def mock_config_entry_v1_1(token_entry: dict[str, Any]) -> MockConfigEntry:
    """Fixture for a config entry."""
    return MockConfigEntry(
        domain=DOMAIN,
        data={
            "auth_implementation": FAKE_AUTH_IMPL,
            "token": token_entry,
        },
        minor_version=1,
    )
