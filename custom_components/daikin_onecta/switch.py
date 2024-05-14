"""Support for Daikin AirBase zones."""
import logging
import re

from homeassistant.components.sensor import (
    CONF_STATE_CLASS,
)
from homeassistant.const import CONF_DEVICE_CLASS
from homeassistant.const import CONF_ICON
from homeassistant.const import CONF_UNIT_OF_MEASUREMENT
from homeassistant.core import callback
from homeassistant.helpers.entity import ToggleEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import COORDINATOR
from .const import DAIKIN_DEVICES
from .const import DOMAIN as DAIKIN_DOMAIN
from .const import ENABLED_DEFAULT
from .const import ENTITY_CATEGORY
from .const import VALUE_SENSOR_MAPPING
from .device import DaikinOnectaDevice

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up Daikin switches based on config_entry."""
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
            embedded_id = management_point["embeddedId"]

            # For all values provide a "value" we provide a sensor
            for value in management_point:
                vv = management_point.get(value)
                if isinstance(vv, dict):
                    value_value = vv.get("value")
                    settable = vv.get("settable", False)
                    values = vv.get("values", [])
                    # When the following check changes also update this in sensor.py
                    if value_value is not None and settable is True and "on" in values and "off" in values:
                        if value == "onOffMode" and management_point_type in supported_management_point_types:
                            # On/off is handled by the HWT and ClimateControl directly, so don't create a separate switch
                            pass
                        elif value == "powerfulMode" and management_point_type in supported_management_point_types:
                            # Powerful is handled by the HWT and ClimateControl directly, so don't create a separate switch
                            pass
                        else:
                            _LOGGER.info(
                                "Device '%s' provides switch on/off '%s'",
                                device.name,
                                value,
                            )
                            sensors.append(
                                DaikinSwitch(
                                    device,
                                    coordinator,
                                    embedded_id,
                                    management_point_type,
                                    value,
                                )
                            )

    async_add_entities(sensors)


class DaikinSwitch(CoordinatorEntity, ToggleEntity):
    def __init__(self, device: DaikinOnectaDevice, coordinator, embedded_id, management_point_type, value) -> None:
        _LOGGER.info("DaikinSwitch '%s' '%s'", management_point_type, value)
        super().__init__(coordinator)
        self._device = device
        self._embedded_id = embedded_id
        self._management_point_type = management_point_type
        self._value = value
        self._unit_of_measurement = None
        self._device_class = None
        self._state_class = None
        self._attr_has_entity_name = True
        sensor_settings = VALUE_SENSOR_MAPPING.get(value)
        if sensor_settings is None:
            _LOGGER.info(
                "No mapping of value '%s' to HA settings, consider adding it to VALUE_SENSOR_MAPPING",
                value,
            )
        else:
            self._attr_icon = sensor_settings[CONF_ICON]
            self._device_class = sensor_settings[CONF_DEVICE_CLASS]
            self._unit_of_measurement = sensor_settings[CONF_UNIT_OF_MEASUREMENT]
            self._attr_entity_registry_enabled_default = sensor_settings[ENABLED_DEFAULT]
            self._state_class = sensor_settings[CONF_STATE_CLASS]
            self._attr_entity_category = sensor_settings[ENTITY_CATEGORY]
        mpt = management_point_type[0].upper() + management_point_type[1:]
        myname = value[0].upper() + value[1:]
        readable = re.findall("[A-Z][^A-Z]*", myname)
        self._attr_name = f"{mpt} {' '.join(readable)}"
        self._attr_unique_id = f"{self._device.id}_{self._management_point_type}_{self._value}"
        self.update_state()
        _LOGGER.info(
            "Device '%s:%s' supports sensor '%s'",
            device.name,
            self._embedded_id,
            self._attr_name,
        )

    def update_state(self) -> None:
        self._switch_state = self.sensor_value()
        self._attr_device_info = self._device.device_info()

    @property
    def available(self) -> bool:
        return self._device.available

    @callback
    def _handle_coordinator_update(self) -> None:
        self.update_state()
        self.async_write_ha_state()

    @property
    def is_on(self):
        return self._switch_state == "on"

    def sensor_value(self):
        """Return the state of the switch."""
        result = ""
        managementPoints = self._device.daikin_data.get("managementPoints", [])
        for management_point in managementPoints:
            if self._embedded_id == management_point["embeddedId"]:
                management_point_type = management_point["managementPointType"]
                if self._management_point_type == management_point_type:
                    cd = management_point.get(self._value)
                    if cd is not None:
                        result = cd.get("value")
        _LOGGER.debug("Device '%s' switch '%s' value '%s'", self._device.name, self._value, result)
        return result

    async def async_turn_on(self, **kwargs):
        """Turn the zone on."""
        result = True
        if not self.is_on:
            result &= await self._device.patch(self._device.id, self._embedded_id, self._value, "", "on")
            if result is False:
                _LOGGER.warning("Device '%s' problem setting '%s' to on", self._device.name, self._value)
            else:
                self._switch_state = "on"
                self.async_write_ha_state()
        else:
            _LOGGER.debug("Device '%s' switch '%s' request to turn on ignored because is already on", self._device.name, self._value)

        return result

    async def async_turn_off(self, **kwargs):
        """Turn the zone off."""
        result = True
        if self.is_on:
            result &= await self._device.patch(self._device.id, self._embedded_id, self._value, "", "off")
            if result is False:
                _LOGGER.warning(
                    "Device '%s' problem setting '%s' to off",
                    self._device.name,
                    self._value,
                )
            else:
                self._switch_state = "off"
                self.async_write_ha_state()
        else:
            _LOGGER.debug("Device '%s' switch '%s' request to turn off ignored because is already off", self._device.name, self._value)

        return result
