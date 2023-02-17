"""Support for the Daikin BRP069A62."""
import logging
_LOGGER = logging.getLogger(__name__)

from homeassistant.components.water_heater import (
    SUPPORT_TARGET_TEMPERATURE,
    SUPPORT_OPERATION_MODE,
    STATE_PERFORMANCE,
    STATE_HEAT_PUMP,
    STATE_OFF,
    WaterHeaterEntity,
)

from homeassistant.const import ATTR_TEMPERATURE, TEMP_CELSIUS

from .const import (
    DOMAIN as DAIKIN_DOMAIN,
    DAIKIN_DEVICES,
    ATTR_TANK_MODE,
    ATTR_TANK_MODE_SET,
    ATTR_TANK_STATE_OFF,
    ATTR_TANK_STATE_HEAT_PUMP,
    ATTR_TANK_STATE_PERFOMANCE,
    ATTR_TANK_TARGET_TEMPERATURE,
)

HA_TANK_MODE_TO_DAIKIN = {
    STATE_PERFORMANCE: ATTR_TANK_STATE_PERFOMANCE,
    STATE_HEAT_PUMP: ATTR_TANK_STATE_HEAT_PUMP,
    STATE_OFF: ATTR_TANK_STATE_OFF,
}

HA_TANK_ATTR_TO_DAIKIN = {
    ATTR_TANK_MODE: ATTR_TANK_MODE_SET,
    ATTR_TANK_TARGET_TEMPERATURE: ATTR_TANK_TARGET_TEMPERATURE,
}


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Old way of setting up the Daikin HVAC platform.

    Can only be called when a user accidentally mentions the platform in their
    config. But even in that case it would have been ignored.
    """


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up Daikin climate entities."""
    for dev_id, device in hass.data[DAIKIN_DOMAIN][DAIKIN_DEVICES].items():
        async_add_entities([DaikinWaterTank(device)], update_before_add=True)


class DaikinWaterTank(WaterHeaterEntity):
    """Representation of a Daikin Water Tank."""

    def __init__(self, device):
        """Initialize the Water device."""
        _LOGGER.info("Initializing Daiking Altherma HotWaterTank...")
        self._device = device
        self._list = {
            ATTR_TANK_MODE: list(HA_TANK_MODE_TO_DAIKIN),
        }
        self._supported_features = SUPPORT_TARGET_TEMPERATURE + SUPPORT_OPERATION_MODE

    async def _set(self, settings):
        """Set device settings using API."""
        values = {}
        for attr in [ATTR_TEMPERATURE, ATTR_TANK_MODE]:
            value = settings.get(attr)
            if value is None:
                continue
            daikin_attr = HA_TANK_ATTR_TO_DAIKIN.get(attr)
            if daikin_attr is not None:
                if attr == ATTR_TANK_MODE:
                    values[daikin_attr] = HA_TANK_MODE_TO_DAIKIN[value]
                elif value in self._list[attr]:
                    values[daikin_attr] = value.lower()
                else:
                    _LOGGER.error("Invalid value %s for %s", attr, value)
            # temperature
            elif attr == ATTR_TEMPERATURE:
                try:
                    values[HA_TANK_ATTR_TO_DAIKIN[ATTR_TANK_TARGET_TEMPERATURE]] = str(int(value))
                except ValueError:
                    _LOGGER.error("Invalid temperature %s", value)
        if values:
            await self._device.set(values)

    @property
    def available(self):
        """Return the availability of the underlying device."""
        return self._device.available

    @property
    def supported_features(self):
        """Return the list of supported features."""
        return self._supported_features

    @property
    def name(self):
        """Return the name of the thermostat, if any."""
        return self._device.name

    @property
    def unique_id(self):
        """Return a unique ID."""
        devID = self._device.getId()
        return f"{devID}"

    @property
    def temperature_unit(self):
        """Return the unit of measurement which this thermostat uses."""
        return TEMP_CELSIUS

    @property
    def current_temperature(self):
        """Return the current temperature."""
        return self._device.tank_temperature

    @property
    def target_temperature(self):
        """Return the temperature we try to reach."""
        return self._device.tank_target_temperature

    @property
    def target_temperature_step(self):
        """Return the supported step of target temperature."""
        stepVal = self._device.tank_target_temperature_step
        return stepVal

    @property
    def min_temp(self):
        """Return the supported step of target temperature."""
        stepVal = self._device.tank_target_temperature_minValue
        return stepVal

    @property
    def max_temp(self):
        """Return the supported step of target temperature."""
        stepVal = self._device.tank_target_temperature_maxValue
        return stepVal

    async def async_set_temperature(self, **kwargs):
        """Set new target temperature."""
        # The service climate.set_temperature can set the hvac_mode too, see
        # https://www.home-assistant.io/integrations/climate/#service-climateset_temperature
        # se we first set the hvac_mode, if provided, then the temperature.
        await self._device.async_set_tank_temperature(kwargs[ATTR_TEMPERATURE])

    async def async_update(self):
        """Retrieve latest state."""
        await self._device.api.async_update()

    @property
    def current_operation(self):
        """Return current operation ie. heat, cool, idle."""
        return self._device.tank_state

    @property
    def operation_list(self):
        """Return the list of available operation modes."""
        return self._device.tank_states

    async def async_set_operation_mode(self, tank_state):
        """Set new target tank mode."""
        tank_state = HA_TANK_MODE_TO_DAIKIN[tank_state]
        await self._device.async_set_tank_state(tank_state)

    @property
    def device_info(self):
        """Return a device description for device registry."""
        return self._device.device_info()
