"""Coordinator for Daikin Onecta integration."""
from __future__ import annotations

from datetime import datetime, timedelta

import logging

from .daikin_base import Appliance

from homeassistant.exceptions import ConfigEntryAuthFailed

from homeassistant.config_entries import ConfigEntry
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
        self.options = config_entry.options
        self.scan_interval = self.options.get("high_scan_interval", 10)

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval = timedelta(minutes=self.scan_interval)
        )

        _LOGGER.info("Daikin coordinator initialized with %s seconds interval.", self.scan_interval)

    async def _async_update_data(self):
        _LOGGER.debug("Daikin coordinator start _async_update_data.")

        daikin_api = self.hass.data[DOMAIN][DAIKIN_API]
        devices = self.hass.data[DOMAIN][DAIKIN_DEVICES]

        if (datetime.now() - daikin_api._last_patch_call).total_seconds() < 30:
            _LOGGER.debug("API UPDATE skipped (just updated from UI)")
            return

        daikin_api.json_data = await daikin_api.getCloudDeviceDetails()
        for dev_data in daikin_api.json_data or []:
            if dev_data["id"] in devices:
                devices[dev_data["id"]].setJsonData(dev_data)
            else:
                device = Appliance(dev_data, daikin_api)
                devices[dev_data["id"]] = device

        hs = datetime.strptime(self.options["high_scan_start"], '%H:%M:%S').time()
        ls = datetime.strptime(self.options["low_scan_start"], '%H:%M:%S').time()

        _LOGGER.debug("Daikin coordinator finished _async_update_data.")
