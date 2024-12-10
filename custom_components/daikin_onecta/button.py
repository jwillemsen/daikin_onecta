"""Component to interface with binary sensors."""
from __future__ import annotations

import logging

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import callback
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import COORDINATOR
from .const import DAIKIN_DEVICES
from .const import DOMAIN as DAIKIN_DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    entities = []

    coordinator = hass.data[DAIKIN_DOMAIN][COORDINATOR]

    for dev_id, device in hass.data[DAIKIN_DOMAIN][DAIKIN_DEVICES].items():
        entities.append(DaikinRefreshButton(device, config_entry, coordinator))

    if entities:
        async_add_entities(entities)


class DaikinRefreshButton(CoordinatorEntity, ButtonEntity):
    """Button to request an immediate device data update."""

    def __init__(self, device, config_entry, coordinator):
        super().__init__(coordinator)
        self._device = device
        self._attr_unique_id = f"{self._device.id}_refresh"
        self._attr_entity_category = EntityCategory.CONFIG
        self._attr_icon = "mdi:refresh"
        self._attr_name = "Refresh"
        self._attr_device_info = self._device.device_info()
        self._attr_has_entity_name = True
        self._config_entry = config_entry

        _LOGGER.info("Device '%s' has refresh button", self._device.name)

    @property
    def available(self) -> bool:
        return self._device.available

    @callback
    def _handle_coordinator_update(self) -> None:
        self.async_write_ha_state()

    async def async_press(self) -> None:
        await self.coordinator._async_update_data()
        self.coordinator.async_update_listeners()
