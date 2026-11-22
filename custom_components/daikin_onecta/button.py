"""Button platform for the Daikin Onecta integration."""

from typing import override

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import OnectaDataUpdateCoordinator
from .entity import DaikinAccountEntity, account_identifier


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the refresh button for the Daikin account."""
    coordinator: OnectaDataUpdateCoordinator = config_entry.runtime_data

    async_add_entities([DaikinRefreshButton(config_entry, coordinator)])


class DaikinRefreshButton(DaikinAccountEntity, ButtonEntity):
    """Button to request an immediate account data update."""

    def __init__(
        self,
        config_entry: ConfigEntry,
        coordinator: OnectaDataUpdateCoordinator,
    ) -> None:
        """Initialize the account refresh button."""
        super().__init__(config_entry, coordinator)
        self._attr_unique_id = f"{account_identifier(config_entry)}_refresh"
        self._attr_entity_category = EntityCategory.CONFIG
        self._attr_icon = "mdi:refresh"
        self._attr_name = "Refresh"
        self._attr_has_entity_name = True

    @property
    @override
    def available(self) -> bool:
        """Allow manual recovery even when the previous update failed."""
        return True

    @callback
    @override
    def _handle_coordinator_update(self) -> None:
        self.async_write_ha_state()

    async def async_press(self) -> None:
        """Request an immediate coordinator refresh."""
        await self.coordinator.async_refresh()
