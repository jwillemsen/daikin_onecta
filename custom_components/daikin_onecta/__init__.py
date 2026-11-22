"""Platform for the Daikin AC."""

import logging

import aiohttp
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady, OAuth2TokenRequestError, OAuth2TokenRequestReauthError
from homeassistant.helpers import config_entry_oauth2_flow, entity_registry as er
from homeassistant.helpers.config_entry_oauth2_flow import ImplementationUnavailableError
from homeassistant.helpers.typing import ConfigType

from daikin_onecta.auth import get_account_id
from daikin_onecta.exceptions import OnectaAccessTokenError

from .binary_sensor import migrate_legacy_binary_sensor_unique_ids
from .const import DOMAIN
from .coordinator import OnectaDataUpdateCoordinator
from .daikin_api import DaikinApi
from .device import migrate_legacy_entity_unique_ids, migrate_legacy_subdevice_identifiers
from .sensor import migrate_legacy_sensor_unique_ids
from .update import migrate_legacy_update_unique_ids

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [
    Platform.CLIMATE,
    Platform.FAN,
    Platform.SENSOR,
    Platform.WATER_HEATER,
    Platform.SWITCH,
    Platform.SELECT,
    Platform.BINARY_SENSOR,
    Platform.BUTTON,
    Platform.UPDATE,
]


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the Daikin Onecta component."""
    return True


async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Establish connection with Daikin."""
    try:
        implementation = await config_entry_oauth2_flow.async_get_config_entry_implementation(hass, config_entry)
    except ImplementationUnavailableError as err:
        raise ConfigEntryNotReady(
            translation_domain=DOMAIN,
            translation_key="oauth2_implementation_unavailable",
        ) from err

    daikin_api = DaikinApi(hass, config_entry, implementation)

    try:
        await daikin_api.async_get_access_token()
    except OAuth2TokenRequestReauthError as err:
        raise ConfigEntryAuthFailed from err
    except (OAuth2TokenRequestError, aiohttp.ClientError) as err:
        raise ConfigEntryNotReady from err

    config_entry.runtime_data = OnectaDataUpdateCoordinator(hass, config_entry, daikin_api)

    await config_entry.runtime_data.async_config_entry_first_refresh()
    migrate_legacy_subdevice_identifiers(hass, config_entry, config_entry.runtime_data.data or {})
    migrate_legacy_entity_unique_ids(hass, config_entry, config_entry.runtime_data.data or {})
    migrate_legacy_binary_sensor_unique_ids(hass, config_entry, config_entry.runtime_data.data or {})
    migrate_legacy_sensor_unique_ids(hass, config_entry, config_entry.runtime_data.data or {})
    migrate_legacy_update_unique_ids(hass, config_entry)

    config_entry.async_on_unload(config_entry.add_update_listener(update_listener))

    await hass.config_entries.async_forward_entry_setups(config_entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    _LOGGER.debug("Unloading integration")
    return await hass.config_entries.async_unload_platforms(config_entry, PLATFORMS)


async def update_listener(hass: HomeAssistant, config_entry: ConfigEntry) -> None:
    """Handle options update."""
    coordinator: OnectaDataUpdateCoordinator = config_entry.runtime_data
    coordinator.update_settings(config_entry)
    coordinator.async_update_listeners()


async def async_migrate_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Migrate old entry."""
    _LOGGER.info("Migration from version %s.%s", config_entry.version, config_entry.minor_version)

    if config_entry.version == 1:
        if config_entry.minor_version < 2:
            try:
                account_id = get_account_id(config_entry.data["token"]["access_token"])
            except (KeyError, OnectaAccessTokenError):
                _LOGGER.exception("Failed to read the account ID from the OAuth token during migration")
                return False
            hass.config_entries.async_update_entry(
                config_entry,
                minor_version=2,
                unique_id=account_id,
            )

        if config_entry.minor_version < 3:
            if config_entry.unique_id is None:
                try:
                    account_id = get_account_id(config_entry.data["token"]["access_token"])
                except (KeyError, OnectaAccessTokenError):
                    _LOGGER.exception("Failed to read the account ID from the OAuth token during migration")
                    return False
                hass.config_entries.async_update_entry(config_entry, unique_id=account_id)
            else:
                account_id = str(config_entry.unique_id)

            migrate_account_entity_unique_ids(hass, config_entry, account_id)
            hass.config_entries.async_update_entry(config_entry, minor_version=3)

    _LOGGER.info("Migration to version %s.%s successful", config_entry.version, config_entry.minor_version)
    return True


def migrate_account_entity_unique_ids(hass: HomeAssistant, config_entry: ConfigEntry, account_id: str) -> None:
    """Move gateway-specific account entities to the shared account IDs.

    Multiple gateways previously created a refresh button and rate-limit sensor
    for the same account. Keep one registry entry for each account entity and
    remove redundant gateway entries, so Home Assistant Core can reuse them.
    """
    entity_registry = er.async_get(hass)
    entries = er.async_entries_for_config_entry(entity_registry, config_entry.entry_id)

    for domain, suffix, legacy_suffixes in (
        ("button", "_refresh", ("_refresh",)),
        ("sensor", "_rate_limit_remaining_day", ("_rate_limit_remaining_day", "_limitsensor_remaining_day")),
    ):
        target_unique_id = f"{account_id}{suffix}"
        target_entry = entity_registry.async_get_entity_id(domain, DOMAIN, target_unique_id)
        legacy_entries = sorted(
            (
                entry
                for entry in entries
                if entry.domain == domain
                and entry.platform == DOMAIN
                and entry.unique_id.endswith(legacy_suffixes)
                and entry.unique_id != target_unique_id
            ),
            key=lambda entry: (entry.entity_id, entry.unique_id),
        )
        if target_entry is None and legacy_entries:
            entity_registry.async_update_entity(legacy_entries.pop(0).entity_id, new_unique_id=target_unique_id)

        for entry in legacy_entries:
            entity_registry.async_remove(entry.entity_id)
