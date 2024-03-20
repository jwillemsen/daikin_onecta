import logging
import re

from homeassistant.components.select import SelectEntity
from homeassistant.core import callback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import COORDINATOR
from .const import DAIKIN_DEVICES
from .const import DOMAIN as DAIKIN_DOMAIN
from .device import DaikinOnectaDevice

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up Daikin climate based on config_entry."""
    coordinator = hass.data[DAIKIN_DOMAIN][COORDINATOR]
    sensors = []
    for dev_id, device in hass.data[DAIKIN_DOMAIN][DAIKIN_DEVICES].items():
        managementPoints = device.daikin_data.get("managementPoints", [])
        for management_point in managementPoints:
            management_point_type = management_point["managementPointType"]
            embedded_id = management_point["embeddedId"]

            # When we have a demandControl we provide a select sensor
            demand = management_point.get("demandControl")
            if demand is not None:
                _LOGGER.info("Device '%s' provides demandControl", device.name)
                sensors.append(DaikinDemandSelect(device, coordinator, embedded_id, management_point_type, "demandControl"))

    async_add_entities(sensors)


class DaikinDemandSelect(CoordinatorEntity, SelectEntity):
    """Daikin DemandControl Select class."""

    def __init__(self, device: DaikinOnectaDevice, coordinator, embedded_id, management_point_type, value) -> None:
        _LOGGER.info("DaikinDemandSelect '%s' '%s'", management_point_type, value)
        super().__init__(coordinator)
        self._device = device
        self._embedded_id = embedded_id
        self._management_point_type = management_point_type
        self._value = value
        mpt = management_point_type[0].upper() + management_point_type[1:]
        myname = value[0].upper() + value[1:]
        readable = re.findall("[A-Z][^A-Z]*", myname)
        self._attr_name = f"{mpt} {' '.join(readable)}"
        self._attr_unique_id = f"{self._device.getId()}_{self._management_point_type}_{self._value}"
        self._attr_has_entity_name = True
        self.update_state()
        _LOGGER.info(
            "Device '%s:%s' supports sensor '%s'",
            device.name,
            self._embedded_id,
            self._attr_name,
        )

    def update_state(self) -> None:
        self._attr_options = self.get_options()
        self._attr_current_option = self.get_current_option()
        self._attr_available = self._device.available
        self._attr_device_info = self._device.device_info()

    @callback
    def _handle_coordinator_update(self) -> None:
        self.update_state()
        self.async_write_ha_state()

    def get_current_option(self):
        """Return the state of the sensor."""
        res = None
        managementPoints = self._device.daikin_data.get("managementPoints", [])
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
        # TODO: Caching update needs to be reworked when Daikin provides this data again
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
            res = await self._device.set_path(
                self._device.getId(),
                self._embedded_id,
                "demandControl",
                "/currentMode",
                new_currentmode,
            )
            if res is False:
                _LOGGER.warning(
                    "Device '%s' problem setting demand control to %s",
                    self._device.name,
                    option,
                )
            else:
                mode["value"] = new_currentmode

            if new_currentmode == "fixed":
                res = await self._device.set_path(
                    self._device.getId(),
                    self._embedded_id,
                    "demandControl",
                    "/modes/fixed",
                    int(option),
                )
                if res is False:
                    _LOGGER.warning(
                        "Device '%s' problem setting demand control to fixed value %s",
                        self._device.name,
                        option,
                    )
                else:
                    vv["value"]["modes"]["fixed"]["value"] = option

        return res

    def get_options(self):
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
