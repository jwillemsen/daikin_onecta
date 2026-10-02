"""Provide Daikin schedule selection entities."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from homeassistant.components.select import SelectEntity
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, SCHEDULE_OFF
from .entity_descriptions import SELECT_DESCRIPTIONS

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.helpers.device_registry import DeviceInfo
    from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

    from .coordinator import OnectaDataUpdateCoordinator
    from .device import DaikinOnectaDevice

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Daikin climate based on config_entry."""
    coordinator: OnectaDataUpdateCoordinator = config_entry.runtime_data
    sensors = []
    for device in (coordinator.data or {}).values():
        for management_point in device.device.management_points:
            if management_point.schedule is not None:
                _LOGGER.info("Device '%s' provides schedule", device.name)
                sensors.append(
                    DaikinScheduleSelect(
                        device,
                        coordinator,
                        management_point.embedded_id,
                        management_point.management_point_type,
                        "schedule",
                    )
                )

    async_add_entities(sensors)


class DaikinScheduleSelect(CoordinatorEntity, SelectEntity):
    """Daikin Schedule Select class."""

    def __init__(self, device: DaikinOnectaDevice, coordinator, embedded_id, management_point_type, value) -> None:
        """Initialize a schedule selection entity."""
        _LOGGER.info("DaikinScheduleSelect '%s' '%s'", management_point_type, value)
        super().__init__(coordinator)
        self._device = device
        self._management_point_type = management_point_type
        mpt = management_point_type[0].upper() + management_point_type[1:]
        assert self._device.ha_device_id is not None
        self._attr_device_info: DeviceInfo = {
            "identifiers": {(DOMAIN, self._device.id + embedded_id)},
            "name": self._device.name + " " + mpt,
            "via_device_id": self._device.ha_device_id,
        }
        self._device.fill_device_info(self._attr_device_info, embedded_id)
        self._embedded_id = embedded_id
        self._value = value
        self._attr_has_entity_name = True
        self._attr_unique_id = f"{self._device.id}_{self._management_point_type}_{self._value}"
        self.entity_description = SELECT_DESCRIPTIONS[value]
        self.update_state()
        _LOGGER.info(
            "Device '%s:%s' supports sensor '%s'",
            device.name,
            self._embedded_id,
            self._value,
        )

    def update_state(self) -> None:
        """Refresh the available and selected schedule options."""
        self._attr_options = self.get_options()
        self._attr_current_option = self.get_current_option()

    @property
    def available(self) -> bool:
        """Return whether the source device is available."""
        return self._device.available

    @callback
    def _handle_coordinator_update(self) -> None:
        self.update_state()
        self.async_write_ha_state()

    def selection(self):
        """Return the schedule selection for the current schedule mode."""
        point = self._device.management_point(self._embedded_id)
        if point is None or point.schedule is None:
            return None
        schedule = point.schedule.value
        current_mode = schedule.current_mode.value if schedule.current_mode is not None else None
        return next((selection for selection in schedule.selections if selection.mode == current_mode), None)

    def get_current_option(self):
        """Return the selected schedule name."""
        selection = self.selection()
        if selection is None or not selection.enabled:
            return SCHEDULE_OFF
        return selection.current_option

    async def async_select_option(self, option: str) -> None:
        """Select or disable a configured schedule."""
        _LOGGER.debug("Device '%s' selecting schedule %s", self._device.name, option)
        selection = self.selection()
        if selection is None:
            return False  # type: ignore[return-value]

        schedule_id = selection.selected
        if option != SCHEDULE_OFF:
            schedule_id = next(
                (schedule.id for schedule in selection.options if schedule.name == option),
                option,
            )

        result = await self._device.put(
            self._device.id,
            self._embedded_id,
            f"schedule/{selection.mode}/current",
            {
                "scheduleId": schedule_id,
                "enabled": option != SCHEDULE_OFF,
            },
        )
        if result:
            self._attr_current_option = option
            self.async_write_ha_state()
        return result  # type: ignore[return-value]

    def get_options(self):
        """Return readable configured schedules."""
        selection = self.selection()
        if selection is None:
            return []
        options = [schedule.name for schedule in selection.options]
        if selection.enabled_settable:
            options.append(SCHEDULE_OFF)
        return options
