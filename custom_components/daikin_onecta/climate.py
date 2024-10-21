"""Support for the Daikin HVAC."""
import logging
import re
from datetime import date
from datetime import timedelta

import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant.components.climate import ClimateEntity
from homeassistant.components.climate import PLATFORM_SCHEMA
from homeassistant.components.climate.const import ATTR_HVAC_MODE
from homeassistant.components.climate.const import ClimateEntityFeature
from homeassistant.components.climate.const import HVACMode
from homeassistant.components.climate.const import PRESET_AWAY
from homeassistant.components.climate.const import PRESET_BOOST
from homeassistant.components.climate.const import PRESET_COMFORT
from homeassistant.components.climate.const import PRESET_ECO
from homeassistant.components.climate.const import PRESET_NONE
from homeassistant.components.climate.const import SWING_BOTH
from homeassistant.components.climate.const import SWING_HORIZONTAL
from homeassistant.components.climate.const import SWING_OFF
from homeassistant.components.climate.const import SWING_VERTICAL
from homeassistant.const import ATTR_TEMPERATURE
from homeassistant.const import CONF_HOST
from homeassistant.const import CONF_NAME
from homeassistant.const import UnitOfTemperature
from homeassistant.core import callback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import COORDINATOR
from .const import DAIKIN_DEVICES
from .const import DOMAIN as DAIKIN_DOMAIN
from .const import FANMODE_FIXED
from .const import SWING_COMFORT
from .const import SWING_COMFORT_HORIZONTAL
from .const import SWING_FLOOR
from .const import SWING_FLOOR_HORIZONTAL

_LOGGER = logging.getLogger(__name__)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({vol.Required(CONF_HOST): cv.string, vol.Optional(CONF_NAME): cv.string})

PRESET_MODES = {PRESET_COMFORT, PRESET_ECO, PRESET_AWAY, PRESET_BOOST}

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


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up Daikin climate based on config_entry."""
    coordinator = hass.data[DAIKIN_DOMAIN][COORDINATOR]
    for dev_id, device in hass.data[DAIKIN_DOMAIN][DAIKIN_DEVICES].items():
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
        self.update_state()

    def update_state(self) -> None:
        self._attr_supported_features = self.get_supported_features()
        self._attr_current_temperature = self.get_current_temperature()
        self._attr_max_temp = self.get_max_temp()
        self._attr_min_temp = self.get_min_temp()
        self._attr_target_temperature_step = self.get_target_temperature_step()
        self._attr_target_temperature = self.get_target_temperature()
        self._attr_hvac_modes = self.get_hvac_modes()
        self._attr_swing_modes = self.get_swing_modes()
        self._attr_preset_modes = self.get_preset_modes()
        self._attr_fan_modes = self.get_fan_modes()
        self._attr_hvac_mode = self.get_hvac_mode()
        self._attr_swing_mode = self.get_swing_mode()
        self._attr_preset_mode = self.get_preset_mode()
        self._attr_fan_mode = self.get_fan_mode()
        self._attr_device_info = self._device.device_info()

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
        if self._device.daikin_data["managementPoints"] is not None:
            for management_point in self._device.daikin_data["managementPoints"]:
                management_point_type = management_point["managementPointType"]
                if management_point_type in supported_management_point_types:
                    cc = management_point
        return cc

    def operation_mode(self):
        cc = self.climate_control()
        return cc.get("operationMode")

    def setpoint(self):
        setpoint = None
        cc = self.climate_control()
        # Check if we have a temperatureControl
        temperature_control = cc.get("temperatureControl")
        if temperature_control is not None:
            operation_mode = cc.get("operationMode").get("value")
            # For not all operationModes there is a temperatureControl setpoint available
            oo = temperature_control["value"]["operationModes"].get(operation_mode)
            if oo is not None:
                setpoint = oo["setpoints"].get(self._setpoint)
            _LOGGER.info(
                "Device '%s': %s operation mode %s has setpoint %s",
                self._device.name,
                self._setpoint,
                operation_mode,
                setpoint,
            )
        return setpoint

    def sensory_data(self, setpoint):
        sensoryData = None
        supported_management_point_types = {"climateControl"}
        if self._device.daikin_data["managementPoints"] is not None:
            for management_point in self._device.daikin_data["managementPoints"]:
                management_point_type = management_point["managementPointType"]
                if management_point_type in supported_management_point_types:
                    # Check if we have a sensoryData
                    sensoryData = management_point.get("sensoryData")
                    _LOGGER.info("Climate: Device sensoryData %s", sensoryData)
                    if sensoryData is not None:
                        sensoryData = sensoryData.get("value").get(setpoint)
                        _LOGGER.info(
                            "Device '%s': %s sensoryData %s",
                            self._device.name,
                            setpoint,
                            sensoryData,
                        )
        return sensoryData

    @property
    def translation_key(self) -> str:
        return "daikin_onecta"

    def get_supported_features(self):
        supported_features = 0
        if hasattr(ClimateEntityFeature, "TURN_OFF"):
            supported_features = ClimateEntityFeature.TURN_OFF | ClimateEntityFeature.TURN_ON
        setpointdict = self.setpoint()
        cc = self.climate_control()
        if setpointdict is not None and setpointdict["settable"] is True:
            supported_features |= ClimateEntityFeature.TARGET_TEMPERATURE
        if len(self.get_preset_modes()) > 1:
            supported_features |= ClimateEntityFeature.PRESET_MODE
        fanControl = cc.get("fanControl")
        if fanControl is not None:
            operationmode = cc["operationMode"]["value"]
            operationmodedict = fanControl["value"]["operationModes"].get(operationmode)
            if operationmodedict is not None:
                if operationmodedict.get("fanSpeed") is not None:
                    supported_features |= ClimateEntityFeature.FAN_MODE
                if operationmodedict.get("fanDirection") is not None:
                    supported_features |= ClimateEntityFeature.SWING_MODE

        _LOGGER.info("Device '%s' supports features %s", self._device.name, supported_features)

        return supported_features

    @property
    def name(self):
        device_name = self._device.name
        myname = self._setpoint[0].upper() + self._setpoint[1:]
        readable = re.findall("[A-Z][^A-Z]*", myname)
        return f"{device_name} {' '.join(readable)}"

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
        _LOGGER.info(
            "Device '%s': %s current temperature '%s'",
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
        _LOGGER.info(
            "Device '%s': %s max temperature '%s'",
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
        _LOGGER.info(
            "Device '%s': %s min temperature '%s'",
            self._device.name,
            self._setpoint,
            min_temp,
        )
        return min_temp

    def get_target_temperature(self):
        value = None
        setpointdict = self.setpoint()
        if setpointdict is not None:
            value = setpointdict["value"]
        _LOGGER.info(
            "Device '%s': %s target temperature '%s'",
            self._device.name,
            self._setpoint,
            value,
        )
        return value

    def get_target_temperature_step(self):
        step_value = None
        setpointdict = self.setpoint()
        if setpointdict is not None:
            step_value = setpointdict["stepValue"]
        _LOGGER.info(
            "Device '%s': %s target temperature step '%s'",
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
            if self._attr_target_temperature != value:
                operationmode = self.operation_mode()
                omv = operationmode["value"]
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

    def get_hvac_mode(self):
        """Return current HVAC mode."""
        mode = HVACMode.OFF
        operationmode = self.operation_mode()
        cc = self.climate_control()
        onoff = cc.get("onOffMode")
        if onoff is not None:
            if onoff["value"] != "off":
                mode = operationmode["value"]
        return DAIKIN_HVAC_TO_HA.get(mode, HVACMode.HEAT_COOL)

    def get_hvac_modes(self):
        """Return the list of available HVAC modes."""
        modes = [HVACMode.OFF]
        operationmode = self.operation_mode()
        if operationmode is not None:
            if operationmode["settable"] is True:
                for mode in operationmode["values"]:
                    ha_mode = DAIKIN_HVAC_TO_HA[mode]
                    if ha_mode not in modes:
                        modes.append(ha_mode)
            currentmode = operationmode["value"]
            ha_currentmode = DAIKIN_HVAC_TO_HA[currentmode]
            if ha_currentmode not in modes:
                modes.append(ha_currentmode)
        return modes

    async def async_set_hvac_mode(self, hvac_mode):
        """Set HVAC mode."""
        _LOGGER.debug(
            "Device '%s' request to set hvac_mode to %s",
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
                    "Device '%s' problem setting onOffMode to %s",
                    self._device.name,
                    on_off_mode,
                )
            else:
                cc["onOffMode"]["value"] = on_off_mode

        if operation_mode is not None:
            # Only set the operationMode when it has changed, also prevents setting it when
            # it is readOnly
            if operation_mode != cc["operationMode"]["value"]:
                result &= await self._device.patch(
                    self._device.id,
                    self._embedded_id,
                    "operationMode",
                    "",
                    operation_mode,
                )
                if result is False:
                    _LOGGER.warning(
                        "Device '%s' problem setting operationMode to %s",
                        self._device.name,
                        operation_mode,
                    )
                else:
                    cc["operationMode"]["value"] = operation_mode

        if result is True:
            # When switching hvac mode it could be that we can set min/max/target/etc
            # which we couldn't set with a previous hvac mode
            self.update_state()
            self.async_write_ha_state()

        return result

    def get_fan_mode(self):
        fan_mode = None
        cc = self.climate_control()
        # Check if we have a fanControl
        fanControl = cc.get("fanControl")
        if fanControl is not None:
            operation_mode = cc["operationMode"]["value"]
            operationmodedict = fanControl["value"]["operationModes"].get(operation_mode)
            if operationmodedict is not None:
                fan_speed = operationmodedict.get("fanSpeed")
                if fan_speed is not None:
                    mode = fan_speed["currentMode"]["value"]
                    if mode == FANMODE_FIXED:
                        fsm = fan_speed.get("modes")
                        if fsm is not None:
                            fixedModes = fsm[mode]
                            fan_mode = str(fixedModes["value"])
                    else:
                        fan_mode = mode

        _LOGGER.info(
            "Device '%s' has fan mode '%s'",
            self._device.name,
            fan_mode,
        )

        return fan_mode

    def get_fan_modes(self):
        fan_modes = []
        cc = self.climate_control()
        # Check if we have a fanControl
        fan_control = cc.get("fanControl")
        if fan_control is not None:
            operation_mode = cc["operationMode"]["value"]
            operationmodedict = fan_control["value"]["operationModes"].get(operation_mode)
            if operationmodedict is not None:
                fan_speed = operationmodedict.get("fanSpeed")
                if fan_speed is not None:
                    _LOGGER.info("Found fanspeed %s", fan_speed)
                    for c in fan_speed["currentMode"]["values"]:
                        if c == FANMODE_FIXED:
                            fsm = fan_speed.get("modes")
                            if fsm is not None:
                                fixedModes = fsm[c]
                                min_val = int(fixedModes["minValue"])
                                max_val = int(fixedModes["maxValue"])
                                step_value = int(fixedModes["stepValue"])
                                for val in range(min_val, max_val + 1, step_value):
                                    fan_modes.append(str(val))
                        else:
                            fan_modes.append(c)

        _LOGGER.info(
            "Device '%s' has fan modes '%s'",
            self._device.name,
            fan_modes,
        )

        return fan_modes

    async def async_set_fan_mode(self, fan_mode):
        """Set the fan mode"""
        _LOGGER.debug(
            "Device '%s' request to set fan_mode to '%s'",
            self._device.name,
            fan_mode,
        )

        res = True
        cc = self.climate_control()
        operationmode = cc["operationMode"]["value"]
        if fan_mode.isnumeric():
            if not self._attr_fan_mode.isnumeric():
                # Only set the currentMode to fixed when we currently don't have set
                # a numeric mode
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
            res &= await self._device.patch(
                self._device.id,
                self._embedded_id,
                "fanControl",
                f"/operationModes/{operationmode}/fanSpeed/modes/fixed",
                new_fixed_mode,
            )
            if res is False:
                _LOGGER.warning(
                    "Device '%s' problem setting fan_mode fixed to %s",
                    self._device.name,
                    new_fixed_mode,
                )
        else:
            res = await self._device.patch(
                self._device.id,
                self._embedded_id,
                "fanControl",
                f"/operationModes/{operationmode}/fanSpeed/currentMode",
                fan_mode,
            )
            if res is False:
                _LOGGER.warning(
                    "Device '%s' problem setting fan_mode to %s",
                    self._device.name,
                    fan_mode,
                )

        if res is True:
            self._attr_fan_mode = fan_mode
            self.async_write_ha_state()

        return res

    def get_swing_mode(self):
        swingMode = None
        cc = self.climate_control()
        fanControl = cc.get("fanControl")
        h = SWING_OFF
        v = SWING_OFF
        if fanControl is not None:
            swingMode = SWING_OFF
            operationmode = cc["operationMode"]["value"]
            operationmodedict = fanControl["value"]["operationModes"].get(operationmode)
            if operationmodedict is not None:
                fan_direction = operationmodedict.get("fanDirection")
                if fan_direction is not None:
                    horizontal = fan_direction.get("horizontal")
                    vertical = fan_direction.get("vertical")
                    if horizontal is not None:
                        h = horizontal["currentMode"]["value"]
                    if vertical is not None:
                        v = vertical["currentMode"]["value"]
        if h == "swing":
            swingMode = SWING_HORIZONTAL
        if v == "swing":
            swingMode = SWING_VERTICAL
        if v == "swing" and h == "swing":
            swingMode = SWING_BOTH
        if v == "floorHeatingAirflow":
            if h == "swing":
                swingMode = SWING_FLOOR_HORIZONTAL
            else:
                swingMode = SWING_FLOOR
        if v == "windNice":
            if h == "swing":
                swingMode = SWING_COMFORT_HORIZONTAL
            else:
                swingMode = SWING_COMFORT

        _LOGGER.info(
            "Device '%s' has swing mode '%s', determined from h:%s v:%s",
            self._device.name,
            swingMode,
            h,
            v,
        )

        return swingMode

    def get_swing_modes(self):
        swingModes = []
        cc = self.climate_control()
        fanControl = cc.get("fanControl")
        if fanControl is not None:
            swingModes = [SWING_OFF]
            operationmode = cc["operationMode"]["value"]
            operationmodedict = fanControl["value"]["operationModes"].get(operationmode)
            if operationmodedict is not None:
                fanDirection = operationmodedict.get("fanDirection")
                if fanDirection is not None:
                    horizontal = fanDirection.get("horizontal")
                    vertical = fanDirection.get("vertical")
                    if horizontal is not None:
                        for mode in horizontal["currentMode"]["values"]:
                            if mode == "swing":
                                swingModes.append(SWING_HORIZONTAL)
                    if vertical is not None:
                        for mode in vertical["currentMode"]["values"]:
                            if mode == "swing":
                                swingModes.append(SWING_VERTICAL)
                                if horizontal is not None:
                                    swingModes.append(SWING_BOTH)
                            if mode == "floorHeatingAirflow":
                                swingModes.append(SWING_FLOOR)
                                if horizontal is not None:
                                    swingModes.append(SWING_FLOOR_HORIZONTAL)
                            if mode == "windNice":
                                swingModes.append(SWING_COMFORT)
                                if horizontal is not None:
                                    swingModes.append(SWING_COMFORT_HORIZONTAL)
        _LOGGER.info("Device '%s' support swing modes %s", self._device.name, swingModes)
        return swingModes

    async def async_set_swing_mode(self, swing_mode):
        _LOGGER.debug(
            "Device '%s' request to set swing_mode to %s",
            self._device.name,
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
                horizontal = fan_direction.get("horizontal")
                vertical = fan_direction.get("vertical")
                if horizontal is not None:
                    new_h_mode = "stop"
                    if swing_mode in (SWING_HORIZONTAL, SWING_BOTH, SWING_COMFORT_HORIZONTAL, SWING_FLOOR_HORIZONTAL):
                        new_h_mode = "swing"
                    res &= await self._device.patch(
                        self._device.id,
                        self._embedded_id,
                        "fanControl",
                        f"/operationModes/{operation_mode}/fanDirection/horizontal/currentMode",
                        new_h_mode,
                    )
                    if res is False:
                        _LOGGER.warning(
                            "Device '%s' problem setting horizontal swing mode to %s",
                            self._device.name,
                            new_h_mode,
                        )

                if vertical is not None:
                    new_v_mode = "stop"
                    if swing_mode in (SWING_VERTICAL, SWING_BOTH):
                        new_v_mode = "swing"
                    if swing_mode in (SWING_FLOOR, SWING_FLOOR_HORIZONTAL):
                        new_v_mode = "floorHeatingAirflow"
                    if swing_mode in (SWING_COMFORT, SWING_COMFORT_HORIZONTAL):
                        new_v_mode = "windNice"
                    res &= await self._device.patch(
                        self._device.id,
                        self._embedded_id,
                        "fanControl",
                        f"/operationModes/{operation_mode}/fanDirection/vertical/currentMode",
                        new_v_mode,
                    )
                    if res is False:
                        _LOGGER.warning(
                            "Device '%s' problem setting vertical swing mode to %s",
                            self._device.name,
                            new_v_mode,
                        )

        if res is True:
            self._attr_swing_mode = swing_mode
            self.async_write_ha_state()

        return res

    def get_preset_mode(self):
        cc = self.climate_control()
        current_preset_mode = PRESET_NONE
        for mode in self.preset_modes:
            daikin_mode = HA_PRESET_TO_DAIKIN[mode]
            preset = cc.get(daikin_mode)
            if preset is not None:
                preset_value = preset.get("value")
                if preset_value is not None:
                    # for example holidayMode value is a dict object with an enabled value
                    if isinstance(preset_value, dict):
                        enabled_value = preset_value.get("enabled")
                        if enabled_value and enabled_value:
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
        for mode in PRESET_MODES:
            daikin_mode = HA_PRESET_TO_DAIKIN[mode]
            preset = cc.get(daikin_mode)
            if preset is not None and preset.get("value") is not None:
                supported_preset_modes.append(mode)

        _LOGGER.info(
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
        if cc["onOffMode"]["value"] == "off":
            result &= await self._device.patch(self._device.id, self._embedded_id, "onOffMode", "", "on")
            if result is False:
                _LOGGER.error("Device '%s' problem setting onOffMode to on", self._device.name)
            else:
                cc["onOffMode"]["value"] = "on"
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
        if cc["onOffMode"]["value"] == "on":
            result &= await self._device.patch(self._device.id, self._embedded_id, "onOffMode", "", "off")
            if result is False:
                _LOGGER.error("Device '%s' problem setting onOffMode to off", self._device.name)
            else:
                cc["onOffMode"]["value"] = "off"
                self._attr_hvac_mode = self.get_hvac_mode()
                self.async_write_ha_state()
        else:
            _LOGGER.debug(
                "Device '%s' request to turn off ignored because device is already off",
                self._device.name,
            )

        return result
