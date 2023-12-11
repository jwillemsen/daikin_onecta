"""Config flow for the Daikin platform."""
import logging

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD

from .daikin_api import DaikinApi
from .const import DOMAIN, CONF_TOKENSET

_LOGGER = logging.getLogger(__name__)


@config_entries.HANDLERS.register(DOMAIN)
class FlowHandler(config_entries.ConfigFlow):
    """Handle a config flow."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_POLL

    def __init__(self):
        """Initialize the Daikin config flow."""
        self.host = None

    @property
    def schema(self):
        """Return current schema."""
        return vol.Schema(
            {vol.Required(CONF_EMAIL): str, vol.Required(CONF_PASSWORD): str}
        )

    async def _create_entry(self, email, password, tokenSet):
        """Register new entry."""
        # if not self.unique_id:
        #    await self.async_set_unique_id(password)
        # self._abort_if_unique_id_configured()
        if self._async_current_entries():
            return self.async_abort(reason="already_configured")

        await self.async_set_unique_id("DaikinResidentialAltherma")
        return self.async_create_entry(
            title="Daikin",
            data={CONF_EMAIL: email, CONF_PASSWORD: password, CONF_TOKENSET: tokenSet},
        )

    async def _attempt_connection(self, email, password):
        """Create device."""
        try:
            daikin_api = DaikinApi(self.hass, None)
        except Exception as e:
            _LOGGER.error("Failed to initialize DaikinApi: %s", e)
            return self.async_abort(reason="init_failed")
        try:
            await daikin_api.retrieveAccessToken(email, password)
        except Exception as e:
            _LOGGER.error("Failed to retrieve Access Token: %s", e)
            return self.async_abort(reason="token_retrieval_failed")
        try:
            await daikin_api.getApiInfo()
        except Exception as e:
            _LOGGER.error("Failed to connect to DaikinApi: %s", e)
            return self.async_abort(reason="cannot_connect")

        return await self._create_entry(email, password, daikin_api.tokenSet)

    async def async_step_user(self, user_input=None):
        """User initiated config flow."""
        if user_input is None:
            return self.async_show_form(step_id="user", data_schema=self.schema)
        return await self._attempt_connection(
            user_input.get(CONF_EMAIL), user_input.get(CONF_PASSWORD)
        )

    async def async_step_import(self, user_input):
        """Import a config entry from YAML."""
        return await self._attempt_connection(
            user_input.get(CONF_EMAIL), user_input.get(CONF_PASSWORD)
        )
