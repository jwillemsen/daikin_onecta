"""Diagnostics support for Daikin Diagnostics."""
from __future__ import annotations

from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntry

from .const import DAIKIN_API
from .const import DAIKIN_DEVICES
from .const import DOMAIN


async def async_get_config_entry_diagnostics(hass: HomeAssistant, config_entry: ConfigEntry) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    daikin_api = hass.data[DOMAIN][DAIKIN_API]
    return {
        "json_data": daikin_api.json_data,
        "rate_limits": daikin_api.rate_limits,
        "options": config_entry.options,
        "oauth2_token_valid": daikin_api.session.valid_token,
    }


async def async_get_device_diagnostics(hass: HomeAssistant, config_entry: ConfigEntry, device: DeviceEntry) -> dict[str, Any]:
    """Return diagnostics for a device entry."""
    data = {}
    dev_id = next(iter(device.identifiers))[1]
    daikin_api = hass.data[DOMAIN][DAIKIN_API]
    daikin_device = hass.data[DOMAIN][DAIKIN_DEVICES].get(dev_id)
    if daikin_device is not None:
        data["device_json_data"] = daikin_device.daikin_data
    data["rate_limits"] = daikin_api.rate_limits
    data["options"] = config_entry.options
    data["oauth2_token_valid"] = daikin_api.session.valid_token
    return data
