"""Test daikin_onecta sensor."""
from datetime import date
from datetime import timedelta
from unittest.mock import AsyncMock
from unittest.mock import patch

import homeassistant.helpers.device_registry as dr
import homeassistant.helpers.entity_registry as er
import pytest
from homeassistant.components.button import DOMAIN as BUTTON_DOMAIN
from homeassistant.components.button import SERVICE_PRESS
from homeassistant.components.climate import ATTR_FAN_MODE
from homeassistant.components.climate import ATTR_HVAC_MODE
from homeassistant.components.climate import ATTR_PRESET_MODE
from homeassistant.components.climate import ATTR_SWING_HORIZONTAL_MODE
from homeassistant.components.climate import ATTR_SWING_MODE
from homeassistant.components.climate import DOMAIN as CLIMATE_DOMAIN
from homeassistant.components.climate import PRESET_AWAY
from homeassistant.components.climate import PRESET_BOOST
from homeassistant.components.climate import PRESET_NONE
from homeassistant.components.climate import SERVICE_SET_FAN_MODE
from homeassistant.components.climate import SERVICE_SET_HVAC_MODE
from homeassistant.components.climate import SERVICE_SET_PRESET_MODE
from homeassistant.components.climate import SERVICE_SET_SWING_HORIZONTAL_MODE
from homeassistant.components.climate import SERVICE_SET_SWING_MODE
from homeassistant.components.climate import SERVICE_TURN_OFF
from homeassistant.components.climate import SERVICE_TURN_ON
from homeassistant.components.climate.const import HVACMode
from homeassistant.components.homeassistant import DOMAIN as HA_DOMAIN
from homeassistant.components.homeassistant import SERVICE_UPDATE_ENTITY
from homeassistant.components.select import ATTR_OPTION
from homeassistant.components.select import DOMAIN as SELECT_DOMAIN
from homeassistant.components.select import SERVICE_SELECT_OPTION
from homeassistant.components.switch import DOMAIN as SWITCH_DOMAIN
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
from homeassistant.const import STATE_ON
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component
from pytest_homeassistant_custom_component.common import MockConfigEntry
from pytest_homeassistant_custom_component.test_util.aiohttp import AiohttpClientMocker
from pytest_homeassistant_custom_component.test_util.aiohttp import URL
from syrupy import SnapshotAssertion

from .conftest import load_fixture_json
from .conftest import snapshot_platform_entities
from custom_components.daikin_onecta.const import DAIKIN_API_URL
from custom_components.daikin_onecta.const import SCHEDULE_OFF
from custom_components.daikin_onecta.coordinator import OnectaRuntimeData
from custom_components.daikin_onecta.diagnostics import async_get_config_entry_diagnostics
from custom_components.daikin_onecta.diagnostics import async_get_device_diagnostics
from custom_components.daikin_onecta.system_health import system_health_info


async def test_homehub(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    onecta_auth: AsyncMock,
    snapshot: SnapshotAssertion,
    entity_registry: er.EntityRegistry,
    aioclient_mock: AiohttpClientMocker,
) -> None:
    """Test entities."""
    await snapshot_platform_entities(hass, aioclient_mock, config_entry, Platform.SENSOR, entity_registry, snapshot, "homehub")

    info = await system_health_info(hass)

    assert info["max_minute"] == 0


async def test_offlinedevice(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    onecta_auth: AsyncMock,
    snapshot: SnapshotAssertion,
    entity_registry: er.EntityRegistry,
    aioclient_mock: AiohttpClientMocker,
) -> None:
    """Test entities."""
    await snapshot_platform_entities(hass, aioclient_mock, config_entry, Platform.SENSOR, entity_registry, snapshot, "offlinedevice")


async def test_dry(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    onecta_auth: AsyncMock,
    snapshot: SnapshotAssertion,
    entity_registry: er.EntityRegistry,
    aioclient_mock: AiohttpClientMocker,
) -> None:
    """Test entities."""
    await snapshot_platform_entities(hass, aioclient_mock, config_entry, Platform.SENSOR, entity_registry, snapshot, "dry")

    assert hass.states.get("climate.lounge_room_temperature").state == HVACMode.DRY


@pytest.mark.asyncio
async def test_fanmode(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    onecta_auth: AsyncMock,
    snapshot: SnapshotAssertion,
    entity_registry: er.EntityRegistry,
    aioclient_mock: AiohttpClientMocker,
) -> None:
    """Test entities."""
    await snapshot_platform_entities(hass, aioclient_mock, config_entry, Platform.SENSOR, entity_registry, snapshot, "fanmode")

    with patch(
        "custom_components.daikin_onecta.DaikinApi.async_get_access_token",
        return_value="XXXXXX",
    ):
        assert hass.states.get("climate.Sala_room_temperature").state == HVACMode.OFF
        assert hass.states.get("climate.Sala_room_temperature").attributes["fan_mode"] == "auto"

        aioclient_mock.patch(
            DAIKIN_API_URL + "/v1/gateway-devices/13995b32-fc6e-43ed-918e-5d2b01095ccb/management-points/climateControl/characteristics/onOffMode",
            status=204,
        )
        aioclient_mock.patch(
            DAIKIN_API_URL
            + "/v1/gateway-devices/13995b32-fc6e-43ed-918e-5d2b01095ccb/management-points/climateControl/characteristics/operationMode",
            status=204,
        )

        await hass.services.async_call(
            CLIMATE_DOMAIN,
            SERVICE_SET_HVAC_MODE,
            {ATTR_ENTITY_ID: "climate.Sala_room_temperature", ATTR_HVAC_MODE: HVACMode.COOL},
            blocking=True,
        )
        await hass.async_block_till_done()
        assert len(aioclient_mock.mock_calls) == 3

        assert hass.states.get("climate.Sala_room_temperature").state == HVACMode.COOL
        assert hass.states.get("climate.Sala_room_temperature").attributes["fan_mode"] == "3"

        aioclient_mock.patch(
            DAIKIN_API_URL
            + "/v1/gateway-devices/13995b32-fc6e-43ed-918e-5d2b01095ccb/management-points/climateControl/characteristics/operationMode",
            status=204,
        )

        await hass.services.async_call(
            CLIMATE_DOMAIN,
            SERVICE_SET_HVAC_MODE,
            {ATTR_ENTITY_ID: "climate.Sala_room_temperature", ATTR_HVAC_MODE: HVACMode.DRY},
            blocking=True,
        )
        await hass.async_block_till_done()
        assert len(aioclient_mock.mock_calls) == 4

        assert hass.states.get("climate.Sala_room_temperature").state == HVACMode.DRY
        assert hass.states.get("climate.Sala_room_temperature").attributes["fan_mode"] == "auto"

        await hass.services.async_call(
            CLIMATE_DOMAIN,
            SERVICE_SET_HVAC_MODE,
            {ATTR_ENTITY_ID: "climate.Sala_room_temperature", ATTR_HVAC_MODE: HVACMode.COOL},
            blocking=True,
        )
        await hass.async_block_till_done()
        assert len(aioclient_mock.mock_calls) == 5

        assert hass.states.get("climate.Sala_room_temperature").state == HVACMode.COOL
        assert hass.states.get("climate.Sala_room_temperature").attributes["fan_mode"] == "3"

        await hass.services.async_call(
            CLIMATE_DOMAIN,
            SERVICE_SET_HVAC_MODE,
            {ATTR_ENTITY_ID: "climate.Sala_room_temperature", ATTR_HVAC_MODE: HVACMode.HEAT},
            blocking=True,
        )
        await hass.async_block_till_done()
        assert len(aioclient_mock.mock_calls) == 6

        assert hass.states.get("climate.Sala_room_temperature").state == HVACMode.HEAT
        assert hass.states.get("climate.Sala_room_temperature").attributes["fan_mode"] == "auto"

        await hass.services.async_call(
            CLIMATE_DOMAIN,
            SERVICE_SET_HVAC_MODE,
            {ATTR_ENTITY_ID: "climate.Sala_room_temperature", ATTR_HVAC_MODE: HVACMode.DRY},
            blocking=True,
        )
        await hass.async_block_till_done()
        assert len(aioclient_mock.mock_calls) == 7

        assert hass.states.get("climate.Sala_room_temperature").state == HVACMode.DRY
        assert hass.states.get("climate.Sala_room_temperature").attributes["fan_mode"] == "auto"


async def test_dry2(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    onecta_auth: AsyncMock,
    snapshot: SnapshotAssertion,
    entity_registry: er.EntityRegistry,
    aioclient_mock: AiohttpClientMocker,
) -> None:
    """Test entities."""
    await snapshot_platform_entities(hass, aioclient_mock, config_entry, Platform.SENSOR, entity_registry, snapshot, "dry2")

    assert hass.states.get("climate.bedroom_3_room_temperature").state == HVACMode.OFF


async def test_schedule(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    onecta_auth: AsyncMock,
    snapshot: SnapshotAssertion,
    entity_registry: er.EntityRegistry,
    aioclient_mock: AiohttpClientMocker,
) -> None:
    """Test entities."""
    await snapshot_platform_entities(hass, aioclient_mock, config_entry, Platform.SENSOR, entity_registry, snapshot, "schedule")

    assert hass.states.get("select.master_climatecontrol_schedule").state == "off"


async def test_ururu(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    onecta_auth: AsyncMock,
    snapshot: SnapshotAssertion,
    entity_registry: er.EntityRegistry,
    aioclient_mock: AiohttpClientMocker,
) -> None:
    """Test entities."""
    await snapshot_platform_entities(hass, aioclient_mock, config_entry, Platform.SENSOR, entity_registry, snapshot, "ururu")

    assert hass.states.get("climate.daikinap95800_room_temperature").state == HVACMode.HEAT


async def test_altherma(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    onecta_auth: AsyncMock,
    snapshot: SnapshotAssertion,
    entity_registry: er.EntityRegistry,
    aioclient_mock: AiohttpClientMocker,
) -> None:
    """Test entities."""
    await snapshot_platform_entities(hass, aioclient_mock, config_entry, Platform.SENSOR, entity_registry, snapshot, "altherma")


async def test_altherma3m(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    onecta_auth: AsyncMock,
    snapshot: SnapshotAssertion,
    entity_registry: er.EntityRegistry,
    aioclient_mock: AiohttpClientMocker,
) -> None:
    """Test entities."""
    await snapshot_platform_entities(hass, aioclient_mock, config_entry, Platform.SENSOR, entity_registry, snapshot, "altherma3m")

    assert hass.states.get("climate.altherma_leaving_water_offset").attributes["min_temp"] == -10
    assert hass.states.get("climate.altherma_leaving_water_offset").attributes["max_temp"] == 10
    assert hass.states.get("climate.altherma_leaving_water_offset").attributes["current_temperature"] == 25
    assert hass.states.get("climate.altherma_leaving_water_offset").attributes["temperature"] == 0


@pytest.mark.asyncio
async def test_altherma_ratelimit(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    onecta_auth: AsyncMock,
    snapshot: SnapshotAssertion,
    entity_registry: er.EntityRegistry,
    aioclient_mock: AiohttpClientMocker,
) -> None:
    """Test entities."""
    await snapshot_platform_entities(hass, aioclient_mock, config_entry, Platform.SENSOR, entity_registry, snapshot, "altherma")

    patch_url = (
        DAIKIN_API_URL + "/v1/gateway-devices/1ece521b-5401-4a42-acce-6f76fba246aa/"
        "management-points/domesticHotWaterTank/characteristics/temperatureControl"
    )

    with patch(
        "custom_components.daikin_onecta.DaikinApi.async_get_access_token",
        return_value="XXXXXX",
    ):
        aioclient_mock.patch(
            patch_url,
            status=429,
            headers={"X-RateLimit-Limit-minute": "0", "X-RateLimit-Limit-day": "0"},
        )

        temp = hass.states.get("water_heater.altherma").attributes["temperature"]

        info = await system_health_info(hass)

        assert info["max_minute"] == 0
        assert info["max_day"] == 0

        # Set the tank temperature to 58, but this should fail because of a rate limit
        await hass.services.async_call(
            WATER_HEATER_DOMAIN,
            SERVICE_SET_TEMPERATURE,
            {ATTR_ENTITY_ID: "water_heater.altherma", ATTR_TEMPERATURE: 58},
            blocking=True,
        )
        await hass.async_block_till_done()

        assert len(aioclient_mock.mock_calls) == 2

        assert aioclient_mock.mock_calls[1][2] == '{"value": 58, "path": "/operationModes/heating/setpoints/domesticHotWaterTemperature"}'
        assert hass.states.get("water_heater.altherma").attributes["temperature"] == temp

        aioclient_mock.get(DAIKIN_API_URL + "/v1/gateway-devices", status=429)

        # Test that updating the data through with a 429 doesn't crash
        onecta_data: OnectaRuntimeData = config_entry.runtime_data
        coordinator = onecta_data.coordinator
        await coordinator._async_update_data()

        aioclient_mock.get(DAIKIN_API_URL + "/v1/gateway-devices", status=200, json=load_fixture_json("altherma"))

        # Test that updating the data through with a status 200 works
        onecta_data: OnectaRuntimeData = config_entry.runtime_data
        coordinator = onecta_data.coordinator
        await coordinator._async_update_data()


async def test_climate_fixedfanmode(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    onecta_auth: AsyncMock,
    snapshot: SnapshotAssertion,
    entity_registry: er.EntityRegistry,
    aioclient_mock: AiohttpClientMocker,
) -> None:
    """Test entities."""
    await snapshot_platform_entities(hass, aioclient_mock, config_entry, Platform.SENSOR, entity_registry, snapshot, "climate_fixedfanmode")

    assert hass.states.get("climate.werkkamer_room_temperature").attributes["fan_mode"] == "3"


async def test_climate_floorheatingairflow(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    onecta_auth: AsyncMock,
    snapshot: SnapshotAssertion,
    entity_registry: er.EntityRegistry,
    aioclient_mock: AiohttpClientMocker,
) -> None:
    """Test entities."""
    await snapshot_platform_entities(hass, aioclient_mock, config_entry, Platform.SENSOR, entity_registry, snapshot, "climate_floorheatingairflow")


async def test_mc80z(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    onecta_auth: AsyncMock,
    snapshot: SnapshotAssertion,
    entity_registry: er.EntityRegistry,
    aioclient_mock: AiohttpClientMocker,
) -> None:
    """Test entities."""
    await snapshot_platform_entities(hass, aioclient_mock, config_entry, Platform.SENSOR, entity_registry, snapshot, "mc80z")

    assert hass.states.get("climate.vloerverwarming_leaving_water_offset").attributes["current_temperature"] == 25
    assert hass.states.get("climate.vloerverwarming_leaving_water_offset").attributes["temperature"] == -3


async def test_holidaymode(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    onecta_auth: AsyncMock,
    snapshot: SnapshotAssertion,
    entity_registry: er.EntityRegistry,
    aioclient_mock: AiohttpClientMocker,
) -> None:
    """Test entities."""
    await snapshot_platform_entities(hass, aioclient_mock, config_entry, Platform.SENSOR, entity_registry, snapshot, "holidaymode")

    assert hass.states.get("climate.ndj_room_temperature").attributes["preset_mode"] == PRESET_AWAY


@pytest.mark.asyncio
async def test_water_heater(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    onecta_auth: AsyncMock,
    snapshot: SnapshotAssertion,
    entity_registry: er.EntityRegistry,
    aioclient_mock: AiohttpClientMocker,
) -> None:
    """Test entities."""
    # Altherma with boost enabled
    await snapshot_platform_entities(hass, aioclient_mock, config_entry, Platform.SENSOR, entity_registry, snapshot, "altherma_boost")

    ce_diag = await async_get_config_entry_diagnostics(hass, config_entry)
    device_registry = dr.async_get(hass)
    device = device_registry.async_get_device(identifiers={("daikin_onecta", "1ece521b-5401-4a42-acce-6f76fba246aa")})
    assert device is not None
    device_diag = await async_get_device_diagnostics(hass, config_entry, device)

    assert ce_diag["json_data"] != ""
    assert ce_diag["rate_limits"] != ""
    assert ce_diag["options"] != ""
    assert ce_diag["oauth2_token_valid"] != ""

    assert device_diag["device_json_data"] != ""
    assert device_diag["rate_limits"] != ""
    assert device_diag["options"] != ""
    assert device_diag["oauth2_token_valid"] != ""

    assert hass.states.get("water_heater.altherma").attributes["operation_mode"] == STATE_PERFORMANCE

    with patch(
        "custom_components.daikin_onecta.DaikinApi.async_get_access_token",
        return_value="XXXXXX",
    ):
        aioclient_mock.patch(
            DAIKIN_API_URL
            + "/v1/gateway-devices/1ece521b-5401-4a42-acce-6f76fba246aa/management-points/domesticHotWaterTank/characteristics/temperatureControl",
            status=204,
            headers={"X-RateLimit-Remaining-minute": "4", "X-RateLimit-Remaining-day": "10"},
        )

        # Set the tank temperature to 58, this should just work
        await hass.services.async_call(
            WATER_HEATER_DOMAIN,
            SERVICE_SET_TEMPERATURE,
            {ATTR_ENTITY_ID: "water_heater.altherma", ATTR_TEMPERATURE: 58},
            blocking=True,
        )
        await hass.async_block_till_done()

        info = await system_health_info(hass)

        assert info["remaining_minute"] == 4
        assert info["remaining_day"] == 10

        assert len(aioclient_mock.mock_calls) == 2
        assert aioclient_mock.mock_calls[1][2] == '{"value": 58, "path": "/operationModes/heating/setpoints/domesticHotWaterTemperature"}'
        assert hass.states.get("water_heater.altherma").attributes["temperature"] == 58

        # Set the tank temperature to 58, this should not result in a call as it is already 58
        await hass.services.async_call(
            WATER_HEATER_DOMAIN,
            SERVICE_SET_TEMPERATURE,
            {ATTR_ENTITY_ID: "water_heater.altherma", ATTR_TEMPERATURE: 58},
            blocking=True,
        )
        await hass.async_block_till_done()

        assert len(aioclient_mock.mock_calls) == 2

        aioclient_mock.patch(
            DAIKIN_API_URL
            + "/v1/gateway-devices/1ece521b-5401-4a42-acce-6f76fba246aa/management-points/domesticHotWaterTank/characteristics/onOffMode",
            status=204,
        )

        # Set the tank off, this should just work
        await hass.services.async_call(
            WATER_HEATER_DOMAIN,
            SERVICE_SET_OPERATION_MODE,
            {ATTR_ENTITY_ID: "water_heater.altherma", ATTR_OPERATION_MODE: STATE_OFF},
            blocking=True,
        )
        await hass.async_block_till_done()

        assert len(aioclient_mock.mock_calls) == 3
        assert aioclient_mock.mock_calls[2][2] == '{"value": "off"}'
        assert hass.states.get("water_heater.altherma").attributes["operation_mode"] == STATE_OFF

        # Set the tank temperature to 54, because the tank is off no call should be done to Daikin
        await hass.services.async_call(
            WATER_HEATER_DOMAIN,
            SERVICE_SET_TEMPERATURE,
            {ATTR_ENTITY_ID: "water_heater.altherma", ATTR_TEMPERATURE: 54},
            blocking=True,
        )
        await hass.async_block_till_done()

        assert len(aioclient_mock.mock_calls) == 3
        assert hass.states.get("water_heater.altherma").attributes["temperature"] == 58

        # aioclient_mock.patch(
        #     DAIKIN_API_URL
        #     + "/v1/gateway-devices/1ece521b-5401-4a42-acce-6f76fba246aa/management-points/domesticHotWaterTank/characteristics/onOffMode",
        #     status=204,
        # )
        aioclient_mock.patch(
            DAIKIN_API_URL
            + "/v1/gateway-devices/1ece521b-5401-4a42-acce-6f76fba246aa/management-points/domesticHotWaterTank/characteristics/powerfulMode",
            status=204,
        )

        # Set the tank to powerful mode, this should result in two calls, first turn the device
        # on and second to set it to performance
        await hass.services.async_call(
            WATER_HEATER_DOMAIN,
            SERVICE_SET_OPERATION_MODE,
            {ATTR_ENTITY_ID: "water_heater.altherma", ATTR_OPERATION_MODE: STATE_PERFORMANCE},
            blocking=True,
        )
        await hass.async_block_till_done()

        assert len(aioclient_mock.mock_calls) == 5
        assert aioclient_mock.mock_calls[3][2] == '{"value": "on"}'
        assert aioclient_mock.mock_calls[4][2] == '{"value": "on"}'
        assert hass.states.get("water_heater.altherma").attributes["operation_mode"] == STATE_PERFORMANCE

        # aioclient_mock.patch(
        #     DAIKIN_API_URL
        #     + "/v1/gateway-devices/1ece521b-5401-4a42-acce-6f76fba246aa/management-points/domesticHotWaterTank/characteristics/powerfulMode",
        #     status=204,
        # )

        # Set the tank to regular on mode, this should only disable powerful mode
        await hass.services.async_call(
            WATER_HEATER_DOMAIN,
            SERVICE_SET_OPERATION_MODE,
            {ATTR_ENTITY_ID: "water_heater.altherma", ATTR_OPERATION_MODE: STATE_HEAT_PUMP},
            blocking=True,
        )
        await hass.async_block_till_done()

        assert len(aioclient_mock.mock_calls) == 6
        assert aioclient_mock.mock_calls[5][2] == '{"value": "off"}'
        assert hass.states.get("water_heater.altherma").attributes["operation_mode"] == STATE_HEAT_PUMP

        # aioclient_mock.patch(
        #     DAIKIN_API_URL
        #     + "/v1/gateway-devices/1ece521b-5401-4a42-acce-6f76fba246aa/management-points/domesticHotWaterTank/characteristics/onOffMode",
        #     status=204,
        # )

        # Turn the tank again off
        await hass.services.async_call(
            WATER_HEATER_DOMAIN,
            SERVICE_SET_OPERATION_MODE,
            {ATTR_ENTITY_ID: "water_heater.altherma", ATTR_OPERATION_MODE: STATE_OFF},
            blocking=True,
        )
        await hass.async_block_till_done()

        assert len(aioclient_mock.mock_calls) == 7
        assert aioclient_mock.mock_calls[6][2] == '{"value": "off"}'
        assert hass.states.get("water_heater.altherma").attributes["operation_mode"] == STATE_OFF

        # aioclient_mock.patch(
        #     DAIKIN_API_URL
        #     + "/v1/gateway-devices/1ece521b-5401-4a42-acce-6f76fba246aa/management-points/domesticHotWaterTank/characteristics/onOffMode",
        #     status=204,
        # )

        # Turn the tank again on
        await hass.services.async_call(
            WATER_HEATER_DOMAIN,
            SERVICE_SET_OPERATION_MODE,
            {ATTR_ENTITY_ID: "water_heater.altherma", ATTR_OPERATION_MODE: STATE_HEAT_PUMP},
            blocking=True,
        )
        await hass.async_block_till_done()

        assert len(aioclient_mock.mock_calls) == 8
        assert aioclient_mock.mock_calls[7][2] == '{"value": "on"}'
        assert hass.states.get("water_heater.altherma").attributes["operation_mode"] == STATE_HEAT_PUMP

        # aioclient_mock.patch(
        #     DAIKIN_API_URL
        #     + "/v1/gateway-devices/1ece521b-5401-4a42-acce-6f76fba246aa/management-points/domesticHotWaterTank/characteristics/onOffMode",
        #     status=204,
        # )

        # Turn the tank again off using turn_off
        await hass.services.async_call(
            WATER_HEATER_DOMAIN,
            SERVICE_TURN_OFF,
            {ATTR_ENTITY_ID: "water_heater.altherma"},
            blocking=True,
        )
        await hass.async_block_till_done()

        assert len(aioclient_mock.mock_calls) == 9
        assert aioclient_mock.mock_calls[8][2] == '{"value": "off"}'
        assert hass.states.get("water_heater.altherma").attributes["operation_mode"] == STATE_OFF

        # Turn the tank again off using turn_off, will be a noop
        await hass.services.async_call(
            WATER_HEATER_DOMAIN,
            SERVICE_TURN_OFF,
            {ATTR_ENTITY_ID: "water_heater.altherma"},
            blocking=True,
        )
        await hass.async_block_till_done()

        assert len(aioclient_mock.mock_calls) == 9

        # aioclient_mock.patch(
        #     DAIKIN_API_URL
        #     + "/v1/gateway-devices/1ece521b-5401-4a42-acce-6f76fba246aa/management-points/domesticHotWaterTank/characteristics/onOffMode",
        #     status=204,
        # )

        # Turn the tank again on using turn_on
        await hass.services.async_call(
            WATER_HEATER_DOMAIN,
            SERVICE_TURN_ON,
            {ATTR_ENTITY_ID: "water_heater.altherma"},
            blocking=True,
        )
        await hass.async_block_till_done()

        assert len(aioclient_mock.mock_calls) == 10
        assert aioclient_mock.mock_calls[9][2] == '{"value": "on"}'
        assert hass.states.get("water_heater.altherma").attributes["operation_mode"] == STATE_HEAT_PUMP

        # Turn the tank again on using turn_on, will be a noop
        await hass.services.async_call(
            WATER_HEATER_DOMAIN,
            SERVICE_TURN_ON,
            {ATTR_ENTITY_ID: "water_heater.altherma"},
            blocking=True,
        )
        await hass.async_block_till_done()

        assert len(aioclient_mock.mock_calls) == 10

        # In order to call update_entity we need to setup the HA core
        await async_setup_component(hass, "homeassistant", {})

        # Try to call update_entity service to trigger an update but because we just did patches
        # this is a noop
        await hass.services.async_call(
            HA_DOMAIN,
            SERVICE_UPDATE_ENTITY,
            {ATTR_ENTITY_ID: "water_heater.altherma"},
            blocking=True,
        )
        await hass.async_block_till_done()

        assert len(aioclient_mock.mock_calls) == 10

        aioclient_mock.clear_requests()
        aioclient_mock.patch(
            DAIKIN_API_URL
            + "/v1/gateway-devices/1ece521b-5401-4a42-acce-6f76fba246aa/management-points/domesticHotWaterTank/characteristics/onOffMode",
            status=429,
            headers={"X-RateLimit-Limit-minute": "0", "X-RateLimit-Limit-day": "0"},
        )

        # Turn the tank off, this should fail and not work due to the daily limit
        try:
            await hass.services.async_call(
                WATER_HEATER_DOMAIN,
                SERVICE_TURN_OFF,
                {ATTR_ENTITY_ID: "water_heater.altherma"},
                blocking=True,
            )
            await hass.async_block_till_done()
        except Exception:
            assert len(aioclient_mock.mock_calls) == 1

        assert len(aioclient_mock.mock_calls) == 1
        assert aioclient_mock.mock_calls[0][2] == '{"value": "off"}'
        assert hass.states.get("water_heater.altherma").attributes["operation_mode"] == STATE_HEAT_PUMP

        aioclient_mock.clear_requests()
        aioclient_mock.patch(
            DAIKIN_API_URL
            + "/v1/gateway-devices/1ece521b-5401-4a42-acce-6f76fba246aa/management-points/domesticHotWaterTank/characteristics/onOffMode",
            status=204,
        )

        # Turn the tank off, this should work again
        await hass.services.async_call(
            WATER_HEATER_DOMAIN,
            SERVICE_TURN_OFF,
            {ATTR_ENTITY_ID: "water_heater.altherma"},
            blocking=True,
        )
        await hass.async_block_till_done()

        assert len(aioclient_mock.mock_calls) == 1
        assert aioclient_mock.mock_calls[0][2] == '{"value": "off"}'
        assert hass.states.get("water_heater.altherma").attributes["operation_mode"] == STATE_OFF

        aioclient_mock.clear_requests()
        aioclient_mock.patch(
            DAIKIN_API_URL
            + "/v1/gateway-devices/1ece521b-5401-4a42-acce-6f76fba246aa/management-points/domesticHotWaterTank/characteristics/onOffMode",
            status=429,
            headers={"X-RateLimit-Limit-minute": "0", "X-RateLimit-Limit-day": "0"},
        )

        # Turn the tank on, this should fail and not work due to the daily limit
        try:
            await hass.services.async_call(
                WATER_HEATER_DOMAIN,
                SERVICE_TURN_ON,
                {ATTR_ENTITY_ID: "water_heater.altherma"},
                blocking=True,
            )
            await hass.async_block_till_done()
        except Exception:
            assert len(aioclient_mock.mock_calls) == 1

        assert len(aioclient_mock.mock_calls) == 1
        assert aioclient_mock.mock_calls[0][2] == '{"value": "on"}'
        assert hass.states.get("water_heater.altherma").attributes["operation_mode"] == STATE_OFF


@pytest.mark.asyncio
async def test_climate(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    onecta_auth: AsyncMock,
    snapshot: SnapshotAssertion,
    entity_registry: er.EntityRegistry,
    aioclient_mock: AiohttpClientMocker,
) -> None:
    """Test entities."""
    await snapshot_platform_entities(hass, aioclient_mock, config_entry, Platform.SENSOR, entity_registry, snapshot, "altherma")

    assert hass.states.get("climate.werkkamer_room_temperature").state == HVACMode.OFF
    assert hass.states.get("binary_sensor.werkkamer_climatecontrol_is_cool_heat_master").state == STATE_ON
    assert hass.states.get("binary_sensor.werkkamer_climatecontrol_is_in_caution_state").state == STATE_OFF
    assert hass.states.get("binary_sensor.werkkamer_climatecontrol_is_in_warning_state").state == STATE_OFF

    with patch(
        "custom_components.daikin_onecta.DaikinApi.async_get_access_token",
        return_value="XXXXXX",
    ):
        aioclient_mock.patch(
            DAIKIN_API_URL
            + "/v1/gateway-devices/6f944461-08cb-4fee-979c-710ff66cea77/management-points/climateControl/characteristics/temperatureControl",
            status=204,
        )
        aioclient_mock.patch(
            DAIKIN_API_URL + "/v1/gateway-devices/6f944461-08cb-4fee-979c-710ff66cea77/management-points/climateControl/characteristics/onOffMode",
            status=204,
        )
        aioclient_mock.patch(
            DAIKIN_API_URL
            + "/v1/gateway-devices/6f944461-08cb-4fee-979c-710ff66cea77/management-points/climateControl/characteristics/operationMode",
            status=204,
        )
        aioclient_mock.patch(
            DAIKIN_API_URL + "/v1/gateway-devices/6f944461-08cb-4fee-979c-710ff66cea77/management-points/climateControl/characteristics/fanControl",
            status=204,
        )
        aioclient_mock.patch(
            DAIKIN_API_URL + "/v1/gateway-devices/6f944461-08cb-4fee-979c-710ff66cea77/management-points/climateControl/characteristics/powerfulMode",
            status=204,
        )
        aioclient_mock.patch(
            DAIKIN_API_URL + "/v1/gateway-devices/6f944461-08cb-4fee-979c-710ff66cea77/management-points/climateControl/characteristics/streamerMode",
            status=204,
        )
        aioclient_mock.post(
            DAIKIN_API_URL + "/v1/gateway-devices/6f944461-08cb-4fee-979c-710ff66cea77/management-points/climateControl/holiday-mode",
            status=204,
        )
        aioclient_mock.put(
            DAIKIN_API_URL + "/v1/gateway-devices/6f944461-08cb-4fee-979c-710ff66cea77/management-points/climateControl/schedule/any/current",
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

        assert len(aioclient_mock.mock_calls) == 2
        assert aioclient_mock.mock_calls[1][2] == '{"value": "on"}'
        assert hass.states.get("climate.werkkamer_room_temperature").state == HVACMode.COOL

        # Turn on the device another time, this shouldn't result in a call to Daikin
        await hass.services.async_call(
            CLIMATE_DOMAIN,
            SERVICE_TURN_ON,
            {ATTR_ENTITY_ID: "climate.werkkamer_room_temperature"},
            blocking=True,
        )
        await hass.async_block_till_done()

        assert len(aioclient_mock.mock_calls) == 2

        # Turn off the device, it was in cool mode
        await hass.services.async_call(
            CLIMATE_DOMAIN,
            SERVICE_TURN_OFF,
            {ATTR_ENTITY_ID: "climate.werkkamer_room_temperature"},
            blocking=True,
        )
        await hass.async_block_till_done()

        assert len(aioclient_mock.mock_calls) == 3
        assert aioclient_mock.mock_calls[2][2] == '{"value": "off"}'
        assert hass.states.get("climate.werkkamer_room_temperature").state == HVACMode.OFF

        # Turn off the device another time, this shouldn't result in a call to Daikin
        await hass.services.async_call(
            CLIMATE_DOMAIN,
            SERVICE_TURN_OFF,
            {ATTR_ENTITY_ID: "climate.werkkamer_room_temperature"},
            blocking=True,
        )
        await hass.async_block_till_done()

        assert len(aioclient_mock.mock_calls) == 3

        # Turn on the device in cooling through hvac mode
        await hass.services.async_call(
            CLIMATE_DOMAIN,
            SERVICE_SET_HVAC_MODE,
            {ATTR_ENTITY_ID: "climate.werkkamer_room_temperature", ATTR_HVAC_MODE: HVACMode.COOL},
            blocking=True,
        )
        await hass.async_block_till_done()

        assert len(aioclient_mock.mock_calls) == 4
        assert aioclient_mock.mock_calls[3][2] == '{"value": "on"}'
        assert hass.states.get("climate.werkkamer_room_temperature").state == HVACMode.COOL

        # Change the device to heating
        await hass.services.async_call(
            CLIMATE_DOMAIN,
            SERVICE_SET_HVAC_MODE,
            {ATTR_ENTITY_ID: "climate.werkkamer_room_temperature", ATTR_HVAC_MODE: HVACMode.HEAT},
            blocking=True,
        )
        await hass.async_block_till_done()

        assert len(aioclient_mock.mock_calls) == 5
        assert aioclient_mock.mock_calls[4][2] == '{"value": "heating"}'
        assert hass.states.get("climate.werkkamer_room_temperature").state == HVACMode.HEAT

        # Turn off the device through the hvac mode
        await hass.services.async_call(
            CLIMATE_DOMAIN,
            SERVICE_SET_HVAC_MODE,
            {ATTR_ENTITY_ID: "climate.werkkamer_room_temperature", ATTR_HVAC_MODE: HVACMode.OFF},
            blocking=True,
        )
        await hass.async_block_till_done()

        assert len(aioclient_mock.mock_calls) == 6
        assert aioclient_mock.mock_calls[5][2] == '{"value": "off"}'
        assert hass.states.get("climate.werkkamer_room_temperature").state == HVACMode.OFF

        # Turn on the device, it was in heat mode
        await hass.services.async_call(
            CLIMATE_DOMAIN,
            SERVICE_TURN_ON,
            {ATTR_ENTITY_ID: "climate.werkkamer_room_temperature"},
            blocking=True,
        )
        await hass.async_block_till_done()

        assert len(aioclient_mock.mock_calls) == 7
        assert aioclient_mock.mock_calls[6][2] == '{"value": "on"}'
        assert hass.states.get("climate.werkkamer_room_temperature").state == HVACMode.HEAT

        # Set the fan mode to 1, will first set the fanControl to fixed, after that the value to 1
        await hass.services.async_call(
            CLIMATE_DOMAIN,
            SERVICE_SET_FAN_MODE,
            {ATTR_ENTITY_ID: "climate.werkkamer_room_temperature", ATTR_FAN_MODE: 1},
            blocking=True,
        )
        await hass.async_block_till_done()

        assert len(aioclient_mock.mock_calls) == 9
        assert aioclient_mock.mock_calls[7][2] == '{"value": "fixed", "path": "/operationModes/heating/fanSpeed/currentMode"}'
        assert aioclient_mock.mock_calls[8][2] == '{"value": 1, "path": "/operationModes/heating/fanSpeed/modes/fixed"}'
        assert hass.states.get("climate.werkkamer_room_temperature").attributes["fan_mode"] == "1"

        # Set the fan mode to 2, should result in 1 call
        await hass.services.async_call(
            CLIMATE_DOMAIN,
            SERVICE_SET_FAN_MODE,
            {ATTR_ENTITY_ID: "climate.werkkamer_room_temperature", ATTR_FAN_MODE: 2},
            blocking=True,
        )
        await hass.async_block_till_done()

        assert len(aioclient_mock.mock_calls) == 10
        assert aioclient_mock.mock_calls[9][2] == '{"value": 2, "path": "/operationModes/heating/fanSpeed/modes/fixed"}'
        assert hass.states.get("climate.werkkamer_room_temperature").attributes["fan_mode"] == "2"

        # Set the fan mode to auto, should result in 1 call
        await hass.services.async_call(
            CLIMATE_DOMAIN,
            SERVICE_SET_FAN_MODE,
            {ATTR_ENTITY_ID: "climate.werkkamer_room_temperature", ATTR_FAN_MODE: "auto"},
            blocking=True,
        )
        await hass.async_block_till_done()

        assert len(aioclient_mock.mock_calls) == 11
        assert aioclient_mock.mock_calls[10][2] == '{"value": "auto", "path": "/operationModes/heating/fanSpeed/currentMode"}'
        assert hass.states.get("climate.werkkamer_room_temperature").attributes["fan_mode"] == "auto"

        # Set the target temperature to 25
        await hass.services.async_call(
            CLIMATE_DOMAIN,
            SERVICE_SET_TEMPERATURE,
            {ATTR_ENTITY_ID: "climate.werkkamer_room_temperature", ATTR_TEMPERATURE: 25},
            blocking=True,
        )
        await hass.async_block_till_done()

        assert len(aioclient_mock.mock_calls) == 12
        assert aioclient_mock.mock_calls[11][2] == '{"value": 25.0, "path": "/operationModes/heating/setpoints/roomTemperature"}'
        assert hass.states.get("climate.werkkamer_room_temperature").attributes["temperature"] == 25

        # Set the target temperature another time to 25, should not result in a call to Daikin
        await hass.services.async_call(
            CLIMATE_DOMAIN,
            SERVICE_SET_TEMPERATURE,
            {ATTR_ENTITY_ID: "climate.werkkamer_room_temperature", ATTR_TEMPERATURE: 25},
            blocking=True,
        )
        await hass.async_block_till_done()

        assert len(aioclient_mock.mock_calls) == 12

        # Set the hvac mode to cool and target temperature to 20 using one call
        await hass.services.async_call(
            CLIMATE_DOMAIN,
            SERVICE_SET_TEMPERATURE,
            {ATTR_ENTITY_ID: "climate.werkkamer_room_temperature", ATTR_HVAC_MODE: HVACMode.COOL, ATTR_TEMPERATURE: 20},
            blocking=True,
        )
        await hass.async_block_till_done()

        assert len(aioclient_mock.mock_calls) == 14
        assert aioclient_mock.mock_calls[12][2] == '{"value": "cooling"}'
        assert aioclient_mock.mock_calls[13][2] == '{"value": 20.0, "path": "/operationModes/cooling/setpoints/roomTemperature"}'
        assert hass.states.get("climate.werkkamer_room_temperature").state == HVACMode.COOL
        assert hass.states.get("climate.werkkamer_room_temperature").attributes["temperature"] == 20

        # Set the horizontal swing mode to swing
        await hass.services.async_call(
            CLIMATE_DOMAIN,
            SERVICE_SET_SWING_HORIZONTAL_MODE,
            {ATTR_ENTITY_ID: "climate.werkkamer_room_temperature", ATTR_SWING_HORIZONTAL_MODE: "swing"},
            blocking=True,
        )
        await hass.async_block_till_done()

        # Set the vertical swing mode to swing
        await hass.services.async_call(
            CLIMATE_DOMAIN,
            SERVICE_SET_SWING_MODE,
            {ATTR_ENTITY_ID: "climate.werkkamer_room_temperature", ATTR_SWING_MODE: "swing"},
            blocking=True,
        )
        await hass.async_block_till_done()

        assert len(aioclient_mock.mock_calls) == 16
        assert aioclient_mock.mock_calls[14][2] == '{"value": "swing", "path": "/operationModes/cooling/fanDirection/horizontal/currentMode"}'
        assert aioclient_mock.mock_calls[15][2] == '{"value": "swing", "path": "/operationModes/cooling/fanDirection/vertical/currentMode"}'
        assert hass.states.get("climate.werkkamer_room_temperature").attributes["swing_horizontal_mode"] == "swing"
        assert hass.states.get("climate.werkkamer_room_temperature").attributes["swing_mode"] == "swing"

        # Set the horizontal swing mode another time to swing, should not result in a call
        await hass.services.async_call(
            CLIMATE_DOMAIN,
            SERVICE_SET_SWING_HORIZONTAL_MODE,
            {ATTR_ENTITY_ID: "climate.werkkamer_room_temperature", ATTR_SWING_HORIZONTAL_MODE: "swing"},
            blocking=True,
        )
        await hass.async_block_till_done()

        # Set the vertical swing mode another time to swing, should not result in a call
        await hass.services.async_call(
            CLIMATE_DOMAIN,
            SERVICE_SET_SWING_MODE,
            {ATTR_ENTITY_ID: "climate.werkkamer_room_temperature", ATTR_SWING_MODE: "swing"},
            blocking=True,
        )
        await hass.async_block_till_done()

        assert len(aioclient_mock.mock_calls) == 16

        # Set the preset mode boost
        await hass.services.async_call(
            CLIMATE_DOMAIN,
            SERVICE_SET_PRESET_MODE,
            {ATTR_ENTITY_ID: "climate.werkkamer_room_temperature", ATTR_PRESET_MODE: PRESET_BOOST},
            blocking=True,
        )
        await hass.async_block_till_done()

        assert len(aioclient_mock.mock_calls) == 17
        assert aioclient_mock.mock_calls[16][2] == '{"value": "on"}'
        assert hass.states.get("climate.werkkamer_room_temperature").attributes["preset_mode"] == PRESET_BOOST

        # Disable the preset mode boost again
        await hass.services.async_call(
            CLIMATE_DOMAIN,
            SERVICE_SET_PRESET_MODE,
            {ATTR_ENTITY_ID: "climate.werkkamer_room_temperature", ATTR_PRESET_MODE: PRESET_NONE},
            blocking=True,
        )
        await hass.async_block_till_done()

        assert len(aioclient_mock.mock_calls) == 18
        assert aioclient_mock.mock_calls[17][2] == '{"value": "off"}'
        assert hass.states.get("climate.werkkamer_room_temperature").attributes["preset_mode"] == PRESET_NONE

        # Turn off the device through the hvac mode
        await hass.services.async_call(
            CLIMATE_DOMAIN,
            SERVICE_SET_HVAC_MODE,
            {ATTR_ENTITY_ID: "climate.werkkamer_room_temperature", ATTR_HVAC_MODE: HVACMode.OFF},
            blocking=True,
        )
        await hass.async_block_till_done()

        assert len(aioclient_mock.mock_calls) == 19
        assert aioclient_mock.mock_calls[18][2] == '{"value": "off"}'
        assert hass.states.get("climate.werkkamer_room_temperature").state == HVACMode.OFF

        # Set the preset mode boost, this should result in two calls, power on the device
        # and set the preset mode. The device was in cool mode, so check that here
        await hass.services.async_call(
            CLIMATE_DOMAIN,
            SERVICE_SET_PRESET_MODE,
            {ATTR_ENTITY_ID: "climate.werkkamer_room_temperature", ATTR_PRESET_MODE: PRESET_BOOST},
            blocking=True,
        )
        await hass.async_block_till_done()

        assert len(aioclient_mock.mock_calls) == 21
        assert aioclient_mock.mock_calls[19][2] == '{"value": "on"}'
        assert aioclient_mock.mock_calls[20][2] == '{"value": "on"}'
        assert hass.states.get("climate.werkkamer_room_temperature").attributes["preset_mode"] == PRESET_BOOST
        assert hass.states.get("climate.werkkamer_room_temperature").state == HVACMode.COOL

        # Test streamer mode switch
        assert hass.states.get("switch.werkkamer_climatecontrol_streamer_mode").state == STATE_OFF

        # Set the streamer mode on
        await hass.services.async_call(
            SWITCH_DOMAIN,
            SERVICE_TURN_ON,
            {ATTR_ENTITY_ID: "switch.werkkamer_climatecontrol_streamer_mode"},
            blocking=True,
        )
        await hass.async_block_till_done()

        assert len(aioclient_mock.mock_calls) == 22
        assert aioclient_mock.mock_calls[21][2] == '{"value": "on"}'
        assert hass.states.get("switch.werkkamer_climatecontrol_streamer_mode").state == STATE_ON

        # Set the streamer mode on a second time shouldn't result in a call to daikin
        await hass.services.async_call(
            SWITCH_DOMAIN,
            SERVICE_TURN_ON,
            {ATTR_ENTITY_ID: "switch.werkkamer_climatecontrol_streamer_mode"},
            blocking=True,
        )
        await hass.async_block_till_done()

        assert len(aioclient_mock.mock_calls) == 22

        # Set the streamer mode off
        await hass.services.async_call(
            SWITCH_DOMAIN,
            SERVICE_TURN_OFF,
            {ATTR_ENTITY_ID: "switch.werkkamer_climatecontrol_streamer_mode"},
            blocking=True,
        )
        await hass.async_block_till_done()

        assert len(aioclient_mock.mock_calls) == 23
        assert aioclient_mock.mock_calls[22][2] == '{"value": "off"}'
        assert hass.states.get("switch.werkkamer_climatecontrol_streamer_mode").state == STATE_OFF

        # Set the streamer mode off a second time shouldn't result in a call to daikin
        await hass.services.async_call(
            SWITCH_DOMAIN,
            SERVICE_TURN_OFF,
            {ATTR_ENTITY_ID: "switch.werkkamer_climatecontrol_streamer_mode"},
            blocking=True,
        )
        await hass.async_block_till_done()

        assert len(aioclient_mock.mock_calls) == 23

        # Set the device in away mode (away mode)
        await hass.services.async_call(
            CLIMATE_DOMAIN,
            SERVICE_SET_PRESET_MODE,
            {ATTR_ENTITY_ID: "climate.werkkamer_room_temperature", ATTR_PRESET_MODE: PRESET_AWAY},
            blocking=True,
        )
        await hass.async_block_till_done()

        assert len(aioclient_mock.mock_calls) == 25
        assert (
            aioclient_mock.mock_calls[24][2]
            == '{"enabled": true, "startDate": "'
            + date.today().isoformat()
            + '", "endDate": "'
            + (date.today() + timedelta(days=60)).isoformat()
            + '"}'
        )
        assert hass.states.get("climate.werkkamer_room_temperature").attributes["preset_mode"] == PRESET_AWAY

        # Set the device in preset mode none again
        await hass.services.async_call(
            CLIMATE_DOMAIN,
            SERVICE_SET_PRESET_MODE,
            {ATTR_ENTITY_ID: "climate.werkkamer_room_temperature", ATTR_PRESET_MODE: PRESET_NONE},
            blocking=True,
        )
        await hass.async_block_till_done()

        assert len(aioclient_mock.mock_calls) == 26
        assert aioclient_mock.mock_calls[25][2] == '{"enabled": false}'
        assert hass.states.get("climate.werkkamer_room_temperature").attributes["preset_mode"] == PRESET_NONE

        # Set the device with schedule 0 enabled
        await hass.services.async_call(
            SELECT_DOMAIN,
            SERVICE_SELECT_OPTION,
            {ATTR_ENTITY_ID: "select.werkkamer_climatecontrol_schedule", ATTR_OPTION: "0"},
            blocking=True,
        )
        await hass.async_block_till_done()

        assert len(aioclient_mock.mock_calls) == 27
        assert aioclient_mock.mock_calls[26][2] == '{"scheduleId": "0", "enabled": true}'
        assert hass.states.get("select.werkkamer_climatecontrol_schedule").state == "0"

        # Set the device with no schedule
        await hass.services.async_call(
            SELECT_DOMAIN,
            SERVICE_SELECT_OPTION,
            {ATTR_ENTITY_ID: "select.werkkamer_climatecontrol_schedule", ATTR_OPTION: SCHEDULE_OFF},
            blocking=True,
        )
        await hass.async_block_till_done()

        assert len(aioclient_mock.mock_calls) == 28
        assert aioclient_mock.mock_calls[27][2] == '{"scheduleId": "0", "enabled": false}'
        assert hass.states.get("select.werkkamer_climatecontrol_schedule").state == SCHEDULE_OFF

        aioclient_mock.put(
            DAIKIN_API_URL
            + "/v1/gateway-devices/1ece521b-5401-4a42-acce-6f76fba246aa/management-points/climateControlMainZone/schedule/cooling/current",
            status=204,
        )

        # Set the device with schedule 'User defined' enabled
        await hass.services.async_call(
            SELECT_DOMAIN,
            SERVICE_SELECT_OPTION,
            {ATTR_ENTITY_ID: "select.altherma_climatecontrol_schedule", ATTR_OPTION: "User defined"},
            blocking=True,
        )
        await hass.async_block_till_done()

        assert len(aioclient_mock.mock_calls) == 29
        assert aioclient_mock.mock_calls[28][2] == '{"scheduleId": "scheduleCoolingRT1", "enabled": true}'
        assert hass.states.get("select.altherma_climatecontrol_schedule").state == "User defined"

        # Set the device with no schedule
        await hass.services.async_call(
            SELECT_DOMAIN,
            SERVICE_SELECT_OPTION,
            {ATTR_ENTITY_ID: "select.altherma_climatecontrol_schedule", ATTR_OPTION: SCHEDULE_OFF},
            blocking=True,
        )
        await hass.async_block_till_done()

        assert len(aioclient_mock.mock_calls) == 30
        assert aioclient_mock.mock_calls[29][2] == '{"scheduleId": "scheduleCoolingRT1", "enabled": false}'
        assert hass.states.get("select.altherma_climatecontrol_schedule").state == SCHEDULE_OFF

        # Turn off the device through the hvac mode
        await hass.services.async_call(
            CLIMATE_DOMAIN,
            SERVICE_SET_HVAC_MODE,
            {ATTR_ENTITY_ID: "climate.werkkamer_room_temperature", ATTR_HVAC_MODE: HVACMode.OFF},
            blocking=True,
        )
        await hass.async_block_till_done()

        assert len(aioclient_mock.mock_calls) == 31
        assert aioclient_mock.mock_calls[30][2] == '{"value": "off"}'
        assert hass.states.get("climate.werkkamer_room_temperature").state == HVACMode.OFF

        # Turn off the device through the hvac mode, because it is already off it shouldn't result
        # in a call to daikin
        await hass.services.async_call(
            CLIMATE_DOMAIN,
            SERVICE_SET_HVAC_MODE,
            {ATTR_ENTITY_ID: "climate.werkkamer_room_temperature", ATTR_HVAC_MODE: HVACMode.OFF},
            blocking=True,
        )
        await hass.async_block_till_done()

        assert len(aioclient_mock.mock_calls) == 31
        assert hass.states.get("climate.werkkamer_room_temperature").state == HVACMode.OFF

        # Enable dry mode
        await hass.services.async_call(
            CLIMATE_DOMAIN,
            SERVICE_SET_HVAC_MODE,
            {ATTR_ENTITY_ID: "climate.werkkamer_room_temperature", ATTR_HVAC_MODE: HVACMode.DRY},
            blocking=True,
        )
        await hass.async_block_till_done()

        assert len(aioclient_mock.mock_calls) == 33
        assert hass.states.get("climate.werkkamer_room_temperature").state == HVACMode.DRY

        # In order to call update_entity we need to setup the HA core
        await async_setup_component(hass, "homeassistant", {})

        # We patch the scan_ignore method to zero so that the coordinator will pull again
        with patch(
            "custom_components.daikin_onecta.OnectaDataUpdateCoordinator.scan_ignore",
            return_value=0,
        ):
            aioclient_mock.get(DAIKIN_API_URL + "/v1/gateway-devices", status=200, json=load_fixture_json("altherma"))
            # Call update_entity service to trigger an update
            await hass.services.async_call(
                HA_DOMAIN,
                SERVICE_UPDATE_ENTITY,
                {ATTR_ENTITY_ID: "climate.werkkamer_room_temperature"},
                blocking=True,
            )
            await hass.async_block_till_done()

            assert len(aioclient_mock.mock_calls) == 34
            assert aioclient_mock.mock_calls[33][1] == URL(DAIKIN_API_URL + "/v1/gateway-devices")

        # Set the swing mode to windnice, should result in a call with windNice
        await hass.services.async_call(
            CLIMATE_DOMAIN,
            SERVICE_SET_SWING_MODE,
            {ATTR_ENTITY_ID: "climate.werkkamer_room_temperature", ATTR_SWING_MODE: "windnice"},
            blocking=True,
        )
        await hass.async_block_till_done()

        assert len(aioclient_mock.mock_calls) == 35
        assert aioclient_mock.mock_calls[34][2] == '{"value": "windNice", "path": "/operationModes/cooling/fanDirection/vertical/currentMode"}'
        assert hass.states.get("climate.werkkamer_room_temperature").attributes["swing_mode"] == "windnice"

        aioclient_mock.clear_requests()
        aioclient_mock.put(
            DAIKIN_API_URL
            + "/v1/gateway-devices/1ece521b-5401-4a42-acce-6f76fba246aa/management-points/climateControlMainZone/schedule/cooling/current",
            status=429,
            headers={"X-RateLimit-Remaining-minute": "0", "X-RateLimit-Remaining-day": "0"},
        )
        # Set the device with schedule 'User defined' enabled, this should fail due to the rate limit
        await hass.services.async_call(
            SELECT_DOMAIN,
            SERVICE_SELECT_OPTION,
            {ATTR_ENTITY_ID: "select.altherma_climatecontrol_schedule", ATTR_OPTION: "User defined"},
            blocking=True,
        )
        await hass.async_block_till_done()

        info = await system_health_info(hass)

        assert info["remaining_minute"] == 0
        assert info["remaining_day"] == 0

        assert len(aioclient_mock.mock_calls) == 1
        assert aioclient_mock.mock_calls[0][2] == '{"scheduleId": "scheduleCoolingRT1", "enabled": true}'
        assert hass.states.get("select.altherma_climatecontrol_schedule").state == SCHEDULE_OFF


async def test_minimal_data(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    onecta_auth: AsyncMock,
    snapshot: SnapshotAssertion,
    entity_registry: er.EntityRegistry,
    aioclient_mock: AiohttpClientMocker,
) -> None:
    """Test entities."""
    await snapshot_platform_entities(hass, aioclient_mock, config_entry, Platform.SENSOR, entity_registry, snapshot, "minimal_data")

    assert hass.states.get("water_heater.altherma").attributes["current_temperature"] == 53
    assert hass.states.get("sensor.altherma_domestichotwatertank_heating_yearly_electrical_consumption").state == "1232"


async def test_gas(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    onecta_auth: AsyncMock,
    snapshot: SnapshotAssertion,
    entity_registry: er.EntityRegistry,
    aioclient_mock: AiohttpClientMocker,
) -> None:
    """Test entities."""
    await snapshot_platform_entities(hass, aioclient_mock, config_entry, Platform.SENSOR, entity_registry, snapshot, "gas")

    assert hass.states.get("climate.my_living_room_room_temperature").attributes["temperature"] == 25


@pytest.mark.asyncio
async def test_button(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    onecta_auth: AsyncMock,
    snapshot: SnapshotAssertion,
    entity_registry: er.EntityRegistry,
    aioclient_mock: AiohttpClientMocker,
) -> None:
    """Test entities."""
    await snapshot_platform_entities(hass, aioclient_mock, config_entry, Platform.SENSOR, entity_registry, snapshot, "dry")

    with patch(
        "custom_components.daikin_onecta.DaikinApi.async_get_access_token",
        return_value="XXXXXX",
    ):
        aioclient_mock.get(DAIKIN_API_URL + "/v1/gateway-devices", status=200, json=load_fixture_json("dry"))

        # Call button service
        await hass.services.async_call(
            BUTTON_DOMAIN,
            SERVICE_PRESS,
            {ATTR_ENTITY_ID: "button.lounge_refresh"},
            blocking=True,
        )
        await hass.async_block_till_done()

        assert len(aioclient_mock.mock_calls) == 2


async def test_altherma_schedule(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    onecta_auth: AsyncMock,
    snapshot: SnapshotAssertion,
    entity_registry: er.EntityRegistry,
    aioclient_mock: AiohttpClientMocker,
) -> None:
    """Test entities."""
    await snapshot_platform_entities(hass, aioclient_mock, config_entry, Platform.SENSOR, entity_registry, snapshot, "altherma_schedule")

    assert hass.states.get("select.altherma_domestichotwatertank_schedule").state == "User defined"
