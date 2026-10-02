"""Support for Daikin binary sensor sensors."""

import logging
from typing import TYPE_CHECKING

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.components.sensor import CONF_STATE_CLASS
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_DEVICE_CLASS, CONF_ICON
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, ENABLED_DEFAULT, ENTITY_CATEGORY, TRANSLATION_KEY, VALUE_SENSOR_MAPPING
from .device import DaikinOnectaDevice

if TYPE_CHECKING:
    from .coordinator import OnectaRuntimeData

_LOGGER = logging.getLogger(__name__)


async def async_setup(hass, async_add_entities):
    """Old way of setting up the Daikin sensors.

    Can only be called when a user accidentally mentions the platform in their
    config. But even in that case it would have been ignored.
    """


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Daikin climate based on config_entry."""
    onecta_data: OnectaRuntimeData = config_entry.runtime_data
    coordinator = onecta_data.coordinator
    sensors = []
    for device in onecta_data.devices.values():
        for management_point in device.device.management_points:
            for value, characteristic in management_point.simple_characteristics().items():
                if characteristic.values is None and isinstance(characteristic.value, bool):
                    sensors.append(
                        DaikinBinarySensor(
                            device,
                            coordinator,
                            management_point.embedded_id,
                            management_point.management_point_type,
                            value,
                        )
                    )

    async_add_entities(sensors)


class DaikinBinarySensor(CoordinatorEntity, BinarySensorEntity):
    """Represent a boolean Daikin characteristic."""

    def __init__(
        self,
        device: DaikinOnectaDevice,
        coordinator,
        embedded_id,
        management_point_type,
        value,
    ) -> None:
        """Initialize the binary sensor from a device characteristic."""
        _LOGGER.info("DaikinBinarySensor '%s' '%s'", management_point_type, value)
        super().__init__(coordinator)
        self._device = device
        self._management_point_type = management_point_type
        mpt = management_point_type[0].upper() + management_point_type[1:]
        self._attr_device_info = {
            "identifiers": {(DOMAIN, self._device.id + self._management_point_type)},
            "name": self._device.name + " " + mpt,
            "via_device_id": self._device.ha_device_id,
        }
        self._device.fill_device_info(self._attr_device_info, management_point_type)
        self._embedded_id = embedded_id
        self._value = value
        self._attr_unique_id = f"{self._device.id}_{self._management_point_type}_None_{self._value}"
        self._attr_has_entity_name = True
        self._attr_device_class = None
        self._attr_state_class = None
        sensor_settings = VALUE_SENSOR_MAPPING.get(value)
        if sensor_settings is not None:
            self._attr_translation_key = sensor_settings[TRANSLATION_KEY]
            self._attr_icon = sensor_settings[CONF_ICON]
            self._attr_device_class = sensor_settings[CONF_DEVICE_CLASS]
            self._attr_entity_registry_enabled_default = sensor_settings[ENABLED_DEFAULT]
            self._attr_state_class = sensor_settings[CONF_STATE_CLASS]
            self._attr_entity_category = sensor_settings[ENTITY_CATEGORY]
        self.update_state()
        _LOGGER.info(
            "Device '%s:%s' supports binary sensor '%s'",
            device.name,
            self._embedded_id,
            self._value,
        )

    def update_state(self) -> None:
        """Refresh the state from the current device data."""
        self._attr_is_on = self.sensor_value()

    @property
    def available(self) -> bool:
        """Return whether the source device is available."""
        return self._device.available

    @callback
    def _handle_coordinator_update(self) -> None:
        self.update_state()
        self.async_write_ha_state()

    def sensor_value(self):
        """Return the binary characteristic value."""
        point = self._device.management_point(self._embedded_id)
        characteristic = point.characteristic(self._value) if point is not None else None
        result = characteristic.value if characteristic is not None else None
        _LOGGER.debug("Device '%s' binary sensor '%s' value '%s'", self._device.name, self._value, result)
        return result
