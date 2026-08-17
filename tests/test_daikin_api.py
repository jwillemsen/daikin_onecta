"""Tests for the Daikin Onecta API client."""
import asyncio
from unittest.mock import AsyncMock
from unittest.mock import MagicMock
from unittest.mock import patch

from aiohttp import ClientConnectionError
from homeassistant.core import HomeAssistant
import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.daikin_onecta.daikin_api import DaikinApi


@pytest.mark.parametrize(
    "error",
    [ClientConnectionError("network unavailable"), asyncio.TimeoutError()],
)
async def test_get_device_details_propagates_network_errors(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    error: Exception,
) -> None:
    """Transient network failures must reach the coordinator retry logic."""
    session = MagicMock()
    session.request.side_effect = error

    with (
        patch(
            "custom_components.daikin_onecta.daikin_api.async_get_clientsession",
            return_value=session,
        ),
        patch.object(
            DaikinApi,
            "async_get_access_token",
            new=AsyncMock(return_value="token"),
        ),
        pytest.raises(type(error)),
    ):
        api = DaikinApi(hass, config_entry, MagicMock())
        await api.getCloudDeviceDetails()
