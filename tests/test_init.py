"""Test daikin_onecta sensor."""
from homeassistant.core import HomeAssistant
from .conftest import selected_platforms, snapshot_platform_entities
from homeassistant.const import Platform

from . import setup_mock_daikin_onecta_config_entry
from homeassistant.setup import async_setup_component

from pytest_homeassistant_custom_component.common import MockConfigEntry
from custom_components.daikin_onecta.const import DOMAIN
from unittest.mock import AsyncMock, patch
from syrupy import SnapshotAssertion
import homeassistant.helpers.entity_registry as er
from unittest.mock import AsyncMock, patch

async def test_entity(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    onecta_auth: AsyncMock,
    snapshot: SnapshotAssertion,
    entity_registry: er.EntityRegistry,
) -> None:
    """Test entities."""
    await snapshot_platform_entities(
        hass,
        config_entry,
        Platform.SENSOR,
        entity_registry,
        snapshot,
    )

async def test_sensor(hass: HomeAssistant) -> None:
    """Verify device information includes expected details."""
    entry = MockConfigEntry(domain=DOMAIN, data={"name": "simple config",})
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    state = hass.states.get("sensor.example_temperature")

    #assert await async_setup_component(hass, "daikin_onecta", {})
    await setup_mock_daikin_onecta_config_entry(hass)
    entity_state = hass.states.get("sensor.altherma_climatecontrol_outdoor_temperature")
    print(entity_state)
    #assert entity_state
#    assert entity_state.state == "4429"



async def test_indoor_sensor(
    hass: HomeAssistant, config_entry: MockConfigEntry, onecta_auth: AsyncMock
) -> None:
    """Test indoor sensor setup."""
    # with selected_platforms([Platform.SENSOR]):
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    prefix = "sensor.parents_bedroom_"

    assert hass.states.get(f"{prefix}temperature").state == "20.3"
    assert hass.states.get(f"{prefix}humidity").state == "63"
    assert hass.states.get(f"{prefix}co2").state == "494"
    assert hass.states.get(f"{prefix}pressure").state == "1014.5"

