"""Test daikin_onecta sensor."""
from unittest.mock import AsyncMock

import homeassistant.helpers.entity_registry as er
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

    await hass.services.async_call(
        WATER_HEATER_DOMAIN,
        SERVICE_SET_TEMPERATURE,
        {ATTR_ENTITY_ID: "water_heater.altherma", ATTR_TEMPERATURE: 58},
        blocking=True,
    )
    await hass.async_block_till_done()

    await hass.services.async_call(
        WATER_HEATER_DOMAIN,
        SERVICE_SET_OPERATION_MODE,
        {ATTR_ENTITY_ID: "water_heater.altherma", ATTR_OPERATION_MODE: STATE_OFF},
        blocking=True,
    )
    await hass.async_block_till_done()
