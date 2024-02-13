from homeassistant.core import HomeAssistant
from homeassistant.components.application_credentials import (
    AuthorizationServer,
    ClientCredential,
)
from homeassistant.helpers import config_entry_oauth2_flow
from .daikin_api import DaikinImplementation

async def async_get_auth_implementation(
    hass: HomeAssistant, auth_domain: str, credential: ClientCredential
) -> config_entry_oauth2_flow.AbstractOAuth2Implementation:
    """Return auth implementation for a custom auth implementation."""
    return DaikinImplementation(
        hass,
        auth_domain,
        credential,
        AuthorizationServer(
            authorize_url="https://idp.onecta.daikineurope.com/v1/oidc/authorize",
            token_url="https://idp.onecta.daikineurope.com/v1/oidc/token"
        ),
    )
