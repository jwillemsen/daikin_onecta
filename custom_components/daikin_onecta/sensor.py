"""Support for Daikin AC sensors."""

import logging
import re

from homeassistant.components.sensor import CONF_STATE_CLASS
from homeassistant.components.sensor import SensorDeviceClass
from homeassistant.components.sensor import SensorEntity
from homeassistant.components.sensor import SensorStateClass
from homeassistant.const import CONF_DEVICE_CLASS
from homeassistant.const import CONF_ICON
from homeassistant.const import CONF_UNIT_OF_MEASUREMENT
from homeassistant.const import UnitOfEnergy
from homeassistant.core import callback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import COORDINATOR
from .const import DAIKIN_DEVICES
from .const import DOMAIN as DAIKIN_DOMAIN
from .const import ENABLED_DEFAULT
from .const import ENTITY_CATEGORY
from .const import SENSOR_PERIOD_WEEKLY
from .const import SENSOR_PERIODS
from .const import VALUE_SENSOR_MAPPING
from .daikin_base import Appliance

_LOGGER = logging.getLogger(__name__)


async def async_setup(hass, async_add_entities):
    """Old way of setting up the Daikin sensors.

    Can only be called when a user accidentally mentions the platform in their
    config. But even in that case it would have been ignored.
    """


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up Daikin climate based on config_entry."""
    coordinator = hass.data[DAIKIN_DOMAIN][COORDINATOR]
    sensors = []
    supported_management_point_types = {
        "domesticHotWaterTank",
        "domesticHotWaterFlowThrough",
        "climateControl",
        "climateControlMainZone",
    }
    for dev_id, device in hass.data[DAIKIN_DOMAIN][DAIKIN_DEVICES].items():
        management_points = device.daikin_data.get("managementPoints", [])
        for management_point in management_points:
            management_point_type = management_point["managementPointType"]
            if management_point_type != 'climateControl':
                continue

            embedded_id = management_point["embeddedId"]

            sd = management_point.get("sensoryData")
            if sd is not None:
                sensory_data = sd.get("value")
                if sensory_data is not None:
                    for sensor in sensory_data:
                        sensors.append(
                            DaikinValueSensor(
                                device,
                                coordinator,
                                embedded_id,
                                management_point_type,
                                "sensoryData",
                                sensor)
                        )

            cd = management_point.get("consumptionData")
            if cd is not None:
                # Retrieve the available operationModes, we can only provide consumption data for
                # supported operation modes
                operation_modes = management_point["operationMode"]["values"]
                cdv = cd.get("value")
                if cdv is not None:
                    cdve = cdv.get("electrical")
                    if cdve is not None:
                        for mode in cdve:
                            # Only handle consumptionData for an operation mode supported by this device
                            if mode in operation_modes:
                                icon = "mdi:fire"
                                if mode == "cooling":
                                    icon = "mdi:snowflake"
                                for period in cdve[mode]:
                                    sensors.append(DaikinEnergySensor(
                                        device,
                                        coordinator,
                                        embedded_id,
                                        management_point_type,
                                        mode,
                                        period,
                                        icon,
                                    ))

    async_add_entities(sensors)


class DaikinEnergySensor(CoordinatorEntity, SensorEntity):
    """Representation of a power/energy consumption sensor."""

    def __init__(
        self,
        device: Appliance,
        coordinator,
        embedded_id,
        management_point_type,
        operation_mode,
        period,
        icon,
    ) -> None:
        super().__init__(coordinator)
        self._device = device
        self._embedded_id = embedded_id
        self._management_point_type = management_point_type
        self._operation_mode = operation_mode
        self._period = period
        self._attr_name = f"{operation_mode.capitalize()} {SENSOR_PERIODS[period]} Electrical Consumption"
        self._attr_unique_id = f"{self._device.getId()}_{self._management_point_type}_electrical_{self._operation_mode}_{self._period}"
        self._attr_entity_category = None
        self._attr_icon = icon
        self._attr_has_entity_name = True
        self._attr_device_class = SensorDeviceClass.ENERGY
        self._attr_state_class = SensorStateClass.TOTAL_INCREASING
        self._attr_native_unit_of_measurement = UnitOfEnergy.KILO_WATT_HOUR
        self._attr_native_value = self.sensor_value()

    @callback
    def _handle_coordinator_update(self) -> None:
        self._attr_native_value = self.sensor_value()
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
                                    energy_values = [0 if v is None else v for v in cdve[mode].get(self._period)]
                                    start_index = 7 if self._period == SENSOR_PERIOD_WEEKLY else 12
                                    energy_value = round(sum(energy_values[start_index:]), 3)

        return energy_value

    @property
    def available(self):
        """Return the availability of the underlying device."""
        return self._device.available

    @property
    def device_info(self):
        """Return a device description for device registry."""
        return self._device.device_info()


class DaikinValueSensor(CoordinatorEntity, SensorEntity):

    def __init__(
        self,
        device: Appliance,
        coordinator,
        embedded_id,
        management_point_type,
        sub_type,
        value,
    ) -> None:
        super().__init__(coordinator)

        self._device = device
        self._embedded_id = embedded_id
        self._management_point_type = management_point_type
        self._sub_type = sub_type
        self._value = value
        self._attr_device_class = None
        self._attr_state_class = None
        self._attr_has_entity_name = True
        self._attr_native_unit_of_measurement = None
        self._attr_unique_id = f"{self._device.getId()}_{self._management_point_type}_{self._sub_type}_{self._value}"
        self._attr_native_value = self.sensor_value()

        myname = value[0].upper() + value[1:]
        readable = re.findall("[A-Z][^A-Z]*", myname)
        self._attr_name = f"{' '.join(readable)}"

        sensor_settings = VALUE_SENSOR_MAPPING.get(value)
        if sensor_settings is not None:
            self._attr_icon = sensor_settings[CONF_ICON]
            self._attr_device_class = sensor_settings[CONF_DEVICE_CLASS]
            self._attr_entity_registry_enabled_default = sensor_settings[ENABLED_DEFAULT]
            self._attr_state_class = sensor_settings[CONF_STATE_CLASS]
            self._attr_entity_category = sensor_settings[ENTITY_CATEGORY]
            self._attr_native_unit_of_measurement = sensor_settings[CONF_UNIT_OF_MEASUREMENT]

    @callback
    def _handle_coordinator_update(self) -> None:
        self._attr_native_value = self.sensor_value()
        self.async_write_ha_state()

    def sensor_value(self):
        res = None
        managementPoints = self._device.daikin_data.get("managementPoints", [])
        for management_point in managementPoints:
            if self._embedded_id == management_point["embeddedId"]:
                if self._sub_type is not None:
                    management_point = management_point.get(self._sub_type).get("value")
                cd = management_point.get(self._value)
                if cd is not None:
                    res = cd.get("value")
        _LOGGER.debug("Device '%s' sensor '%s' value '%s'", self._device.name, self._value, res)
        return res

    @property
    def available(self):
        """Return the availability of the underlying device."""
        return self._device.available

    @property
    def device_info(self):
        """Return a device description for device registry."""
        return self._device.device_info()
