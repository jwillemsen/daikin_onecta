"""Test daikin_onecta sensor."""
from homeassistant.core import HomeAssistant

from . import setup_mock_daikin_onecta_config_entry
from homeassistant.setup import async_setup_component

from pytest_homeassistant_custom_component.common import MockConfigEntry
from custom_components.daikin_onecta.const import DOMAIN

TEST_HUB_SENSOR_POWER_GRID_ENTITY_ID = "sensor.daikin_onecta_test_site_power_grid"
TEST_HUB_SENSOR_POWER_EXPORT_ENTITY_ID = "sensor.daikin_onecta_test_site_power_export"
TEST_HUB_SENSOR_POWER_IMPORT_ENTITY_ID = "sensor.daikin_onecta_test_site_power_import"
TEST_EDDI_SENSOR_TEMP_1_ENTITY_ID = "sensor.daikin_onecta_test_eddi_1_temp_tank_1"
TEST_EDDI_SENSOR_TEMP_2_ENTITY_ID = "sensor.daikin_onecta_test_eddi_1_temp_tank_2"


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

