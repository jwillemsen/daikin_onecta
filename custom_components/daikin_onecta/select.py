"""Provide Daikin schedule and operation mode selection entities."""

import logging
import re
from typing import TYPE_CHECKING, override

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from daikin_onecta.models import ClimateControl

from .const import SCHEDULE_OFF
from .device import DaikinOnectaDevice
from .entity import DaikinManagementPointEntity
from .entity_descriptions import SELECT_DESCRIPTIONS

if TYPE_CHECKING:
    from .coordinator import OnectaDataUpdateCoordinator

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
            if management_point.schedule_state is not None:
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

            climate_control = management_point.climate_control
            operation_mode = climate_control.operation_mode if climate_control is not None else None
            if operation_mode is not None and operation_mode.settable:
                _LOGGER.info("Device '%s' provides operation mode", device.name)
                sensors.append(
                    DaikinOperationModeSelect(
                        device,
                        coordinator,
                        management_point.embedded_id,
                        management_point.management_point_type,
                    )
                )

    async_add_entities(sensors)


class DaikinScheduleSelect(DaikinManagementPointEntity, SelectEntity):
    """Daikin Schedule Select class."""

    def __init__(
        self,
        device: DaikinOnectaDevice,
        coordinator,
        embedded_id: str,
        management_point_type: str,
        value: str,
    ) -> None:
        """Initialize a schedule selection entity."""
        _LOGGER.info("DaikinScheduleSelect '%s' '%s'", management_point_type, value)
        super().__init__(device, coordinator, embedded_id, management_point_type)
        self._management_point_type = management_point_type
        self._value = value
        self._attr_has_entity_name = True
        self._attr_unique_id = f"{self._device.id}_{self._embedded_id}_{self._value}"
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

    @callback
    @override
    def _handle_coordinator_update(self) -> None:
        self.update_state()
        self.async_write_ha_state()

    def selection(self):
        """Return the schedule selection for the current schedule mode."""
        point = self._device.management_point(self._embedded_id)
        schedule = point.schedule_state if point is not None else None
        if schedule is None:
            return None
        return schedule.active_selection

    def get_current_option(self):
        """Return the selected schedule name."""
        selection = self.selection()
        if selection is None or not selection.enabled:
            return SCHEDULE_OFF
        return selection.current_option

    @override
    async def async_select_option(self, option: str) -> None:
        """Select or disable a configured schedule."""
        _LOGGER.debug("Device '%s' selecting schedule %s", self._device.name, option)
        selection = self.selection()
        if selection is None:
            return

        schedule_id = selection.selected
        if option != SCHEDULE_OFF:
            schedule_id = next(
                (schedule.id for schedule in selection.options if schedule.name == option),
                option,
            )

        await self._async_execute_command(
            lambda client: client.schedule(self._device.id, self._embedded_id).set_current(
                selection.mode,
                schedule_id,
                enabled=option != SCHEDULE_OFF,
            ),
            "schedule_select_failed",
        )
        point = self._device.management_point(self._embedded_id)
        schedule_state = point.schedule_state if point is not None else None
        if schedule_state is not None:
            schedule_state.apply_selection(
                selection.mode,
                schedule_id,
                enabled=option != SCHEDULE_OFF,
            )
        self.update_state()
        self.async_write_ha_state()
        return

    def get_options(self):
        """Return readable configured schedules."""
        selection = self.selection()
        if selection is None:
            return []
        options = [schedule.name for schedule in selection.options]
        if selection.enabled_settable:
            options.append(SCHEDULE_OFF)
        return options


def _daikin_mode_to_option(mode: str) -> str:
    """Translate a native Daikin operation mode into a translation-key safe option."""
    return re.sub(r"(?<!^)(?=[A-Z])", "_", mode).lower()


class DaikinOperationModeSelect(DaikinManagementPointEntity, SelectEntity):
    """Daikin operation mode select.

    Shows and sets the stored operation mode independently of the power state, so a
    unit that is off can be prepared for heating or cooling without switching it on.
    On multi-split systems all indoor units must share the operation mode of the
    outdoor unit, otherwise Daikin reports an operation mode conflict.
    """

    _attr_has_entity_name = True

    def __init__(
        self,
        device: DaikinOnectaDevice,
        coordinator,
        embedded_id: str,
        management_point_type: str,
    ) -> None:
        """Initialize an operation mode selection entity."""
        super().__init__(device, coordinator, embedded_id, management_point_type)
        self._attr_unique_id = f"{self._device.id}_{self._embedded_id}_operationMode"
        self.entity_description = SELECT_DESCRIPTIONS["operationModeSelect"]
        self.update_state()

    def climate_control(self) -> ClimateControl | None:
        """Return the library's typed climate-control state view."""
        management_point = self._device.management_point(self._embedded_id)
        return management_point.climate_control if management_point is not None else None

    def update_state(self) -> None:
        """Refresh the available and selected operation modes."""
        cc = self.climate_control()
        modes = cc.operation_modes if cc is not None else []
        self._options_to_modes = {_daikin_mode_to_option(mode): mode for mode in modes}
        self._attr_options = list(self._options_to_modes)
        current = cc.current_operation_mode if cc is not None else None
        self._attr_current_option = _daikin_mode_to_option(current) if current is not None else None

    @callback
    @override
    def _handle_coordinator_update(self) -> None:
        self.update_state()
        self.async_write_ha_state()

    @override
    async def async_select_option(self, option: str) -> None:
        """Set the operation mode without changing the power state."""
        mode = self._options_to_modes.get(option)
        cc = self.climate_control()
        if mode is None or cc is None or cc.operation_mode is None or mode == cc.operation_mode.value:
            return
        _LOGGER.debug("Device '%s' setting operation mode to %s", self._device.name, mode)
        await self._async_execute_command(
            lambda client: client.climate_control(self._device.id, self._embedded_id).set_operation_mode(mode),
            "select_operation_mode_failed",
        )
        cc.operation_mode.value = mode
        self.update_state()
        self.async_write_ha_state()
        # The climate entity shares this state; let it pick up the new mode right away.
        self.coordinator.async_update_listeners()
