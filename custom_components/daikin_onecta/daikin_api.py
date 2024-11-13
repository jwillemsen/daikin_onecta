"""Platform for the Daikin AC."""
import asyncio
import functools
import logging
from datetime import datetime
from http import HTTPStatus

import requests
from aiohttp import ClientResponseError
from homeassistant import config_entries
from homeassistant import core
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers import config_entry_oauth2_flow
from homeassistant.helpers import issue_registry as ir

from .const import DAIKIN_API_URL
from .const import DOMAIN

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
            "ratelimit_reset": 0,
        }

        # The following lock is used to serialize http requests to Daikin cloud
        # to prevent receiving old settings while a PATCH is ongoing.
        self._cloud_lock = asyncio.Lock()

        _LOGGER.info("Daikin Onecta API initialized.")

    async def async_get_access_token(self) -> str:
        """Return a valid access token."""
        if not self.session.valid_token:
            try:
                await self.session.async_ensure_token_valid()
            except ClientResponseError as ex:
                # https://developers.home-assistant.io/docs/integration_setup_failures/#handling-expired-credentials
                if ex.status == HTTPStatus.BAD_REQUEST:
                    raise ConfigEntryAuthFailed(f"Problem refreshing token: {ex}") from ex
                raise ex

        return self.session.token["access_token"]

    async def doBearerRequest(self, method, resourceUrl, options=None):
        async with self._cloud_lock:
            token = await self.async_get_access_token()

            resourceUrl = DAIKIN_API_URL + resourceUrl
            headers = {"Accept-Encoding": "gzip", "Authorization": "Bearer " + token, "Content-Type": "application/json"}

            _LOGGER.debug("BEARER REQUEST URL: %s", resourceUrl)
            _LOGGER.debug("BEARER TYPE %s JSON: %s", method, options)

            func = functools.partial(requests.request, url=resourceUrl, method=method, headers=headers, data=options)
            try:
                res = await self.hass.async_add_executor_job(func)
            except Exception as e:
                _LOGGER.error("REQUEST TYPE %s FAILED: %s", method, e)
                if method == "GET":
                    return []
                else:
                    return False

            self.rate_limits["minute"] = int(res.headers.get("X-RateLimit-Limit-minute", 0))
            self.rate_limits["day"] = int(res.headers.get("X-RateLimit-Limit-day", 0))
            self.rate_limits["remaining_minutes"] = int(res.headers.get("X-RateLimit-Remaining-minute", 0))
            self.rate_limits["remaining_day"] = int(res.headers.get("X-RateLimit-Remaining-day", 0))
            self.rate_limits["retry_after"] = int(res.headers.get("retry-after", 0))
            self.rate_limits["ratelimit_reset"] = int(res.headers.get("ratelimit-reset", 0))

            if self.rate_limits["remaining_minutes"] > 0:
                ir.async_delete_issue(self.hass, DOMAIN, "minute_rate_limit")

            if self.rate_limits["remaining_day"] > 0:
                ir.async_delete_issue(self.hass, DOMAIN, "day_rate_limit")

            _LOGGER.debug("BEARER RESPONSE CODE: %s LIMIT: %s", res.status_code, self.rate_limits)

        if method == "GET" and res.status_code == 200:
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
                    learn_more_url="https://developer.cloud.daikineurope.com/docs/b0dffcaa-7b51-428a-bdff-a7c8a64195c0/general_api_guidelines#doc-heading-rate-limitation",
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
                    learn_more_url="https://developer.cloud.daikineurope.com/docs/b0dffcaa-7b51-428a-bdff-a7c8a64195c0/general_api_guidelines#doc-heading-rate-limitation",
                    translation_key="day_rate_limit",
                )
            if method == "GET":
                return []
            else:
                return False
        elif res.status_code == 204:
            self._last_patch_call = datetime.now()
            return True

        _LOGGER.error("REQUEST TYPE %s FOR %s WITH OPTIONS %s FAILED: %s %s", method, resourceUrl, options, res.status_code, res.text)

        raise Exception(
            "Communication failed! Status: "
            + str(res.status_code)
            + " "
            + res.text
            + " Method: "
            + method
            + " Url: "
            + resourceUrl
            + " Options: "
            + str(options)
        )

    async def getCloudDeviceDetails(self):
        """Get pure Device Data from the Daikin cloud devices."""
        return await self.doBearerRequest("GET", "/v1/gateway-devices")
