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
    credential.client_id = "emU20GdJDiiUxI_HnFGz69dD"
    credential.client_secret = "TNL1ePwnOkf6o2gKiI8InS8nVwTz2G__VYkv6WznzJGUnwLHLTmKYp-7RZc6FA3yS6D0Wgj_snvqsU5H_LPHQA"

    return DaikinImplementation(
        hass,
        auth_domain,
        credential,
        AuthorizationServer(
            authorize_url="https://idp.onecta.daikineurope.com/v1/oidc/authorize",
            token_url="https://idp.onecta.daikineurope.com/v1/oidc/token"
        ),
    )
