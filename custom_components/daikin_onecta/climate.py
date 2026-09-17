"""Support for the Daikin HVAC."""
import logging
import re
from datetime import date
from datetime import timedelta

import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant.components.climate import ClimateEntity
from homeassistant.components.climate import FAN_HIGH
from homeassistant.components.climate import FAN_LOW
from homeassistant.components.climate import FAN_MEDIUM
from homeassistant.components.climate import FAN_MIDDLE
from homeassistant.components.climate import PLATFORM_SCHEMA
from homeassistant.components.climate.const import ATTR_HVAC_MODE
from homeassistant.components.climate.const import ClimateEntityFeature
from homeassistant.components.climate.const import HVACMode
from homeassistant.components.climate.const import PRESET_AWAY
from homeassistant.components.climate.const import PRESET_BOOST
from homeassistant.components.climate.const import PRESET_COMFORT
from homeassistant.components.climate.const import PRESET_ECO
from homeassistant.components.climate.const import PRESET_NONE
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_TEMPERATURE
from homeassistant.const import CONF_HOST
from homeassistant.const import CONF_NAME
from homeassistant.const import UnitOfTemperature
from homeassistant.core import callback
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_HOMEKIT_FAN_MODE_ALIASES
from .const import DOMAIN
from .const import FANMODE_FIXED
from .const import TRANSLATION_KEY
from .const import VALUE_SENSOR_MAPPING
from .coordinator import OnectaRuntimeData

_LOGGER = logging.getLogger(__name__)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({vol.Required(CONF_HOST): cv.string, vol.Optional(CONF_NAME): cv.string})

PRESET_MODES = {PRESET_COMFORT, PRESET_ECO, PRESET_AWAY, PRESET_BOOST}

DAIKIN_FAN_MODE_QUIET = "quiet"

HOMEKIT_FIXED_FAN_MODE_ALIASES = {
    FAN_MIDDLE: "2",
    FAN_MEDIUM: "3",
    FAN_HIGH: "5",
}

HA_HVAC_TO_DAIKIN = {
    HVACMode.FAN_ONLY: "fanOnly",
    HVACMode.DRY: "dry",
    HVACMode.COOL: "cooling",
    HVACMode.HEAT: "heating",
    HVACMode.HEAT_COOL: "auto",
    HVACMode.OFF: "off",
}

DAIKIN_HVAC_TO_HA = {
    "fanOnly": HVACMode.FAN_ONLY,
    "dry": HVACMode.DRY,
    "cooling": HVACMode.COOL,
    "heating": HVACMode.HEAT,
    "heatingDay": HVACMode.HEAT,
    "heatingNight": HVACMode.HEAT,
    "auto": HVACMode.HEAT_COOL,
    "off": HVACMode.OFF,
    "humidification": HVACMode.DRY,
}

HA_PRESET_TO_DAIKIN = {
    PRESET_AWAY: "holidayMode",
    PRESET_NONE: "off",
    PRESET_BOOST: "powerfulMode",
    PRESET_COMFORT: "comfortMode",
    PRESET_ECO: "econoMode",
}


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Daikin climate based on config_entry."""
    onecta_data: OnectaRuntimeData = config_entry.runtime_data
    coordinator = onecta_data.coordinator
    for device in onecta_data.devices.values():
        modes = []
        device_model = device.daikin_data["deviceModel"]
        supported_management_point_types = {"climateControl"}
        managementPoints = device.daikin_data.get("managementPoints", [])
        embedded_id = ""
        for management_point in managementPoints:
            management_point_type = management_point["managementPointType"]
            if management_point_type in supported_management_point_types:
                embedded_id = management_point.get("embeddedId")
                # Check if we have a temperatureControl
                temperatureControl = management_point.get("temperatureControl")
                if temperatureControl is not None:
                    for operationmode in temperatureControl["value"]["operationModes"]:
                        # for modes in operationmode["setpoints"]:
                        for c in temperatureControl["value"]["operationModes"][operationmode]["setpoints"]:
                            modes.append(c)
        # Remove duplicates
        modes = list(dict.fromkeys(modes))
        _LOGGER.info("Climate: Device '%s' has modes %s", device_model, modes)
        for mode in modes:
            async_add_entities(
                [DaikinClimate(device, mode, coordinator, embedded_id)],
                update_before_add=False,
            )


class DaikinClimate(CoordinatorEntity, ClimateEntity):
    """Representation of a Daikin HVAC."""

    _enable_turn_on_off_backwards_compatibility = False  # Remove with HA 2025.1

    # Setpoint is the setpoint string under
    # temperatureControl/value/operationsModes/mode/setpoints, for example roomTemperature/leavingWaterOffset
    def __init__(self, device, setpoint, coordinator, embedded_id):
        """Initialize the climate device."""
        super().__init__(coordinator)
        _LOGGER.info(
            "Device '%s' initializing Daikin Climate for controlling %s...",
            device.name,
            setpoint,
        )
        self._device = device
        self._embedded_id = embedded_id
        self._setpoint = setpoint
        self._attr_temperature_unit = UnitOfTemperature.CELSIUS
        self._attr_unique_id = f"{self._device.id}_{self._setpoint}"
        self._attr_device_info = {"identifiers": {(DOMAIN, self._device.id)}, "name": self._device.name}
        self._attr_has_entity_name = True
        self._device.fill_device_info(self._attr_device_info, "gateway")
        sensor_settings = VALUE_SENSOR_MAPPING.get(setpoint)
        self._attr_translation_key = sensor_settings[TRANSLATION_KEY]
        self.update_state()

    def update_state(self) -> None:
        # NOTE: after a successful PATCH, action handlers below (async_turn_on,
        # async_set_hvac_mode, etc.) optimistically write the new value directly into
        # self._device.daikin_data (the cached cloud JSON) *and* set the matching
        # self._attr_* here/there, so that HA reflects the change immediately without
        # waiting for the next poll. That means daikin_data and self._attr_* are two
        # views of the same state that must be kept in sync by hand in every handler;
        # a future handler that mutates one and forgets the other will only surface as
        # a UI/state mismatch until the next coordinator refresh overwrites both.
        self._attr_supported_features = self.get_supported_features()
        self._attr_current_temperature = self.get_current_temperature()
        self._attr_max_temp = self.get_max_temp()
        self._attr_min_temp = self.get_min_temp()
        self._attr_target_temperature_step = self.get_target_temperature_step()
        self._attr_target_temperature = self.get_target_temperature()
        self._attr_hvac_modes = self.get_hvac_modes()
        self._attr_swing_modes = self.get_swing_modes()
        self._attr_swing_horizontal_modes = self.get_swing_horizontal_modes()
        self._attr_preset_modes = self.get_preset_modes()
        self._attr_fan_modes = self.get_fan_modes()
        self._attr_hvac_mode = self.get_hvac_mode()
        self._attr_swing_mode = self.get_swing_mode()
        self._attr_swing_horizontal_mode = self.get_swing_horizontal_mode()
        self._attr_preset_mode = self.get_preset_mode()
        self._attr_fan_mode = self.get_fan_mode()

    @callback
    def _handle_coordinator_update(self) -> None:
        self.update_state()
        self.async_write_ha_state()

    @property
    def available(self) -> bool:
        return self._device.available

    def climate_control(self):
        cc = None
        supported_management_point_types = {"climateControl"}
        management_points = self._device.daikin_data.get("managementPoints", [])
        for management_point in management_points:
            management_point_type = management_point["managementPointType"]
            if management_point_type in supported_management_point_types:
                cc = management_point
        return cc

    def operation_mode(self):
        om = None
        cc = self.climate_control()
        if cc is not None:
            om = cc.get("operationMode")
        return om

    @property
    def _homekit_fan_mode_aliases_enabled(self):
        """Return whether HomeKit fan mode aliases are enabled."""
        return self.coordinator.options.get(CONF_HOMEKIT_FAN_MODE_ALIASES, False)

    def _homekit_fan_mode_aliases(self, fan_speed):
        """Return HomeKit fan mode aliases available for the fan speed data."""
        aliases = {}
        if not self._homekit_fan_mode_aliases_enabled:
            return aliases

        current_mode = fan_speed.get("currentMode", {})
        current_mode_values = current_mode.get("values", [])
        if DAIKIN_FAN_MODE_QUIET in current_mode_values:
            aliases[FAN_LOW] = DAIKIN_FAN_MODE_QUIET

        if FANMODE_FIXED not in current_mode_values:
            return aliases

        fixed_mode = fan_speed.get("modes", {}).get(FANMODE_FIXED)
        if fixed_mode is None:
            return aliases

        min_val = int(fixed_mode["minValue"])
        max_val = int(fixed_mode["maxValue"])
        step_value = int(fixed_mode["stepValue"])
        fixed_values = {str(val) for val in range(min_val, max_val + 1, step_value)}

        for alias, daikin_mode in HOMEKIT_FIXED_FAN_MODE_ALIASES.items():
            if daikin_mode in fixed_values:
                aliases[alias] = daikin_mode

        return aliases

    def _get_homekit_fan_mode(self, fan_speed, fan_mode):
        """Return the HomeKit alias for a Daikin fan mode when available."""
        if not self._homekit_fan_mode_aliases_enabled:
            return fan_mode

        aliases = self._homekit_fan_mode_aliases(fan_speed)
        for alias, daikin_mode in aliases.items():
            if fan_mode == daikin_mode:
                return alias

        return fan_mode

    def _resolve_homekit_fan_mode_alias(self, fan_speed, fan_mode):
        """Return the Daikin fan mode represented by a HomeKit alias."""
        return self._homekit_fan_mode_aliases(fan_speed).get(fan_mode, fan_mode)

    def setpoint(self):
        setpoint = None
        cc = self.climate_control()
        if cc is not None:
            # Check if we have a temperatureControl
            temperature_control = cc.get("temperatureControl")
            if temperature_control is not None:
                operation_mode_data = cc.get("operationMode")
                if operation_mode_data is not None:
                    operation_mode = operation_mode_data.get("value")
                    # For not all operationModes there is a temperatureControl setpoint available
                    oo = temperature_control["value"]["operationModes"].get(operation_mode)
                    if oo is not None:
                        setpoint = oo["setpoints"].get(self._setpoint)
                    _LOGGER.debug(
                        "Device '%s' %s operation mode %s has setpoint %s",
                        self._device.name,
                        self._setpoint,
                        operation_mode,
                        setpoint,
                    )
        return setpoint

    def sensory_data(self, setpoint):
        sensoryData = None
        supported_management_point_types = {"climateControl"}
        management_points = self._device.daikin_data.get("managementPoints", [])
        for management_point in management_points:
            management_point_type = management_point["managementPointType"]
            if management_point_type in supported_management_point_types:
                # Check if we have a sensoryData
                sensoryData = management_point.get("sensoryData")
                _LOGGER.debug("Climate: Device sensoryData %s", sensoryData)
                if sensoryData is not None:
                    value = sensoryData.get("value")
                    if value is not None:
                        sensoryData = value.get(setpoint)
                        _LOGGER.debug(
                            "Device '%s' %s sensoryData %s",
                            self._device.name,
                            setpoint,
                            sensoryData,
                        )
        return sensoryData

    def get_supported_features(self):
        supported_features = 0
        if hasattr(ClimateEntityFeature, "TURN_OFF"):
            supported_features = ClimateEntityFeature.TURN_OFF | ClimateEntityFeature.TURN_ON
        setpointdict = self.setpoint()
        if setpointdict is not None and setpointdict["settable"] is True:
            supported_features |= ClimateEntityFeature.TARGET_TEMPERATURE
        if len(self.get_preset_modes()) > 1:
            supported_features |= ClimateEntityFeature.PRESET_MODE
        cc = self.climate_control()
        if cc is not None:
            fanControl = cc.get("fanControl")
            if fanControl is not None:
                operation_mode_data = cc.get("operationMode")
                if operation_mode_data is not None:
                    operationmode = operation_mode_data.get("value")
                    operationmodedict = fanControl["value"]["operationModes"].get(operationmode)
                    if operationmodedict is not None:
                        if operationmodedict.get("fanSpeed") is not None:
                            supported_features |= ClimateEntityFeature.FAN_MODE
                        fan_direction = operationmodedict.get("fanDirection")
                        if fan_direction is not None:
                            if fan_direction.get("vertical") is not None:
                                supported_features |= ClimateEntityFeature.SWING_MODE
                            if fan_direction.get("horizontal") is not None:
                                supported_features |= ClimateEntityFeature.SWING_HORIZONTAL_MODE

            _LOGGER.debug("Device '%s' supports features %s", self._device.name, supported_features)

        return supported_features

    @property
    def name(self):
        myname = self._setpoint[0].upper() + self._setpoint[1:]
        readable = re.findall("[A-Z][^A-Z]*", myname)
        return f"{' '.join(readable)}"

    def get_current_temperature(self):
        current_temp = None
        sensory_data = self.sensory_data(self._setpoint)
        # Check if there is a sensoryData which is for the same setpoint, if so, return that
        if sensory_data is not None:
            current_temp = sensory_data["value"]
        else:
            # There is no sensoryData with the same name as the setpoint we are using, see
            # if we are using leavingWaterOffset, at that moment see if we have a
            # leavingWaterTemperature temperature
            lwsensor = self.sensory_data("leavingWaterTemperature")
            if self._setpoint == "leavingWaterOffset" and lwsensor is not None:
                current_temp = lwsensor["value"]
        _LOGGER.debug(
            "Device '%s' %s current temperature '%s'",
            self._device.name,
            self._setpoint,
            current_temp,
        )
        return current_temp

    def get_max_temp(self):
        max_temp = None
        setpointdict = self.setpoint()
        if setpointdict is not None:
            max_temp = setpointdict["maxValue"]
        else:
            max_temp = super().max_temp
        _LOGGER.debug(
            "Device '%s' %s max temperature '%s'",
            self._device.name,
            self._setpoint,
            max_temp,
        )
        return max_temp

    def get_min_temp(self):
        min_temp = None
        setpointdict = self.setpoint()
        if setpointdict is not None:
            min_temp = setpointdict["minValue"]
        else:
            min_temp = super().min_temp
        _LOGGER.debug(
            "Device '%s' %s min