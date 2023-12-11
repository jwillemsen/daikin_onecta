"""Support for the Daikin HVAC."""
import logging

import voluptuous as vol

from homeassistant.components.climate import PLATFORM_SCHEMA, ClimateEntity
from homeassistant.components.climate.const import (
    ATTR_HVAC_MODE,
    ATTR_PRESET_MODE, # DAMIANO lasciare
    HVAC_MODE_COOL,
    HVAC_MODE_HEAT,
    HVAC_MODE_HEAT_COOL,
    HVAC_MODE_OFF,
    HVAC_MODE_DRY,
    HVAC_MODE_FAN_ONLY,
    PRESET_AWAY,
    PRESET_COMFORT,
    PRESET_ECO,
    PRESET_NONE,
    SUPPORT_TARGET_TEMPERATURE,
    SUPPORT_PRESET_MODE,
    DEFAULT_MAX_TEMP,
    DEFAULT_MIN_TEMP,
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
    ATTR_ON_OFF_CLIMATE,
    ATTR_ON_OFF_TANK,
    ATTR_STATE_OFF,
    ATTR_STATE_ON,
    ATTR_CONTROL_MODE,
    ATTR_OPERATION_MODE,
    ATTR_TARGET_ROOM_TEMPERATURE,
    ATTR_TARGET_LEAVINGWATER_OFFSET,
    ATTR_TARGET_LEAVINGWATER_TEMPERATURE,
)

import re

_LOGGER = logging.getLogger(__name__)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {vol.Required(CONF_HOST): cv.string, vol.Optional(CONF_NAME): cv.string}
)


PRESET_MODES = {PRESET_COMFORT, PRESET_ECO, PRESET_AWAY}

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

DAIKIN_ATTR_ADVANCED = "adv"


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Old way of setting up the Daikin HVAC platform.

    Can only be called when a user accidentally mentions the platform in their
    config. But even in that case it would have been ignored.
    """


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up Daikin climate based on config_entry."""
    for dev_id, device in hass.data[DAIKIN_DOMAIN][DAIKIN_DEVICES].items():
        modes = []
        device_model = device.desc["deviceModel"]
        supported_management_point_types = {'climateControl'}
        if device.daikin_data["managementPoints"] is not None:
            for management_point in device.daikin_data["managementPoints"]:
                management_point_type = management_point["managementPointType"]
                if  management_point_type in supported_management_point_types:
                    # Check if we have a temperaturControl
                    temperatureControl = management_point.get("temperatureControl")
                    if temperatureControl is not None:
                        for operationmode in temperatureControl["value"]["operationModes"]:
                            #for modes in operationmode["setpoints"]:
                            for c in temperatureControl["value"]["operationModes"][operationmode]["setpoints"]:
                                _LOGGER.info("FOUND %s", c)
                                modes.append(c)
        # Remove duplicates
        modes = list(dict.fromkeys(modes))
        _LOGGER.info("Climate: Device %s has modes %s", device_model, modes)
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


        # self._supported_preset_modes = [PRESET_NONE]
        # self._current_preset_mode = PRESET_NONE
        # for mode in PRESET_MODES:
        #     support_preset = self._device.support_preset_mode(mode)
        #     if support_preset:
        #         self._supported_preset_modes.append(mode)
        #         self._supported_features |= SUPPORT_PRESET_MODE
        #     _LOGGER.info("Support_preset_mode {}: {}".format(mode,support_preset))

    async def _set(self, settings):
        """Set device settings using API."""
        values = {}

        for attr in [ATTR_TEMPERATURE, ATTR_HVAC_MODE]:
            value = settings.get(attr)
            if value is None:
                continue

            daikin_attr = HA_ATTR_TO_DAIKIN.get(attr)
            if daikin_attr is not None:
                if attr == ATTR_HVAC_MODE:
                    values[daikin_attr] = HA_HVAC_TO_DAIKIN[value]
                elif value in self._list[attr]:
                    values[daikin_attr] = value.lower()
                else:
                    _LOGGER.error("Invalid value %s for %s", attr, value)

            # temperature
            elif attr == ATTR_TEMPERATURE:
                try:
                    availableOperationModes = self._device.getValidValues(ATTR_OPERATION_MODE)
                    operationMode = self._device.getValue(ATTR_OPERATION_MODE)
                    if operationMode not in availableOperationModes:
                        return None

                    # Check which controlMode is used to control the device
                    controlMode = self._device.getValue(ATTR_CONTROL_MODE)
                    if controlMode == "roomTemperature":
                          values[HA_ATTR_TO_DAIKIN[ATTR_ROOM_TEMPERATURE]] = str(int(value))
                    if controlMode in ("leavingWaterTemperature", "externalRoomTemperature"):
                        if self._device.getData(ATTR_TARGET_LEAVINGWATER_OFFSET) is not None:
                            values[HA_ATTR_TO_DAIKIN[ATTR_LEAVINGWATER_OFFSET]] = str(int(value))
                        if self._device.getData(ATTR_TARGET_LEAVINGWATER_TEMPERATURE) is not None:
                            values[HA_ATTR_TO_DAIKIN[ATTR_LEAVINGWATER_TEMPERATURE]] = str(int(value))
                except ValueError:
                    _LOGGER.error("Invalid temperature %s", value)

        if values:
            await self._device.set(values)

    def setpoint(self):
        setpoint = None
        supported_management_point_types = {'climateControl'}
        if self._device.daikin_data["managementPoints"] is not None:
            for management_point in self._device.daikin_data["managementPoints"]:
                management_point_type = management_point["managementPointType"]
                if  management_point_type in supported_management_point_types:
                    # Check if we have a temperaturControl
                    temperatureControl = management_point.get("temperatureControl")
                    _LOGGER.info("Climate: Device temperatureControl %s", temperatureControl)
                    if temperatureControl is not None:
                        operationMode = management_point.get("operationMode").get("value")
                        setpoint = temperatureControl["value"]["operationModes"][operationMode]["setpoints"].get(self._setpoint)
                        _LOGGER.info("Climate: %s operation mode %s has setpoint %s", self._setpoint, operationMode, setpoint)
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
    def available(self):
        """Return the availability of the underlying device."""
        return self._device.available

    @property
    def supported_features(self):
        supported_features = 0
        setpointdict = self.setpoint()
        if setpointdict is not None and setpointdict["settable"] == True:
            supported_features = SUPPORT_TARGET_TEMPERATURE
        _LOGGER.info("Support features %s", supported_features)
        return supported_features

    @property
    def name(self):
        myname = self._setpoint[0].upper() + self._setpoint[1:]
        readable = re.findall('[A-Z][^A-Z]*', myname)
        """Return the name of the thermostat, if any."""
        #print("DAMIANO name = %s",self._device.name)
        return f"{self._device.name} {' '.join(readable)}"

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
        """Set new target temperature."""
        # The service climate.set_temperature can set the hvac_mode too, see
        # https://www.home-assistant.io/integrations/climate/#service-climateset_temperature
        # se we first set the hvac_mode, if provided, then the temperature.
        if ATTR_HVAC_MODE in kwargs:
            await self.async_set_hvac_mode(kwargs[ATTR_HVAC_MODE])

        await self._device.async_set_temperature(kwargs[ATTR_TEMPERATURE])
        # ADDED for instant update
        await self._device.api.async_update()

    @property
    def hvac_mode(self):
        """Return current operation ie. heat, cool, idle."""
        return self._device.hvac_mode

    @property
    def hvac_modes(self):
        """Return the list of available operation modes."""
        return self._device.hvac_modes

    async def async_set_hvac_mode(self, hvac_mode):
        """Set HVAC mode."""
        await self._device.async_set_hvac_mode(HA_HVAC_TO_DAIKIN[hvac_mode])

    @property
    def preset_mode(self):
        """Return the preset_mode."""
        self._current_preset_mode = PRESET_NONE
        for mode in self._supported_preset_modes:
            if self._device.preset_mode_status(mode) == ATTR_STATE_ON:
                self._current_preset_mode = mode
        return self._current_preset_mode

    async def async_set_preset_mode(self, preset_mode):
        """Set preset mode."""
        curr_mode = self.preset_mode
        if curr_mode != PRESET_NONE:
            await self._device.set_preset_mode_status(curr_mode, ATTR_STATE_OFF)
        if preset_mode != PRESET_NONE:
            await self._device.set_preset_mode_status(preset_mode, ATTR_STATE_ON)

    @property
    def preset_modes(self):
        """List of available preset modes."""
        return self._supported_preset_modes

    async def async_update(self):
        """Retrieve latest state."""
        await self._device.api.async_update()

    async def async_turn_on(self):
        """Turn device CLIMATE on."""
        await self._device.setValue(ATTR_ON_OFF_CLIMATE, ATTR_STATE_ON)

    async def async_turn_off(self):
        """Turn device CLIMATE off."""
        await self._device.setValue(ATTR_ON_OFF_CLIMATE, ATTR_STATE_OFF)

    @property
    def device_info(self):
        """Return a device description for device registry."""
        return self._device.device_info()
