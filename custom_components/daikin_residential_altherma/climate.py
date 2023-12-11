"""Support for the Daikin HVAC."""
import logging

import voluptuous as vol

from homeassistant.components.climate import PLATFORM_SCHEMA, ClimateEntity
from homeassistant.components.climate.const import (
    ATTR_HVAC_MODE,
    ATTR_PRESET_MODE,
    HVAC_MODE_COOL,
    HVAC_MODE_HEAT,
    HVAC_MODE_HEAT_COOL,
    HVAC_MODE_OFF,
    HVAC_MODE_DRY,
    HVAC_MODE_FAN_ONLY,
    PRESET_AWAY,
    PRESET_COMFORT,
    PRESET_BOOST,
    PRESET_ECO,
    PRESET_NONE,
    SUPPORT_TARGET_TEMPERATURE,
    SUPPORT_PRESET_MODE,
    SUPPORT_FAN_MODE,
    SUPPORT_SWING_MODE,
    FAN_AUTO,
)
from homeassistant.const import ATTR_TEMPERATURE, CONF_HOST, CONF_NAME, TEMP_CELSIUS
import homeassistant.helpers.config_validation as cv

from .const import (
    DOMAIN as DAIKIN_DOMAIN,
    DAIKIN_DEVICES,
    ATTR_LEAVINGWATER_TEMPERATURE,
    ATTR_OUTSIDE_TEMPERATURE,
    ATTR_ROOM_TEMPERATURE,
    ATTR_LEAVINGWATER_OFFSET,
    ATTR_STATE_OFF,
    ATTR_STATE_ON,
    ATTR_OPERATION_MODE,
    ATTR_TARGET_ROOM_TEMPERATURE,
    ATTR_TARGET_LEAVINGWATER_OFFSET,
    ATTR_TARGET_LEAVINGWATER_TEMPERATURE,
    FAN_QUIET,
)

import re

_LOGGER = logging.getLogger(__name__)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {vol.Required(CONF_HOST): cv.string, vol.Optional(CONF_NAME): cv.string}
)

PRESET_MODES = {
    PRESET_COMFORT,
    PRESET_ECO,
    PRESET_AWAY,
    PRESET_BOOST
}

HA_HVAC_TO_DAIKIN = {
    HVAC_MODE_FAN_ONLY: "fanOnly",
    HVAC_MODE_DRY: "dry",
    HVAC_MODE_COOL: "cooling",
    HVAC_MODE_HEAT: "heating",
    HVAC_MODE_HEAT_COOL: "auto",
    HVAC_MODE_OFF: "off",
}

HA_ATTR_TO_DAIKIN = {
    ATTR_PRESET_MODE: "en_hol",
    ATTR_HVAC_MODE: "mode",
    ATTR_LEAVINGWATER_OFFSET: "c",
    ATTR_LEAVINGWATER_TEMPERATURE: "c",
    ATTR_OUTSIDE_TEMPERATURE: "otemp",
    ATTR_ROOM_TEMPERATURE: "stemp",
}

DAIKIN_HVAC_TO_HA = {
    "fanOnly": HVAC_MODE_FAN_ONLY,
    "dry": HVAC_MODE_DRY,
    "cooling": HVAC_MODE_COOL,
    "heating": HVAC_MODE_HEAT,
    "heatingDay": HVAC_MODE_HEAT,
    "heatingNight": HVAC_MODE_HEAT,
    "auto": HVAC_MODE_HEAT_COOL,
    "off": HVAC_MODE_OFF,
}

HA_PRESET_TO_DAIKIN = {
    PRESET_AWAY: "holidayMode",
    PRESET_NONE: "off",
    PRESET_BOOST: "powerfulMode",
    PRESET_COMFORT: "comfortMode",
    PRESET_ECO: "econoMode",
}

DAIKIN_FAN_TO_HA = {
    "auto": FAN_AUTO,
    "quiet": FAN_QUIET
}

HA_FAN_TO_DAIKIN = {
    DAIKIN_FAN_TO_HA["auto"]: "auto",
    DAIKIN_FAN_TO_HA["quiet"]: "quiet",
}

async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Old way of setting up the Daikin HVAC platform.

    Can only be called when a user accidentally mentions the platform in their
    config. But even in that case it would have been ignored.
    """


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up Daikin climate based on config_entry."""
    for dev_id, device in hass.data[DAIKIN_DOMAIN][DAIKIN_DEVICES].items():
        modes = []
        device_model = device.daikin_data["deviceModel"]
        supported_management_point_types = {'climateControl'}
        if device.daikin_data["managementPoints"] is not None:
            for management_point in device.daikin_data["managementPoints"]:
                management_point_type = management_point["managementPointType"]
                if  management_point_type in supported_management_point_types:
                    # Check if we have a temperatureControl
                    temperatureControl = management_point.get("temperatureControl")
                    if temperatureControl is not None:
                        for operationmode in temperatureControl["value"]["operationModes"]:
                            #for modes in operationmode["setpoints"]:
                            for c in temperatureControl["value"]["operationModes"][operationmode]["setpoints"]:
                                _LOGGER.info("Found temperature mode %s", c)
                                modes.append(c)
        # Remove duplicates
        modes = list(dict.fromkeys(modes))
        _LOGGER.info("Climate: Device %s has modes %s %s", device_model, modes)
        for mode in modes:
            async_add_entities([DaikinClimate(device, mode)], update_before_add=True)

class DaikinClimate(ClimateEntity):
    """Representation of a Daikin HVAC."""

    # Setpoint is the setpoint string under temperatureControl/value/operationsModes/mode/setpoints, for example roomTemperature/leavingWaterOffset
    def __init__(self, device, setpoint):
        """Initialize the climate device."""
        _LOGGER.info("Initializing Daiking Climate for controlling %s...", setpoint)
        self._device = device
        self._list = {
            ATTR_HVAC_MODE: list(HA_HVAC_TO_DAIKIN),
        }
        self._setpoint = setpoint

    async def _set(self, settings):
        raise NotImplementedError

    def climateControl(self):
        cc = None
        supported_management_point_types = {'climateControl'}
        if self._device.daikin_data["managementPoints"] is not None:
            for management_point in self._device.daikin_data["managementPoints"]:
                management_point_type = management_point["managementPointType"]
                if  management_point_type in supported_management_point_types:
                    cc = management_point
        return cc

    def operationMode(self):
        operationMode = None
        supported_management_point_types = {'climateControl'}
        if self._device.daikin_data["managementPoints"] is not None:
            for management_point in self._device.daikin_data["managementPoints"]:
                management_point_type = management_point["managementPointType"]
                if  management_point_type in supported_management_point_types:
                    operationMode = management_point.get("operationMode")
        return operationMode

    def setpoint(self):
        setpoint = None
        supported_management_point_types = {'climateControl'}
        if self._device.daikin_data["managementPoints"] is not None:
            for management_point in self._device.daikin_data["managementPoints"]:
                management_point_type = management_point["managementPointType"]
                if  management_point_type in supported_management_point_types:
                    # Check if we have a temperatureControl
                    temperatureControl = management_point.get("temperatureControl")
                    _LOGGER.info("Climate: Device temperatureControl %s", temperatureControl)
                    if temperatureControl is not None:
                        operationMode = management_point.get("operationMode").get("value")
                        setpoint = temperatureControl["value"]["operationModes"][operationMode]["setpoints"].get(self._setpoint)
                        _LOGGER.info("Climate: %s operation mode %s has setpoint %s", self._setpoint, operationMode, setpoint)
        return setpoint


    # Return the dictionary fanControl for the current operationMode
    def fanControl(self):
        fancontrol = None
        supported_management_point_types = {'climateControl'}
        if self._device.daikin_data["managementPoints"] is not None:
            for management_point in self._device.daikin_data["managementPoints"]:
                management_point_type = management_point["managementPointType"]
                if  management_point_type in supported_management_point_types:
                    # Check if we have a temperatureControl
                    temperatureControl = management_point.get("fanControl")
                    _LOGGER.info("Climate: Device fanControl %s", temperatureControl)
                    if temperatureControl is not None:
                        operationMode = management_point.get("operationMode").get("value")
                        fancontrol = temperatureControl["value"]["operationModes"][operationMode].get(self._setpoint)
                        _LOGGER.info("Climate: %s operation mode %s has fanControl %s", self._setpoint, operationMode, setpoint)
        return setpoint

    def sensoryData(self):
        sensoryData = None
        supported_management_point_types = {'climateControl'}
        if self._device.daikin_data["managementPoints"] is not None:
            for management_point in self._device.daikin_data["managementPoints"]:
                management_point_type = management_point["managementPointType"]
                if  management_point_type in supported_management_point_types:
                    # Check if we have a temperaturControl
                    sensoryData = management_point.get("sensoryData")
                    _LOGGER.info("Climate: Device sensoryData %s", sensoryData)
                    if sensoryData is not None:
                        sensoryData = sensor = sensoryData.get("value").get(self._setpoint)
                        _LOGGER.info("Climate: %s operation mode %s has sensoryData %s", self._setpoint, sensoryData)
        return sensoryData

    @property
    def embedded_id(self):
        cc = self.climateControl()
        return cc["embeddedId"]

    @property
    def available(self):
        """Return the availability of the underlying device."""
        return self._device.available

    @property
    def supported_features(self):
        supported_features = 0
        setpointdict = self.setpoint()
        cc = self.climateControl()
        if setpointdict is not None and setpointdict["settable"] == True:
            supported_features = SUPPORT_TARGET_TEMPERATURE
        if len(self.preset_modes) > 1:
            supported_features |= SUPPORT_PRESET_MODE
        if cc.get("fanControl") is not None:
            supported_features |= SUPPORT_FAN_MODE
        _LOGGER.info("Support features %s", supported_features)
        # todo add support for swing mode
        return supported_features

    @property
    def name(self):
        device_name = self._device.name
        supported_management_point_types = {'climateControl'}
        if self._device.daikin_data["managementPoints"] is not None:
            for management_point in self._device.daikin_data["managementPoints"]:
                management_point_type = management_point["managementPointType"]
                if  management_point_type in supported_management_point_types:
                    namepoint = management_point.get("name")
                    if namepoint is not None:
                        device_name = namepoint["value"]
        myname = self._setpoint[0].upper() + self._setpoint[1:]
        readable = re.findall('[A-Z][^A-Z]*', myname)
        return f"{device_name} {' '.join(readable)}"

    @property
    def unique_id(self):
        """Return a unique ID."""
        devID = self._device.getId()
        return f"{devID}_{self._setpoint}"

    @property
    def temperature_unit(self):
        """Return the unit of measurement which this thermostat uses."""
        return TEMP_CELSIUS

    @property
    def current_temperature(self):
        currentTemp = None
        sensoryData = self.sensoryData()
        setpointdict = self.setpoint()
        # Check if there is a sensoryData which is for the same setpoint, if so, return that
        if sensoryData is not None:
            currentTemp = sensoryData["value"]
        else:
            if setpointdict is not None:
                currentTemp = setpointdict["value"]
        _LOGGER.debug("Device '%s' current temperature '%s'", self._device.name, currentTemp)
        return currentTemp

    @property
    def max_temp(self):
        maxTemp = None
        setpointdict = self.setpoint()
        if setpointdict is not None:
            maxTemp = setpointdict["maxValue"]
        _LOGGER.debug("Device '%s' max temperature '%s'", self._device.name, maxTemp)
        return maxTemp

    @property
    def min_temp(self):
        minValue = None
        setpointdict = self.setpoint()
        if setpointdict is not None:
            minValue = setpointdict["minValue"]
        _LOGGER.debug("Device '%s' max temperature '%s'", self._device.name, minValue)
        return minValue

    @property
    def target_temperature(self):
        value = None
        setpointdict = self.setpoint()
        if setpointdict is not None:
            value = setpointdict["value"]
        _LOGGER.debug("Device '%s' target temperature '%s'", self._device.name, value)
        return value

    @property
    def target_temperature_step(self):
        stepValue = None
        setpointdict = self.setpoint()
        if setpointdict is not None:
            stepValue = setpointdict["stepValue"]
        _LOGGER.debug("Device '%s' step value '%s'", self._device.name, stepValue)
        return stepValue

    async def async_set_temperature(self, **kwargs):
        # """Set new target temperature."""
        # # The service climate.set_temperature can set the hvac_mode too, see
        # # https://www.home-assistant.io/integrations/climate/#service-climateset_temperature
        # # se we first set the hvac_mode, if provided, then the temperature.
        # if ATTR_HVAC_MODE in kwargs:
        #     await self.async_set_hvac_mode(kwargs[ATTR_HVAC_MODE])
        #
        # await self._device.async_set_temperature(kwargs[ATTR_TEMPERATURE])
        # # ADDED for instant update
        # await self._device.api.async_update()
        operationmode = self.operationMode()
        omv = operationmode["value"]
        value = kwargs[ATTR_TEMPERATURE]
        res = await self._device.set_path(self._device.getId(), self.embedded_id, "temperatureControl", f"/operationModes/{omv}/setpoints/{self._setpoint}", int(value))
        # When updating the value to the daikin cloud worked update our local cached version
        if res:
            setpointdict = self.setpoint()
            if setpointdict is not None:
                setpointdict["value"] = int(value)

    @property
    def hvac_mode(self):
        """Return current HVAC mode."""
        mode = HVAC_MODE_OFF
        operationmode = self.operationMode()
        cc = self.climateControl()
        if cc["onOffMode"]["value"] != "off":
            mode = operationmode["value"]
        return DAIKIN_HVAC_TO_HA.get(mode, HVAC_MODE_HEAT_COOL)

    @property
    def hvac_modes(self):
        """Return the list of available HVAC modes."""
        modes = [HVAC_MODE_OFF]
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

        # First determine the new settings for onOffMode/operationMode, we need these to set them to Daikin
        # and update our local cached version when succeeded
        onOffMode = ""
        operationMode = ""
        if hvac_mode == HVAC_MODE_OFF:
            onOffMode = "off"
        else:
            if self.hvac_mode == HVAC_MODE_OFF:
                onOffMode = "on"
            operationMode = HA_HVAC_TO_DAIKIN[hvac_mode]

        # Only set the on/off to Daikin when we need to change it
        if onOffMode != "":
            result &= await self._device.set_path(self._device.getId(), self.embedded_id, "onOffMode", "", onOffMode)
        if operationMode != "":
            result &= await self._device.set_path(self._device.getId(), self.embedded_id, "operationMode", "", operationMode)

        if result is False:
            _LOGGER.warning("Device '%s' problem setting hvac mode %s", self._device.name, hvac_mode)
        else:
            # Update local cached version
            cc = self.climateControl()
            cc["onOffMode"]["value"] == onOffMode
            cc["operationMode"]["value"] == operationMode

        return result


    @property
    def fan_mode(self):
        """Return the fan setting."""
        return None

    @property
    def fan_modes(self):
        fan_modes = []
        fanspeed = None
        supported_management_point_types = {'climateControl'}
        if self._device.daikin_data["managementPoints"] is not None:
            for management_point in self._device.daikin_data["managementPoints"]:
                management_point_type = management_point["managementPointType"]
                if  management_point_type in supported_management_point_types:
                    # Check if we have a fanControl
                    fanControl = management_point.get("fanControl")
                    if fanControl is not None:
                        operationmode = management_point["operationMode"]["value"]
                        fanspeed = fanControl["value"]["operationModes"][operationmode]["fanSpeed"]
                        _LOGGER.info("Found fanspeed %s", fanspeed)
                        for c in fanspeed["currentMode"]["values"]:
                            _LOGGER.info("Found fan mode %s", c)
                            if c in DAIKIN_FAN_TO_HA:
                                fan_modes.append(DAIKIN_FAN_TO_HA[c])
                            else:
                                fsm = fanspeed.get("modes")
                                if fsm is not None:
                                    _LOGGER.info("Found fixed %s", fsm)
                                    fixedModes = fsm[c]
                                    minVal = int(fixedModes["minValue"])
                                    maxVal = int(fixedModes["maxValue"])
                                    for val in range(minVal, maxVal + 1):
                                        fan_modes.append(str(val))

        return fan_modes

    async def async_set_fan_mode(self, fan_mode):
        """Set new fan mode."""
        #await self._device.async_set_fan_mode(fan_mode)

    @property
    def swing_mode(self):
        """Return the swing setting."""
        return None

    @property
    def swing_modes(self):
        """List of available swing modes."""
        return []

    async def async_set_swing_mode(self, swing_mode):
        """Set new swing mode."""
        #await self._device.async_set_swing_mode(swing_mode)

    @property
    def preset_mode(self):
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
        """Set preset mode."""
        curr_mode = self.preset_mode
        daikin_mode = HA_PRESET_TO_DAIKIN[curr_mode]
        if curr_mode != PRESET_NONE:
            await self._device.set_path(self._device.getId(), self.embedded_id, daikin_mode, "", "off")
        if preset_mode != PRESET_NONE:
            await self._device.set_path(self._device.getId(), self.embedded_id, daikin_mode, "", "on")

    @property
    def preset_modes(self):
        supported_preset_modes = [PRESET_NONE]
        cc = self.climateControl()
        # self._current_preset_mode = PRESET_NONE
        for mode in PRESET_MODES:
            daikin_mode = HA_PRESET_TO_DAIKIN[mode]
            preset = cc.get(daikin_mode)
            if preset is not None and preset.get("value") is not None:
                _LOGGER.info("Device support %s %s", daikin_mode, mode)
                supported_preset_modes.append(mode)
            else:
                _LOGGER.info("Device doesn't support %s %s", daikin_mode, mode)

        _LOGGER.info("Support_preset_modes {}: {}".format(mode,supported_preset_modes))

        return supported_preset_modes

    async def async_update(self):
        """Retrieve latest state."""
        await self._device.api.async_update()

    async def async_turn_on(self):
        """Turn device CLIMATE on."""
        await self._device.set_path(self._device.getId(), self.embedded_id, "onOffMode", "", "on")

    async def async_turn_off(self):
        """Turn device CLIMATE off."""
        await self._device.set_path(self._device.getId(), self.embedded_id, "onOffMode", "", "off")

    @property
    def device_info(self):
        """Return a device description for device registry."""
        return self._device.device_info()
