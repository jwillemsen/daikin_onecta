from homeassistant.components.select import SelectEntity
from homeassistant.helpers import entity_platform

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

async def async_setup_entry(hass, entry, async_add_entities):
    """Set up Daikin climate based on config_entry."""
    sensors = []
    prog = 0

    for dev_id, device in hass.data[DAIKIN_DOMAIN][DAIKIN_DEVICES].items():
        managementPoints = device.daikin_data("managementPoints", [])
        for management_point in managementPoints:
            management_point_type = management_point["managementPointType"]
            embedded_id = management_point["embeddedId"]

            # When we have a demandControl we provide a select sensor
            demand = management_point.get("demandControl")
            if demand is not None:
                _LOGGER.info("Device '%s' provides demandControl", device.name)
                sensor2 = DaikinDemandSelect(device, embedded_id, management_point_type, "demandControl")
                sensors.append(sensor2)

    async_add_entities(sensors)

class DaikinDemandSelect(SelectEntity):
    """myenergi Sensor class."""

    def __init__(self, device: Appliance, embedded_id, management_point_type, value) -> None:
        _LOGGER.info("DaikinDemandSelect '%s' '%s'", management_point_type, value);
        self._device = device
        self._embedded_id = embedded_id
        self._management_point_type = management_point_type
        self._value = value
        mpt = management_point_type[0].upper() + management_point_type[1:]
        myname = value[0].upper() + value[1:]
        readable = re.findall('[A-Z][^A-Z]*', myname)
        self._attr_name = f"{mpt} {' '.join(readable)}"
        self._attr_unique_id = f"{self._device.getId()}_{self._management_point_type}_{self._value}"
        self._attr_has_entity_name = True
        _LOGGER.info("Device '%s:%s' supports sensor '%s'", device.name, self._embedded_id, self._attr_name)

    @property
    def available(self):
        """Return the availability of the underlying device."""
        return self._device.available

    @property
    def current_option(self):
        """Return the state of the sensor."""
        res = None
        managementPoints = self.daikin_data.get("managementPoints", [])
        for management_point in managementPoints:
            if self._embedded_id == management_point["embeddedId"]:
                management_point_type = management_point["managementPointType"]
                if self._management_point_type == management_point_type:
                    vv = management_point[self._value]
                    mode = vv["value"]["currentMode"]["value"]
                    if mode == "scheduled":
                        pass
                    elif mode == "fixed":
                        res = str(vv["value"]["modes"]["fixed"]["value"])
                    else:
                        res = mode
        return res

    async def async_select_option(self, option: str) -> None:
        mode = None
        managementPoints = self._device.daikin_data.get("managementPoints")
        if managementPoints is not None:
            for management_point in managementPoints:
                if self._embedded_id == management_point["embeddedId"]:
                    management_point_type = management_point["managementPointType"]
                    if self._management_point_type == management_point_type:
                        vv = management_point[self._value]
                        mode = vv["value"]["currentMode"]
            new_currentmode = "fixed"
            if option in ("auto", "off"):
                new_currentmode = option
            res = await self._device.set_path(self._device.getId(), self._embedded_id, "demandControl", f"/currentMode", new_currentmode)
            if res is False:
                _LOGGER.warning("Device '%s' problem setting demand control to %s", self._device.name, option)
            else:
                mode["value"] = new_currentmode

            if new_currentmode == "fixed":
                res = await self._device.set_path(self._device.getId(), self._embedded_id, "demandControl", f"/modes/fixed", int(option))
                if res is False:
                    _LOGGER.warning("Device '%s' problem setting demand control to fixed value %s", self._device.name, option)
                else:
                    vv["value"]["modes"]["fixed"]["value"] = option

        return res

    @property
    def options(self):
      opt = []
      for management_point in self._device.daikin_data["managementPoints"]:
          if self._embedded_id == management_point["embeddedId"]:
              management_point_type = management_point["managementPointType"]
              if self._management_point_type == management_point_type:
                  vv = management_point[self._value]
                  for mode in vv["value"]["currentMode"]["values"]:
                      if mode == "scheduled":
                          pass
                      elif mode == "fixed":
                          fixedValues = vv["value"]["modes"]["fixed"]
                          minVal = int(fixedValues["minValue"])
                          maxVal = int(fixedValues["maxValue"])
                          for val in range(minVal, maxVal + 1, fixedValues["stepValue"]):
                              opt.append(str(val))
                      else:
                          opt.append(mode)
      return opt

    @property
    def device_info(self):
        """Return a device description for device registry."""
        return self._device.device_info()

    async def async_update(self):
        """Retrieve latest state."""
        await self._device.api.async_update()
