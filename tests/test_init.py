"""Test daikin_onecta sensor."""
from unittest.mock import AsyncMock
from unittest.mock import patch

import homeassistant.helpers.entity_registry as er
import responses
from homeassistant.components.climate import ATTR_HVAC_MODE
from homeassistant.components.climate import ATTR_FAN_MODE
from homeassistant.components.climate import DOMAIN as CLIMATE_DOMAIN
from homeassistant.components.climate import SERVICE_SET_HVAC_MODE
from homeassistant.components.climate import SERVICE_TURN_OFF
from homeassistant.components.climate import SERVICE_TURN_ON
from homeassistant.components.climate import SERVICE_SET_FAN_MODE
from homeassistant.components.climate.const import HVACMode
from homeassistant.components.water_heater import ATTR_OPERATION_MODE
from homeassistant.components.water_heater import ATTR_TEMPERATURE
from homeassistant.components.water_heater import DOMAIN as WATER_HEATER_DOMAIN
from homeassistant.components.water_heater import SERVICE_SET_OPERATION_MODE
from homeassistant.components.water_heater import SERVICE_SET_TEMPERATURE
from homeassistant.components.water_heater import STATE_HEAT_PUMP
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
async def test_water_heater(
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
        responses.patch(
            DAIKIN_API_URL
            + "/v1/gateway-devices/1ece521b-5401-4a42-acce-6f76fba246aa/management-points/domesticHotWaterTank/characteristics/powerfulMode",
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

        # Set the tank to powerful mode, this should result in two calls, first turn the device
        # on and second to set it to performance
        await hass.services.async_call(
            WATER_HEATER_DOMAIN,
            SERVICE_SET_OPERATION_MODE,
            {ATTR_ENTITY_ID: "water_heater.altherma", ATTR_OPERATION_MODE: STATE_PERFORMANCE},
            blocking=True,
        )
        await hass.async_block_till_done()

        assert len(responses.calls) == 4
        assert responses.calls[2].request.body == '{"value": "on"}'
        assert responses.calls[3].request.body == '{"value": "on"}'
        assert hass.states.get("water_heater.altherma").attributes["operation_mode"] == STATE_PERFORMANCE

        # Set the tank to regular on mode, this should only disable powerful mode
        await hass.services.async_call(
            WATER_HEATER_DOMAIN,
            SERVICE_SET_OPERATION_MODE,
            {ATTR_ENTITY_ID: "water_heater.altherma", ATTR_OPERATION_MODE: STATE_HEAT_PUMP},
            blocking=True,
        )
        await hass.async_block_till_done()

        assert len(responses.calls) == 5
        assert responses.calls[4].request.body == '{"value": "off"}'
        assert hass.states.get("water_heater.altherma").attributes["operation_mode"] == STATE_HEAT_PUMP

        # Turn the tank again off
        await hass.services.async_call(
            WATER_HEATER_DOMAIN,
            SERVICE_SET_OPERATION_MODE,
            {ATTR_ENTITY_ID: "water_heater.altherma", ATTR_OPERATION_MODE: STATE_OFF},
            blocking=True,
        )
        await hass.async_block_till_done()

        assert len(responses.calls) == 6
        assert responses.calls[5].request.body == '{"value": "off"}'
        assert hass.states.get("water_heater.altherma").attributes["operation_mode"] == STATE_OFF

        # Turn the tank again on
        await hass.services.async_call(
            WATER_HEATER_DOMAIN,
            SERVICE_SET_OPERATION_MODE,
            {ATTR_ENTITY_ID: "water_heater.altherma", ATTR_OPERATION_MODE: STATE_HEAT_PUMP},
            blocking=True,
        )
        await hass.async_block_till_done()

        assert len(responses.calls) == 7
        assert responses.calls[6].request.body == '{"value": "on"}'
        assert hass.states.get("water_heater.altherma").attributes["operation_mode"] == STATE_HEAT_PUMP


@responses.activate
async def test_climate(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    onecta_auth: AsyncMock,
    snapshot: SnapshotAssertion,
    entity_registry: er.EntityRegistry,
) -> None:
    """Test entities."""
    await snapshot_platform_entities(hass, config_entry, Platform.SENSOR, entity_registry, snapshot, "altherma")

    assert hass.states.get("climate.werkkamer_room_temperature").state == HVACMode.OFF

    with patch(
        "custom_components.daikin_onecta.DaikinApi.async_get_access_token",
        return_value="XXXXXX",
    ):
        # responses.patch(
        #     DAIKIN_API_URL
        #     + "/v1/gateway-devices/6f944461-08cb-4fee-979c-710ff66cea77/management-points/climateControl/characteristics/temperatureControl",
        #     status=204,
        # )
        responses.patch(
            DAIKIN_API_URL + "/v1/gateway-devices/6f944461-08cb-4fee-979c-710ff66cea77/management-points/climateControl/characteristics/onOffMode",
            status=204,
        )
        responses.patch(
            DAIKIN_API_URL
            + "/v1/gateway-devices/6f944461-08cb-4fee-979c-710ff66cea77/management-points/climateControl/characteristics/operationMode",
            status=204,
        )
        responses.patch(
            DAIKIN_API_URL
            + "/v1/gateway-devices/6f944461-08cb-4fee-979c-710ff66cea77/management-points/climateControl/characteristics/fanControl",
            status=204,
        )

        # Turn on the device, it was in cool mode
        await hass.services.async_call(
            CLIMATE_DOMAIN,
            SERVICE_TURN_ON,
            {ATTR_ENTITY_ID: "climate.werkkamer_room_temperature"},
            blocking=True,
        )
        await hass.async_block_till_done()

        assert len(responses.calls) == 1
        assert responses.calls[0].request.body == '{"value": "on"}'
        assert hass.states.get("climate.werkkamer_room_temperature").state == HVACMode.COOL

        # Turn on the device another time, this shouldn't result in a call to Daikin
        await hass.services.async_call(
            CLIMATE_DOMAIN,
            SERVICE_TURN_ON,
            {ATTR_ENTITY_ID: "climate.werkkamer_room_temperature"},
            blocking=True,
        )
        await hass.async_block_till_done()

        assert len(responses.calls) == 1

        # Turn off the device, it was in cool mode
        await hass.services.async_call(
            CLIMATE_DOMAIN,
            SERVICE_TURN_OFF,
            {ATTR_ENTITY_ID: "climate.werkkamer_room_temperature"},
            blocking=True,
        )
        await hass.async_block_till_done()

        assert len(responses.calls) == 2
        assert responses.calls[1].request.body == '{"value": "off"}'
        assert hass.states.get("climate.werkkamer_room_temperature").state == HVACMode.OFF

        # Turn off the device another time, this shouldn't result in a call to Daikin
        await hass.services.async_call(
            CLIMATE_DOMAIN,
            SERVICE_TURN_OFF,
            {ATTR_ENTITY_ID: "climate.werkkamer_room_temperature"},
            blocking=True,
        )
        await hass.async_block_till_done()

        assert len(responses.calls) == 2

        # Turn on the device in cooling through hvac mode
        await hass.services.async_call(
            CLIMATE_DOMAIN,
            SERVICE_SET_HVAC_MODE,
            {ATTR_ENTITY_ID: "climate.werkkamer_room_temperature", ATTR_HVAC_MODE: HVACMode.COOL},
            blocking=True,
        )
        await hass.async_block_till_done()

        assert len(responses.calls) == 3
        assert responses.calls[2].request.body == '{"value": "on"}'
        assert hass.states.get("climate.werkkamer_room_temperature").state == HVACMode.COOL

        # Change the device to heating
        await hass.services.async_call(
            CLIMATE_DOMAIN,
            SERVICE_SET_HVAC_MODE,
            {ATTR_ENTITY_ID: "climate.werkkamer_room_temperature", ATTR_HVAC_MODE: HVACMode.HEAT},
            blocking=True,
        )
        await hass.async_block_till_done()

        assert len(responses.calls) == 4
        assert responses.calls[3].request.body == '{"value": "heating"}'
        assert hass.states.get("climate.werkkamer_room_temperature").state == HVACMode.HEAT

        # Turn off the device through the hvac mode
        await hass.services.async_call(
            CLIMATE_DOMAIN,
            SERVICE_SET_HVAC_MODE,
            {ATTR_ENTITY_ID: "climate.werkkamer_room_temperature", ATTR_HVAC_MODE: HVACMode.OFF},
            blocking=True,
        )
        await hass.async_block_till_done()

        assert len(responses.calls) == 5
        assert responses.calls[4].request.body == '{"value": "off"}'
        assert hass.states.get("climate.werkkamer_room_temperature").state == HVACMode.OFF

        # Turn on the device, it was in heat mode
        await hass.services.async_call(
            CLIMATE_DOMAIN,
            SERVICE_TURN_ON,
            {ATTR_ENTITY_ID: "climate.werkkamer_room_temperature"},
            blocking=True,
        )
        await hass.async_block_till_done()

        assert len(responses.calls) == 6
        assert responses.calls[5].request.body == '{"value": "on"}'
        assert hass.states.get("climate.werkkamer_room_temperature").state == HVACMode.HEAT

        # Set the fan mode to 1, will first set the fanControl to fixed, after that the value to 1
        await hass.services.async_call(
            CLIMATE_DOMAIN,
            SERVICE_SET_FAN_MODE,
            {ATTR_ENTITY_ID: "climate.werkkamer_room_temperature", ATTR_FAN_MODE: 1},
            blocking=True,
        )
        await hass.async_block_till_done()

        assert len(responses.calls) == 8
        assert responses.calls[6].request.body == '{"value": "fixed", "path": "/operationModes/heating/fanSpeed/currentMode"}'
        assert responses.calls[7].request.body == '{"value": 1, "path": "/operationModes/heating/fanSpeed/modes/fixed"}'
        assert hass.states.get("climate.werkkamer_room_temperature").attributes["fan_mode"] == "1"

        # Set the fan mode to 2, should result in 1 call
        await hass.services.async_call(
            CLIMATE_DOMAIN,
            SERVICE_SET_FAN_MODE,
            {ATTR_ENTITY_ID: "climate.werkkamer_room_temperature", ATTR_FAN_MODE: 2},
            blocking=True,
        )
        await hass.async_block_till_done()

        assert len(responses.calls) == 9
        assert responses.calls[8].request.body == '{"value": 2, "path": "/operationModes/heating/fanSpeed/modes/fixed"}'
        assert hass.states.get("climate.werkkamer_room_temperature").attributes["fan_mode"] == "2"

        # Set the fan mode to auto, should result in 1 call
        await hass.services.async_call(
            CLIMATE_DOMAIN,
            SERVICE_SET_FAN_MODE,
            {ATTR_ENTITY_ID: "climate.werkkamer_room_temperature", ATTR_FAN_MODE: "auto"},
            blocking=True,
        )
        await hass.async_block_till_done()

        assert len(responses.calls) == 10
        assert responses.calls[9].request.body == '{"value": "auto", "path": "/operationModes/heating/fanSpeed/currentMode"}'
        assert hass.states.get("climate.werkkamer_room_temperature").attributes["fan_mode"] == "auto"
