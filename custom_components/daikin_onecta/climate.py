"""Support for the Daikin HVAC."""

import logging

import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant.components.climate import ClimateEntity
from homeassistant.components.climate import PLATFORM_SCHEMA
from homeassistant.components.climate.const import ClimateEntityFeature
from homeassistant.components.climate.const import FAN_AUTO
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
from .const import FAN_QUIET

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
}

HA_PRESET_TO_DAIKIN = {
    PRESET_AWAY: "holidayMode",
    PRESET_NONE: "off",
    PRESET_BOOST: "powerfulMode",
    PRESET_COMFORT: "comfortMode",
    PRESET_ECO: "econoMode",
}

DAIKIN_FAN_TO_HA = {"auto": FAN_AUTO, "quiet": FAN_QUIET}

HA_FAN_TO_DAIKIN = {
    DAIKIN_FAN_TO_HA["auto"]: "auto",
    DAIKIN_FAN_TO_HA["quiet"]: "quiet",
}


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up Daikin climate based on config_entry."""
    coordinator = hass.data[DAIKIN_DOMAIN][COORDINATOR]
    for dev_id, device in hass.data[DAIKIN_DOMAIN][DAIKIN_DEVICES].items():
        modes = []
        supported_management_point_types = {"climateControl"}
        management_points = device.daikin_data.get("managementPoints", [])
        for management_point in management_points:
            management_point_type = management_point["managementPointType"]
            if management_point_type in supported_management_point_types:
                # Check if we have a temperatureControl
                temperature_control = management_point.get("temperatureControl")
                if temperature_control is not None:
                    for operation_mode in temperature_control["value"]["operationModes"]:
                        for c in temperature_control["value"]["operationModes"][operation_mode]["setpoints"]:
                            modes.append(c)
        # Remove duplicates
        modes = list(dict.fromkeys(modes))
        for mode in modes:
            async_add_entities([DaikinClimate(device, mode, coordinator)], update_before_add=False)


class DaikinClimate(CoordinatorEntity, ClimateEntity):
    """Representation of a Daikin HVAC."""

    _enable_turn_on_off_backwards_compatibility = False  # Remove with HA 2025.1

    # Setpoint is the setpoint string under
    # temperatureControl/value/operationsModes/mode/setpoints, for example roomTemperature/leavingWaterOffset
    def __init__(self, device, setpoint, coordinator):
        """Initialize the climate device."""
        super().__init__(coordinator)
        self._device = device
        self._setpoint = setpoint
        self._attr_supported_features = self.get_supported_features()
        self._attr_temperature_unit = UnitOfTemperature.CELSIUS
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

    @callback
    def _handle_coordinator_update(self) -> None:
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
        self.async_write_ha_state()

    async def _set(self, settings):
        raise NotImplementedError

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
        set_point = None
        cc = self.climate_control()
        # Check if we have a temperatureControl
        temperature_control = cc.get("temperatureControl")
        if temperature_control is not None:
            operation_mode = cc.get("operationMode").get("value")
            # For not all operationModes there is a temperatureControl setpoint available
            oo = temperature_control["value"]["operationModes"].get(operation_mode)
            if oo is not None:
                set_point = oo["setpoints"].get(self._setpoint)
        return set_point

    # Return the dictionary fanControl for the current operationMode
    def fan_control(self):
        fan_control = None
        supported_management_point_types = {"climateControl"}
        if self._device.daikin_data["managementPoints"] is not None:
            for management_point in self._device.daikin_data["managementPoints"]:
                management_point_type = management_point["managementPointType"]
                if management_point_type in supported_management_point_types:
                    # Check if we have a temperatureControl
                    temperature_control = management_point.get("fanControl")
                    if temperature_control is not None:
                        operation_mode = management_point.get("operationMode").get("value")
                        fan_control = temperature_control["value"]["operationModes"][operation_mode].get(self._setpoint)
        return fan_control

    def sensory_data(self):
        sensory_data = None
        supported_management_point_types = {"climateControl"}
        if self._device.daikin_data["managementPoints"] is not None:
            for management_point in self._device.daikin_data["managementPoints"]:
                management_point_type = management_point["managementPointType"]
                if management_point_type in supported_management_point_types:
                    # Check if we have a sensoryData
                    sensory_data = management_point.get("sensoryData")
                    if sensory_data is not None:
                        sensory_data = sensory_data.get("value").get(self._setpoint)

        return sensory_data

    @property
    def translation_key(self) -> str:
        return "daikin_onecta"

    @property
    def embedded_id(self):
        cc = self.climate_control()
        return cc["embeddedId"]

    @property
    def available(self):
        """Return the availability of the underlying device."""
        return self._device.available

    def get_supported_features(self):
        supported_features = 0
        if hasattr(ClimateEntityFeature, "TURN_OFF"):
            supported_features = ClimateEntityFeature.TURN_OFF | ClimateEntityFeature.TURN_ON
        setpoint_dict = self.setpoint()
        cc = self.climate_control()
        if setpoint_dict is not None and setpoint_dict["settable"] is True:
            supported_features |= ClimateEntityFeature.TARGET_TEMPERATURE
        if len(self.get_preset_modes()) > 1:
            supported_features |= ClimateEntityFeature.PRESET_MODE
        fan_control = cc.get("fanControl")
        if fan_control is not None:
            operation_mode = cc["operationMode"]["value"]
            if fan_control["value"]["operationModes"][operation_mode].get("fanSpeed") is not None:
                supported_features |= ClimateEntityFeature.FAN_MODE
            if fan_control["value"]["operationModes"][operation_mode].get("fanDirection") is not None:
                supported_features |= ClimateEntityFeature.SWING_MODE

        return supported_features

    @property
    def name(self):
        return self._device.name

    @property
    def unique_id(self):
        """Return a unique ID."""
        return f"{self._device.getId()}_{self._setpoint}"

    def get_current_temperature(self):
        current_temp = None
        sensory_data = self.sensory_data()
        setpoint_dict = self.setpoint()
        # Check if there is a sensoryData which is for the same setpoint, if so, return that
        if sensory_data is not None:
            current_temp = sensory_data["value"]
        else:
            if setpoint_dict is not None:
                current_temp = setpoint_dict["value"]

        return current_temp

    def get_max_temp(self):
        max_temp = None
        setpoint_dict = self.setpoint()
        if setpoint_dict is not None:
            max_temp = setpoint_dict["maxValue"]
        return max_temp

    def get_min_temp(self):
        min_value = None
        setpoint_dict = self.setpoint()
        if setpoint_dict is not None:
            min_value = setpoint_dict["minValue"]
        return min_value

    def get_target_temperature(self):
        value = None
        setpoint_dict = self.setpoint()
        if setpoint_dict is not None:
            value = setpoint_dict["value"]
        return value

    def get_target_temperature_step(self):
        step_value = None
        setpoint_dict = self.setpoint()
        if setpoint_dict is not None:
            step_value = setpoint_dict["stepValue"]
        return step_value

    async def async_set_temperature(self, **kwargs):
        # """Set new target temperature."""
        operation_mode = self.operation_mode()
        omv = operation_mode["value"]
        value = kwargs[ATTR_TEMPERATURE]
        res = await self._device.set_path(
            self._device.getId(),
            self.embedded_id,
            "temperatureControl",
            f"/operationModes/{omv}/setpoints/{self._setpoint}",
            value,
        )
        # When updating the value to the daikin cloud worked update our local cached version
        if res:
            setpoint_dict = self.setpoint()
            if setpoint_dict is not None:
                self._attr_target_temperature = value
                self.async_write_ha_state()

    def get_hvac_mode(self):
        """Return current HVAC mode."""
        mode = HVACMode.OFF
        operation_mode = self.operation_mode()
        cc = self.climate_control()
        if cc["onOffMode"]["value"] != "off":
            mode = operation_mode["value"]
        return DAIKIN_HVAC_TO_HA.get(mode, HVACMode.HEAT_COOL)

    def get_hvac_modes(self):
        """Return the list of available HVAC modes."""
        modes = [HVACMode.OFF]
        operation_mode = self.operation_mode()
        if operation_mode is not None:
            for mode in operation_mode["values"]:
                ha_mode = DAIKIN_HVAC_TO_HA[mode]
                if ha_mode not in modes:
                    modes.append(ha_mode)
        return modes

    async def async_set_hvac_mode(self, hvac_mode):
        """Set HVAC mode."""
        result = True

        # First determine the new settings for onOffMode/operationMode
        on_off_mode = None
        operation_mode = None
        if hvac_mode == HVACMode.OFF:
            on_off_mode = "off"
        else:
            if self.hvac_mode == HVACMode.OFF:
                on_off_mode = "on"
            operation_mode = HA_HVAC_TO_DAIKIN[hvac_mode]

        cc = self.climate_control()

        # Only set the on/off to Daikin when we need to change it
        if on_off_mode is not None:
            result &= await self._device.set_path(self._device.getId(), self.embedded_id, "onOffMode", "", on_off_mode)
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
                result &= await self._device.set_path(
                    self._device.getId(),
                    self.embedded_id,
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
            self._attr_hvac_mode = hvac_mode
            # When switching hvac mode it could be that we can set min/max/target/etc
            # which we couldn't set with a previous hvac mode
            self._attr_supported_features = self.get_supported_features()
            self._attr_current_temperature = self.get_current_temperature()
            self._attr_max_temp = self.get_max_temp()
            self._attr_min_temp = self.get_min_temp()
            self._attr_target_temperature_step = self.get_target_temperature_step()
            self._attr_target_temperature = self.get_target_temperature()
            self._attr_swing_modes = self.get_swing_modes()
            self._attr_preset_modes = self.get_preset_modes()
            self._attr_fan_modes = self.get_fan_modes()
            self._attr_swing_mode = self.get_swing_mode()
            self._attr_preset_mode = self.get_preset_mode()
            self._attr_fan_mode = self.get_fan_mode()

            self.async_write_ha_state()

        return result

    def get_fan_mode(self):
        fan_mode = None
        cc = self.climate_control()
        # Check if we have a fanControl
        fan_control = cc.get("fanControl")
        if fan_control is not None:
            operation_mode = cc["operationMode"]["value"]
            fan_speed = fan_control["value"]["operationModes"][operation_mode]["fanSpeed"]
            mode = fan_speed["currentMode"]["value"]
            if mode in DAIKIN_FAN_TO_HA:
                fan_mode = DAIKIN_FAN_TO_HA[mode]
            else:
                fsm = fan_speed.get("modes")
                if fsm is not None:
                    fan_mode = str(fsm[mode]["value"])

        return fan_mode

    def get_fan_modes(self):
        fan_modes = []
        cc = self.climate_control()
        # Check if we have a fanControl
        fan_control = cc.get("fanControl")
        if fan_control is not None:
            operation_mode = cc["operationMode"]["value"]
            fan_speed = fan_control["value"]["operationModes"][operation_mode]["fanSpeed"]
            for c in fan_speed["currentMode"]["values"]:
                if c in DAIKIN_FAN_TO_HA:
                    fan_modes.append(DAIKIN_FAN_TO_HA[c])
                else:
                    fsm = fan_speed.get("modes")
                    if fsm is not None:
                        fixed_modes = fsm[c]
                        min_val = int(fixed_modes["minValue"])
                        max_val = int(fixed_modes["maxValue"])
                        step_value = int(fixed_modes["stepValue"])
                        for val in range(min_val, max_val + 1, step_value):
                            fan_modes.append(str(val))

        return fan_modes

    async def async_set_fan_mode(self, fan_mode):
        """Set the preset mode status."""
        cc = self.climate_control()
        operation_mode = cc["operationMode"]["value"]
        res = False
        if fan_mode in HA_FAN_TO_DAIKIN.keys():
            res = await self._device.set_path(
                self._device.getId(),
                self.embedded_id,
                "fanControl",
                f"/operationModes/{operation_mode}/fanSpeed/currentMode",
                fan_mode,
            )
            if res is False:
                _LOGGER.warning(
                    "Device '%s' problem setting fan_mode to %s",
                    self._device.name,
                    fan_mode,
                )

        else:
            if fan_mode.isnumeric():
                mode = int(fan_mode)
                res = await self._device.set_path(
                    self._device.getId(),
                    self.embedded_id,
                    "fanControl",
                    f"/operationModes/{operation_mode}/fanSpeed/currentMode",
                    "fixed",
                )
                if res is False:
                    _LOGGER.warning(
                        "Device '%s' problem setting fan_mode to fixed",
                        self._device.name,
                    )

                res &= await self._device.set_path(
                    self._device.getId(),
                    self.embedded_id,
                    "fanControl",
                    f"/operationModes/{operation_mode}/fanSpeed/modes/fixed",
                    mode,
                )
                if res is False:
                    _LOGGER.warning(
                        "Device '%s' problem setting fan_mode fixed to %s",
                        self._device.name,
                        mode,
                    )

        if res is True:
            self._attr_fan_mode = fan_mode
            self.async_write_ha_state()

        return res

    def get_swing_mode(self):
        swing_mode = None
        cc = self.climate_control()
        fan_control = cc.get("fanControl")
        h = SWING_OFF
        v = SWING_OFF
        if fan_control is not None:
            swing_mode = SWING_OFF
            operation_mode = cc["operationMode"]["value"]
            fan_direction = fan_control["value"]["operationModes"][operation_mode].get("fanDirection")
            if fan_direction is not None:
                horizontal = fan_direction.get("horizontal")
                vertical = fan_direction.get("vertical")
                if horizontal is not None:
                    h = horizontal["currentMode"]["value"]
                if vertical is not None:
                    v = vertical["currentMode"]["value"]
        if h == "swing":
            swing_mode = SWING_HORIZONTAL
        if v == "swing":
            swing_mode = SWING_VERTICAL
        if v == "swing" and h == "swing":
            swing_mode = SWING_BOTH
        if v == "floorHeatingAirflow":
            if h == "swing":
                swing_mode = "floorHeatingAirflow and Horizontal"
            else:
                swing_mode = "floorHeatingAirflow"
        if v == "windNice":
            if h == "swing":
                swing_mode = "Comfort Airflow and Horizontal"
            else:
                swing_mode = "Comfort Airflow"

        return swing_mode

    def get_swing_modes(self):
        swing_modes = []
        cc = self.climate_control()
        fan_control = cc.get("fanControl")
        if fan_control is not None:
            swing_modes = [SWING_OFF]
            operation_mode = cc["operationMode"]["value"]
            fan_direction = fan_control["value"]["operationModes"][operation_mode].get("fanDirection")
            if fan_direction is not None:
                horizontal = fan_direction.get("horizontal")
                vertical = fan_direction.get("vertical")
                if horizontal is not None:
                    for mode in horizontal["currentMode"]["values"]:
                        if mode == "swing":
                            swing_modes.append(SWING_HORIZONTAL)
                if vertical is not None:
                    for mode in vertical["currentMode"]["values"]:
                        if mode == "swing":
                            swing_modes.append(SWING_VERTICAL)
                            if horizontal is not None:
                                swing_modes.append(SWING_BOTH)
                        if mode == "floorHeatingAirflow":
                            swing_modes.append(mode)
                            if horizontal is not None:
                                swing_modes.append("floorHeatingAirflow and Horizontal")
                        if mode == "windNice":
                            swing_modes.append("Comfort Airflow")
                            if horizontal is not None:
                                swing_modes.append("Comfort Airflow and Horizontal")
        return swing_modes

    async def async_set_swing_mode(self, swing_mode):
        res = True
        cc = self.climate_control()
        fan_control = cc.get("fanControl")
        if fan_control is not None:
            operation_mode = cc["operationMode"]["value"]
            fan_direction = fan_control["value"]["operationModes"][operation_mode].get("fanDirection")
            if fan_direction is not None:
                horizontal = fan_direction.get("horizontal")
                vertical = fan_direction.get("vertical")
                if horizontal is not None:
                    new_h_mode = "stop"
                    if swing_mode in (
                        SWING_HORIZONTAL,
                        SWING_BOTH,
                        "Comfort Airflow and Horizontal",
                        "floorHeatingAirflow and Horizontal",
                    ):
                        new_h_mode = "swing"
                    res &= await self._device.set_path(
                        self._device.getId(),
                        self.embedded_id,
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
                    if swing_mode in (
                        "floorHeatingAirflow",
                        "floorHeatingAirflow and Horizontal",
                    ):
                        new_v_mode = "floorHeatingAirflow"
                    if swing_mode in (
                        "Comfort Airflow",
                        "Comfort Airflow and Horizontal",
                    ):
                        new_v_mode = "windNice"
                    res &= await self._device.set_path(
                        self._device.getId(),
                        self.embedded_id,
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
                if preset_value is not None and preset_value == "on":
                    current_preset_mode = mode
        return current_preset_mode

    async def async_set_preset_mode(self, preset_mode):
        result = True
        new_daikin_mode = HA_PRESET_TO_DAIKIN[preset_mode]

        if self.preset_mode != PRESET_NONE:
            current_mode = HA_PRESET_TO_DAIKIN[self.preset_mode]
            result &= await self._device.set_path(self._device.getId(), self.embedded_id, current_mode, "", "off")
            if result is False:
                _LOGGER.warning(
                    "Device '%s' problem setting %s to off",
                    self._device.name,
                    current_mode,
                )

        if preset_mode != PRESET_NONE:
            if self.hvac_mode == HVACMode.OFF and preset_mode == PRESET_BOOST:
                result &= await self.async_turn_on()

            result &= await self._device.set_path(self._device.getId(), self.embedded_id, new_daikin_mode, "", "on")
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
        # self._current_preset_mode = PRESET_NONE
        for mode in PRESET_MODES:
            daikin_mode = HA_PRESET_TO_DAIKIN[mode]
            preset = cc.get(daikin_mode)
            if preset is not None and preset.get("value") is not None:
                supported_preset_modes.append(mode)

        return supported_preset_modes

    async def async_turn_on(self):
        """Turn device CLIMATE on."""
        cc = self.climate_control()
        result = await self._device.set_path(self._device.getId(), self.embedded_id, "onOffMode", "", "on")
        if result is False:
            _LOGGER.warning("Device '%s' problem setting onOffMode to on", self._device.name)
        else:
            cc["onOffMode"]["value"] = "on"
            self._attr_hvac_mode = self.get_hvac_mode()
            self.async_write_ha_state()
        return result

    async def async_turn_off(self):
        result = await self._device.set_path(self._device.getId(), self.embedded_id, "onOffMode", "", "off")
        if result is False:
            _LOGGER.warning("Device '%s' problem setting onOffMode to off", self._device.name)
        else:
            self._attr_hvac_mode = HVACMode.OFF
            self.async_write_ha_state()

        return result

    @property
    def device_info(self):
        """Return a device description for device registry."""
        return self._device.device_info()
