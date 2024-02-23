"""Support for Daikin AirBase zones."""
from homeassistant.helpers.entity import ToggleEntity

from .daikin_base import Appliance

from homeassistant.const import (
    CONF_DEVICE_CLASS,
    CONF_ICON,
    CONF_NAME,
    CONF_TYPE,
    CONF_UNIT_OF_MEASUREMENT,
)

from .const import (
    DOMAIN as DAIKIN_DOMAIN,
    DAIKIN_DEVICES,
    ATTR_STATE_OFF,
    ATTR_STATE_ON,
    VALUE_SENSOR_MAPPING,
    ENABLED_DEFAULT,
    ENTITY_CATEGORY,
)

from homeassistant.components.sensor import (
    CONF_STATE_CLASS,
)

import logging
_LOGGER = logging.getLogger(__name__)

import re

async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up Daikin climate based on config_entry."""
    sensors = []
    prog = 0

    #sensor.altherma_daily_heat_energy_consumption, altherma_daily_heat_tank_energy_consumption
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
                    settable = vv.get("settable", False)
                    values = vv.get("values", [])
                    if value_value is not None and settable == True and "on" in values and "off" in values:
                        _LOGGER.info("Device '%s' provides switch on/off '%s'", device.name, value)
                        sensor2 = DaikinSwitch(device, embedded_id, management_point_type, value)
                        sensors.append(sensor2)

    async_add_entities(sensors)

class DaikinSwitch(ToggleEntity):

    def __init__(self, device: Appliance, embedded_id, management_point_type, value) -> None:
        _LOGGER.info("DaikinSwitch '%s' '%s'", management_point_type, value);
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
        self._attr_unique_id = f"{self._device.getId()}_{self._management_point_type}_{self._value}"
        _LOGGER.info("Device '%s:%s' supports sensor '%s'", device.name, self._embedded_id, self._attr_name)

    @property
    def available(self):
        """Return the availability of the underlying device."""
        return self._device.available

    @property
    def is_on(self):
        """Return the state of the switch."""
        result = None
        managementPoints = self._device.daikin_data.get("managementPoints", [])
        for management_point in managementPoints:
            if self._embedded_id == management_point["embeddedId"]:
                management_point_type = management_point["managementPointType"]
                if self._management_point_type == management_point_type:
                    cd = management_point.get(self._value)
                    if cd is not None:
                        result = cd.get("value")
        _LOGGER.debug("Device '%s' switch '%s' value '%s'", self._device.name, self._value, result)
        return result == "on"

    @property
    def device_info(self):
        """Return a device description for device registry."""
        return self._device.device_info()

    async def async_turn_on(self, **kwargs):
        """Turn the zone on."""
        result = await self._device.set_path(self._device.getId(), self._embedded_id, self._value, "", "on")
        if result is False:
          _LOGGER.warning("Device '%s' problem setting '%s' to on", self._device.name, self._value)
        else:
          for management_point in self._device.daikin_data["managementPoints"]:
              if self._embedded_id == management_point["embeddedId"]:
                  management_point_type = management_point["managementPointType"]
                  if self._management_point_type == management_point_type:
                    management_point[self._value]["value"] = "on"
        return result

    async def async_turn_off(self, **kwargs):
        """Turn the zone off."""
        result = await self._device.set_path(self._device.getId(), self._embedded_id, self._value, "", "off")
        if result is False:
          _LOGGER.warning("Device '%s' problem setting '%s' to off", self._device.name, self._value)
        else:
          for management_point in self._device.daikin_data["managementPoints"]:
              if self._embedded_id == management_point["embeddedId"]:
                  management_point_type = management_point["managementPointType"]
                  if self._management_point_type == management_point_type:
                    management_point[self._value]["value"] = "off"
        return result
