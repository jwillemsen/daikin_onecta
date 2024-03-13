"""Test daikin_onecta sensor."""
from homeassistant.core import HomeAssistant

from . import setup_mock_daikin_onecta_config_entry

TEST_HUB_SENSOR_POWER_GRID_ENTITY_ID = "sensor.daikin_onecta_test_site_power_grid"
TEST_HUB_SENSOR_POWER_EXPORT_ENTITY_ID = "sensor.daikin_onecta_test_site_power_export"
TEST_HUB_SENSOR_POWER_IMPORT_ENTITY_ID = "sensor.daikin_onecta_test_site_power_import"
TEST_EDDI_SENSOR_TEMP_1_ENTITY_ID = "sensor.daikin_onecta_test_eddi_1_temp_tank_1"
TEST_EDDI_SENSOR_TEMP_2_ENTITY_ID = "sensor.daikin_onecta_test_eddi_1_temp_tank_2"


async def test_sensor(hass: HomeAssistant) -> None:
    """Verify device information includes expected details."""

    await setup_mock_daikin_onecta_config_entry(hass)
    entity_state = hass.states.get("sensor.altherma_climatecontrol_outdoor_temperature")
    print(entity_state)
    assert entity_state
#    assert entity_state.state == "4429"

