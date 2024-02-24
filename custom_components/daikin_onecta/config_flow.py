"""Config flow for the Daikin platform."""
import logging

from collections.abc import Mapping
from typing import Any

from homeassistant import config_entries
from homeassistant.helpers import config_entry_oauth2_flow
from homeassistant.data_entry_flow import FlowResult
from homeassistant.core import callback
from homeassistant.config_entries import ConfigEntry

from .const import DOMAIN

import voluptuous as vol

from datetime import timedelta
SCAN_INTERVAL = timedelta(seconds=60)

_LOGGER = logging.getLogger(__name__)

class OptionsFlowHandler(config_entries.OptionsFlow):
    """Config flow options handler for myenergi."""

    def __init__(self, config_entry):
        """Initialize HACS options flow."""
        self.config_entry = config_entry
        self.options = dict(config_entry.options)

    async def async_step_init(
        self, user_input: dict[str, str] | None = None
    ) -> FlowResult:
        """Handle a flow initialized by the user."""
        if user_input is not None:
            self.options.update(user_input)
            return await self._update_options()

        errors = {}
        scan_interval = self.config_entry.options.get(
            "scan_interval", SCAN_INTERVAL.total_seconds()
        )
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required("scan_interval"): str,
                }
            ),
            errors=errors,
        )

    async def _update_options(self):
        """Update config entry options."""
        return self.async_create_entry(
            title=self.config_entry.data.get("Hub "), data=self.options
        )

class FlowHandler(
    config_entry_oauth2_flow.AbstractOAuth2FlowHandler,
    domain=DOMAIN,
):
    """Handle a config flow."""
    """See https://developers.home-assistant.io/docs/core/platform/application_credentials/ """
    """ https://developer.cloud.daikineurope.com/docs/b0dffcaa-7b51-428a-bdff-a7c8a64195c0/getting_started """
    VERSION = 1
    DOMAIN = DOMAIN
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_POLL

    @property
    def extra_authorize_data(self) -> dict[str, str]:
        """Extra data that needs to be appended to the authorize url."""
        return {
            "scope": "openid onecta:basic.integration",
            "client_id": "emU20GdJDiiUxI_HnFGz69dD",
            "client_secret": "TNL1ePwnOkf6o2gKiI8InS8nVwTz2G__VYkv6WznzJGUnwLHLTmKYp-7RZc6FA3yS6D0Wgj_snvqsU5H_LPHQA"
        }

    async def async_oauth_create_entry(self, data: dict) -> FlowResult:
        """Create an oauth config entry or update existing entry for reauth."""
        existing_entry = await self.async_set_unique_id(DOMAIN)
        if existing_entry:
            self.hass.config_entries.async_update_entry(existing_entry, data=data)
            await self.hass.config_entries.async_reload(existing_entry.entry_id)
            return self.async_abort(reason="reauth_successful")

        return await super().async_oauth_create_entry(data)

    async def async_step_user(self, user_input: dict | None = None) -> FlowResult:
        """Handle a flow start."""
        await self.async_set_unique_id(DOMAIN)

        if (
            self.source != config_entries.SOURCE_REAUTH
            and self._async_current_entries()
        ):
            return self.async_abort(reason="single_instance_allowed")

        return await super().async_step_user(user_input)

    async def async_step_reauth(self, entry_data: Mapping[str, Any]) -> FlowResult:
        """Perform reauth upon an API authentication error."""
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Dialog that informs the user that reauth is required."""
        if user_input is None:
            return self.async_show_form(step_id="reauth_confirm")
        return await self.async_step_user()

    @property
    def logger(self) -> logging.Logger:
        """Return logger."""
        return logging.getLogger(__name__)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlowHandler:
        """Options callback for AccuWeather."""
        return OptionsFlowHandler(config_entry)

