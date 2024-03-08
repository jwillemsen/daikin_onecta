"""Platform for the Daikin AC."""

import asyncio
import functools
import logging
from datetime import datetime

import requests
from homeassistant import config_entries
from homeassistant import core
from homeassistant.helpers import config_entry_oauth2_flow
from homeassistant.helpers import issue_registry as ir

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
        self.session = config_entry_oauth2_flow.OAuth2Session(hass, entry, implementation)

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
            "retry_after": 0,
            "ratelimit_reset": 0
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
            if options is not None and "method" in options and options["method"] == "PATCH":
                _LOGGER.debug("BEARER REQUEST JSON: %s", options["json"])
                func = functools.partial(requests.patch, resourceUrl, headers=headers, data=options["json"])
            else:
                func = functools.partial(requests.get, resourceUrl, headers=headers)
            try:
                res = await self.hass.async_add_executor_job(func)
            except Exception as e:
                _LOGGER.error("REQUEST FAILED: %s", e)
                return []

            self.rate_limits["minute"] = int(res.headers.get("X-RateLimit-Limit-minute", 0))
            self.rate_limits["day"] = int(res.headers.get("X-RateLimit-Limit-day", 0))
            self.rate_limits["remaining_minutes"] = int(res.headers.get("X-RateLimit-Remaining-minute", 0))
            self.rate_limits["remaining_day"] = int(res.headers.get("X-RateLimit-Remaining-day", 0))
            self.rate_limits["remaining_minutes"] = int(res.headers.get("X-RateLimit-Remaining-minute", 0))
            self.rate_limits["retry_after"] = int(res.headers.get("retry-after", 0))
            self.rate_limits["ratelimit_reset"] = int(res.headers.get("ratelimit-reset", 0))

            if self.rate_limits["remaining_minutes"] > 0:
                ir.async_delete_issue(self.hass, DOMAIN, "minute_rate_limit")

            if self.rate_limits["remaining_day"] > 0:
                ir.async_delete_issue(self.hass, DOMAIN, "day_rate_limit")

            _LOGGER.debug("BEARER RESPONSE CODE: %s LIMIT: %s", res.status_code, self.rate_limits)

        if res.status_code == 200:
            try:
                return res.json()
            except Exception:
                _LOGGER.error("RETRIEVE JSON FAILED: %s", res.text)
                return False
        elif res.status_code == 429:
            if self.rate_limits["remaining_minutes"] == 0:
                ir.async_create_issue(
                    self.hass,
                    DOMAIN,
                    "minute_rate_limit",
                    is_fixable=False,
                    is_persistent=True,
                    severity=ir.IssueSeverity.ERROR,
                    learn_more_url="https://developer.cloud.daikineurope.com/docs/b0dffcaa-7b51-428a-bdff-a7c8a64195c0/rate_limitation",
                    translation_key="minute_rate_limit",
                )

            if self.rate_limits["remaining_day"] == 0:
                ir.async_create_issue(
                    self.hass,
                    DOMAIN,
                    "day_rate_limit",
                    is_fixable=False,
                    is_persistent=True,
                    severity=ir.IssueSeverity.ERROR,
                    learn_more_url="https://developer.cloud.daikineurope.com/docs/b0dffcaa-7b51-428a-bdff-a7c8a64195c0/rate_limitation",
                    translation_key="day_rate_limit",
                )
            if options is not None and "method" in options and options["method"] == "PATCH":
                return False
            else:
                return []
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
        if (datetime.now() - self._last_patch_call).total_seconds() < self._config_entry.options.get("scan_ignore", 30):
            _LOGGER.debug("API UPDATE skipped (just updated from UI)")
            return False

        _LOGGER.debug("API UPDATE")

        self.json_data = await self.getCloudDeviceDetails()
        for dev_data in self.json_data or []:
            if dev_data["id"] in self.hass.data[DOMAIN][DAIKIN_DEVICES]:
                self.hass.data[DOMAIN][DAIKIN_DEVICES][dev_data["id"]].setJsonData(dev_data)
        return self.hass.data[DOMAIN][DAIKIN_DEVICES]
