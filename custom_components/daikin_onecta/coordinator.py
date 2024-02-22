"""Coordinator for Daikin Onecta integration."""
from __future__ import annotations

from datetime import timedelta

import logging

from homeassistant.exceptions import ConfigEntryAuthFailed

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_SCAN_INTERVAL,
)
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .const import DOMAIN, DAIKIN_API, DAIKIN_DEVICES

_LOGGER = logging.getLogger(__name__)

class OnectaDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching data from the API."""

    def __init__(self, hass: HomeAssistant, config_entry: ConfigEntry) -> None:
        """Initialize."""
        self.scan_interval: int = (
            1 * 60
        )

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=self.scan_interval),
        )

    async def _async_update_data(self):
        await self.hass.data[DOMAIN][DAIKIN_API].get_daikin_data()
