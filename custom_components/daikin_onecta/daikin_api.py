"""Platform for the Daikin AC."""
import asyncio
import base64
import functools
import json
import logging
import os
import re
import time
from datetime import datetime
from datetime import timedelta

import requests
from homeassistant import config_entries
from homeassistant import core
from homeassistant.helpers import config_entry_oauth2_flow
from homeassistant.util import Throttle

from .const import DAIKIN_DEVICES
from .const import DOMAIN
from .daikin_base import Appliance

_LOGGER = logging.getLogger(__name__)


class DaikinApi:
    """Daikin Onecta API."""

    def __init__(
        self,
        hass: core.HomeAssistant,
        entry: config_entries.ConfigEntry,
        implementation: config_entry_oauth2_flow.AbstractOAuth2Implementation,
    ):
        """Initialize a new Daikin Onecta API."""
        _LOGGER.debug("Initialing Daikin Onecta API...")
        self.hass = hass
        self._config_entry = entry
        self.session = config_entry_oauth2_flow.OAuth2Session(
            hass, entry, implementation
        )

        # The Daikin cloud returns old settings if queried with a GET
        # immediately after a PATCH request. Se we use this attribute
        # to check when we had the last patch command, if it is less then
        # 10 seconds ago we skip the get
        self._last_patch_call = datetime.min

        # Store the limits as member so that we can add these to the diagnostics
        self.rate_limits = {
            "minute": 0,
            "day": 0,
            "remaining_minutes": 0,
            "remaining_day": 0,
        }

        # The following lock is used to serialize http requests to Daikin cloud
        # to prevent receiving old settings while a PATCH is ongoing.
        self._cloud_lock = asyncio.Lock()

        _LOGGER.info("Daikin Onecta API initialized.")

    async def async_get_access_token(self) -> str:
        """Return a valid access token."""
        if not self.session.valid_token:
            await self.session.async_ensure_token_valid()
        return self.session.token["access_token"]

    async def doBearerRequest(self, resourceUrl, options=None):
        async with self._cloud_lock:
            token = await self.async_get_access_token()
            if token is None:
                raise Exception("Missing token. Please repeat Authentication process.")

            if not resourceUrl.startswith("http"):
                resourceUrl = "https://api.onecta.daikineurope.com" + resourceUrl

            headers = {
                "Authorization": "Bearer " + token,
                "Content-Type": "application/json",
            }

            _LOGGER.debug("BEARER REQUEST URL: %s", resourceUrl)
            if (
                options is not None
                and "method" in options
                and options["method"] == "PATCH"
            ):
                _LOGGER.debug("BEARER REQUEST JSON: %s", options["json"])
                func = functools.partial(
                    requests.patch, resourceUrl, headers=headers, data=options["json"]
                )
            else:
                func = functools.partial(requests.get, resourceUrl, headers=headers)
            try:
                res = await self.hass.async_add_executor_job(func)
            except Exception as e:
                _LOGGER.error("REQUEST FAILED: %s", e)
                return []

            self.rate_limits["minute"] = res.headers.get("X-RateLimit-Limit-minute", 0)
            self.rate_limits["day"] = res.headers.get("X-RateLimit-Limit-day", 0)
            self.rate_limits["remaining_minutes"] = res.headers.get(
                "X-RateLimit-Remaining-minute", 0
            )
            self.rate_limits["remaining_day"] = res.headers.get(
                "X-RateLimit-Remaining-day", 0
            )

            _LOGGER.debug(
                "BEARER RESPONSE CODE: %s LIMIT: %s", res.status_code, self.rate_limits
            )

        if res.status_code == 200:
            try:
                return res.json()
            except Exception:
                _LOGGER.error("RETRIEVE JSON FAILED: %s", res.text)
                return False
        elif res.status_code == 204:
            self._last_patch_call = datetime.now()
            return True

        raise Exception("Communication failed! Status: " + str(res.status_code))

    async def getCloudDeviceDetails(self):
        """Get pure Device Data from the Daikin cloud devices."""
        json_puredata = await self.doBearerRequest("/v1/gateway-devices")
        return json_puredata

    async def getCloudDevices(self):
        """Get array of DaikinOnectaDevice objects and get their data."""
        self.json_data = await self.getCloudDeviceDetails()

        res = {}
        for dev_data in self.json_data or []:
            device = Appliance(dev_data, self)
            res[dev_data["id"]] = device
        return res

    async def get_daikin_data(self):
        """Pull the latest data from Daikin only when the last patch call is more than 30 seconds ago."""
        if (
            datetime.now() - self._last_patch_call
        ).total_seconds() < self._config_entry.options.get("scan_ignore", 30):
            _LOGGER.debug("API UPDATE skipped (just updated from UI)")
            return False

        _LOGGER.debug("API UPDATE")

        self.json_data = await self.getCloudDeviceDetails()
        for dev_data in self.json_data or []:
            if dev_data["id"] in self.hass.data[DOMAIN][DAIKIN_DEVICES]:
                self.hass.data[DOMAIN][DAIKIN_DEVICES][dev_data["id"]].setJsonData(
                    dev_data
                )
        return self.hass.data[DOMAIN][DAIKIN_DEVICES]
