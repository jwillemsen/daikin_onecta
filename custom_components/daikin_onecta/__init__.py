"""Platform for the Daikin AC."""
import asyncio
import datetime
import logging
import voluptuous as vol
from aiohttp import ClientError
from datetime import date, datetime, timedelta

from homeassistant.config_entries import SOURCE_IMPORT, ConfigEntry
from homeassistant.const import SERVICE_RELOAD
from homeassistant.helpers.typing import HomeAssistantType
from homeassistant.helpers import config_entry_oauth2_flow
from homeassistant.exceptions import ConfigEntryNotReady

from .const import DOMAIN, DAIKIN_API, DAIKIN_DEVICES, COORDINATOR

from .daikin_api import DaikinApi

from .coordinator import OnectaDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

PARALLEL_UPDATES = 0

SERVICE_FORCE_UPDATE = "force_update"
SERVICE_PULL_DEVICES = "pull_devices"

SIGNAL_DELETE_ENTITY = "daikin_delete"
SIGNAL_UPDATE_ENTITY = "daikin_update"

COMPONENT_TYPES = ["climate", "sensor", "water_heater", "switch", "select"]

async def async_setup(hass, config):
    """Setup the Daikin Onecta component."""

    async def _handle_reload(service):
        """Handle reload service call."""
        _LOGGER.info("Reloading integration: retrieving new TokenSet.")
        try:
            daikin_api = hass.data[DOMAIN][DAIKIN_API]
            data = daikin_api._config_entry.data.copy()
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

async def async_setup_entry(hass: HomeAssistantType, config_entry: ConfigEntry):
    """Establish connection with Daikin."""
    implementation = (
        await config_entry_oauth2_flow.async_get_config_entry_implementation(
            hass, config_entry
        )
    )

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

    for component in COMPONENT_TYPES:
        hass.async_create_task(
            hass.config_entries.async_forward_entry_setup(config_entry, component)
        )

    return True

async def async_unload_entry(hass, config_entry):
    """Unload a config entry."""
    _LOGGER.debug("Unloading integration...")
    await asyncio.gather(
        *(
            hass.config_entries.async_forward_entry_unload(config_entry, component)
            for component in COMPONENT_TYPES
        )
    )
    hass.data[DOMAIN].clear()
    if not hass.data[DOMAIN]:
        hass.data.pop(DOMAIN)
    return True


async def daikin_api_setup(hass, host, key, uuid, password):
    """Create a Daikin instance only once."""
    return

async def update_listener(hass, config_entry):
    """Handle options update."""
    coordinator = hass.data[DOMAIN][COORDINATOR]
    val = config_entry.options.get("high_scan_interval", 10)
    scan_interval = timedelta(minutes=val)
    _LOGGER.info("Daikin coordinator changing interval to %s", scan_interval)
    coordinator.update_interval = scan_interval
