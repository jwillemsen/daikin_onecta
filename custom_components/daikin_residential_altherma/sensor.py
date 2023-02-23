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

from homeassistant.helpers.entity import EntityCategory

from .daikin_base import Appliance

from .const import (
    DOMAIN as DAIKIN_DOMAIN,
    DAIKIN_DEVICES,
    ATTR_COOL_ENERGY,
    ATTR_HEAT_ENERGY,
    ATTR_HEAT_TANK_ENERGY,
    ATTR_LEAVINGWATER_TEMPERATURE,
    ATTR_LEAVINGWATER_OFFSET,
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
    ATTR_ERROR_CODE,
    #TANK
    ATTR_TANK_HEATUP_MODE,
    ATTR_TANK_IS_HOLIDAY_MODE_ACTIVE,
    ATTR_TANK_IS_IN_EMERGENCY_STATE,
    ATTR_TANK_IS_IN_ERROR_STATE,
    ATTR_TANK_IS_IN_INSTALLER_STATE,
    ATTR_TANK_IS_IN_WARNING_STATE,
    ATTR_TANK_IS_POWERFUL_MODE_ACTIVE,
    ATTR_TANK_ERROR_CODE,
    SENSOR_TYPE_ENERGY,
    SENSOR_TYPE_POWER,
    SENSOR_TYPE_TEMPERATURE,
    SENSOR_TYPE_INFO,
    SENSOR_TYPE_GATEWAY_DIAGNOSTIC,
    SENSOR_PERIODS,
    SENSOR_TYPES,
    ATTR_WIFI_STRENGTH,
    ATTR_WIFI_SSID,
    ATTR_LOCAL_SSID,
    ATTR_MAC_ADDRESS,
    ATTR_SERIAL_NUMBER,
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

        if device.getData(ATTR_LEAVINGWATER_OFFSET) is not None:
            sensor = DaikinSensor.factory(device, ATTR_LEAVINGWATER_OFFSET,"")
            sensors.append(sensor)
        else:
            _LOGGER.info("DAIKIN RESIDENTIAL ALTHERMA: device NOT supports room_leavingwater offset")

        if device.getData(ATTR_ROOM_TEMPERATURE) is not None:
            sensor = DaikinSensor.factory(device, ATTR_ROOM_TEMPERATURE,"")
            sensors.append(sensor)
        else:
            _LOGGER.info("DAIKIN RESIDENTIAL ALTHERMA: device NOT supports room_temperature")

        if device.getData(ATTR_TANK_TEMPERATURE) is not None:
            sensor = DaikinSensor.factory(device, ATTR_TANK_TEMPERATURE,"")
            sensors.append(sensor)
        else:
            _LOGGER.info("DAIKIN RESIDENTIAL ALTHERMA: device NOT supports tank_temperature")

        if device.getData(ATTR_OUTSIDE_TEMPERATURE) is not None:
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
                if device.getData(ATTR_TANK_TEMPERATURE) is not None:
                    sensor = DaikinSensor.factory(device, ATTR_HEAT_TANK_ENERGY,"", period)
                    _LOGGER.debug("append sensor = %s", sensor)
                    sensors.append(sensor)
                else:
                    _LOGGER.info("DAIKIN RESIDENTIAL ALTHERMA: device NOT support_tank_temperature")
        else:
            _LOGGER.info("DAIKIN RESIDENTIAL ALTHERMA: device NOT supports energy_consumption")

        if device.getData(ATTR_SETPOINT_MODE) is not None:
            sensor = DaikinSensor.factory(device, ATTR_SETPOINT_MODE,"")
            _LOGGER.debug("append sensor = %s", sensor)
            sensors.append(sensor)
        else:
            _LOGGER.info("DAIKIN RESIDENTIAL ALTHERMA: device NOT support setpoint_mode", sensor)

        if device.getData(ATTR_TANK_SETPOINT_MODE) is not None:
            sensor = DaikinSensor.factory(device, ATTR_TANK_SETPOINT_MODE,"")
            _LOGGER.debug("append sensor = %s", sensor)
            sensors.append(sensor)
        else:
            _LOGGER.info("DAIKIN RESIDENTIAL ALTHERMA: device NOT support tank setpoint_mode", sensor)

        if device.getData(ATTR_CONTROL_MODE) is not None:
            sensor = DaikinSensor.factory(device, ATTR_CONTROL_MODE,"")
            _LOGGER.debug("append sensor = %s", sensor)
            sensors.append(sensor)
        else:
            _LOGGER.info("DAIKIN RESIDENTIAL ALTHERMA: device NOT support control_mode", sensor)

        if device.getData(ATTR_IS_HOLIDAY_MODE_ACTIVE) is not None:
            sensor = DaikinSensor.factory(device, ATTR_IS_HOLIDAY_MODE_ACTIVE,"")
            _LOGGER.debug("append sensor = %s", sensor)
            sensors.append(sensor)
        else:
            _LOGGER.info("DAIKIN RESIDENTIAL ALTHERMA: device NOT supports is_holiday_mode_active")

        if device.getData(ATTR_IS_IN_EMERGENCY_STATE) is not None:
            sensor = DaikinSensor.factory(device, ATTR_IS_IN_EMERGENCY_STATE,"")
            _LOGGER.debug("append sensor = %s", sensor)
            sensors.append(sensor)
        else:
            _LOGGER.info("DAIKIN RESIDENTIAL ALTHERMA: device NOT supports is_in_emergency_state")

        if device.getData(ATTR_IS_IN_ERROR_STATE) is not None:
            sensor = DaikinSensor.factory(device, ATTR_IS_IN_ERROR_STATE,"")
            _LOGGER.debug("append sensor = %s", sensor)
            sensors.append(sensor)
        else:
            _LOGGER.info("DAIKIN RESIDENTIAL ALTHERMA: device NOT supports is_in_error_state")

        if device.getData(ATTR_IS_IN_INSTALLER_STATE) is not None:
            sensor = DaikinSensor.factory(device, ATTR_IS_IN_INSTALLER_STATE,"")
            _LOGGER.debug("append sensor = %s", sensor)
            sensors.append(sensor)
        else:
            _LOGGER.info("DAIKIN RESIDENTIAL ALTHERMA: device NOT supports is_in_installer_state")

        if device.getData(ATTR_IS_IN_WARNING_STATE) is not None:
            sensor = DaikinSensor.factory(device, ATTR_IS_IN_WARNING_STATE,"")
            _LOGGER.debug("append sensor = %s", sensor)
            sensors.append(sensor)
        else:
            _LOGGER.info("DAIKIN RESIDENTIAL ALTHERMA: device NOT supports is_in_warning_state")

        if device.getData(ATTR_ERROR_CODE) is not None:
            sensor = DaikinSensor.factory(device, ATTR_ERROR_CODE,"")
            _LOGGER.debug("append sensor = %s", sensor)
            sensors.append(sensor)
        else:
            _LOGGER.info("DAIKIN RESIDENTIAL ALTHERMA: device NOT supports error code")

        if device.getData(ATTR_WIFI_STRENGTH) is not None:
            _LOGGER.debug("device %s supports wifi signal strength", device.name)
            sensor = DaikinSensor.factory(device, ATTR_WIFI_STRENGTH, "")
            sensors.append(sensor)
        if device.getData(ATTR_WIFI_SSID) is not None:
            _LOGGER.debug("device %s supports wifi ssid", device.name)
            sensor = DaikinSensor.factory(device, ATTR_WIFI_SSID, "")
            sensors.append(sensor)
        if device.getData(ATTR_LOCAL_SSID) is not None:
            _LOGGER.debug("device %s supports local ssid", device.name)
            sensor = DaikinSensor.factory(device, ATTR_LOCAL_SSID, "")
            sensors.append(sensor)
        if device.getData(ATTR_MAC_ADDRESS) is not None:
            _LOGGER.debug("device %s supports mac address", device.name)
            sensor = DaikinSensor.factory(device, ATTR_MAC_ADDRESS, "")
            sensors.append(sensor)
        if device.getData(ATTR_SERIAL_NUMBER) is not None:
            _LOGGER.debug("device %s supports serial number", device.name)
            sensor = DaikinSensor.factory(device, ATTR_SERIAL_NUMBER, "")
            sensors.append(sensor)

        #heatup
        if device.getData(ATTR_TANK_HEATUP_MODE) is not None:
            sensor = DaikinSensor.factory(device, ATTR_TANK_HEATUP_MODE,"")
            _LOGGER.debug("append sensor = %s", sensor)
            sensors.append(sensor)
        else:
            _LOGGER.info("DAIKIN RESIDENTIAL ALTHERMA: device NOT supports support_heatupMode")

        # TANK
        # TODO: ripartire da qui
        if device.getData(ATTR_TANK_IS_HOLIDAY_MODE_ACTIVE) is not None:
            sensor = DaikinSensor.factory(device, ATTR_TANK_IS_HOLIDAY_MODE_ACTIVE,"TANK")
            _LOGGER.debug("append sensor = %s", sensor)
            sensors.append(sensor)
        else:
            _LOGGER.info("DAIKIN RESIDENTIAL ALTHERMA: device NOT supports is_holiday_mode_active")

        if device.getData(ATTR_TANK_IS_IN_EMERGENCY_STATE) is not None:
            sensor = DaikinSensor.factory(device, ATTR_TANK_IS_IN_EMERGENCY_STATE,"TANK")
            _LOGGER.debug("append sensor = %s", sensor)
            sensors.append(sensor)
        else:
            _LOGGER.info("DAIKIN RESIDENTIAL ALTHERMA: device NOT supports is_in_emergency_state")

        if device.getData(ATTR_TANK_IS_IN_ERROR_STATE) is not None:
            sensor = DaikinSensor.factory(device, ATTR_TANK_IS_IN_ERROR_STATE,"TANK")
            _LOGGER.debug("append sensor = %s", sensor)
            sensors.append(sensor)
        else:
            _LOGGER.info("DAIKIN RESIDENTIAL ALTHERMA: device NOT supports is_in_error_state")

        if device.getData(ATTR_TANK_IS_IN_INSTALLER_STATE) is not None:
            sensor = DaikinSensor.factory(device, ATTR_TANK_IS_IN_INSTALLER_STATE,"TANK")
            _LOGGER.debug("append sensor = %s", sensor)
            sensors.append(sensor)
        else:
            _LOGGER.info("DAIKIN RESIDENTIAL ALTHERMA: device NOT supports is_in_installer_state")

        if device.getData(ATTR_TANK_IS_IN_WARNING_STATE) is not None:
            sensor = DaikinSensor.factory(device, ATTR_TANK_IS_IN_WARNING_STATE,"TANK")
            _LOGGER.debug("append sensor = %s", sensor)
            sensors.append(sensor)
        else:
            _LOGGER.info("DAIKIN RESIDENTIAL ALTHERMA: device NOT supports is_in_warning_state")

        if device.getData(ATTR_TANK_IS_POWERFUL_MODE_ACTIVE) is not None:
            sensor = DaikinSensor.factory(device, ATTR_TANK_IS_POWERFUL_MODE_ACTIVE,"TANK")
            _LOGGER.debug("append sensor = %s", sensor)
            sensors.append(sensor)
        else:
            _LOGGER.info("DAIKIN RESIDENTIAL ALTHERMA: device NOT supports is_powerful_mode_active")

        if device.getData(ATTR_TANK_ERROR_CODE) is not None:
            sensor = DaikinSensor.factory(device, ATTR_TANK_ERROR_CODE,"TANK")
            _LOGGER.debug("append sensor = %s", sensor)
            sensors.append(sensor)
        else:
            _LOGGER.info("DAIKIN RESIDENTIAL ALTHERMA: device NOT supports tank error code")

    async_add_entities(sensors)


class DaikinSensor(SensorEntity):
    """Representation of a Sensor."""

    @staticmethod
    def factory(device: Appliance, monitored_state: str, type, period=""):
        """Initialize any DaikinSensor."""
        try:
            cls = {
                SENSOR_TYPE_TEMPERATURE: DaikinClimateSensor,
                SENSOR_TYPE_POWER: DaikinEnergySensor,
                SENSOR_TYPE_ENERGY: DaikinEnergySensor,
                SENSOR_TYPE_INFO: DaikinInfoSensor,
                SENSOR_TYPE_GATEWAY_DIAGNOSTIC: DaikinGatewaySensor,
            }[SENSOR_TYPES[monitored_state][CONF_TYPE]]
            return cls(device, monitored_state,type, period)
        except Exception as error:
            # print("error: " + error)
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
        _LOGGER.info("Initialized sensor: {}".format(self._name))

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

    @property
    def entity_category(self):
        """
        Return the entity_category the sensor.
        CONFIG:Set to config for an entity which allows changing the configuration
         of a device, for example a switch entity making it possible to turn the
         background illumination of a switch on and off.

        DIAGNOSTIC: Set to diagnostic for an entity exposing some configuration
         parameter or diagnostics of a device but does not allow changing it,

        SYSTEM: Set to system for an entity which is not useful for the user
         to interact with. """

        configList = [
            ATTR_SETPOINT_MODE,
            ATTR_TANK_SETPOINT_MODE,
            ATTR_CONTROL_MODE,
            ATTR_IS_HOLIDAY_MODE_ACTIVE,
            ATTR_TANK_HEATUP_MODE,
            ATTR_TANK_IS_HOLIDAY_MODE_ACTIVE,
            ATTR_TANK_IS_POWERFUL_MODE_ACTIVE
            ]
        diagnosticList =[
            ATTR_IS_IN_EMERGENCY_STATE,
            ATTR_IS_IN_ERROR_STATE,
            ATTR_IS_IN_INSTALLER_STATE,
            ATTR_IS_IN_WARNING_STATE,
            ATTR_ERROR_CODE,
            ATTR_TANK_IS_IN_EMERGENCY_STATE,
            ATTR_TANK_IS_IN_ERROR_STATE,
            ATTR_TANK_IS_IN_INSTALLER_STATE,
            ATTR_TANK_IS_IN_WARNING_STATE,
            ATTR_TANK_ERROR_CODE,
            ATTR_WIFI_STRENGTH,
            ATTR_WIFI_SSID,
            ATTR_LOCAL_SSID,
            ATTR_MAC_ADDRESS,
            ATTR_SERIAL_NUMBER,
            ]
        try:
            if self._device_attribute in configList:
                self._entity_category = EntityCategory.CONFIG
                return self._entity_category
            elif self._device_attribute in diagnosticList:
                self._entity_category = EntityCategory.DIAGNOSTIC
                return self._entity_category

            else:
                return None
        except Exception as e:
            _LOGGER.info("entity_category not supported by this Home Assistant. /n \
                    Try to update")
            return None

    async def async_update(self):
        """Retrieve latest state."""
        await self._device.api.async_update()

class DaikinInfoSensor(DaikinSensor):
    """Representation of a Climate Sensor."""

    @property
    def state(self):
        """Return the internal state of the sensor."""
        return self._device.getValue(self._device_attribute)

    @property
    def state_class(self):
        return STATE_CLASS_MEASUREMENT

class DaikinClimateSensor(DaikinSensor):
    """Representation of a Climate Sensor."""

    @property
    def state(self):
        """Return the internal state of the sensor."""
        return self._device.getValue(self._device_attribute)

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

class DaikinGatewaySensor(DaikinSensor):
    """Representation of a WiFi Sensor."""

    # set default category for these entities
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    @property
    def state(self):
        """Return the internal state of the sensor."""
        return self._device.getValue(self._device_attribute)

    @property
    def state_class(self):
        if self._device_attribute == ATTR_WIFI_STRENGTH:
            return STATE_CLASS_MEASUREMENT
        else:
            return None

    @property
    def entity_registry_enabled_default(self):
        # auto disable these entities when added for the first time
        # except the wifi signal
        return self._device_attribute == ATTR_WIFI_STRENGTH
