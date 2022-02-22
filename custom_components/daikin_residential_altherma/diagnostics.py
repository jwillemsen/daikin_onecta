"""Diagnostics support for Daikin Diagnostics."""
from __future__ import annotations
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntry

from .const import DOMAIN, DAIKIN_API, DAIKIN_DEVICES


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    data = {}
    daikin_api = hass.data[DOMAIN][DAIKIN_API]
    data["tokenset"] = {**entry.data}
    data["json_data"] = daikin_api.json_data
    return data


async def async_get_device_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry, device: DeviceEntry
) -> dict[str, Any]:
    """Return diagnostics for a device entry."""
    data = {}
    dev_id = next(iter(device.identifiers))[1]
    daikin_device = hass.data[DOMAIN][DAIKIN_DEVICES][dev_id]
    data["device"] = device
    data["device_json_data"] = daikin_device.getDescription()
    return data
