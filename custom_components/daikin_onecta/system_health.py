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
    if entries:
        config_entry = entries[0]
        onecta_data: OnectaRuntimeData = config_entry.runtime_data
        daikin_api = onecta_data.daikin_api
        return {
            "api_status": system_health.async_check_can_reach_url(hass, DAIKIN_API_URL + "/v1/gateway-devices"),
            "oauth2_status": system_health.async_check_can_reach_url(hass, OAUTH2_AUTHORIZE),
            "max_minute": daikin_api.rate_limits["minute"],
            "max_day": daikin_api.rate_limits["day"],
            "remaining_minute": daikin_api.rate_limits["remaining_minutes"],
            "remaining_day": daikin_api.rate_limits["remaining_day"],
            "retry_after": daikin_api.rate_limits["retry_after"],
            "ratelimit_reset": daikin_api.rate_limits["ratelimit_reset"],
            "oauth2_token_valid": daikin_api.session.valid_token,
        }
