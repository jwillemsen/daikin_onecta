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
        device_model = device.device.device_model
        supported_management_point_types = {"climateControl"}
        embedded_id = ""
        for management_point in device.device.management_points:
            if management_point.management_point_type in supported_management_point_types:
                embedded_id = management_point.embedded_id
                if management_point.temperature_control is not None:
                    for operation_mode in management_point.temperature_control.value.operation_modes.values():
                        modes.extend(operation_mode.setpoints)
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
        """Return the typed climate-control management point."""
        return self._device.management_point(self._embedded_id)

    def operation_mode(self):
        """Return the operation-mode characteristic."""
        cc = self.climate_control()
        return cc.operation_mode if cc is not None else None

    def fan_operation(self):
        """Return fan controls for the active operation mode."""
        cc = self.climate_control()
        if cc is None or cc.fan_control is None or cc.operation_mode is None:
            return None
        return cc.fan_control.value.operation_modes.get(cc.operation_mode.value)

    def preset_characteristic(self, daikin_mode):
        """Return a preset characteristic by Daikin API name."""
        cc = self.climate_control()
        if cc is None:
            return None
        if daikin_mode == "holidayMode":
            return cc.holiday_mode
        return cc.characteristic(daikin_mode)

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
        """Return the active operation-mode setpoint."""
        cc = self.climate_control()
        if cc is None or cc.temperature_control is None or cc.operation_mode is None:
            return None
        operation_mode = cc.temperature_control.value.operation_modes.get(cc.operation_mode.value)
        if operation_mode is None:
            return None
        return operation_mode.setpoints.get(self._setpoint)

    def sensory_data(self, setpoint):
        """Return a sensory characteristic by Daikin API name."""
        cc = self.climate_control()
        if cc is None or cc.sensory_data is None:
            return None
        attribute = {
            "roomTemperature": "room_temperature",
            "outdoorTemperature": "outdoor_temperature",
            "leavingWaterTemperature": "leaving_water_temperature",
            "tankTemperature": "tank_temperature",
            "roomHumidity": "room_humidity",
            "pm1Concentration": "pm1_concentration",
            "pm25Concentration": "pm25_concentration",
            "pm10Concentration": "pm10_concentration",
        }.get(setpoint)
        return getattr(cc.sensory_data.value, attribute) if attribute is not None else None

    def get_supported_features(self):
        supported_features = 0
        if hasattr(ClimateEntityFeature, "TURN_OFF"):
            supported_features = ClimateEntityFeature.TURN_OFF | ClimateEntityFeature.TURN_ON
        setpointdict = self.setpoint()
        if setpointdict is not None and setpointdict.settable:
            supported_features |= ClimateEntityFeature.TARGET_TEMPERATURE
        if len(self.get_preset_modes()) > 1:
            supported_features |= ClimateEntityFeature.PRESET_MODE
        cc = self.climate_control()
        if cc is not None:
            fan_operation = self.fan_operation()
            if fan_operation is not None:
                if fan_operation.fan_speed is not None:
                    supported_features |= ClimateEntityFeature.FAN_MODE
                if fan_operation.fan_direction is not None:
                    if fan_operation.fan_direction.vertical is not None:
                        supported_features |= ClimateEntityFeature.SWING_MODE
                    if fan_operation.fan_direction.horizontal is not None:
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
            current_temp = sensory_data.value
        else:
            # There is no sensoryData with the same name as the setpoint we are using, see
            # if we are using leavingWaterOffset, at that moment see if we have a
            # leavingWaterTemperature temperature
            lwsensor = self.sensory_data("leavingWaterTemperature")
            if self._setpoint == "leavingWaterOffset" and lwsensor is not None:
                current_temp = lwsensor.value
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
            max_temp = setpointdict.max_value
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
            min_temp = setpointdict.min_value
        else:
            min_temp = super().min_temp
        _LOGGER.debug(
            "Device '%s' %s min temperature '%s'",
            self._device.name,
            self._setpoint,
            min_temp,
        )
        return min_temp

    def get_target_temperature(self):
        value = None
        setpointdict = self.setpoint()
        if setpointdict is not None:
            value = setpointdict.value
        _LOGGER.debug(
            "Device '%s' %s target temperature '%s'",
            self._device.name,
            self._setpoint,
            value,
        )
        return value

    def get_target_temperature_step(self):
        step_value = None
        setpointdict = self.setpoint()
        if setpointdict is not None:
            if setpointdict.step_value is not None:
                step_value = setpointdict.step_value
            else:
                step_value = super().target_temperature_step
        _LOGGER.debug(
            "Device '%s' %s target temperature step '%s'",
            self._device.name,
            self._setpoint,
            step_value,
        )
        return step_value

    async def async_set_temperature(self, **kwargs):
        # """Set new target temperature."""
        if ATTR_HVAC_MODE in kwargs:
            await self.async_set_hvac_mode(kwargs[ATTR_HVAC_MODE])

        if ATTR_TEMPERATURE in kwargs:
            value = kwargs[ATTR_TEMPERATURE]
            _LOGGER.debug(
                "Device '%s' request to set temperature to '%s'",
                self._device.name,
                value,
            )
            if self._attr_target_temperature != value:
                operationmode = self.operation_mode()
                if operationmode is not None:
                    omv = operationmode.value
                    res = await self._device.patch(
                        self._device.id,
                        self._embedded_id,
                        "temperatureControl",
                        f"/operationModes/{omv}/setpoints/{self._setpoint}",
                        value,
                    )
                    # When updating the value to the daikin cloud worked update our local cached version
                    if res:
                        setpointdict = self.setpoint()
                        if setpointdict is not None:
                            self._attr_target_temperature = value
                            self.async_write_ha_state()
                    else:
                        _LOGGER.warning(
                            "Device '%s' problem setting temperature to '%s'",
                            self._device.name,
                            value,
                        )

    def get_hvac_mode(self):
        """Return current HVAC mode."""
        mode = HVACMode.OFF
        operationmode = self.operation_mode()
        cc = self.climate_control()
        if cc is not None:
            onoff = cc.on_off_mode
            if onoff is not None and onoff.value != "off" and operationmode is not None:
                mode = operationmode.value
            _LOGGER.debug(
                "Device '%s' %s hvac mode '%s'",
                self._device.name,
                self._setpoint,
                mode,
            )
        return DAIKIN_HVAC_TO_HA.get(mode, HVACMode.HEAT_COOL)

    def get_hvac_modes(self):
        """Return the list of available HVAC modes."""
        modes = [HVACMode.OFF]
        operationmode = self.operation_mode()
        if operationmode is not None:
            if operationmode.settable:
                for mode in operationmode.values or []:
                    ha_mode = DAIKIN_HVAC_TO_HA[mode]
                    if ha_mode not in modes:
                        modes.append(ha_mode)
            currentmode = operationmode.value
            ha_currentmode = DAIKIN_HVAC_TO_HA[currentmode]
            if ha_currentmode not in modes:
                modes.append(ha_currentmode)
        return modes

    async def async_set_hvac_mode(self, hvac_mode):
        """Set HVAC mode."""
        _LOGGER.debug(
            "Device '%s' request to set hvac_mode to '%s'",
            self._device.name,
            hvac_mode,
        )

        result = True

        # First determine the new settings for onOffMode/operationMode
        on_off_mode = None
        operation_mode = None
        if hvac_mode == HVACMode.OFF:
            if self.hvac_mode != HVACMode.OFF:
                on_off_mode = "off"
        else:
            if self.hvac_mode == HVACMode.OFF:
                on_off_mode = "on"
            operation_mode = HA_HVAC_TO_DAIKIN[hvac_mode]

        cc = self.climate_control()

        # Only set the on/off to Daikin when we need to change it
        if on_off_mode is not None:
            result &= await self._device.patch(self._device.id, self._embedded_id, "onOffMode", "", on_off_mode)
            if result is False:
                _LOGGER.warning(
                    "Device '%s' problem setting onOffMode to '%s'",
                    self._device.name,
                    on_off_mode,
                )
            else:
                cc.on_off_mode.value = on_off_mode

        # Only set the operationMode when it has changed, also prevents setting it when
        # it is readOnly
        if operation_mode is not None and cc.operation_mode is not None and operation_mode != cc.operation_mode.value:
            result &= await self._device.patch(
                self._device.id,
                self._embedded_id,
                "operationMode",
                "",
                operation_mode,
            )
            if result is False:
                _LOGGER.warning(
                    "Device '%s' problem setting operationMode to '%s'",
                    self._device.name,
                    operation_mode,
                )
            else:
                cc.operation_mode.value = operation_mode

        if result is True:
            # When switching hvac mode it could be that we can set min/max/target/etc
            # which we couldn't set with a previous hvac mode
            self.update_state()
            self.async_write_ha_state()

        return result

    def get_fan_mode(self):
        """Return the active fan mode."""
        fan_operation = self.fan_operation()
        if fan_operation is None or fan_operation.fan_speed is None:
            return None
        fan_speed = fan_operation.fan_speed
        mode = fan_speed.current_mode.value
        if mode == FANMODE_FIXED and fan_speed.modes and FANMODE_FIXED in fan_speed.modes:
            mode = str(fan_speed.modes[FANMODE_FIXED].value)
        return self._get_homekit_fan_mode(fan_speed, mode)

    def get_fan_modes(self):
        """Return available fan modes."""
        fan_operation = self.fan_operation()
        if fan_operation is None or fan_operation.fan_speed is None:
            return []
        fan_speed = fan_operation.fan_speed
        fan_modes = []
        for mode in fan_speed.current_mode.values or []:
            if mode == FANMODE_FIXED and fan_speed.modes and FANMODE_FIXED in fan_speed.modes:
                fixed = fan_speed.modes[FANMODE_FIXED]
                if fixed.min_value is not None and fixed.max_value is not None and fixed.step_value is not None:
                    fan_modes.extend(
                        str(value)
                        for value in range(int(fixed.min_value), int(fixed.max_value) + 1, int(fixed.step_value))
                    )
            else:
                fan_modes.append(mode)
        for alias in self._homekit_fan_mode_aliases(fan_speed):
            if alias not in fan_modes:
                fan_modes.append(alias)
        return fan_modes

    async def async_set_fan_mode(self, fan_mode):
        """Set the fan mode"""
        fan_mode = str(fan_mode)
        _LOGGER.debug(
            "Device '%s' request to set fan_mode to '%s'",
            self._device.name,
            fan_mode,
        )

        res = True
        cc = self.climate_control()
        operationmode = cc["operationMode"]["value"]
        fan_control = cc.get("fanControl")
        if fan_control is None:
            # Should not normally happen: HA only offers fan mode controls when
            # get_supported_features() found a fanControl block. Guard against it
            # anyway (e.g. a stale/forced service call) instead of raising.
            _LOGGER.warning(
                "Device '%s' request to set fan_mode ignored, device has no fanControl",
                self._device.name,
            )
            return False
        fan_speed = fan_control["value"]["operationModes"][operationmode].get("fanSpeed")
        requested_fan_mode = fan_mode
        fan_mode = self._resolve_homekit_fan_mode_alias(fan_speed, fan_mode)
        if fan_mode.isnumeric():
            if fan_speed["currentMode"]["value"] != FANMODE_FIXED:
                # Only set currentMode to fixed when it isn't already fixed.
                res = await self._device.patch(
                    self._device.id,
                    self._embedded_id,
                    "fanControl",
                    f"/operationModes/{operationmode}/fanSpeed/currentMode",
                    FANMODE_FIXED,
                )
                if res is False:
                    _LOGGER.warning(
                        "Device '%s' problem setting fan_mode to fixed",
                        self._device.name,
                    )

            new_fixed_mode = int(fan_mode)
            if fan_speed["modes"]["fixed"]["value"] != new_fixed_mode:
                res &= await self._device.patch(
                    self._device.id,
                    self._embedded_id,
                    "fanControl",
                    f"/operationModes/{operationmode}/fanSpeed/modes/fixed",
                    new_fixed_mode,
                )
                if res is False:
                    _LOGGER.warning(
                        "Device '%s' problem setting fan_mode fixed to '%s'",
                        self._device.name,
                        new_fixed_mode,
                    )
            else:
                _LOGGER.debug(
                    "Device '%s' request to set fan mode '%s' ignored already set",
                    self._device.name,
                    fan_mode,
                )
        else:
            if fan_speed["currentMode"]["value"] != fan_mode:
                res = await self._device.patch(
                    self._device.id,
                    self._embedded_id,
                    "fanControl",
                    f"/operationModes/{operationmode}/fanSpeed/currentMode",
                    fan_mode,
                )
                if res is False:
                    _LOGGER.warning(
                        "Device '%s' problem setting fan_mode to '%s'",
                        self._device.name,
                        fan_mode,
                    )
            else:
                _LOGGER.debug(
                    "Device '%s' request to set fan mode '%s' ignored already set",
                    self._device.name,
                    fan_mode,
                )

        if res is True:
            if fan_mode.isnumeric():
                fan_speed["currentMode"]["value"] = FANMODE_FIXED
                fan_speed["modes"][FANMODE_FIXED]["value"] = int(fan_mode)
            else:
                fan_speed["currentMode"]["value"] = fan_mode
            self._attr_fan_mode = requested_fan_mode
            self.async_write_ha_state()

        return res

    def __get_swing_mode(self, direction):
        """Return current swing mode for an axis."""
        fan_operation = self.fan_operation()
        if fan_operation is None or fan_operation.fan_direction is None:
            return ""
        axis = getattr(fan_operation.fan_direction, direction)
        return axis.current_mode.value.lower() if axis is not None else ""

    def get_swing_mode(self):
        return self.__get_swing_mode("vertical")

    def get_swing_horizontal_mode(self):
        return self.__get_swing_mode("horizontal")

    def __get_swing_modes(self, direction):
        """Return supported swing modes for an axis."""
        fan_operation = self.fan_operation()
        if fan_operation is None or fan_operation.fan_direction is None:
            return []
        axis = getattr(fan_operation.fan_direction, direction)
        if axis is None:
            return []
        return [mode.lower() for mode in axis.current_mode.values or []]

    def get_swing_modes(self):
        return self.__get_swing_modes("vertical")

    def get_swing_horizontal_modes(self):
        return self.__get_swing_modes("horizontal")

    async def __set_swing(self, direction, swing_mode):
        _LOGGER.debug(
            "Device '%s' request to set swing %s mode to '%s'",
            self._device.name,
            direction,
            swing_mode,
        )
        res = True
        cc = self.climate_control()
        fan_control = cc.get("fanControl")
        operation_mode = cc["operationMode"]["value"]
        if fan_control is not None:
            operation_mode = cc["operationMode"]["value"]
            fan_direction = fan_control["value"]["operationModes"][operation_mode].get("fanDirection")
            if fan_direction is not None:
                fd = fan_direction.get(direction)
                if fd is not None:
                    new_mode = "stop"
                    # For translation the current mode is always lower case, but we need to send
                    # the daikin mixed case mode, so search that
                    for mode in fd["currentMode"]["values"]:
                        if swing_mode == mode.lower():
                            new_mode = mode
                    res = await self._device.patch(
                        self._device.id,
                        self._embedded_id,
                        "fanControl",
                        f"/operationModes/{operation_mode}/fanDirection/{direction}/currentMode",
                        new_mode,
                    )
                    if res is False:
                        _LOGGER.warning(
                            "Device '%s' problem setting %s swing mode to '%s'",
                            self._device.name,
                            direction,
                            new_mode,
                        )
        return res

    async def async_set_swing_mode(self, swing_mode):
        res = True
        if self.swing_mode != swing_mode:
            res = await self.__set_swing("vertical", swing_mode)

            if res is True:
                self._attr_swing_mode = swing_mode
                self.async_write_ha_state()
        else:
            _LOGGER.debug(
                "Device '%s' request to set vertical swing mode '%s' ignored already set",
                self._device.name,
                swing_mode,
            )

        return res

    async def async_set_swing_horizontal_mode(self, swing_mode):
        res = True
        if self.swing_horizontal_mode != swing_mode:
            res = await self.__set_swing("horizontal", swing_mode)

            if res is True:
                self._attr_swing_horizontal_mode = swing_mode
                self.async_write_ha_state()
        else:
            _LOGGER.debug(
                "Device '%s' request to set horizontal swing mode '%s' ignored already set",
                self._device.name,
                swing_mode,
            )

        return res

    def get_preset_mode(self):
        current_preset_mode = PRESET_NONE
        cc = self.climate_control()
        if cc is not None:
            for mode in self.preset_modes:
                daikin_mode = HA_PRESET_TO_DAIKIN[mode]
                preset = cc.get(daikin_mode)
                if preset is not None:
                    preset_value = preset.get("value")
                    if preset_value is not None:
                        # for example holidayMode value is a dict object with an enabled value
                        if isinstance(preset_value, dict):
                            enabled_value = preset_value.get("enabled")
                            if enabled_value is not None and enabled_value:
                                current_preset_mode = mode
                        if preset_value == "on":
                            current_preset_mode = mode
        return current_preset_mode

    async def async_set_preset_mode(self, preset_mode):
        _LOGGER.debug("Device '%s' request set preset mode %s", self._device.name, preset_mode)
        result = True
        new_daikin_mode = HA_PRESET_TO_DAIKIN[preset_mode]

        if self.preset_mode != PRESET_NONE:
            current_mode = HA_PRESET_TO_DAIKIN[self.preset_mode]
            if self.preset_mode == PRESET_AWAY:
                value = {"enabled": False}
                result &= await self._device.post(self._device.id, self._embedded_id, "holiday-mode", value)
                if result is False:
                    _LOGGER.warning(
                        "Device '%s' problem setting %s to off",
                        self._device.name,
                        current_mode,
                    )
            else:
                result &= await self._device.patch(self._device.id, self._embedded_id, current_mode, "", "off")
                if result is False:
                    _LOGGER.warning(
                        "Device '%s' problem setting %s to off",
                        self._device.name,
                        current_mode,
                    )

        if preset_mode != PRESET_NONE:
            if self.hvac_mode == HVACMode.OFF and preset_mode == PRESET_BOOST:
                result &= await self.async_turn_on()

            if preset_mode == PRESET_AWAY:
                value = {"enabled": True, "startDate": date.today().isoformat(), "endDate": (date.today() + timedelta(days=60)).isoformat()}
                result &= await self._device.post(self._device.id, self._embedded_id, "holiday-mode", value)
                if result is False:
                    _LOGGER.warning(
                        "Device '%s' problem setting %s to on",
                        self._device.name,
                        new_daikin_mode,
                    )
            else:
                result &= await self._device.patch(self._device.id, self._embedded_id, new_daikin_mode, "", "on")
                if result is False:
                    _LOGGER.warning(
                        "Device '%s' problem setting %s to on",
                        self._device.name,
                        new_daikin_mode,
                    )

        if result is True:
            self._attr_preset_mode = preset_mode
            self.async_write_ha_state()

        return result

    def get_preset_modes(self):
        supported_preset_modes = [PRESET_NONE]
        cc = self.climate_control()
        if cc is not None:
            for mode in PRESET_MODES:
                daikin_mode = HA_PRESET_TO_DAIKIN[mode]
                preset = cc.get(daikin_mode)
                if preset is not None and preset.get("value") is not None:
                    supported_preset_modes.append(mode)

            _LOGGER.debug(
                "Device '%s' supports preset_modes %s",
                self._device.name,
                format(supported_preset_modes),
            )

            supported_preset_modes.sort()

        return supported_preset_modes

    async def async_turn_on(self):
        """Turn device CLIMATE on."""
        _LOGGER.debug("Device '%s' request to turn on", self._device.name)
        cc = self.climate_control()
        result = True
        if cc.on_off_mode is not None and cc.on_off_mode.value == "off":
            result &= await self._device.patch(self._device.id, self._embedded_id, "onOffMode", "", "on")
            if result is False:
                _LOGGER.error("Device '%s' problem setting onOffMode to on", self._device.name)
            else:
                cc.on_off_mode.value = "on"
                self._attr_hvac_mode = self.get_hvac_mode()
                self.async_write_ha_state()
        else:
            _LOGGER.debug(
                "Device '%s' request to turn on ignored because device is already on",
                self._device.name,
            )

        return result

    async def async_turn_off(self):
        _LOGGER.debug("Device '%s' request to turn off", self._device.name)
        cc = self.climate_control()
        result = True
        if cc.on_off_mode is not None and cc.on_off_mode.value == "on":
            result &= await self._device.patch(self._device.id, self._embedded_id, "onOffMode", "", "off")
            if result is False:
                _LOGGER.error("Device '%s' problem setting onOffMode to off", self._device.name)
            else:
                cc.on_off_mode.value = "off"
                self._attr_hvac_mode = self.get_hvac_mode()
                self.async_write_ha_state()
        else:
            _LOGGER.debug(
                "Device '%s' request to turn off ignored because device is already off",
                self._device.name,
            )

        return result
