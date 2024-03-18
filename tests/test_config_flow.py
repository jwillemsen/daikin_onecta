"""Test the daikin_onecta config flow."""

from unittest.mock import patch

import pytest
from homeassistant import config_entries
from homeassistant.components.application_credentials import (
    async_import_client_credential,
)
from homeassistant.components.application_credentials import ClientCredential
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_entry_oauth2_flow
from homeassistant.setup import async_setup_component

from custom_components.daikin_onecta.const import DOMAIN
from custom_components.daikin_onecta.const import OAUTH2_AUTHORIZE
from custom_components.daikin_onecta.const import OAUTH2_TOKEN

CLIENT_ID = "emU20GdJDiiUxI_HnFGz69dD"
CLIENT_SECRET = "TNL1ePwnOkf6o2gKiI8InS8nVwTz2G__VYkv6WznzJGUnwLHLTmKYp-7RZc6FA3yS6D0Wgj_snvqsU5H_LPHQA"


@pytest.fixture(autouse=True)
async def setup_credentials(hass: HomeAssistant) -> None:
    """Fixture to setup credentials."""
    assert await async_setup_component(hass, "application_credentials", {})
    await async_import_client_credential(
        hass,
        DOMAIN,
        ClientCredential(CLIENT_ID, CLIENT_SECRET),
        DOMAIN,
    )


async def test_full_flow(
    hass: HomeAssistant,
    hass_client_no_auth,
    aioclient_mock,
    current_request_with_host,
    setup_credentials,
) -> None:
    """Check full flow."""
    assert await async_setup_component(hass, "daikin_onecta", {})

    await async_import_client_credential(
        hass, DOMAIN, ClientCredential(CLIENT_ID, CLIENT_SECRET)
    )

    result = await hass.config_entries.flow.async_init(
        "daikin_onecta", context={"source": config_entries.SOURCE_USER}
    )
    state = config_entry_oauth2_flow._encode_jwt(
        hass,
        {
            "flow_id": result["flow_id"],
            "redirect_uri": "https://example.com/auth/external/callback",
        },
    )

    assert result["url"] == (
        f"{OAUTH2_AUTHORIZE}?response_type=code&client_id={CLIENT_ID}"
        "&redirect_uri=https://example.com/auth/external/callback"
        f"&state={state}"
        f"&scope=openid+onecta:basic.integration"
        f"&client_secret={CLIENT_SECRET}"
    )

    client = await hass_client_no_auth()
    resp = await client.get(f"/auth/external/callback?code=abcd&state={state}")
    assert resp.status == 200
    assert resp.headers["content-type"] == "text/html; charset=utf-8"

    aioclient_mock.post(
        OAUTH2_TOKEN,
        json={
            "refresh_token": "mock-refresh-token",
            "access_token": "mock-access-token",
            "type": "Bearer",
            "expires_in": 60,
        },
    )

    with patch(
        "custom_components.daikin_onecta.async_setup_entry", return_value=True
    ) as mock_setup:
        await hass.config_entries.flow.async_configure(result["flow_id"])

    assert len(hass.config_entries.async_entries(DOMAIN)) == 1
    assert len(mock_setup.mock_calls) == 1
