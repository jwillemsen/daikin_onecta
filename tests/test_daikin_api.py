"""Tests for the Daikin Onecta API client."""
from unittest.mock import AsyncMock
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
from daikin_onecta import OnectaConnectionError
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.daikin_onecta.daikin_api import DaikinApi


async def test_get_device_details_propagates_connection_error(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
) -> None:
    """Propagate library connection errors to the coordinator."""
    with (
        patch(
            "custom_components.daikin_onecta.daikin_api.OnectaClient.get_gateway_devices",
            new=AsyncMock(side_effect=OnectaConnectionError("network unavailable")),
        ),
        pytest.raises(OnectaConnectionError, match="network unavailable"),
    ):
        api = DaikinApi(hass, config_entry, MagicMock())
        await api.get_cloud_device_details()
