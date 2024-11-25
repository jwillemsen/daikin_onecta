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
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import COORDINATOR
from .const import DAIKIN_API
from .const import DAIKIN_DEVICES
from .const import DOMAIN as DAIKIN_DOMAIN
from .const import ENABLED_DEFAULT
from .const import ENTITY_CATEGORY
from .const import SENSOR_PERIOD_WEEKLY
from .const import SENSOR_PERIODS
from .const import VALUE_SENSOR_MAPPING
from .device import DaikinOnectaDevice

_LOGGER = logging.getLogger(__name__)


async def async_setup(hass, async_add_entities):
    """Old way of setting up the Daikin sensors.

    Can only be called when a user accidentally mentions the platform in their
    config. But even in that case it would have been ignored.
    """


def handle_energy_sensors(coordinator, device, embedded_id, management_point_type, operation_modes, sensor_type, cdve, sensors):
    _LOGGER.info("Device '%s' provides '%s'", device.name, sensor_type)
    for mode in cdve:
        # Only handle consumptionData for an operation mode supported by this device
        if mode in operation_modes:
            _LOGGER.info(
                "Device '%s' provides mode %s %s",
                device.name,
                management_point_type,
                mode,
            )
            for period in cdve[mode]:
                _LOGGER.info(
                    "Device '%s:%s' provides mode %s %s supports period %s",
                    device.name,
                    embedded_id,
                    management_point_type,
                    mode,
                    period,
                )
                periodName = SENSOR_PERIODS[period]
                sensor = f"{device.name} {sensor_type} {management_point_type} {mode} {periodName}"
                _LOGGER.info("Proposing sensor '%s'", sensor)
                sensors.append(DaikinEnergySensor(device, coordinator, embedded_id, management_point_type, sensor_type, mode, period))
        else:
            _LOGGER.info(
                "Ignoring consumption data '%s', not a supported operation_mode",
                mode,
            )


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up Daikin climate based on config_entry."""
    coordinator = hass.data[DAIKIN_DOMAIN][COORDINATOR]
    daikin_api = hass.data[DAIKIN_DOMAIN][DAIKIN_API]
    sensors = []
    supported_management_point_types = {
        "domesticHotWaterTank",
        "domesticHotWaterFlowThrough",
        "climateControl",
        "climateControlMainZone",
    }
    for dev_id, device in hass.data[DAIKIN_DOMAIN][DAIKIN_DEVICES].items():
        # For each rate limit we provide a sensor
        for name in daikin_api.rate_limits.keys():
            sensors.append(DaikinLimitSensor(hass, device, coordinator, name))

        management_points = device.daikin_data.get("managementPoints", [])
        for management_point in management_points:
            management_point_type = management_point["managementPointType"]
            embedded_id = management_point["embeddedId"]

            # For all values provide a "value" we provide a sensor
            for value in management_point:
                vv = management_point.get(value)
                if isinstance(vv, dict):
                    value_value = vv.get("value")
                    settable = vv.get("settable", False)
                    values = vv.get("values", [])
                    if value_value is not None and settable is True and "on" in values and "off" in values:
                        # Don't create when it is settable and values on/off, that is a switch
                        pass
                    elif len(values) == 0 and value_value is not None and isinstance(value_value, bool):
                        # We don't have mutiple values and the value is a bool, this is a binary sensor
                        pass
                    elif value == "operationMode" and management_point_type in supported_management_point_types:
                        # operationMode is handled by the HWT and ClimateControl directly, so don't create a separate sensor for that
                        pass
                    elif value_value is not None and not isinstance(value_value, dict):
                        sensors.append(
                            DaikinValueSensor(
                                device,
                                coordinator,
                                embedded_id,
                                management_point_type,
                                None,
                                value,
                            )
                        )

            sd = management_point.get("sensoryData")
            if sd is not None:
                sensory_data = sd.get("value")
                _LOGGER.info("Device '%s' provides sensoryData '%s'", device.name, sensory_data)
                if sensory_data is not None:
                    for sensor in sensory_data:
                        _LOGGER.info("Device '%s' provides sensor '%s'", device.name, sensor)
                        sensors.append(
                            DaikinValueSensor(
                                device,
                                coordinator,
                                embedded_id,
                                management_point_type,
                                "sensoryData",
                                sensor,
                            )
                        )

            cd = management_point.get("consumptionData")
            if cd is not None:
                # Retrieve the available operationModes, we can only provide consumption data for
                # supported operation modes
                opmode = management_point.get("operationMode")
                if opmode is not None:
                    operation_modes = opmode["values"]
                    cdv = cd.get("value")
                    if cdv is not None:
                        for type in ["electrical", "gas"]:
                            cdve = cdv.get(type)
                            if cdve is not None:
                                handle_energy_sensors(coordinator, device, embedded_id, management_point_type, operation_modes, type, cdve, sensors)

    async_add_entities(sensors)


class DaikinEnergySensor(CoordinatorEntity, SensorEntity):
    """Representation of a power/energy consumption sensor."""

    def __init__(
        self,
        device: DaikinOnectaDevice,
        coordinator,
        embedded_id,
        management_point_type,
        sensor_type,
        operation_mode,
        period,
    ) -> None:
        super().__init__(coordinator)
        self._device = device
        self._embedded_id = embedded_id
        self._management_point_type = management_point_type
        self._operation_mode = operation_mode
        self._period = period
        periodName = SENSOR_PERIODS[period]
        mpt = management_point_type[0].upper() + management_point_type[1:]
        self._attr_name = f"{mpt} {operation_mode.capitalize()} {periodName} {sensor_type.capitalize()} Consumption"
        self._attr_unique_id = f"{self._device.id}_{self._management_point_type}_{sensor_type}_{self._operation_mode}_{self._period}"
        self._attr_entity_category = None
        self._attr_icon = "mdi:fire"
        if operation_mode == "cooling":
            self._attr_icon = "mdi:snowflake"
        self._attr_has_entity_name = True
        self._attr_device_class = SensorDeviceClass.ENERGY
        self._attr_state_class = SensorStateClass.TOTAL_INCREASING
        self._attr_native_unit_of_measurement = UnitOfEnergy.KILO_WATT_HOUR
        self._sensor_type = sensor_type
        self.update_state()
        _LOGGER.info(
            "Device '%s:%s' supports sensor '%s'",
            device.name,
            self._embedded_id,
            self._attr_name,
        )

    def update_state(self) -> None:
        self._attr_native_value = self.sensor_value()
        self._attr_device_info = self._device.device_info()

    @property
    def available(self) -> bool:
        return self._device.available

    @callback
    def _handle_coordinator_update(self) -> None:
        self.update_state()
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
                        cdve = cdv.get(self._sensor_type)
                        if cdve is not None:
                            for mode in cdve:
                                # Only handle consumptionData for an operation mode supported by this device
                                if mode == self._operation_mode:
                                    energy_values = [0 if v is None else v for v in cdve[mode].get(self._period)]
                                    start_index = 7 if self._period == SENSOR_PERIOD_WEEKLY else 12
                                    energy_value = round(sum(energy_values[start_index:]), 3)
                                    _LOGGER.info(
                                        "Device '%s' has energy value '%s' for '%s' mode %s %s period %s",
                                        self._device.name,
                                        energy_value,
                                        self._sensor_type,
                                        management_point_type,
                                        mode,
                                        self._period,
                                    )

        return energy_value


class DaikinValueSensor(CoordinatorEntity, SensorEntity):
    def __init__(
        self,
        device: DaikinOnectaDevice,
        coordinator,
        embedded_id,
        management_point_type,
        sub_type,
        value,
    ) -> None:
        _LOGGER.info("DaikinValueSensor '%s' '%s' '%s'", management_point_type, sub_type, value)
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
        sensor_settings = VALUE_SENSOR_MAPPING.get(value)
        if sensor_settings is None:
            _LOGGER.info(
                "No mapping of value '%s' to HA settings, consider adding it to VALUE_SENSOR_MAPPING",
                value,
            )
        else:
            self._attr_icon = sensor_settings[CONF_ICON]
            self._attr_device_class = sensor_settings[CONF_DEVICE_CLASS]
            self._attr_entity_registry_enabled_default = sensor_settings[ENABLED_DEFAULT]
            self._attr_state_class = sensor_settings[CONF_STATE_CLASS]
            self._attr_entity_category = sensor_settings[ENTITY_CATEGORY]
            self._attr_native_unit_of_measurement = sensor_settings[CONF_UNIT_OF_MEASUREMENT]
        mpt = management_point_type[0].upper() + management_point_type[1:]
        myname = value[0].upper() + value[1:]
        readable = re.findall("[A-Z][^A-Z]*", myname)
        self._attr_name = f"{mpt} {' '.join(readable)}"
        self._attr_unique_id = f"{self._device.id}_{self._management_point_type}_{self._sub_type}_{self._value}"
        self._attr_translation_key = f"{self._management_point_type.lower()}_{self._value.lower()}"
        self.update_state()
        _LOGGER.info(
            "Device '%s:%s' supports sensor '%s'",
            device.name,
            self._embedded_id,
            self._value,
        )

    def update_state(self) -> None:
        self._attr_native_value = self.sensor_value()
        self._attr_device_info = self._device.device_info()

    @property
    def available(self) -> bool:
        return self._device.available

    @callback
    def _handle_coordinator_update(self) -> None:
        self.update_state()
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


class DaikinLimitSensor(CoordinatorEntity, SensorEntity):
    def __init__(
        self,
        hass: HomeAssistant,
        device: DaikinOnectaDevice,
        coordinator,
        limit_key,
    ) -> None:
        _LOGGER.info("Device '%s' LimitSensor '%s'", device.name, limit_key)
        super().__init__(coordinator)
        self._hass = hass
        self._device = device
        self._limit_key = limit_key
        self._attr_has_entity_name = True
        self._attr_icon = "mdi:information-outline"
        self._attr_entity_category = EntityCategory.DIAGNOSTIC
        self._attr_name = f"RateLimit {self._limit_key}"
        self._attr_unique_id = f"{self._device.id}_limitsensor_{self._limit_key}"
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self.update_state()
        _LOGGER.info(
            "Device '%s' supports sensor '%s'",
            device.name,
            self._attr_name,
        )

    def update_state(self) -> None:
        self._attr_device_info = self._device.device_info()
        self._attr_native_value = self.sensor_value()

    @callback
    def _handle_coordinator_update(self) -> None:
        self.update_state()
        self.async_write_ha_state()

    def sensor_value(self):
        daikin_api = self._hass.data[DAIKIN_DOMAIN][DAIKIN_API]
        return daikin_api.rate_limits[self._limit_key]

    @property
    def device_info(self):
        """Return a device description for device registry."""
        return self._device.device_info()
