"""Support for Daikin binary sensor sensors."""
import logging
import re

from homeassistant.components.binary_sensor import (
    BinarySensorEntity,
)
from homeassistant.components.sensor import CONF_STATE_CLASS
from homeassistant.const import CONF_DEVICE_CLASS
from homeassistant.const import CONF_ICON
from homeassistant.core import callback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .const import ENABLED_DEFAULT
from .const import ENTITY_CATEGORY
from .const import VALUE_SENSOR_MAPPING
from .const import TRANSLATION_KEY
from .coordinator import OnectaRuntimeData
from .device import DaikinOnectaDevice

_LOGGER = logging.getLogger(__name__)


async def async_setup(hass, async_add_entities):
    """Old way of setting up the Daikin sensors.

    Can only be called when a user accidentally mentions the platform in their
    config. But even in that case it would have been ignored.
    """


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up Daikin climate based on config_entry."""
    onecta_data: OnectaRuntimeData = config_entry.runtime_data
    coordinator = onecta_data.coordinator
    sensors = []
    for dev_id, device in onecta_data.devices.items():
        management_points = device.daikin_data.get("managementPoints", [])
        for management_point in management_points:
            management_point_type = management_point["managementPointType"]
            embedded_id = management_point["embeddedId"]

            # For all values provide a "value" we provide a sensor
            for value in management_point:
                vv = management_point.get(value)
                if isinstance(vv, dict):
                    value_value = vv.get("value")
                    values = vv.get("values")
                    if values is None and value_value is not None and isinstance(value_value, bool):
                        # We don't have multiple values and we do have a value which is a boolean
                        sensors.append(
                            DaikinBinarySensor(
                                device,
                                coordinator,
                                embedded_id,
                                management_point_type,
                                value,
                            )
                        )

    async_add_entities(sensors)


class DaikinBinarySensor(CoordinatorEntity, BinarySensorEntity):
    def __init__(
        self,
        device: DaikinOnectaDevice,
        coordinator,
        embedded_id,
        management_point_type,
        value,
    ) -> None:
        _LOGGER.info("DaikinBinarySensor '%s' '%s'", management_point_type, value)
        super().__init__(coordinator)
        self._device = device
        self._management_point_type = management_point_type
        mpt = management_point_type[0].upper() + management_point_type[1:]
        self._attr_device_info = {
            "identifiers": {(DOMAIN, self._device.id + self._management_point_type)},
            "name": self._device.name + " " + mpt,
            "via_device": (DOMAIN, self._device.id),
        }
        self._device.fill_device_info(self._attr_device_info, management_point_type)
        self._embedded_id = embedded_id
        self._value = value
        self._attr_device_class = None
        self._attr_state_class = None
        self._attr_has_entity_name = True
        sensor_settings = VALUE_SENSOR_MAPPING.get(value)
        if sensor_settings is not None:
            self._attr_icon = sensor_settings[CONF_ICON]
            self._attr_device_class = sensor_settings[CONF_DEVICE_CLASS]
            self._attr_entity_registry_enabled_default = sensor_settings[ENABLED_DEFAULT]
            self._attr_state_class = sensor_settings[CONF_STATE_CLASS]
            self._attr_entity_category = sensor_settings[ENTITY_CATEGORY]
            self._attr_translation_key = sensor_settings[TRANSLATION_KEY]
        myname = value[0].upper() + value[1:]
        readable = re.findall("[A-Z][^A-Z]*", myname)
        self._attr_name = f"{' '.join(readable)}"
        self._attr_unique_id = f"{self._device.id}_{self._management_point_type}_None_{self._value}"
        self.update_state()
        _LOGGER.info(
            "Device '%s:%s' supports binary sensor '%s'",
            device.name,
            self._embedded_id,
            self._value,
        )

    def update_state(self) -> None:
        self._attr_is_on = self.sensor_value()

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
                cd = management_point.get(self._value)
                if cd is not None:
                    res = cd.get("value")
        _LOGGER.debug("Device '%s' binary sensor '%s' value '%s'", self._device.name, self._value, res)
        return res
