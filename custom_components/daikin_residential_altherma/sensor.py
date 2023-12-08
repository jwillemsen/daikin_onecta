"""Support for Daikin AC sensors."""

from unicodedata import name
from homeassistant.const import (
    CONF_DEVICE_CLASS,
    CONF_ICON,
    CONF_NAME,
    CONF_TYPE,
    CONF_UNIT_OF_MEASUREMENT,
    DEVICE_CLASS_ENERGY,
    ENERGY_KILO_WATT_HOUR,
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
    ATTR_LEAVINGWATER_TEMPERATURE,
    ATTR_LEAVINGWATER_OFFSET,
    ATTR_OUTSIDE_TEMPERATURE,
    ATTR_ROOM_TEMPERATURE,
    ATTR_TANK_TEMPERATURE,
    ATTR_SETPOINT_MODE,
    ATTR_OPERATION_MODE,
    ATTR_TANK_SETPOINT_MODE,
    ATTR_CONTROL_MODE,
    ATTR_IS_HOLIDAY_MODE_ACTIVE,
    ATTR_IS_IN_EMERGENCY_STATE,
    ATTR_IS_IN_ERROR_STATE,
    ATTR_IS_IN_INSTALLER_STATE,
    ATTR_IS_IN_WARNING_STATE,
    ATTR_ERROR_CODE,
    #TANK
    ATTR_TANK_OPERATION_MODE,
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
    SENSOR_PERIOD_WEEKLY,
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

    #sensor.altherma_daily_heat_energy_consumption, altherma_daily_heat_tank_energy_consumption
    for dev_id, device in hass.data[DAIKIN_DOMAIN][DAIKIN_DEVICES].items():
        if device.daikin_data["managementPoints"] is not None:
            for management_point in device.daikin_data["managementPoints"]:
                management_point_type = management_point["managementPointType"]
                embedded_id = management_point["embeddedId"]
                cd = management_point.get("consumptionData")
                if cd is not None:
                    _LOGGER.info("Device '%s' provides consumptionData", device.name)
                    # Retrieve the available operationModes, we can only provide consumption data for
                    # supported operation modes
                    operation_modes = management_point["operationMode"]["values"]
                    cdv = cd.get("value")
                    if cdv is not None:
                        cdve = cdv.get("electrical")
                        _LOGGER.info("Device '%s' provides electrical", device.name)
                        if cdve is not None:
                            for mode in cdve:
                                # Only handle consumptionData for an operation mode supported by this device
                                if mode in operation_modes:
                                    _LOGGER.info("Device '%s' provides mode %s %s", device.name, management_point_type, mode)
                                    icon = "mdi:fire"
                                    if mode == "cooling":
                                        icon = "mdi:snowflake"
                                    for period in cdve[mode]:
                                    #periods = {'d', 'w', 'm'}
                                    #for period in periods:
                                    #    if cdvem.get(period):
                                        _LOGGER.info("Device '%s:%s' provides mode %s %s supports period %s", device.name, embedded_id, management_point_type, mode, period)
                                        periodName = SENSOR_PERIODS[period]
                                        sensor = f"{device.name} {management_point_type} {mode} {periodName}"
                                        _LOGGER.info("Proposing sensor %s", sensor)
                                        sensorv = DaikinEnergySensor (device, embedded_id, management_point_type, mode,  period, icon)
                                        sensors.append(sensorv)
                                else:
                                    _LOGGER.info("Ignoring consumption data %s, not a supported operation_mode", mode)


        if device.getData(ATTR_LEAVINGWATER_TEMPERATURE) is not None:
            sensor = DaikinSensor.factory(device, ATTR_LEAVINGWATER_TEMPERATURE,"")
            sensors.append(sensor)
        else:
            _LOGGER.info("Device '%s' NOT supports '%s'", device.name, ATTR_LEAVINGWATER_TEMPERATURE)

        if device.getData(ATTR_LEAVINGWATER_OFFSET) is not None:
            sensor = DaikinSensor.factory(device, ATTR_LEAVINGWATER_OFFSET,"")
            sensors.append(sensor)
        else:
            _LOGGER.info("Device '%s' NOT supports '%s'", device.name, ATTR_LEAVINGWATER_OFFSET)

        if device.getData(ATTR_ROOM_TEMPERATURE) is not None:
            sensor = DaikinSensor.factory(device, ATTR_ROOM_TEMPERATURE,"")
            sensors.append(sensor)
        else:
            _LOGGER.info("Device '%s' NOT supports '%s'", device.name, ATTR_ROOM_TEMPERATURE)

        if device.getData(ATTR_TANK_TEMPERATURE) is not None:
            sensor = DaikinSensor.factory(device, ATTR_TANK_TEMPERATURE,"")
            sensors.append(sensor)
        else:
            _LOGGER.info("Device '%s' NOT supports '%s'", device.name, ATTR_TANK_TEMPERATURE)

        if device.getData(ATTR_OUTSIDE_TEMPERATURE) is not None:
            sensor = DaikinSensor.factory(device, ATTR_OUTSIDE_TEMPERATURE,"")
            sensors.append(sensor)
        else:
            _LOGGER.info("Device '%s' NOT supports '%s'", device.name, ATTR_OUTSIDE_TEMPERATURE)

        if device.getData(ATTR_OPERATION_MODE) is not None:
            sensor = DaikinSensor.factory(device, ATTR_OPERATION_MODE,"")
            sensors.append(sensor)
        else:
            _LOGGER.info("Device '%s' NOT supports '%s'", device.name, ATTR_OPERATION_MODE)

        if device.getData(ATTR_SETPOINT_MODE) is not None:
            sensor = DaikinSensor.factory(device, ATTR_SETPOINT_MODE,"")
            sensors.append(sensor)
        else:
            _LOGGER.info("Device '%s' NOT supports '%s'", device.name, ATTR_SETPOINT_MODE)

        if device.getData(ATTR_TANK_SETPOINT_MODE) is not None:
            sensor = DaikinSensor.factory(device, ATTR_TANK_SETPOINT_MODE,"")
            sensors.append(sensor)
        else:
            _LOGGER.info("Device '%s' NOT supports '%s'", device.name, ATTR_TANK_SETPOINT_MODE)

        if device.getData(ATTR_CONTROL_MODE) is not None:
            sensor = DaikinSensor.factory(device, ATTR_CONTROL_MODE,"")
            sensors.append(sensor)
        else:
            _LOGGER.info("Device '%s' NOT supports '%s'", device.name, ATTR_CONTROL_MODE)

        if device.getData(ATTR_IS_HOLIDAY_MODE_ACTIVE) is not None:
            sensor = DaikinSensor.factory(device, ATTR_IS_HOLIDAY_MODE_ACTIVE,"")
            sensors.append(sensor)
        else:
            _LOGGER.info("Device '%s' NOT supports '%s'", device.name, ATTR_IS_HOLIDAY_MODE_ACTIVE)

        if device.getData(ATTR_IS_IN_EMERGENCY_STATE) is not None:
            sensor = DaikinSensor.factory(device, ATTR_IS_IN_EMERGENCY_STATE,"")
            sensors.append(sensor)
        else:
            _LOGGER.info("Device '%s' NOT supports '%s'", device.name, ATTR_IS_IN_EMERGENCY_STATE)

        if device.getData(ATTR_IS_IN_ERROR_STATE) is not None:
            sensor = DaikinSensor.factory(device, ATTR_IS_IN_ERROR_STATE,"")
            sensors.append(sensor)
        else:
            _LOGGER.info("Device '%s' NOT supports '%s'", device.name, ATTR_IS_IN_ERROR_STATE)

        if device.getData(ATTR_IS_IN_INSTALLER_STATE) is not None:
            sensor = DaikinSensor.factory(device, ATTR_IS_IN_INSTALLER_STATE,"")
            sensors.append(sensor)
        else:
            _LOGGER.info("Device '%s' NOT supports '%s'", device.name, ATTR_IS_IN_INSTALLER_STATE)

        if device.getData(ATTR_IS_IN_WARNING_STATE) is not None:
            sensor = DaikinSensor.factory(device, ATTR_IS_IN_WARNING_STATE,"")
            sensors.append(sensor)
        else:
            _LOGGER.info("Device '%s' NOT supports '%s'", device.name, ATTR_IS_IN_WARNING_STATE)

        if device.getData(ATTR_ERROR_CODE) is not None:
            sensor = DaikinSensor.factory(device, ATTR_ERROR_CODE,"")
            sensors.append(sensor)
        else:
            _LOGGER.info("Device '%s' NOT supports '%s'", device.name, ATTR_ERROR_CODE)

        if device.getData(ATTR_WIFI_STRENGTH) is not None:
            sensor = DaikinSensor.factory(device, ATTR_WIFI_STRENGTH, "")
            sensors.append(sensor)
        else:
            _LOGGER.info("Device '%s' NOT supports '%s'", device.name, ATTR_WIFI_STRENGTH)

        if device.getData(ATTR_WIFI_SSID) is not None:
            sensor = DaikinSensor.factory(device, ATTR_WIFI_SSID, "")
            sensors.append(sensor)
        else:
            _LOGGER.info("Device '%s' NOT supports '%s'", device.name, ATTR_WIFI_STRENGTH)

        if device.getData(ATTR_LOCAL_SSID) is not None:
            sensor = DaikinSensor.factory(device, ATTR_LOCAL_SSID, "")
            sensors.append(sensor)
        else:
            _LOGGER.info("Device '%s' NOT supports '%s'", device.name, ATTR_LOCAL_SSID)

        if device.getData(ATTR_MAC_ADDRESS) is not None:
            sensor = DaikinSensor.factory(device, ATTR_MAC_ADDRESS, "")
            sensors.append(sensor)
        else:
            _LOGGER.info("Device '%s' NOT supports '%s'", device.name, ATTR_MAC_ADDRESS)

        if device.getData(ATTR_SERIAL_NUMBER) is not None:
            sensor = DaikinSensor.factory(device, ATTR_SERIAL_NUMBER, "")
            sensors.append(sensor)
        else:
            _LOGGER.info("Device '%s' NOT supports '%s'", device.name, ATTR_SERIAL_NUMBER)

        if device.getData(ATTR_TANK_HEATUP_MODE) is not None:
            sensor = DaikinSensor.factory(device, ATTR_TANK_HEATUP_MODE,"")
            sensors.append(sensor)
        else:
            _LOGGER.info("Device '%s' NOT supports '%s'", device.name, ATTR_TANK_HEATUP_MODE)

        if device.getData(ATTR_TANK_OPERATION_MODE) is not None:
            sensor = DaikinSensor.factory(device, ATTR_TANK_OPERATION_MODE,"TANK")
            sensors.append(sensor)
        else:
            _LOGGER.info("Device '%s' NOT supports '%s'", device.name, ATTR_TANK_OPERATION_MODE)

        if device.getData(ATTR_TANK_IS_HOLIDAY_MODE_ACTIVE) is not None:
            sensor = DaikinSensor.factory(device, ATTR_TANK_IS_HOLIDAY_MODE_ACTIVE,"TANK")
            sensors.append(sensor)
        else:
            _LOGGER.info("Device '%s' NOT supports '%s'", device.name, ATTR_TANK_IS_HOLIDAY_MODE_ACTIVE)

        if device.getData(ATTR_TANK_IS_IN_EMERGENCY_STATE) is not None:
            sensor = DaikinSensor.factory(device, ATTR_TANK_IS_IN_EMERGENCY_STATE,"TANK")
            sensors.append(sensor)
        else:
            _LOGGER.info("Device '%s' NOT supports '%s'", device.name, ATTR_TANK_IS_IN_EMERGENCY_STATE)

        if device.getData(ATTR_TANK_IS_IN_ERROR_STATE) is not None:
            sensor = DaikinSensor.factory(device, ATTR_TANK_IS_IN_ERROR_STATE,"TANK")
            sensors.append(sensor)
        else:
            _LOGGER.info("Device '%s' NOT supports '%s'", device.name, ATTR_TANK_IS_IN_ERROR_STATE)

        if device.getData(ATTR_TANK_IS_IN_INSTALLER_STATE) is not None:
            sensor = DaikinSensor.factory(device, ATTR_TANK_IS_IN_INSTALLER_STATE,"TANK")
            sensors.append(sensor)
        else:
            _LOGGER.info("Device '%s' NOT supports '%s'", device.name, ATTR_TANK_IS_IN_INSTALLER_STATE)

        if device.getData(ATTR_TANK_IS_IN_WARNING_STATE) is not None:
            sensor = DaikinSensor.factory(device, ATTR_TANK_IS_IN_WARNING_STATE,"TANK")
            sensors.append(sensor)
        else:
            _LOGGER.info("Device '%s' NOT supports '%s'", device.name, ATTR_TANK_IS_IN_WARNING_STATE)

        if device.getData(ATTR_TANK_IS_POWERFUL_MODE_ACTIVE) is not None:
            sensor = DaikinSensor.factory(device, ATTR_TANK_IS_POWERFUL_MODE_ACTIVE,"TANK")
            sensors.append(sensor)
        else:
            _LOGGER.info("Device '%s' NOT supports '%s'", device.name, ATTR_TANK_IS_POWERFUL_MODE_ACTIVE)

        if device.getData(ATTR_TANK_ERROR_CODE) is not None:
            sensor = DaikinSensor.factory(device, ATTR_TANK_ERROR_CODE,"TANK")
            sensors.append(sensor)
        else:
            _LOGGER.info("Device '%s' NOT supports '%s'", device.name, ATTR_TANK_ERROR_CODE)

    async_add_entities(sensors)

class DaikinSensor(SensorEntity):
    """Representation of a Sensor."""

    @staticmethod
    def factory(device: Appliance, monitored_state: str, type):
        """Initialize any DaikinSensor."""
        try:
            cls = {
                SENSOR_TYPE_TEMPERATURE: DaikinClimateSensor,
                SENSOR_TYPE_POWER: DaikinEnergySensor,
                SENSOR_TYPE_ENERGY: DaikinEnergySensor,
                SENSOR_TYPE_INFO: DaikinInfoSensor,
                SENSOR_TYPE_GATEWAY_DIAGNOSTIC: DaikinGatewaySensor,
            }[SENSOR_TYPES[monitored_state][CONF_TYPE]]
            return cls(device, monitored_state,type)
        except Exception as error:
            # print("error: " + error)
            _LOGGER.error("%s", format(error))
            return

    def __init__(self, device: Appliance, monitored_state: str, type) -> None:
        """Initialize the sensor."""
        self._device = device
        self._sensor = SENSOR_TYPES[monitored_state]
        if type == '':
            # Name for Heat Pump Flags
            self._name = f"{device.name} {self._sensor[CONF_NAME]}"
        elif type == 'TANK':
            # Name for Hot Water Tank Flags
            #self._name = f"{device.name} TANK {self._sensor[CONF_NAME]}"
            self._name = f"{device.name} {self._sensor[CONF_NAME]}"
        self._device_attribute = monitored_state
        _LOGGER.info("Device '%s' supports sensor '%s'", device.name, self._name)

    @property
    def available(self):
        """Return the availability of the underlying device."""
        return self._device.available

    @property
    def unique_id(self):
        """Return a unique ID."""
        devID = self._device.getId()
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
            if self._device_attribute in diagnosticList:
                return EntityCategory.DIAGNOSTIC
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
#                                    sensor = f"{device.name} {management_point_type} {mode} {periodName}"

    def __init__(self, device: Appliance, embedded_id, management_point_type, operation_mode,  period, icon) -> None:
        self._device = device
        self._icon = icon
        self._sensor = SENSOR_TYPE_ENERGY
        self._embedded_id = embedded_id
        self._management_point_type = management_point_type
        self._operation_mode = operation_mode
        self._period = period
        self._attr_entity_category = None
        periodName = SENSOR_PERIODS[period]
        self._name = f"{device.name} {management_point_type.capitalize()} {operation_mode.capitalize()} {periodName} Energy Consumption"
        _LOGGER.info("Device '%s'  %s supports sensor '%s'", self._embedded_id, device.name, self._name)

    @property
    def state(self):
        """Return the state of the sensor."""
        energy_value = None
        for management_point in self._device.daikin_data["managementPoints"]:
            if self._embedded_id == management_point["embeddedId"]:
                management_point_type = management_point["managementPointType"]
                cd = management_point.get("consumptionData")
                if cd is not None:
                    _LOGGER.info("Device '%s' provides consumptionData", self._device.name)
                    # Retrieve the available operationModes, we can only provide consumption data for
                    # supported operation modes
                    cdv = cd.get("value")
                    if cdv is not None:
                        cdve = cdv.get("electrical")
                        _LOGGER.info("Device '%s' provides electrical", self._device.name)
                        if cdve is not None:
                            for mode in cdve:
                                # Only handle consumptionData for an operation mode supported by this device
                                if mode == self._operation_mode:
                                    _LOGGER.info("Device '%s' has energy value for mode %s %s", self._device.name, management_point_type, mode)
                                    energy_values = [
                                        0 if v is None else v
                                        for v in cdve[mode].get(self._period)
                                    ]
                                    start_index = 7 if self._period == SENSOR_PERIOD_WEEKLY else 12
                                    #_LOGGER.info("%s", energy_values)
                                    #_LOGGER.info("%s", sum(energy_values[start_index:]))
                                    #value =
                                    energy_value = round(sum(energy_values[start_index:]), 3)

                                    #periods = {'d', 'w', 'm'}
                                    #for period in periods:
                                    #    if cdvem.get(period):
                                #     _LOGGER.info("Device '%s' provides mode %s %s supports period %s", device.name, management_point_type, mode, period)
                                #     periodName = SENSOR_PERIODS[period]
                                #     sensor = f"{device.name} {management_point_type} {mode} {periodName}"
                                #     _LOGGER.info("Proposing sensor %s", sensor)
                                # else:
                                #     _LOGGER.info("Ignoring consumption data %s, not a supported operation_mode", mode)

        return energy_value

    @property
    def unique_id(self):
        """Return a unique ID."""
        return f"{self._device.getId()}_{self._management_point_type}_{self._operation_mode}_{self._period}"

    @property
    def device_class(self):
        """Return the class of this device."""
        return DEVICE_CLASS_ENERGY

    @property
    def icon(self):
        """Return the icon of this device."""
        return self._icon

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement."""
        return ENERGY_KILO_WATT_HOUR

    @property
    def state_class(self):
        return STATE_CLASS_TOTAL_INCREASING

    @property
    def entity_category(self):
        return None

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
