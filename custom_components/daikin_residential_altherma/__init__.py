"""Platform for the Daikin AC."""
import asyncio
import datetime
import logging
import voluptuous as vol

from homeassistant.config_entries import SOURCE_IMPORT, ConfigEntry
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD, SERVICE_RELOAD
from homeassistant.helpers.typing import HomeAssistantType

from .const import DOMAIN, DAIKIN_API, DAIKIN_DEVICES, CONF_TOKENSET

from .daikin_api import DaikinApi

_LOGGER = logging.getLogger(__name__)

ENTRY_IS_SETUP = "daikin_entry_is_setup"

PARALLEL_UPDATES = 0

SERVICE_FORCE_UPDATE = "force_update"
SERVICE_PULL_DEVICES = "pull_devices"

SIGNAL_DELETE_ENTITY = "daikin_delete"
SIGNAL_UPDATE_ENTITY = "daikin_update"

TOKENSET_FILE = "tokenset.json"

MIN_TIME_BETWEEN_UPDATES = datetime.timedelta(seconds=2)

COMPONENT_TYPES = ["climate", "sensor", "switch"]


CONFIG_SCHEMA = vol.Schema(
    vol.All(
        {
            DOMAIN: vol.Schema(
                {vol.Required(CONF_EMAIL): str, vol.Required(CONF_PASSWORD): str}
            )
        }
    ),
    extra=vol.ALLOW_EXTRA,
)


async def async_setup(hass, config):
    """Setup the Daikin Residential component."""

    async def _handle_reload(service):
        """Handle reload service call."""
        _LOGGER.info("Reloading integration: retrieving new TokenSet.")
        try:
            daikin_api = hass.data[DOMAIN][DAIKIN_API]
            data = daikin_api._config_entry.data.copy()
            await daikin_api.retrieveAccessToken(data[CONF_EMAIL], data[CONF_PASSWORD])
            data[CONF_TOKENSET] = daikin_api.tokenSet
            hass.config_entries.async_update_entry(
                entry=daikin_api._config_entry, data=data
            )
        except Exception as e:
            _LOGGER.error("Failed to reload integration: %s", e)

    hass.helpers.service.async_register_admin_service(
        DOMAIN, SERVICE_RELOAD, _handle_reload
    )

    if DOMAIN not in config:
        return True

    conf = config.get(DOMAIN)
    if conf is not None:
        hass.async_create_task(
            hass.config_entries.flow.async_init(
                DOMAIN, context={"source": SOURCE_IMPORT}, data=conf
            )
        )

    return True


async def async_setup_entry(hass: HomeAssistantType, entry: ConfigEntry):
    """Establish connection with Daikin."""

    daikin_api = DaikinApi(hass, entry)
    await daikin_api.getCloudDeviceDetails()

    devices = await daikin_api.getCloudDevices()
    hass.data[DOMAIN] = {DAIKIN_API: daikin_api, DAIKIN_DEVICES: devices}

    for component in COMPONENT_TYPES:
        hass.async_create_task(
            hass.config_entries.async_forward_entry_setup(entry, component)
        )
    return True


async def async_unload_entry(hass, config_entry):
    """Unload a config entry."""
    _LOGGER.debug("Unloading integration...")
    await asyncio.wait(
        [
            hass.config_entries.async_forward_entry_unload(config_entry, component)
            for component in COMPONENT_TYPES
        ]
    )
    hass.data[DOMAIN].clear()
    if not hass.data[DOMAIN]:
        hass.data.pop(DOMAIN)
    return True


async def daikin_api_setup(hass, host, key, uuid, password):
    """Create a Daikin instance only once."""
    return
