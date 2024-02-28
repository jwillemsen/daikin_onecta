"""Support for the Daikin HVAC."""

import logging
import re

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
        device_model = device.daikin_data["deviceModel"]
        supported_management_point_types = {"climateControl"}
        managementPoints = device.daikin_data.get("managementPoints", [])
        for management_point in managementPoints:
            management_point_type = management_point["managementPointType"]
            if management_point_type in supported_management_point_types:
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
            async_add_entities([DaikinClimate(device, mode, coordinator)], update_before_add=False)


class DaikinClimate(CoordinatorEntity, ClimateEntity):
    """Representation of a Daikin HVAC."""

    _enable_turn_on_off_backwards_compatibility = False  # Remove with HA 2025.1

    # Setpoint is the setpoint string under
    # temperatureControl/value/operationsModes/mode/setpoints, for example roomTemperature/leavingWaterOffset
    def __init__(self, device, setpoint, coordinator):
        """Initialize the climate device."""
        super().__init__(coordinator)
        _LOGGER.info(
            "Device '%s' initializing Daikin Climate for controlling %s...",
            device.name,
            setpoint,
        )
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

    def climateControl(self):
        cc = None
        supported_management_point_types = {"climateControl"}
        if self._device.daikin_data["managementPoints"] is not None:
            for management_point in self._device.daikin_data["managementPoints"]:
                management_point_type = management_point["managementPointType"]
                if management_point_type in supported_management_point_types:
                    cc = management_point
        return cc

    def operationMode(self):
        cc = self.climateControl()
        return cc.get("operationMode")

    def setpoint(self):
        setpoint = None
        cc = self.climateControl()
        # Check if we have a temperatureControl
        temperatureControl = cc.get("temperatureControl")
        if temperatureControl is not None:
            operationMode = cc.get("operationMode").get("value")
            # For not all operationModes there is a temperatureControl setpoint available
            oo = temperatureControl["value"]["operationModes"].get(operationMode)
            if oo is not None:
                setpoint = oo["setpoints"].get(self._setpoint)
            _LOGGER.info(
                "Device '%s': %s operation mode %s has setpoint %s",
                self._device.name,
                self._setpoint,
                operationMode,
                setpoint,
            )
        return setpoint

    # Return the dictionary fanControl for the current operationMode
    def fanControl(self):
        fancontrol = None
        supported_management_point_types = {"climateControl"}
        if self._device.daikin_data["managementPoints"] is not None:
            for management_point in self._device.daikin_data["managementPoints"]:
                management_point_type = management_point["managementPointType"]
                if management_point_type in supported_management_point_types:
                    # Check if we have a temperatureControl
                    temperatureControl = management_point.get("fanControl")
                    _LOGGER.info("Climate: Device fanControl %s", temperatureControl)
                    if temperatureControl is not None:
                        operationMode = management_point.get("operationMode").get("value")
                        fancontrol = temperatureControl["value"]["operationModes"][operationMode].get(self._setpoint)
                        _LOGGER.info(
                            "Device '%s': %s operation mode %s has fanControl %s",
                            self._device.name,
                            self._setpoint,
                            operationMode,
                            fancontrol,
                        )
        return fancontrol

    def sensoryData(self):
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
                        sensoryData = sensoryData.get("value").get(self._setpoint)
                        _LOGGER.info(
                            "Device '%s': %s sensoryData %s",
                            self._device.name,
                            self._setpoint,
                            sensoryData,
                        )
        return sensoryData

    @property
    def translation_key(self) -> str:
        return "daikin_onecta"

    @property
    def embedded_id(self):
        cc = self.climateControl()
        return cc["embeddedId"]

    @property
    def available(self):
        """Return the availability of the underlying device."""
        return self._device.available

    def get_supported_features(self):
        supported_features = ClimateEntityFeature.TURN_OFF | ClimateEntityFeature.TURN_ON
        setpointdict = self.setpoint()
        cc = self.climateControl()
        if setpointdict is not None and setpointdict["settable"] is True:
            supported_features |= ClimateEntityFeature.TARGET_TEMPERATURE
        if len(self.get_preset_modes()) > 1:
            supported_features |= ClimateEntityFeature.PRESET_MODE
        fanControl = cc.get("fanControl")
        if fanControl is not None:
            operationmode = cc["operationMode"]["value"]
            if fanControl["value"]["operationModes"][operationmode].get("fanSpeed") is not None:
                supported_features |= ClimateEntityFeature.FAN_MODE
            if fanControl["value"]["operationModes"][operationmode].get("fanDirection") is not None:
                supported_features |= ClimateEntityFeature.SWING_MODE

        _LOGGER.info("Device '%s' supports features %s", self._device.name, supported_features)

        return supported_features

    @property
    def name(self):
        device_name = self._device.name
        cc = self.climateControl()
        namepoint = cc.get("name")
        if namepoint is not None:
            device_name = namepoint["value"]
        myname = self._setpoint[0].upper() + self._setpoint[1:]
        readable = re.findall("[A-Z][^A-Z]*", myname)
        return f"{device_name} {' '.join(readable)}"

    @property
    def unique_id(self):
        """Return a unique ID."""
        devID = self._device.getId()
        return f"{devID}_{self._setpoint}"

    def get_current_temperature(self):
        currentTemp = None
        sensoryData = self.sensoryData()
        setpointdict = self.setpoint()
        # Check if there is a sensoryData which is for the same setpoint, if so, return that
        if sensoryData is not None:
            currentTemp = sensoryData["value"]
        else:
            if setpointdict is not None:
                currentTemp = setpointdict["value"]
        _LOGGER.info(
            "Device '%s': %s current temperature '%s'",
            self._device.name,
            self._setpoint,
            currentTemp,
        )
        return currentTemp

    def get_max_temp(self):
        maxTemp = None
        setpointdict = self.setpoint()
        if setpointdict is not None:
            maxTemp = setpointdict["maxValue"]
        _LOGGER.info(
            "Device '%s': %s max temperature '%s'",
            self._device.name,
            self._setpoint,
            maxTemp,
        )
        return maxTemp

    def get_min_temp(self):
        minValue = None
        setpointdict = self.setpoint()
        if setpointdict is not None:
            minValue = setpointdict["minValue"]
        _LOGGER.info(
            "Device '%s': %s min temperature '%s'",
            self._device.name,
            self._setpoint,
            minValue,
        )
        return minValue

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
        stepValue = None
        setpointdict = self.setpoint()
        if setpointdict is not None:
            stepValue = setpointdict["stepValue"]
        _LOGGER.info(
            "Device '%s': %s target temperature step '%s'",
            self._device.name,
            self._setpoint,
            stepValue,
        )
        return stepValue

    async def async_set_temperature(self, **kwargs):
        # """Set new target temperature."""
        operationmode = self.operationMode()
        omv = operationmode["value"]
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
            setpointdict = self.setpoint()
            if setpointdict is not None:
                self._attr_target_temperature = value
                self.async_write_ha_state()

    def get_hvac_mode(self):
        """Return current HVAC mode."""
        mode = HVACMode.OFF
        operationmode = self.operationMode()
        cc = self.climateControl()
        if cc["onOffMode"]["value"] != "off":
            mode = operationmode["value"]
        return DAIKIN_HVAC_TO_HA.get(mode, HVACMode.HEAT_COOL)

    def get_hvac_modes(self):
        """Return the list of available HVAC modes."""
        modes = [HVACMode.OFF]
        operationmode = self.operationMode()
        if operationmode is not None:
            for mode in operationmode["values"]:
                ha_mode = DAIKIN_HVAC_TO_HA[mode]
                if ha_mode not in modes:
                    modes.append(ha_mode)
        return modes

    async def async_set_hvac_mode(self, hvac_mode):
        """Set HVAC mode."""
        result = True

        # First determine the new settings for onOffMode/operationMode
        onOffMode = None
        operationMode = None
        if hvac_mode == HVACMode.OFF:
            onOffMode = "off"
        else:
            if self.hvac_mode == HVACMode.OFF:
                onOffMode = "on"
            operationMode = HA_HVAC_TO_DAIKIN[hvac_mode]

        cc = self.climateControl()

        # Only set the on/off to Daikin when we need to change it
        if onOffMode is not None:
            result &= await self._device.set_path(self._device.getId(), self.embedded_id, "onOffMode", "", onOffMode)
            if result is False:
                _LOGGER.warning(
                    "Device '%s' problem setting onOffMode to %s",
                    self._device.name,
                    onOffMode,
                )
            else:
                cc["onOffMode"]["value"] = onOffMode

        if operationMode is not None:
            result &= await self._device.set_path(
                self._device.getId(),
                self.embedded_id,
                "operationMode",
                "",
                operationMode,
            )
            if result is False:
                _LOGGER.warning(
                    "Device '%s' problem setting operationMode to %s",
                    self._device.name,
                    operationMode,
                )
            else:
                cc["operationMode"]["value"] = operationMode

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
        cc = self.climateControl()
        # Check if we have a fanControl
        fanControl = cc.get("fanControl")
        if fanControl is not None:
            operationmode = cc["operationMode"]["value"]
            fanspeed = fanControl["value"]["operationModes"][operationmode]["fanSpeed"]
            mode = fanspeed["currentMode"]["value"]
            if mode in DAIKIN_FAN_TO_HA:
                fan_mode = DAIKIN_FAN_TO_HA[mode]
            else:
                fsm = fanspeed.get("modes")
                if fsm is not None:
                    _LOGGER.info("FSM %s", fsm)
                    fixedModes = fsm[mode]
                    fan_mode = str(fixedModes["value"])

        return fan_mode

    def get_fan_modes(self):
        fan_modes = []
        fanspeed = None
        cc = self.climateControl()
        # Check if we have a fanControl
        fanControl = cc.get("fanControl")
        if fanControl is not None:
            operationmode = cc["operationMode"]["value"]
            fanspeed = fanControl["value"]["operationModes"][operationmode]["fanSpeed"]
            _LOGGER.info("Found fanspeed %s", fanspeed)
            for c in fanspeed["currentMode"]["values"]:
                _LOGGER.info("Device '%s' found fan mode %s", self._device.name, c)
                if c in DAIKIN_FAN_TO_HA:
                    fan_modes.append(DAIKIN_FAN_TO_HA[c])
                else:
                    fsm = fanspeed.get("modes")
                    if fsm is not None:
                        _LOGGER.info("Device '%s' found fixed %s", self._device.name, fsm)
                        fixedModes = fsm[c]
                        minVal = int(fixedModes["minValue"])
                        maxVal = int(fixedModes["maxValue"])
                        stepValue = int(fixedModes["stepValue"])
                        for val in range(minVal, maxVal + 1, stepValue):
                            fan_modes.append(str(val))

        return fan_modes

    async def async_set_fan_mode(self, fan_mode):
        """Set the preset mode status."""
        cc = self.climateControl()
        operationmode = cc["operationMode"]["value"]
        if fan_mode in HA_FAN_TO_DAIKIN.keys():
            res = await self._device.set_path(
                self._device.getId(),
                self.embedded_id,
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

        else:
            if fan_mode.isnumeric():
                mode = int(fan_mode)
                res = await self._device.set_path(
                    self._device.getId(),
                    self.embedded_id,
                    "fanControl",
                    f"/operationModes/{operationmode}/fanSpeed/currentMode",
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
                    f"/operationModes/{operationmode}/fanSpeed/modes/fixed",
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
        swingMode = None
        cc = self.climateControl()
        fanControl = cc.get("fanControl")
        h = SWING_OFF
        v = SWING_OFF
        if fanControl is not None:
            swingMode = SWING_OFF
            operationmode = cc["operationMode"]["value"]
            fanDirection = fanControl["value"]["operationModes"][operationmode].get("fanDirection")
            if fanDirection is not None:
                horizontal = fanDirection.get("horizontal")
                vertical = fanDirection.get("vertical")
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
                swingMode = "floorHeatingAirflow and Horizontal"
            else:
                swingMode = "floorHeatingAirflow"
        if v == "windNice":
            if h == "swing":
                swingMode = "Comfort Airflow and Horizontal"
            else:
                swingMode = "Comfort Airflow"

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
        cc = self.climateControl()
        fanControl = cc.get("fanControl")
        if fanControl is not None:
            swingModes = [SWING_OFF]
            operationmode = cc["operationMode"]["value"]
            fanDirection = fanControl["value"]["operationModes"][operationmode].get("fanDirection")
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
                            swingModes.append(mode)
                            if horizontal is not None:
                                swingModes.append("floorHeatingAirflow and Horizontal")
                        if mode == "windNice":
                            swingModes.append("Comfort Airflow")
                            if horizontal is not None:
                                swingModes.append("Comfort Airflow and Horizontal")
        _LOGGER.info("Device '%s' support swing modes %s", self._device.name, swingModes)
        return swingModes

    async def async_set_swing_mode(self, swing_mode):
        res = True
        cc = self.climateControl()
        fanControl = cc.get("fanControl")
        operationmode = cc["operationMode"]["value"]
        if fanControl is not None:
            operationmode = cc["operationMode"]["value"]
            fanDirection = fanControl["value"]["operationModes"][operationmode].get("fanDirection")
            if fanDirection is not None:
                horizontal = fanDirection.get("horizontal")
                vertical = fanDirection.get("vertical")
                if horizontal is not None:
                    new_hMode = "stop"
                    if swing_mode in (
                        SWING_HORIZONTAL,
                        SWING_BOTH,
                        "Comfort Airflow and Horizontal",
                        "floorHeatingAirflow and Horizontal",
                    ):
                        new_hMode = "swing"
                    res &= await self._device.set_path(
                        self._device.getId(),
                        self.embedded_id,
                        "fanControl",
                        f"/operationModes/{operationmode}/fanDirection/horizontal/currentMode",
                        new_hMode,
                    )
                    if res is False:
                        _LOGGER.warning(
                            "Device '%s' problem setting horizontal swing mode to %s",
                            self._device.name,
                            new_hMode,
                        )

                if vertical is not None:
                    new_vMode = "stop"
                    if swing_mode in (SWING_VERTICAL, SWING_BOTH):
                        new_vMode = "swing"
                    if swing_mode in (
                        "floorHeatingAirflow",
                        "floorHeatingAirflow and Horizontal",
                    ):
                        new_vMode = "floorHeatingAirflow"
                    if swing_mode in (
                        "Comfort Airflow",
                        "Comfort Airflow and Horizontal",
                    ):
                        new_vMode = "windNice"
                    res &= await self._device.set_path(
                        self._device.getId(),
                        self.embedded_id,
                        "fanControl",
                        f"/operationModes/{operationmode}/fanDirection/vertical/currentMode",
                        new_vMode,
                    )
                    if res is False:
                        _LOGGER.warning(
                            "Device '%s' problem setting vertical swing mode to %s",
                            self._device.name,
                            new_vMode,
                        )

        if res is True:
            self._attr_swing_mode = swing_mode
            self.async_write_ha_state()

        return res

    def get_preset_mode(self):
        cc = self.climateControl()
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
        cc = self.climateControl()
        # self._current_preset_mode = PRESET_NONE
        for mode in PRESET_MODES:
            daikin_mode = HA_PRESET_TO_DAIKIN[mode]
            preset = cc.get(daikin_mode)
            if preset is not None and preset.get("value") is not None:
                supported_preset_modes.append(mode)

        _LOGGER.info(
            "Device '%s' supports pre preset_modes %s",
            self._device.name,
            format(supported_preset_modes),
        )

        return supported_preset_modes

    async def async_turn_on(self):
        """Turn device CLIMATE on."""
        cc = self.climateControl()
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
