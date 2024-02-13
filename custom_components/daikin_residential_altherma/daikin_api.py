"""Platform for the Daikin AC."""
import base64
import datetime
import functools
import logging
import os
import re
import requests
import time
import asyncio
import json

from homeassistant.util import Throttle
from homeassistant.helpers import config_entry_oauth2_flow
from homeassistant import config_entries, core

from .const import DOMAIN, DAIKIN_DEVICES

from .daikin_base import Appliance

_LOGGER = logging.getLogger(__name__)

MIN_TIME_BETWEEN_UPDATES = datetime.timedelta(seconds=15)

class DaikinApi:
    """Daikin Residential API."""

    def __init__(self,
                hass: core.HomeAssistant,
                entry: config_entries.ConfigEntry,
                implementation: config_entry_oauth2_flow.AbstractOAuth2Implementation,):
        """Initialize a new Daikin Residential Altherma API."""
        _LOGGER.debug("Initialing Daikin Residential Altherma API...")
        self.hass = hass
        self._config_entry = entry
        self.session = config_entry_oauth2_flow.OAuth2Session(
            hass, entry, implementation
        )

        # The Daikin cloud returns old settings if queried with a GET
        # immediately after a PATCH request. Se we use this attribute
        # to skip the first GET if a PATCH request has just been executed.
        self._just_updated = False

        # The following lock is used to serialize http requests to Daikin cloud
        # to prevent receiving old settings while a PATCH is ongoing.
        self._cloud_lock = asyncio.Lock()

        _LOGGER.info("Daikin Residential Altherma API initialized.")

    async def async_get_access_token(self) -> str:
        """Return a valid access token."""
        await self.session.async_ensure_token_valid()
        return self.session.token["access_token"]

    async def doBearerRequest(self, resourceUrl, options=None, refreshed=False):
        token = self.session.token["access_token"]
        if token is None:
            raise Exception("Missing TokenSet. Please repeat Authentication process.")

        if not resourceUrl.startswith("http"):
            resourceUrl = "https://api.onecta.daikineurope.com" + resourceUrl

        headers = {
            "Authorization": "Bearer " + token,
            "Content-Type": "application/json",
        }

        async with self._cloud_lock:
            _LOGGER.debug("BEARER REQUEST URL: %s", resourceUrl)
            _LOGGER.debug("BEARER REQUEST HEADERS: %s", headers)
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
            _LOGGER.debug("BEARER RESPONSE CODE: %s", res.status_code)

        if res.status_code == 200:
            try:
                return res.json()
            except Exception:
                _LOGGER.error("RETRIEVE JSON FAILED: %s", res.text)
                return False
        elif res.status_code == 204:
            self._just_updated = True
            return True

        if not refreshed and res.status_code == 401:
            _LOGGER.debug("TOKEN EXPIRED: will refresh it (%s)", res.status_code)
            await self.async_get_access_token()
            return await self.doBearerRequest(resourceUrl, options, True)

        raise Exception("Communication failed! Status: " + str(res.status_code))

    async def getApiInfo(self):
        """Get Daikin API Info."""
        return await self.doBearerRequest("/v1/info")

    async def getCloudDeviceDetails(self):
        """Get pure Device Data from the Daikin cloud devices."""
        json_puredata = await self.doBearerRequest("/v1/gateway-devices")
        return json_puredata

    async def getCloudDevices(self):
        """Get array of DaikinResidentialDevice objects and get their data."""
        self.json_data = await self.getCloudDeviceDetails()

        res = {}
        for dev_data in self.json_data or []:
            device = Appliance(dev_data, self)
            res[dev_data["id"]] = device
        return res

    @Throttle(MIN_TIME_BETWEEN_UPDATES)
    async def async_update(self, **kwargs):
        """Pull the latest data from Daikin."""
        if self._just_updated:
            self._just_updated = False
            _LOGGER.debug("API UPDATE skipped (just updated from UI)")
            return False

        _LOGGER.debug("API UPDATE")

        self.json_data = await self.getCloudDeviceDetails()
        for dev_data in self.json_data or []:

            if dev_data["id"] in self.hass.data[DOMAIN][DAIKIN_DEVICES]:
                self.hass.data[DOMAIN][DAIKIN_DEVICES][dev_data["id"]].setJsonData(
                    dev_data
                )
