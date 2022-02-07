"""Support for Daikin AC sensors."""

from unicodedata import name
from homeassistant.const import (
    CONF_DEVICE_CLASS,
    CONF_ICON,
    CONF_NAME,
    CONF_TYPE,
    CONF_UNIT_OF_MEASUREMENT,
)

from homeassistant.components.sensor import (
    SensorEntity,
    STATE_CLASS_MEASUREMENT,
    STATE_CLASS_TOTAL_INCREASING,
)

from .daikin_base import Appliance

from .const import (
    DOMAIN as DAIKIN_DOMAIN,
    DAIKIN_DEVICES,
    ATTR_COOL_ENERGY,
    ATTR_HEAT_ENERGY,
    ATTR_HEAT_TANK_ENERGY,
    ATTR_LEAVINGWATER_TEMPERATURE,
    ATTR_OUTSIDE_TEMPERATURE,
    ATTR_ROOM_TEMPERATURE,
    ATTR_TANK_TEMPERATURE,
    ATTR_SETPOINT_MODE,
    ATTR_TANK_SETPOINT_MODE,
    ATTR_CONTROL_MODE,
    ATTR_IS_HOLIDAY_MODE_ACTIVE,
    ATTR_IS_IN_EMERGENCY_STATE,
    ATTR_IS_IN_ERROR_STATE,
    ATTR_IS_IN_INSTALLER_STATE,
    ATTR_IS_IN_WARNING_STATE,
    ATTR_TANK_HEATUP_MODE,
    ATTR_TANK_IS_HOLIDAY_MODE_ACTIVE,
    ATTR_TANK_IS_IN_EMERGENCY_STATE,
    ATTR_TANK_IS_IN_ERROR_STATE,
    ATTR_TANK_IS_IN_INSTALLER_STATE,
    ATTR_TANK_IS_IN_WARNING_STATE,
    ATTR_TANK_IS_POWERFUL_MODE_ACTIVE,
    SENSOR_TYPE_ENERGY,
    SENSOR_TYPE_POWER,
    SENSOR_TYPE_TEMPERATURE,
    SENSOR_TYPE_INFO,
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
        sensor = DaikinSensor.factory(device, ATTR_LEAVINGWATER_TEMPERATURE,"")
        sensors.append(sensor)

        if device.support_room_temperature:
            sensor = DaikinSensor.factory(device, ATTR_ROOM_TEMPERATURE,"")
            sensors.append(sensor)
        else:
            _LOGGER.info("DAIKIN RESIDENTIAL ALTHERMA: device NOT supports room_temperature")

        if device.support_tank_temperature:
            sensor = DaikinSensor.factory(device, ATTR_TANK_TEMPERATURE,"")
            sensors.append(sensor)
        else:
            _LOGGER.info("DAIKIN RESIDENTIAL ALTHERMA: device NOT supports tank_temperature")

        if device.support_outside_temperature:
            sensor = DaikinSensor.factory(device, ATTR_OUTSIDE_TEMPERATURE,"")
            sensors.append(sensor)
        else:
            _LOGGER.info("DAIKIN RESIDENTIAL ALTHERMA: device NOT supports outside_temperature")

        if device.support_energy_consumption:
            for period in SENSOR_PERIODS:
                if device.supports_cooling:
                    sensor = DaikinSensor.factory(device, ATTR_COOL_ENERGY,"", period)
                    _LOGGER.debug("append sensor = %s", sensor)
                    sensors.append(sensor)
                else:
                    _LOGGER.info("DAIKIN RESIDENTIAL ALTHERMA: device NOT supports_cooling")

                sensor = DaikinSensor.factory(device, ATTR_HEAT_ENERGY,"", period)
                sensors.append(sensor)

                # When we don't have a tank temperature we also don't have
                # tank energy values
                if device.support_tank_temperature:
                    sensor = DaikinSensor.factory(device, ATTR_HEAT_TANK_ENERGY,"", period)
                    _LOGGER.debug("append sensor = %s", sensor)
                    sensors.append(sensor)
                else:
                    _LOGGER.info("DAIKIN RESIDENTIAL ALTHERMA: device NOT support_tank_temperature")
        else:
            _LOGGER.info("DAIKIN RESIDENTIAL ALTHERMA: device NOT supports energy_consumption")

        if device.support_setpoint_mode:
            sensor = DaikinSensor.factory(device, ATTR_SETPOINT_MODE,"")
            _LOGGER.debug("append sensor = %s", sensor)
            sensors.append(sensor)
        else:
            _LOGGER.info("DAIKIN RESIDENTIAL ALTHERMA: device NOT support_control_mode", sensor)
            
        if device.support_tank_setpoint_mode:
            sensor = DaikinSensor.factory(device, ATTR_TANK_SETPOINT_MODE,"")
            _LOGGER.debug("append sensor = %s", sensor)
            sensors.append(sensor)
        else:
            _LOGGER.info("DAIKIN RESIDENTIAL ALTHERMA: device NOT support_control_mode", sensor)

        if device.support_control_mode:
            sensor = DaikinSensor.factory(device, ATTR_CONTROL_MODE,"")
            _LOGGER.debug("append sensor = %s", sensor)
            sensors.append(sensor)
        else:
            _LOGGER.info("DAIKIN RESIDENTIAL ALTHERMA: device NOT support_control_mode", sensor)

        if device.support_is_holiday_mode_active:
            sensor = DaikinSensor.factory(device, ATTR_IS_HOLIDAY_MODE_ACTIVE,"")
            _LOGGER.debug("append sensor = %s", sensor)
            sensors.append(sensor)
        else:
            _LOGGER.info("DAIKIN RESIDENTIAL ALTHERMA: device NOT supports is_holiday_mode_active")

        if device.support_is_in_emergency_state:
            sensor = DaikinSensor.factory(device, ATTR_IS_IN_EMERGENCY_STATE,"")
            _LOGGER.debug("append sensor = %s", sensor)
            sensors.append(sensor)
        else:
            _LOGGER.info("DAIKIN RESIDENTIAL ALTHERMA: device NOT supports is_in_emergency_state")

        if device.support_is_in_error_state:
            sensor = DaikinSensor.factory(device, ATTR_IS_IN_ERROR_STATE,"")
            _LOGGER.debug("append sensor = %s", sensor)
            sensors.append(sensor)
        else:
            _LOGGER.info("DAIKIN RESIDENTIAL ALTHERMA: device NOT supports is_in_error_state")

        if device.support_is_in_installer_state:
            sensor = DaikinSensor.factory(device, ATTR_IS_IN_INSTALLER_STATE,"")
            _LOGGER.debug("append sensor = %s", sensor)
            sensors.append(sensor)
        else:
            _LOGGER.info("DAIKIN RESIDENTIAL ALTHERMA: device NOT supports is_in_installer_state")

        if device.support_is_in_warning_state:
            sensor = DaikinSensor.factory(device, ATTR_IS_IN_WARNING_STATE,"")
            _LOGGER.debug("append sensor = %s", sensor)
            sensors.append(sensor)
        else:
            _LOGGER.info("DAIKIN RESIDENTIAL ALTHERMA: device NOT supports is_in_warning_state")

        #heatup
        if device.support_heatupMode:
            sensor = DaikinSensor.factory(device, ATTR_TANK_HEATUP_MODE,"")
            _LOGGER.debug("append sensor = %s", sensor)
            sensors.append(sensor)
        else:
            _LOGGER.info("DAIKIN RESIDENTIAL ALTHERMA: device NOT supports is_in_warning_state")

        # TANK
        # TODO: ripartire da qui
        if device.support_tank_is_holiday_mode_active:
            sensor = DaikinSensor.factory(device, ATTR_TANK_IS_HOLIDAY_MODE_ACTIVE,"TANK")
            _LOGGER.debug("append sensor = %s", sensor)
            sensors.append(sensor)
        else:
            _LOGGER.info("DAIKIN RESIDENTIAL ALTHERMA: device NOT supports is_holiday_mode_active")

        if device.support_tank_is_in_emergency_state:
            sensor = DaikinSensor.factory(device, ATTR_TANK_IS_IN_EMERGENCY_STATE,"TANK")
            _LOGGER.debug("append sensor = %s", sensor)
            sensors.append(sensor)
        else:
            _LOGGER.info("DAIKIN RESIDENTIAL ALTHERMA: device NOT supports is_in_emergency_state")

        if device.support_tank_is_in_error_state:
            sensor = DaikinSensor.factory(device, ATTR_TANK_IS_IN_ERROR_STATE,"TANK")
            _LOGGER.debug("append sensor = %s", sensor)
            sensors.append(sensor)
        else:
            _LOGGER.info("DAIKIN RESIDENTIAL ALTHERMA: device NOT supports is_in_error_state")

        if device.support_tank_is_in_installer_state:
            sensor = DaikinSensor.factory(device, ATTR_TANK_IS_IN_INSTALLER_STATE,"TANK")
            _LOGGER.debug("append sensor = %s", sensor)
            sensors.append(sensor)
        else:
            _LOGGER.info("DAIKIN RESIDENTIAL ALTHERMA: device NOT supports is_in_installer_state")

        if device.support_tank_is_in_warning_state:
            sensor = DaikinSensor.factory(device, ATTR_TANK_IS_IN_WARNING_STATE,"TANK")
            _LOGGER.debug("append sensor = %s", sensor)
            sensors.append(sensor)
        else:
            _LOGGER.info("DAIKIN RESIDENTIAL ALTHERMA: device NOT supports is_in_warning_state")

        if device.support_tank_is_powerful_mode_active:
            sensor = DaikinSensor.factory(device, ATTR_TANK_IS_POWERFUL_MODE_ACTIVE,"TANK")
            _LOGGER.debug("append sensor = %s", sensor)
            sensors.append(sensor)
        else:
            _LOGGER.info("DAIKIN RESIDENTIAL ALTHERMA: device NOT supports is_powerful_mode_active")

    #for s in sensors:
    #    print("{} - {}".format(s.name,s.unique_id))
    #print("DAMIANO add_entities: %s", sensors)
    async_add_entities(sensors)


class DaikinSensor(SensorEntity):
    """Representation of a Sensor."""

    @staticmethod
    def factory(device: Appliance, monitored_state: str, type, period=""):
        """Initialize any DaikinSensor."""
        try:
            # DAMIANO
            #monitored_state = monitored_state.replace("T-@Tank","")
            print(type)
            cls = {
                SENSOR_TYPE_TEMPERATURE: DaikinClimateSensor,
                SENSOR_TYPE_POWER: DaikinEnergySensor,
                SENSOR_TYPE_ENERGY: DaikinEnergySensor,
                SENSOR_TYPE_INFO: DaikinInfoSensor,
            }[SENSOR_TYPES[monitored_state][CONF_TYPE]]
            return cls(device, monitored_state,type, period)
        except Exception as error:
            print("error: " + error)
            _LOGGER.error("%s", format(error))
            return

    def __init__(self, device: Appliance, monitored_state: str, type,  period="") -> None:
        """Initialize the sensor."""
        self._device = device
        self._sensor = SENSOR_TYPES[monitored_state]
        self._period = period
        if period != "":
            periodName = SENSOR_PERIODS[period]
            self._name = f"{device.name} {periodName} {self._sensor[CONF_NAME]}"
        else:
            if type == '':
                # Name for Heat Pump Flags
                self._name = f"{device.name} {self._sensor[CONF_NAME]}"
            elif type == 'TANK':
                # Name for Hot Water Tank Flags
                #self._name = f"{device.name} TANK {self._sensor[CONF_NAME]}"
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

    @property
    def device_info(self):
        """Return a device description for device registry."""
        return self._device.device_info()

    '''
    @property
    def state(self):
        """Return the internal state of the sensor."""
        if self._device_attribute == ATTR_CONTROL_MODE:
            return self._device.control_mode
        return None
    '''

    async def async_update(self):
        """Retrieve latest state."""
        await self._device.api.async_update()

class DaikinInfoSensor(DaikinSensor):
    """Representation of a Climate Sensor."""

    @property
    def state(self):
        """Return the internal state of the sensor."""
        print("state")
        if self._device_attribute == ATTR_SETPOINT_MODE:
            return self._device.setpoint_mode

        if self._device_attribute == ATTR_TANK_SETPOINT_MODE:
            return self._device.tank_setpoint_mode

        if self._device_attribute == ATTR_CONTROL_MODE:
            return self._device.control_mode

        if self._device_attribute == ATTR_IS_HOLIDAY_MODE_ACTIVE:
            return self._device.is_holiday_mode_active

        if self._device_attribute == ATTR_IS_IN_EMERGENCY_STATE:
            return self._device.is_in_emergency_state

        if self._device_attribute == ATTR_IS_IN_ERROR_STATE:
            return self._device.is_in_error_state

        if self._device_attribute == ATTR_IS_IN_INSTALLER_STATE:
            return self._device.is_in_installer_state

        if self._device_attribute == ATTR_IS_IN_WARNING_STATE:
            return self._device.is_in_warning_state

        if self._device_attribute == ATTR_TANK_HEATUP_MODE:
            return self._device.heatupMode            

        if self._device_attribute == ATTR_TANK_IS_HOLIDAY_MODE_ACTIVE:
            return self._device.tank_is_holiday_mode_active

        if self._device_attribute == ATTR_TANK_IS_IN_EMERGENCY_STATE:
            return self._device.tank_is_in_emergency_state

        if self._device_attribute == ATTR_TANK_IS_IN_ERROR_STATE:
            return self._device.tank_is_in_error_state

        if self._device_attribute == ATTR_TANK_IS_IN_INSTALLER_STATE:
            return self._device.tank_is_in_installer_state

        if self._device_attribute == ATTR_TANK_IS_IN_WARNING_STATE:
            return self._device.tank_is_in_warning_state

        if self._device_attribute == ATTR_TANK_IS_POWERFUL_MODE_ACTIVE:
            return self._device.tank_is_powerful_mode_active
        return None

    @property
    def state_class(self):
        return STATE_CLASS_MEASUREMENT

class DaikinClimateSensor(DaikinSensor):
    """Representation of a Climate Sensor."""

    @property
    def state(self):
        """Return the internal state of the sensor."""
        if self._device_attribute == ATTR_LEAVINGWATER_TEMPERATURE:
            return self._device.leaving_water_temperature

        if self._device_attribute == ATTR_OUTSIDE_TEMPERATURE:
            return self._device.outside_temperature

        if self._device_attribute == ATTR_TANK_TEMPERATURE:
            return self._device.tank_temperature

        if self._device_attribute == ATTR_ROOM_TEMPERATURE:
            return self._device.room_temperature

        return None

    @property
    def state_class(self):
        return STATE_CLASS_MEASUREMENT

class DaikinEnergySensor(DaikinSensor):
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

    @property
    def state_class(self):
        return STATE_CLASS_TOTAL_INCREASING
