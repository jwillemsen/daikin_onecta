"""Test daikin_onecta sensor."""
from unittest.mock import AsyncMock
from unittest.mock import patch

import homeassistant.helpers.entity_registry as er
import responses
from homeassistant.components.water_heater import ATTR_OPERATION_MODE
from homeassistant.components.water_heater import ATTR_TEMPERATURE
from homeassistant.components.water_heater import DOMAIN as WATER_HEATER_DOMAIN
from homeassistant.components.water_heater import SERVICE_SET_OPERATION_MODE
from homeassistant.components.water_heater import SERVICE_SET_TEMPERATURE
from homeassistant.components.water_heater import STATE_PERFORMANCE
from homeassistant.const import ATTR_ENTITY_ID
from homeassistant.const import Platform
from homeassistant.const import STATE_OFF
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry
from syrupy import SnapshotAssertion

from .conftest import snapshot_platform_entities
from custom_components.daikin_onecta.const import DAIKIN_API_URL


async def test_altherma(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    onecta_auth: AsyncMock,
    snapshot: SnapshotAssertion,
    entity_registry: er.EntityRegistry,
) -> None:
    """Test entities."""
    await snapshot_platform_entities(hass, config_entry, Platform.SENSOR, entity_registry, snapshot, "altherma")


async def test_mc80z(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    onecta_auth: AsyncMock,
    snapshot: SnapshotAssertion,
    entity_registry: er.EntityRegistry,
) -> None:
    """Test entities."""
    await snapshot_platform_entities(hass, config_entry, Platform.SENSOR, entity_registry, snapshot, "mc80z")


@responses.activate
async def test_altherma_boost(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    onecta_auth: AsyncMock,
    snapshot: SnapshotAssertion,
    entity_registry: er.EntityRegistry,
) -> None:
    """Test entities."""
    # Altherma with boost enabled
    await snapshot_platform_entities(hass, config_entry, Platform.SENSOR, entity_registry, snapshot, "altherma_boost")

    assert hass.states.get("water_heater.altherma").attributes["operation_mode"] == STATE_PERFORMANCE

    #    device_registry = dr.async_get(hass)
    #    device = device_registry.async_get_device(identifiers={("daikin_onecta", "altherma")})
    #    assert device is not None

    #    assert (
    #    await get_diagnostics_for_device(hass, hass_client, config_entry, device)
    #        == DEVICE_DIAGNOSTIC_DATA
    #    )

    with patch(
        "custom_components.daikin_onecta.DaikinApi.async_get_access_token",
        return_value="XXXXXX",
    ):
        responses.patch(
            DAIKIN_API_URL
            + "/v1/gateway-devices/1ece521b-5401-4a42-acce-6f76fba246aa/management-points/domesticHotWaterTank/characteristics/temperatureControl",
            status=204,
        )
        responses.patch(
            DAIKIN_API_URL
            + "/v1/gateway-devices/1ece521b-5401-4a42-acce-6f76fba246aa/management-points/domesticHotWaterTank/characteristics/onOffMode",
            status=204,
        )

        # Set the tank temperature to 58, this should just work
        await hass.services.async_call(
            WATER_HEATER_DOMAIN,
            SERVICE_SET_TEMPERATURE,
            {ATTR_ENTITY_ID: "water_heater.altherma", ATTR_TEMPERATURE: 58},
            blocking=True,
        )
        await hass.async_block_till_done()

        assert len(responses.calls) == 1
        assert responses.calls[0].request.body == '{"value": 58, "path": "/operationModes/heating/setpoints/domesticHotWaterTemperature"}'
        assert hass.states.get("water_heater.altherma").attributes["temperature"] == 58

        # Set the tank off, this should just work
        await hass.services.async_call(
            WATER_HEATER_DOMAIN,
            SERVICE_SET_OPERATION_MODE,
            {ATTR_ENTITY_ID: "water_heater.altherma", ATTR_OPERATION_MODE: STATE_OFF},
            blocking=True,
        )
        await hass.async_block_till_done()

        assert len(responses.calls) == 2
        assert responses.calls[1].request.body == '{"value": "off"}'
        assert hass.states.get("water_heater.altherma").attributes["operation_mode"] == STATE_OFF

        # Set the tank temperature to 54, because the tank is off no call should be done to Daikin
        await hass.services.async_call(
            WATER_HEATER_DOMAIN,
            SERVICE_SET_TEMPERATURE,
            {ATTR_ENTITY_ID: "water_heater.altherma", ATTR_TEMPERATURE: 54},
            blocking=True,
        )
        await hass.async_block_till_done()

        assert len(responses.calls) == 2
        assert hass.states.get("water_heater.altherma").attributes["temperature"] == 58
