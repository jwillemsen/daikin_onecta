"""Support for Daikin AC sensors."""

from unicodedata import name
from homeassistant.const import (
    CONF_DEVICE_CLASS,
    CONF_ICON,
    CONF_NAME,
    CONF_TYPE,
    CONF_UNIT_OF_MEASUREMENT,
    UnitOfEnergy,
)

from homeassistant.components.sensor import (
    SensorEntity,
    CONF_STATE_CLASS,
    SensorStateClass,
    SensorDeviceClass,
)

from homeassistant.helpers.entity import EntityCategory

from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)

from homeassistant.core import callback

from .daikin_base import Appliance

from .const import (
    DOMAIN as DAIKIN_DOMAIN,
    DAIKIN_DEVICES,
    SENSOR_TYPE_ENERGY,
    SENSOR_TYPE_POWER,
    SENSOR_PERIODS,
    SENSOR_PERIOD_WEEKLY,
    VALUE_SENSOR_MAPPING,
    ENABLED_DEFAULT,
    ENTITY_CATEGORY,
    COORDINATOR,
)

import logging
_LOGGER = logging.getLogger(__name__)

import re

async def async_setup(hass, async_add_entities):
    """Old way of setting up the Daikin sensors.

    Can only be called when a user accidentally mentions the platform in their
    config. But even in that case it would have been ignored.
    """

async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up Daikin climate based on config_entry."""
    sensors = []
    prog = 0
    coordinator = hass.data[DAIKIN_DOMAIN][COORDINATOR]

    for dev_id, device in hass.data[DAIKIN_DOMAIN][DAIKIN_DEVICES].items():
        managementPoints = device.daikin_data.get("managementPoints", [])
        for management_point in managementPoints:
            management_point_type = management_point["managementPointType"]
            embedded_id = management_point["embeddedId"]

            # For all values provide a "value" we provide a sensor
            for value in management_point:
                vv = management_point.get(value)
                if type(vv) == dict:
                    value_value = vv.get("value")
                    if value_value is not None and type(value_value) != dict:
                        sensor2 = DaikinValueSensor(device, coordinator, embedded_id, management_point_type, None, value)
                        sensors.append(sensor2)

            sd = management_point.get("sensoryData")
            if sd is not None:
                sensoryData = sd.get("value")
                _LOGGER.info("Device '%s' provides sensoryData '%s'", device.name, sensoryData)
                if sensoryData is not None:
                    for sensor in sensoryData:
                        _LOGGER.info("Device '%s' provides sensor '%s'", device.name, sensor)
                        sensor2 = DaikinValueSensor(device, coordinator, embedded_id, management_point_type, "sensoryData", sensor)
                        sensors.append(sensor2)

            cd = management_point.get("consumptionData")
            if cd is not None:
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
                                    _LOGGER.info("Device '%s:%s' provides mode %s %s supports period %s", device.name, embedded_id, management_point_type, mode, period)
                                    periodName = SENSOR_PERIODS[period]
                                    sensor = f"{device.name} {management_point_type} {mode} {periodName}"
                                    _LOGGER.info("Proposing sensor '%s'", sensor)
                                    sensorv = DaikinEnergySensor (device, coordinator, embedded_id, management_point_type, mode,  period, icon)
                                    sensors.append(sensorv)
                            else:
                                _LOGGER.info("Ignoring consumption data '%s', not a supported operation_mode", mode)

    async_add_entities(sensors)

class DaikinEnergySensor(CoordinatorEntity, SensorEntity):
    """Representation of a power/energy consumption sensor."""

    def __init__(self, device: Appliance, coordinator, embedded_id, management_point_type, operation_mode,  period, icon) -> None:
        super().__init__(coordinator)
        self._device = device
        self._embedded_id = embedded_id
        self._management_point_type = management_point_type
        self._operation_mode = operation_mode
        self._period = period
        periodName = SENSOR_PERIODS[period]
        mpt = management_point_type[0].upper() + management_point_type[1:]
        self._attr_name = f"{mpt} {operation_mode.capitalize()} {periodName} Electrical Consumption"
        self._attr_unique_id = f"{self._device.getId()}_{self._management_point_type}_{self._operation_mode}_{self._period}"
        self._attr_entity_category = None
        self._attr_icon = icon
        self._attr_has_entity_name = True
        self._state = self.sensor_value()
        _LOGGER.info("Device '%s:%s' supports sensor '%s'", device.name, self._embedded_id, self._attr_name)

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    @callback
    def _handle_coordinator_update(self) -> None:
        self._state = self.sensor_value()
        self.async_write_ha_state()

    def sensor_value(self):
        energy_value = None
        for management_point in self._device.daikin_data["managementPoints"]:
            if self._embedded_id == management_point["embeddedId"]:
                management_point_type = management_point["managementPointType"]
                cd = management_point.get("consumptionData")
                if cd is not None:
                    # Retrieve the available operationModes, we can only provide consumption data for
                    # supported operation modes
                    cdv = cd.get("value")
                    if cdv is not None:
                        cdve = cdv.get("electrical")
                        if cdve is not None:
                            for mode in cdve:
                                # Only handle consumptionData for an operation mode supported by this device
                                if mode == self._operation_mode:
                                    energy_values = [
                                        0 if v is None else v
                                        for v in cdve[mode].get(self._period)
                                    ]
                                    start_index = 7 if self._period == SENSOR_PERIOD_WEEKLY else 12
                                    energy_value = round(sum(energy_values[start_index:]), 3)
                                    _LOGGER.info("Device '%s' has energy value '%s' for mode %s %s period %s", self._device.name, energy_value, management_point_type, mode, self._period)

        return energy_value

    @property
    def available(self):
        """Return the availability of the underlying device."""
        return self._device.available

    @property
    def device_info(self):
        """Return a device description for device registry."""
        return self._device.device_info()

    @property
    def unit_of_measurement(self):
        return UnitOfEnergy.KILO_WATT_HOUR

    @property
    def state_class(self):
        return SensorStateClass.TOTAL_INCREASING

    @property
    def device_class(self):
        return SensorDeviceClass.ENERGY

class DaikinValueSensor(CoordinatorEntity, SensorEntity):

    def __init__(self, device: Appliance, coordinator, embedded_id, management_point_type, sub_type, value) -> None:
        _LOGGER.info("DaikinValueSensor '%s' '%s' '%s'", management_point_type, sub_type, value);
        super().__init__(coordinator)
        self._device = device
        self._embedded_id = embedded_id
        self._management_point_type = management_point_type
        self._sub_type = sub_type
        self._value = value
        self._unit_of_measurement = None
        self._device_class = None
        self._state_class = None
        self._attr_has_entity_name = True
        sensor_settings = VALUE_SENSOR_MAPPING.get(value)
        if sensor_settings is None:
            _LOGGER.info("No mapping of value '%s' to HA settings, consider adding it to VALUE_SENSOR_MAPPING", value);
        else:
            self._attr_icon = sensor_settings[CONF_ICON]
            self._device_class = sensor_settings[CONF_DEVICE_CLASS]
            self._unit_of_measurement = sensor_settings[CONF_UNIT_OF_MEASUREMENT]
            self._attr_entity_registry_enabled_default = sensor_settings[ENABLED_DEFAULT]
            self._state_class = sensor_settings[CONF_STATE_CLASS]
            self._attr_entity_category = sensor_settings[ENTITY_CATEGORY]
        mpt = management_point_type[0].upper() + management_point_type[1:]
        myname = value[0].upper() + value[1:]
        readable = re.findall('[A-Z][^A-Z]*', myname)
        self._attr_name = f"{mpt} {' '.join(readable)}"
        self._attr_unique_id = f"{self._device.getId()}_{self._management_point_type}_{self._sub_type}_{self._value}"
        self._state = self.sensor_value()
        _LOGGER.info("Device '%s:%s' supports sensor '%s'", device.name, self._embedded_id, self._attr_name)

    @callback
    def _handle_coordinator_update(self) -> None:
        self._state = self.sensor_value()
        self.async_write_ha_state()

    def sensor_value(self):
        res = None
        managementPoints = self._device.daikin_data.get("managementPoints", [])
        for management_point in managementPoints:
            if self._embedded_id == management_point["embeddedId"]:
                management_point_type = management_point["managementPointType"]
                if self._sub_type is not None:
                    management_point = management_point.get(self._sub_type).get("value")
                cd = management_point.get(self._value)
                if cd is not None:
                    res = cd.get("value")
        _LOGGER.debug("Device '%s' sensor '%s' value '%s'", self._device.name, self._value, res)
        return res

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    @property
    def available(self):
        """Return the availability of the underlying device."""
        return self._device.available

    @property
    def unit_of_measurement(self):
        return self._unit_of_measurement

    @property
    def state_class(self):
        return self._state_class

    @property
    def device_class(self):
        return self._device_class

    @property
    def device_info(self):
        """Return a device description for device registry."""
        return self._device.device_info()
