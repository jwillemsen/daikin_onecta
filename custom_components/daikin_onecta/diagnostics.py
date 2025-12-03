"""Diagnostics support for Daikin Diagnostics."""
from __future__ import annotations

from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.device_registry import DeviceEntry

from .coordinator import OnectaRuntimeData


async def async_get_config_entry_diagnostics(hass: HomeAssistant, config_entry: ConfigEntry) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    entity_registry = er.async_get(hass)
    entities_data: dict[str, dict[str, Any]] = {}

    for entity_entry in er.async_entries_for_config_entry(entity_registry, config_entry.entry_id):
        entity_id = entity_entry.entity_id
        state = hass.states.get(entity_id)

        entity_info: dict[str, Any] = {
            "entity_id": entity_id,
            "unique_id": entity_entry.unique_id,
            "platform": entity_entry.platform,
            "original_name": entity_entry.original_name,
            "disabled": entity_entry.disabled,
            "translation_key": entity_entry.translation_key,
        }

        if state:
            entity_info["state"] = state.state
            entity_info["attributes"] = dict(state.attributes)

        entities_data[entity_id] = entity_info

    onecta_data: OnectaRuntimeData = config_entry.runtime_data
    daikin_api = onecta_data.daikin_api
    return {
        "json_data": daikin_api.json_data,
        "rate_limits": daikin_api.rate_limits,
        "options": config_entry.options,
        "oauth2_token_valid": daikin_api.session.valid_token,
        "entities": entities_data,
    }


async def async_get_device_diagnostics(hass: HomeAssistant, config_entry: ConfigEntry, device: DeviceEntry) -> dict[str, Any]:
    """Return diagnostics for a device entry."""
    data = {}
    dev_id = next(iter(device.identifiers))[1]
    onecta_data: OnectaRuntimeData = config_entry.runtime_data
    daikin_api = onecta_data.daikin_api
    daikin_device = onecta_data.devices.get(dev_id)
    if daikin_device is not None:
        data["device_json_data"] = daikin_device.daikin_data
    data["rate_limits"] = daikin_api.rate_limits
    data["options"] = config_entry.options
    data["oauth2_token_valid"] = daikin_api.session.valid_token
    return data
