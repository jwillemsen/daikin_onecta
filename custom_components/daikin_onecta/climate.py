"""Support for the Daikin HVAC."""

from collections.abc import Awaitable, Callable
from datetime import date, timedelta
import logging
import re
from typing import override

from homeassistant.components.climate import FAN_HIGH, FAN_LOW, FAN_MEDIUM, FAN_MIDDLE, ClimateEntity
from homeassistant.components.climate.const import (
    ATTR_HVAC_MODE,
    PRESET_AWAY,
    PRESET_BOOST,
    PRESET_COMFORT,
    PRESET_ECO,
    PRESET_NONE,
    ClimateEntityFeature,
    HVACMode,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_TEMPERATURE, UnitOfTemperature
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.util import dt as dt_util

from daikin_onecta.client import ClimateControlClient
from daikin_onecta.models import ClimateControl

from .const import CONF_HOMEKIT_FAN_MODE_ALIASES, FANMODE_FIXED
from .coordinator import OnectaDataUpdateCoordinator
from .entity import DaikinEntity
from .entity_descriptions import CLIMATE_DESCRIPTIONS

_LOGGER = logging.getLogger(__name__)

PRESET_MODES = (PRESET_BOOST, PRESET_AWAY, PRESET_COMFORT, PRESET_ECO)

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
    coordinator: OnectaDataUpdateCoordinator = config_entry.runtime_data
    for device in (coordinator.data or {}).values():
        modes: list[str] = []
        device_model = device.device.device_model
        embedded_id = ""
        for management_point in device.device.management_points_by_type("climateControl"):
            embedded_id = management_point.embedded_id
            climate_control = management_point.climate_control
            if climate_control is not None:
                modes.extend(climate_control.setpoint_types)
        # Remove duplicates
        modes = list(dict.fromkeys(modes))
        _LOGGER.info("Climate: Device '%s' has modes %s", device_model, modes)
        for mode in modes:
            async_add_entities(
                [DaikinClimate(device, mode, coordinator, embedded_id)],
                update_before_add=False,
            )


class DaikinClimate(DaikinEntity, ClimateEntity):
    """Representation of a Daikin HVAC."""

    coordinator: OnectaDataUpdateCoordinator

    _enable_turn_on_off_backwards_compatibility = False  # Remove with HA 2025.1

    # Setpoint is the setpoint string under
    # temperatureControl/value/operationsModes/mode/setpoints, for example roomTemperature/leavingWaterOffset
    def __init__(self, device, setpoint, coordinator: OnectaDataUpdateCoordinator, embedded_id):
        """Initialize the climate device."""
        super().__init__(device, coordinator)
        _LOGGER.info(
            "Device '%s' initializing Daikin Climate for controlling %s",
            device.name,
            setpoint,
        )
        self._embedded_id = embedded_id
        self._setpoint = setpoint
        self._attr_temperature_unit = UnitOfTemperature.CELSIUS
        self._attr_unique_id = f"{self._device.id}_{self._embedded_id}_{self._setpoint}"
        self._attr_has_entity_name = True
        self.entity_description = CLIMATE_DESCRIPTIONS[setpoint]
        self.update_state()

    def update_state(self) -> None:
        """Refresh all state attributes from the device."""
        # Successful writes update the typed model optimistically so Home
        # Assistant reflects the new state without waiting for the next poll.
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

    async def _async_execute_climate_command(
        self,
        command: Callable[[ClimateControlClient], Awaitable[None]],
        translation_key: str,
    ) -> bool:
        """Execute a typed climate command through the shared cloud adapter."""
        await self._async_execute_command(
            lambda client: command(client.climate_control(self._device.id, self._embedded_id)),
            translation_key,
        )
        return True

    @callback
    @override
    def _handle_coordinator_update(self) -> None:
        self.update_state()
        self.async_write_ha_state()

    def climate_control(self) -> ClimateControl | None:
        """Return the library's typed climate-control state view."""
        management_point = self._device.management_point(self._embedded_id)
        return management_point.climate_control if management_point is not None else None

    def operation_mode(self):
        """Return the operation-mode characteristic."""
        cc = self.climate_control()
        return cc.operation_mode if cc is not None else None

    def fan_operation(self):
        """Return fan controls for the active operation mode."""
        cc = self.climate_control()
        return cc.fan_operation() if cc is not None else None

    def preset_characteristic(self, daikin_mode):
        """Return a preset characteristic by Daikin API name."""
        cc = self.climate_control()
        return cc.mode_characteristic(daikin_mode) if cc is not None else None

    @property
    def _homekit_fan_mode_aliases_enabled(self):
        """Return whether HomeKit fan mode aliases are enabled."""
        return self.coordinator.options.get(CONF_HOMEKIT_FAN_MODE_ALIASES, False)

    def homekit_fan_mode_aliases(self, fan_speed):
        """Return HomeKit fan mode aliases available for the fan speed data."""
        aliases: dict[str, str] = {}
        if not self._homekit_fan_mode_aliases_enabled:
            return aliases

        current_mode_values = fan_speed.current_mode.values or []
        if DAIKIN_FAN_MODE_QUIET in current_mode_values:
            aliases[FAN_LOW] = DAIKIN_FAN_MODE_QUIET

        if FANMODE_FIXED not in current_mode_values or not fan_speed.modes:
            return aliases
        fixed_mode = fan_speed.modes.get(FANMODE_FIXED)
        if fixed_mode is None or fixed_mode.min_value is None or fixed_mode.max_value is None or fixed_mode.step_value is None:
            return aliases
        fixed_values = {
            str(value)
            for value in range(
                int(fixed_mode.min_value),
                int(fixed_mode.max_value) + 1,
                int(fixed_mode.step_value),
            )
        }
        aliases.update({alias: daikin_mode for alias, daikin_mode in HOMEKIT_FIXED_FAN_MODE_ALIASES.items() if daikin_mode in fixed_values})
        return aliases

    def get_homekit_fan_mode(self, fan_speed, fan_mode):
        """Return the HomeKit alias for a Daikin fan mode when available."""
        if not self._homekit_fan_mode_aliases_enabled:
            return fan_mode

        aliases = self.homekit_fan_mode_aliases(fan_speed)
        for alias, daikin_mode in aliases.items():
            if fan_mode == daikin_mode:
                return alias

        return fan_mode

    def resolve_homekit_fan_mode_alias(self, fan_speed, fan_mode):
        """Return the Daikin fan mode represented by a HomeKit alias."""
        return self.homekit_fan_mode_aliases(fan_speed).get(fan_mode, fan_mode)

    def setpoint(self):
        """Return the active operation-mode setpoint."""
        cc = self.climate_control()
        return cc.setpoint(self._setpoint) if cc is not None else None

    def sensory_data(self, setpoint):
        """Return a sensory characteristic by Daikin API name."""
        cc = self.climate_control()
        return cc.sensory_data(setpoint) if cc is not None else None

    def get_supported_features(self):
        """Return the features supported by this climate entity."""
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
    @override
    def name(self):
        """Return the readable setpoint name."""
        myname = self._setpoint[0].upper() + self._setpoint[1:]
        readable = re.findall("[A-Z][^A-Z]*", myname)
        return f"{' '.join(readable)}"

    def get_current_temperature(self):
        """Return the current temperature for this setpoint."""
        cc = self.climate_control()
        current_temp = cc.current_temperature(self._setpoint) if cc is not None else None
        _LOGGER.debug(
            "Device '%s' %s current temperature '%s'",
            self._device.name,
            self._setpoint,
            current_temp,
        )
        return current_temp

    def get_max_temp(self):
        """Return the maximum configurable temperature."""
        max_temp = None
        setpointdict = self.setpoint()
        max_temp = setpointdict.max_value if setpointdict is not None else super().max_temp
        _LOGGER.debug(
            "Device '%s' %s max temperature '%s'",
            self._device.name,
            self._setpoint,
            max_temp,
        )
        return max_temp

    def get_min_temp(self):
        """Return the minimum configurable temperature."""
        min_temp = None
        setpointdict = self.setpoint()
        min_temp = setpointdict.min_value if setpointdict is not None else super().min_temp
        _LOGGER.debug(
            "Device '%s' %s min temperature '%s'",
            self._device.name,
            self._setpoint,
            min_temp,
        )
        return min_temp

    def get_target_temperature(self):
        """Return the configured target temperature."""
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
        """Return the target temperature increment."""
        step_value = None
        setpointdict = self.setpoint()
        if setpointdict is not None:
            step_value = setpointdict.step_value if setpointdict.step_value is not None else super().target_temperature_step
        _LOGGER.debug(
            "Device '%s' %s target temperature step '%s'",
            self._device.name,
            self._setpoint,
            step_value,
        )
        return step_value

    @override
    async def async_set_temperature(self, **kwargs):
        """Set the HVAC mode and/or target temperature."""
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
                    res = await self._async_execute_climate_command(
                        lambda climate: climate.set_temperature(omv, self._setpoint, value),
                        "climate_set_temperature_failed",
                    )
                    # When updating the value to the daikin cloud worked update our local cached version
                    if res:
                        setpointdict = self.setpoint()
                        if setpointdict is not None:
                            setpointdict.value = value
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

    @override
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
            result &= await self._async_execute_climate_command(
                lambda climate: climate.set_power(on_off_mode == "on"),
                "climate_set_hvac_mode_failed",
            )
            if result is False:
                _LOGGER.warning(
                    "Device '%s' problem setting onOffMode to '%s'",
                    self._device.name,
                    on_off_mode,
                )
            elif cc is not None and cc.on_off_mode is not None:
                cc.on_off_mode.value = on_off_mode

        # Only set the operationMode when it has changed, also prevents setting it when
        # it is readOnly
        if operation_mode is not None and cc is not None and cc.operation_mode is not None and operation_mode != cc.operation_mode.value:
            result &= await self._async_execute_climate_command(
                lambda climate: climate.set_operation_mode(operation_mode),
                "climate_set_hvac_mode_failed",
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
        return self.get_homekit_fan_mode(fan_speed, mode)

    def get_fan_modes(self):
        """Return available fan modes."""
        fan_operation = self.fan_operation()
        if fan_operation is None or fan_operation.fan_speed is None:
            return []
        fan_speed = fan_operation.fan_speed
        fan_modes: list[str] = []
        for mode in fan_speed.current_mode.values or []:
            if mode == FANMODE_FIXED and fan_speed.modes and FANMODE_FIXED in fan_speed.modes:
                fixed = fan_speed.modes[FANMODE_FIXED]
                if fixed.min_value is not None and fixed.max_value is not None and fixed.step_value is not None:
                    fan_modes.extend(str(value) for value in range(int(fixed.min_value), int(fixed.max_value) + 1, int(fixed.step_value)))
            else:
                fan_modes.append(mode)
        for alias in self.homekit_fan_mode_aliases(fan_speed):
            if alias not in fan_modes:
                fan_modes.append(alias)
        return fan_modes

    @override
    async def async_set_fan_mode(self, fan_mode):
        """Set the fan mode."""
        requested_fan_mode = str(fan_mode)
        fan_operation = self.fan_operation()
        cc = self.climate_control()
        if fan_operation is None or fan_operation.fan_speed is None or cc is None or cc.operation_mode is None:
            return False
        fan_speed = fan_operation.fan_speed
        operation_mode = cc.operation_mode.value
        fan_mode = self.resolve_homekit_fan_mode_alias(fan_speed, requested_fan_mode)
        result = True
        if fan_mode.isnumeric():
            if fan_speed.current_mode.value != FANMODE_FIXED:
                result = await self._async_execute_climate_command(
                    lambda climate: climate.set_fan_mode(operation_mode, FANMODE_FIXED),
                    "climate_set_fan_mode_failed",
                )
            fixed = fan_speed.modes.get(FANMODE_FIXED) if fan_speed.modes else None
            new_fixed_mode = int(fan_mode)
            if result and fixed is not None and fixed.value != new_fixed_mode:
                result &= await self._async_execute_climate_command(
                    lambda climate: climate.set_fixed_fan_speed(operation_mode, new_fixed_mode),
                    "climate_set_fan_mode_failed",
                )
            if result:
                fan_speed.current_mode.value = FANMODE_FIXED
                if fixed is not None:
                    fixed.value = new_fixed_mode
        elif fan_speed.current_mode.value != fan_mode:
            result = await self._async_execute_climate_command(
                lambda climate: climate.set_fan_mode(operation_mode, fan_mode),
                "climate_set_fan_mode_failed",
            )
            if result:
                fan_speed.current_mode.value = fan_mode

        if result:
            self._attr_fan_mode = requested_fan_mode
            self.async_write_ha_state()
        return result

    def __get_swing_mode(self, direction):
        """Return current swing mode for an axis."""
        fan_operation = self.fan_operation()
        if fan_operation is None or fan_operation.fan_direction is None:
            return ""
        axis = getattr(fan_operation.fan_direction, direction)
        return axis.current_mode.value.lower() if axis is not None else ""

    def get_swing_mode(self):
        """Return the vertical swing mode."""
        return self.__get_swing_mode("vertical")

    def get_swing_horizontal_mode(self):
        """Return the horizontal swing mode."""
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
        """Return the supported vertical swing modes."""
        return self.__get_swing_modes("vertical")

    def get_swing_horizontal_modes(self):
        """Return the supported horizontal swing modes."""
        return self.__get_swing_modes("horizontal")

    async def __set_swing(self, direction, swing_mode):
        """Set a fan-direction mode."""
        fan_operation = self.fan_operation()
        cc = self.climate_control()
        if fan_operation is None or fan_operation.fan_direction is None or cc is None or cc.operation_mode is None:
            return False
        axis = getattr(fan_operation.fan_direction, direction)
        if axis is None:
            return False
        new_mode = next(
            (mode for mode in axis.current_mode.values or [] if swing_mode == mode.lower()),
            "stop",
        )
        operation_mode = cc.operation_mode.value
        result = await self._async_execute_climate_command(
            lambda climate: climate.set_fan_direction(operation_mode, direction, new_mode),
            "climate_set_swing_mode_failed",
        )
        if result:
            axis.current_mode.value = new_mode
        return result

    @override
    async def async_set_swing_mode(self, swing_mode):
        """Set the vertical swing mode."""
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

    @override
    async def async_set_swing_horizontal_mode(self, swing_mode):
        """Set the horizontal swing mode."""
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
        """Return the active preset mode."""
        for mode in PRESET_MODES:
            preset = self.preset_characteristic(HA_PRESET_TO_DAIKIN[mode])
            if preset is None:
                continue
            if mode == PRESET_AWAY:
                if preset.value.enabled:
                    return mode
            elif preset.value == "on":
                return mode
        return PRESET_NONE

    async def _async_disable_preset_mode(self, preset_mode) -> bool:
        """Disable the current Daikin preset mode."""
        daikin_mode = HA_PRESET_TO_DAIKIN[preset_mode]
        if preset_mode == PRESET_AWAY:
            result = await self._async_execute_climate_command(
                lambda climate: climate.set_holiday_mode(False),
                "climate_set_preset_mode_failed",
            )
        else:
            result = await self._async_execute_climate_command(
                lambda climate: climate.set_mode_characteristic(daikin_mode, False),
                "climate_set_preset_mode_failed",
            )
        if not result:
            _LOGGER.warning("Device '%s' problem setting %s to off", self._device.name, daikin_mode)
        return result

    async def _async_enable_preset_mode(self, preset_mode) -> bool:
        """Enable the requested Daikin preset mode."""
        daikin_mode = HA_PRESET_TO_DAIKIN[preset_mode]
        turned_on = True
        if self.hvac_mode == HVACMode.OFF and preset_mode == PRESET_BOOST:
            turned_on = await self.async_turn_on()
        if preset_mode == PRESET_AWAY:
            today: date = dt_util.now().date()
            result = await self._async_execute_climate_command(
                lambda climate: climate.set_holiday_mode(True, start_date=today, end_date=today + timedelta(days=60)),
                "climate_set_preset_mode_failed",
            )
        else:
            result = await self._async_execute_climate_command(
                lambda climate: climate.set_mode_characteristic(daikin_mode, True),
                "climate_set_preset_mode_failed",
            )
        if not result:
            _LOGGER.warning("Device '%s' problem setting %s to on", self._device.name, daikin_mode)
        return turned_on and result

    @override
    async def async_set_preset_mode(self, preset_mode):
        """Set the active preset mode."""
        _LOGGER.debug("Device '%s' request set preset mode %s", self._device.name, preset_mode)
        result = True

        if self.preset_mode != PRESET_NONE:
            result &= await self._async_disable_preset_mode(self.preset_mode)

        if preset_mode != PRESET_NONE:
            result &= await self._async_enable_preset_mode(preset_mode)

        if result is True:
            self._attr_preset_mode = preset_mode
            self.async_write_ha_state()

        return result

    def get_preset_modes(self):
        """Return supported preset modes."""
        supported = [PRESET_NONE]
        supported.extend(mode for mode in PRESET_MODES if self.preset_characteristic(HA_PRESET_TO_DAIKIN[mode]) is not None)
        supported.sort()
        return supported

    @override
    async def async_turn_on(self):
        """Turn device CLIMATE on."""
        _LOGGER.debug("Device '%s' request to turn on", self._device.name)
        cc = self.climate_control()
        result = True
        on_off_mode = cc.on_off_mode if cc is not None else None
        if on_off_mode is not None and on_off_mode.value == "off":
            result &= await self._async_execute_climate_command(
                lambda climate: climate.set_power(True),
                "climate_turn_on_failed",
            )
            if result is False:
                _LOGGER.error("Device '%s' problem setting onOffMode to on", self._device.name)
            else:
                on_off_mode.value = "on"
                self._attr_hvac_mode = self.get_hvac_mode()
                self.async_write_ha_state()
        else:
            _LOGGER.debug(
                "Device '%s' request to turn on ignored because device is already on",
                self._device.name,
            )

        return result

    @override
    async def async_turn_off(self):
        """Turn the climate entity off."""
        _LOGGER.debug("Device '%s' request to turn off", self._device.name)
        cc = self.climate_control()
        result = True
        on_off_mode = cc.on_off_mode if cc is not None else None
        if on_off_mode is not None and on_off_mode.value == "on":
            result &= await self._async_execute_climate_command(
                lambda climate: climate.set_power(False),
                "climate_turn_off_failed",
            )
            if result is False:
                _LOGGER.error("Device '%s' problem setting onOffMode to off", self._device.name)
            else:
                on_off_mode.value = "off"
                self._attr_hvac_mode = self.get_hvac_mode()
                self.async_write_ha_state()
        else:
            _LOGGER.debug(
                "Device '%s' request to turn off ignored because device is already off",
                self._device.name,
            )

        return result
