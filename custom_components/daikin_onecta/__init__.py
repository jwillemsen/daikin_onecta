"""Platform for the Daikin AC."""
import asyncio
import logging

from aiohttp import ClientError
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers import config_entry_oauth2_flow

from .const import COORDINATOR
from .const import DAIKIN_API
from .const import DAIKIN_DEVICES
from .const import DOMAIN
from .coordinator import OnectaDataUpdateCoordinator
from .daikin_api import DaikinApi

_LOGGER = logging.getLogger(__name__)

PARALLEL_UPDATES = 0

SERVICE_FORCE_UPDATE = "force_update"
SERVICE_PULL_DEVICES = "pull_devices"

SIGNAL_DELETE_ENTITY = "daikin_delete"
SIGNAL_UPDATE_ENTITY = "daikin_update"

COMPONENT_TYPES = ["climate", "sensor", "water_heater", "switch", "select", "binary_sensor", "button"]


async def async_setup(hass, config):
    """Setup the Daikin Onecta component."""
    return True


async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Establish connection with Daikin."""
    implementation = await config_entry_oauth2_flow.async_get_config_entry_implementation(hass, config_entry)

    hass.data.update({DOMAIN: {}})
    hass.data[DOMAIN][DAIKIN_DEVICES] = {}
    daikin_api = DaikinApi(hass, config_entry, implementation)
    hass.data[DOMAIN][DAIKIN_API] = daikin_api

    try:
        await daikin_api.async_get_access_token()
    except ClientError as err:
        raise ConfigEntryNotReady from err

    coordinator = OnectaDataUpdateCoordinator(hass, config_entry)
    hass.data[DOMAIN][COORDINATOR] = coordinator

    try:
        await coordinator.async_config_entry_first_refresh()
    except Exception as ex:
        raise ConfigEntryNotReady(f"Config Not Ready: {ex}")

    config_entry.async_on_unload(config_entry.add_update_listener(update_listener))

    await hass.config_entries.async_forward_entry_setups(config_entry, COMPONENT_TYPES)

    return True


async def async_unload_entry(hass, config_entry):
    """Unload a config entry."""
    _LOGGER.debug("Unloading integration...")
    await asyncio.gather(*(hass.config_entries.async_forward_entry_unload(config_entry, component) for component in COMPONENT_TYPES))
    hass.data[DOMAIN].clear()
    if not hass.data[DOMAIN]:
        hass.data.pop(DOMAIN)
    return True


async def update_listener(hass, config_entry):
    """Handle options update."""
    coordinator = hass.data[DOMAIN][COORDINATOR]
    coordinator.update_settings(config_entry)
