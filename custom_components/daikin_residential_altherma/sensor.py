"""Support for Daikin AC sensors."""
from homeassistant.const import (
    CONF_DEVICE_CLASS,
    CONF_ICON,
    CONF_NAME,
    CONF_TYPE,
    CONF_UNIT_OF_MEASUREMENT,
)
from homeassistant.helpers.entity import Entity

from .daikin_base import Appliance

from .const import (
    DOMAIN as DAIKIN_DOMAIN,
    DAIKIN_DEVICES,
    ATTR_COOL_ENERGY,
    ATTR_HEAT_ENERGY,
    ATTR_HEAT_TANK_ENERGY,
    ATTR_INSIDE_TEMPERATURE,
    ATTR_OUTSIDE_TEMPERATURE,
    ATTR_ROOM_TEMPERATURE,
    ATTR_TANK_TEMPERATURE,
    SENSOR_TYPE_ENERGY,
    SENSOR_TYPE_HUMIDITY,
    SENSOR_TYPE_POWER,
    SENSOR_TYPE_TEMPERATURE,
    SENSOR_PERIODS,
    SENSOR_TYPES,
)

import logging
_LOGGER = logging.getLogger(__name__)

async def async_setup(hass, async_add_entities):
    """Old way of setting up the Daikin sensors.

    Can only be called when a user accidentally mentions the platform in their
    config. But even in that case it would have been ignored.
    """


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up Daikin climate based on config_entry."""
    sensors = []
    prog = 0

    for dev_id, device in hass.data[DAIKIN_DOMAIN][DAIKIN_DEVICES].items():
        sensor = DaikinSensor.factory(device, ATTR_INSIDE_TEMPERATURE)
        print("DAMIANO append sensor = {}".format(sensor))
        sensors.append(sensor)

        if device.support_room_temperature:
            sensor = DaikinSensor.factory(device, ATTR_ROOM_TEMPERATURE)
            sensors.append(sensor)

        if device.support_tank_temperature:
            sensor = DaikinSensor.factory(device, ATTR_TANK_TEMPERATURE)
            sensors.append(sensor)

        if device.support_outside_temperature:
            sensor = DaikinSensor.factory(device, ATTR_OUTSIDE_TEMPERATURE)
            sensors.append(sensor)

        if device.support_energy_consumption:
            for period in SENSOR_PERIODS:
                sensor = DaikinSensor.factory(device, ATTR_COOL_ENERGY, period)
                sensors.append(sensor)

                sensor = DaikinSensor.factory(device, ATTR_HEAT_ENERGY, period)
                sensors.append(sensor)

                sensor = DaikinSensor.factory(device, ATTR_HEAT_TANK_ENERGY, period)
                sensors.append(sensor)

    #print("DAMIANO add_entities: %s", sensors)
    async_add_entities(sensors)


class DaikinSensor(Entity):
    """Representation of a Sensor."""

    @staticmethod
    def factory(device: Appliance, monitored_state: str, period=""):
        """Initialize any DaikinSensor."""
        #print("DAMIANO monitored_state = %s",monitored_state)
        cls = {
            SENSOR_TYPE_TEMPERATURE: DaikinClimateSensor,
            SENSOR_TYPE_HUMIDITY: DaikinClimateSensor,
            SENSOR_TYPE_POWER: DaikinPowerSensor,
            SENSOR_TYPE_ENERGY: DaikinPowerSensor,
        }[SENSOR_TYPES[monitored_state][CONF_TYPE]]
        return cls(device, monitored_state, period)

    def __init__(self, device: Appliance, monitored_state: str, period="") -> None:
        """Initialize the sensor."""
        self._device = device
        self._sensor = SENSOR_TYPES[monitored_state]
        self._period = period
        if period != "":
            periodName = SENSOR_PERIODS[period]
            self._name = f"{device.name} {periodName} {self._sensor[CONF_NAME]}"
        else:
            self._name = f"{device.name} {self._sensor[CONF_NAME]}"
        self._device_attribute = monitored_state
        print("  DAMIANO Initialized sensor: {}".format(self._name))

    @property
    def available(self):
        """Return the availability of the underlying device."""
        return self._device.available

    @property
    def unique_id(self):
        """Return a unique ID."""
        devID = self._device.getId()
        if self._period != "":
            return f"{devID}_{self._device_attribute}_{self._period}"
        return f"{devID}_{self._device_attribute}"

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def state(self):
        """Return the state of the sensor."""
        raise NotImplementedError

    @property
    def device_class(self):
        """Return the class of this device."""
        return self._sensor.get(CONF_DEVICE_CLASS)

    @property
    def icon(self):
        """Return the icon of this device."""
        return self._sensor.get(CONF_ICON)

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement."""
        uom = self._sensor[CONF_UNIT_OF_MEASUREMENT]
        return uom

    async def async_update(self):
        """Retrieve latest state."""
        await self._device.api.async_update()

    @property
    def device_info(self):
        """Return a device description for device registry."""
        return self._device.device_info()


class DaikinClimateSensor(DaikinSensor):
    """Representation of a Climate Sensor."""

    @property
    def state(self):
        """Return the internal state of the sensor."""
        if self._device_attribute == ATTR_INSIDE_TEMPERATURE:
            #DAMIANO
            # return self._device.inside_temperature
            return self._device.leavingWaterTemperature

        if self._device_attribute == ATTR_OUTSIDE_TEMPERATURE:
            return self._device.outside_temperature

        if self._device_attribute == ATTR_TANK_TEMPERATURE:
            return self._device.tank_temperature

        if self._device_attribute == ATTR_ROOM_TEMPERATURE:
            return self._device.room_temperature

        return None


class DaikinPowerSensor(DaikinSensor):
    """Representation of a power/energy consumption sensor."""

    @property
    def state(self):
        """Return the state of the sensor."""
        if self._device_attribute == ATTR_COOL_ENERGY:
            return round(self._device.energy_consumption("cooling", self._period), 3)

        if self._device_attribute == ATTR_HEAT_ENERGY:
            return round(self._device.energy_consumption("heating", self._period), 3)

        # DAMIANO
        if self._device_attribute == ATTR_HEAT_TANK_ENERGY:
            return round(self._device.energy_consumption_tank("heating", self._period), 3)
        return None
