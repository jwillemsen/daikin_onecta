"""Provide info to system health."""
from __future__ import annotations

from typing import Any

from homeassistant.components import system_health
from homeassistant.core import callback
from homeassistant.core import HomeAssistant

from .const import DAIKIN_API_URL
from .const import DOMAIN
from .const import OAUTH2_AUTHORIZE
from .coordinator import OnectaRuntimeData


@callback
def async_register(hass: HomeAssistant, register: system_health.SystemHealthRegistration) -> None:
    """Register system health callbacks."""
    register.async_register_info(system_health_info)


async def system_health_info(hass: HomeAssistant) -> dict[str, Any]:
    """Get info for the info page."""
    entries = hass.config_entries.async_entries(DOMAIN)
    if not entries:
        return {"error": "Integration not configured"}
    config_entry = entries[0]
    onecta_data: OnectaRuntimeData = config_entry.runtime_data
    daikin_api = onecta_data.daikin_api
    return {
        "Daikin API server": system_health.async_check_can_reach_url(hass, DAIKIN_API_URL + "/v1/gateway-devices"),
        "Daikin OAuth server": system_health.async_check_can_reach_url(hass, OAUTH2_AUTHORIZE),
        "Minute": daikin_api.rate_limits["minute"],
        "Day": daikin_api.rate_limits["day"],
        "Remaining minute": daikin_api.rate_limits["remaining_minutes"],
        "Remaining day": daikin_api.rate_limits["remaining_day"],
        "Retry after": daikin_api.rate_limits["retry_after"],
        "Ratelimit reset": daikin_api.rate_limits["ratelimit_reset"],
    }
