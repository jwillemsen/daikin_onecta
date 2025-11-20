"""Coordinator for Daikin Onecta integration."""
from __future__ import annotations

import logging
import random
from dataclasses import dataclass
from datetime import datetime
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import DAIKIN_API
from .const import DOMAIN
from .device import DaikinOnectaDevice

_LOGGER = logging.getLogger(__name__)


@dataclass
class OnectaRuntimeData:
    """Runtime Data for Onecta integration."""

    coordinator: OnectaDataUpdateCoordinator
    devices: dict[str, Any]


class OnectaDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching data from the API."""

    def __init__(self, hass: HomeAssistant, config_entry: ConfigEntry) -> None:
        """Initialize."""
        self.options = config_entry.options
        self._config_entry = config_entry

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=self.determine_update_interval(hass),
        )

        _LOGGER.info(
            "Daikin coordinator initialized with %s interval.",
            self.update_interval,
        )

    def scan_ignore(self):
        return self.options.get("scan_ignore", 30)

    async def _async_update_data(self):
        _LOGGER.debug("Daikin coordinator start _async_update_data.")

        daikin_api = self.hass.data[DOMAIN][DAIKIN_API]
        onecta_data: OnectaRuntimeData = self._config_entry.runtime_data
        devices = onecta_data.devices
        scan_ignore_value = self.scan_ignore()

        if (datetime.now() - daikin_api._last_patch_call).total_seconds() < scan_ignore_value:
            self.update_interval = timedelta(seconds=scan_ignore_value)
            _LOGGER.debug(
                "API UPDATE skipped (just updated from UI)",
            )
        else:
            daikin_api.json_data = await daikin_api.getCloudDeviceDetails()
            for dev_data in daikin_api.json_data or []:
                if dev_data["id"] in devices:
                    devices[dev_data["id"]].setJsonData(dev_data)
                else:
                    device = DaikinOnectaDevice(dev_data, daikin_api)
                    devices[dev_data["id"]] = device

            self.update_interval = self.determine_update_interval(self.hass)

        _LOGGER.debug(
            "Daikin coordinator finished _async_update_data, next interval %s.",
            self.update_interval,
        )

    def update_settings(self, config_entry: ConfigEntry):
        _LOGGER.debug("Daikin coordinator updating settings.")
        self.options = config_entry.options
        self.update_interval = self.determine_update_interval(self.hass)
        _LOGGER.info("Daikin coordinator changed interval to '%s'", self.update_interval)

    def determine_update_interval(self, hass: HomeAssistant):
        # Default of low scan minutes interval
        scan_interval = self.options.get("low_scan_interval", 30) * 60
        high_scan_interval = self.options.get("high_scan_interval", 10) * 60
        hs = datetime.strptime(self.options.get("high_scan_start", "07:00:00"), "%H:%M:%S").time()
        ls_datetime = datetime.strptime(self.options.get("low_scan_start", "22:00:00"), "%H:%M:%S")
        ls = ls_datetime.time()
        if self.in_between(datetime.now().time(), hs, ls):
            scan_interval = high_scan_interval
        else:
            # When switching from high to low frequency polling we need to randomize the first
            # poll so that we spread the load to daikin, so for example when we have a low start at
            # 22:00 and a high scan interval of 9 minutes we randomize the next poll when it is
            # between 22:00 and 22:09
            if self.in_between(datetime.now().time(), ls, (ls_datetime + timedelta(seconds=high_scan_interval)).time()):
                scan_interval = random.randint(60, int(scan_interval))

        # When we hit our daily rate limit we check the retry_after which is the amount of seconds
        # we have to wait before we can make a call again
        daikin_api = hass.data[DOMAIN][DAIKIN_API]
        if daikin_api.rate_limits["remaining_day"] == 0:
            scan_interval = max(daikin_api.rate_limits["retry_after"] + 60, scan_interval)

        return timedelta(seconds=scan_interval)

    def in_between(self, now, start, end):
        if start <= end:
            return start <= now < end
        else:
            return start <= now or now < end
