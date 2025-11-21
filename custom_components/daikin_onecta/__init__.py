"""Platform for the Daikin AC."""
import asyncio
import logging

from aiohttp import ClientError
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers import config_entry_oauth2_flow

from .coordinator import OnectaDataUpdateCoordinator
from .coordinator import OnectaRuntimeData
from .daikin_api import DaikinApi

_LOGGER = logging.getLogger(__name__)

COMPONENT_TYPES = ["climate", "sensor", "water_heater", "switch", "select", "binary_sensor", "button"]


async def async_setup(hass, config):
    """Setup the Daikin Onecta component."""
    return True


async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Establish connection with Daikin."""
    implementation = await config_entry_oauth2_flow.async_get_config_entry_implementation(hass, config_entry)

    daikin_api = DaikinApi(hass, config_entry, implementation)

    try:
        await daikin_api.async_get_access_token()
    except ClientError as err:
        raise ConfigEntryNotReady from err

    config_entry.runtime_data = OnectaRuntimeData(coordinator=None, daikin_api=daikin_api, devices={})
    config_entry.runtime_data.coordinator = OnectaDataUpdateCoordinator(hass, config_entry)

    try:
        await config_entry.runtime_data.coordinator.async_config_entry_first_refresh()
    except Exception as ex:
        raise ConfigEntryNotReady(f"Config Not Ready: {ex}")

    config_entry.async_on_unload(config_entry.add_update_listener(update_listener))

    await hass.config_entries.async_forward_entry_setups(config_entry, COMPONENT_TYPES)

    return True


async def async_unload_entry(hass, config_entry):
    """Unload a config entry."""
    _LOGGER.debug("Unloading integration...")
    await asyncio.gather(*(hass.config_entries.async_forward_entry_unload(config_entry, component) for component in COMPONENT_TYPES))
    return True


async def update_listener(hass, config_entry):
    """Handle options update."""
    onecta_data: OnectaRuntimeData = config_entry.runtime_data
    coordinator = onecta_data.coordinator
    coordinator.update_settings(config_entry)
