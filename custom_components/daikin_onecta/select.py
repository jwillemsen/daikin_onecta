import logging

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_ICON
from homeassistant.core import callback
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .const import ENABLED_DEFAULT
from .const import SCHEDULE_OFF
from .const import TRANSLATION_KEY
from .const import VALUE_SENSOR_MAPPING
from .coordinator import OnectaRuntimeData
from .device import DaikinOnectaDevice

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Daikin climate based on config_entry."""
    onecta_data: OnectaRuntimeData = config_entry.runtime_data
    coordinator = onecta_data.coordinator
    sensors = []
    for dev_id, device in onecta_data.devices.items():
        managementPoints = device.daikin_data.get("managementPoints", [])
        for management_point in managementPoints:
            # When we have a schedule we provide a select sensor
            schedule = management_point.get("schedule")
            if schedule is not None:
                management_point_type = management_point["managementPointType"]
                embedded_id = management_point["embeddedId"]
                _LOGGER.info("Device '%s' provides schedule", device.name)
                sensors.append(DaikinScheduleSelect(device, coordinator, embedded_id, management_point_type, "schedule"))

    async_add_entities(sensors)


class DaikinScheduleSelect(CoordinatorEntity, SelectEntity):
    """Daikin Schedule Select class."""

    def __init__(self, device: DaikinOnectaDevice, coordinator, embedded_id, management_point_type, value) -> None:
        _LOGGER.info("DaikinScheduleSelect '%s' '%s'", management_point_type, value)
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
        self._attr_has_entity_name = True
        self._attr_unique_id = f"{self._device.id}_{self._management_point_type}_{self._value}"
        sensor_settings = VALUE_SENSOR_MAPPING.get(value)
        if sensor_settings is not None:
            self._attr_icon = sensor_settings[CONF_ICON]
            self._attr_entity_registry_enabled_default = sensor_settings[ENABLED_DEFAULT]
            self._attr_translation_key = sensor_settings[TRANSLATION_KEY]
        self.update_state()
        _LOGGER.info(
            "Device '%s:%s' supports sensor '%s'",
            device.name,
            self._embedded_id,
            self._value,
        )

    def update_state(self) -> None:
        self._attr_options = self.get_options()
        self._attr_current_option = self.get_current_option()

    @property
    def available(self) -> bool:
        return self._device.available

    @callback
    def _handle_coordinator_update(self) -> None:
        self.update_state()
        self.async_write_ha_state()

    def get_current_option(self):
        """Return the state of the sensor."""
        res = None
        management_points = self._device.daikin_data.get("managementPoints", [])
        for management_point in management_points:
            if self._embedded_id == management_point["embeddedId"]:
                management_point_type = management_point["managementPointType"]
                if self._management_point_type == management_point_type:
                    scheduledict = management_point.get(self._value)
                    if scheduledict is not None:
                        currentMode = scheduledict["value"]["currentMode"]["value"]
                        # When there is no schedule enabled we return none
                        if not scheduledict["value"]["modes"][currentMode]["enabled"]["value"]:
                            res = SCHEDULE_OFF
                        else:
                            currentSchedule = scheduledict["value"]["modes"][currentMode]["currentSchedule"]["value"]
                            res = scheduledict["value"]["modes"][currentMode]["schedules"][currentSchedule]["name"]["value"]
                            if not res:
                                res = currentSchedule
        return res

    async def async_select_option(self, option: str) -> None:
        _LOGGER.debug("Device '%s' selecting schedule %s", self._device.name, option)
        currentMode = ""
        scheduleid = option
        management_points = self._device.daikin_data.get("managementPoints", [])
        for management_point in management_points:
            if self._embedded_id == management_point["embeddedId"]:
                management_point_type = management_point["managementPointType"]
                if self._management_point_type == management_point_type:
                    scheduledict = management_point.get(self._value)
                    if scheduledict is not None:
                        currentMode = scheduledict["value"]["currentMode"]["value"]
                        # Look for a schedule with the user selected readable name, when we find it, we use the schedule id
                        # related to that name
                        for scheduleName in scheduledict["value"]["modes"][currentMode]["currentSchedule"]["values"]:
                            readableName = scheduledict["value"]["modes"][currentMode]["schedules"][scheduleName]["name"]["value"]
                            if not readableName:
                                readableName = scheduleName
                            if option == SCHEDULE_OFF:
                                if readableName == self._attr_current_option:
                                    scheduleid = scheduleName
                                    break
                            else:
                                if readableName == option:
                                    scheduleid = scheduleName
                                    break

        value = {"scheduleId": scheduleid, "enabled": option != SCHEDULE_OFF}
        result = await self._device.put(self._device.id, self._embedded_id, f"schedule/{currentMode}/current", value)
        if result is False:
            _LOGGER.warning(
                "Device '%s' problem selecting schedule %s",
                self._device.name,
                scheduleid,
            )
        else:
            self._attr_current_option = option
            self.async_write_ha_state()

        return result

    def get_options(self):
        opt = []
        management_points = self._device.daikin_data.get("managementPoints", [])
        for management_point in management_points:
            if self._embedded_id == management_point["embeddedId"]:
                management_point_type = management_point["managementPointType"]
                if self._management_point_type == management_point_type:
                    scheduledict = management_point.get(self._value)
                    if scheduledict is not None:
                        currentMode = scheduledict["value"]["currentMode"]["value"]
                        for scheduleName in scheduledict["value"]["modes"][currentMode]["currentSchedule"]["values"]:
                            readableName = scheduledict["value"]["modes"][currentMode]["schedules"][scheduleName]["name"].get("value")
                            # The schedule can maybe have an empty name set, use at that moment the internal ID
                            if not readableName:
                                readableName = scheduleName
                            opt.append(readableName)

                        # Only add off when the schedule current mode enabled settable is true
                        if scheduledict["value"]["modes"][currentMode]["enabled"]["settable"]:
                            _LOGGER.info("Device '%s:%s' enabled can be set, so providing %s", self._device.name, self._embedded_id, SCHEDULE_OFF)

                            opt.append(SCHEDULE_OFF)

        return opt
