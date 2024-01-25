"""Support for the Daikin BRP069A62."""
import logging
_LOGGER = logging.getLogger(__name__)

from homeassistant.components.water_heater import (
    STATE_PERFORMANCE,
    STATE_HEAT_PUMP,
    STATE_OFF,
    WaterHeaterEntity,
    WaterHeaterEntityFeature,
)

from homeassistant.const import (
    ATTR_TEMPERATURE,
    UnitOfTemperature
)

from .const import (
    DOMAIN as DAIKIN_DOMAIN,
    DAIKIN_DEVICES,
    ATTR_STATE_OFF,
    ATTR_STATE_ON,
)

async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Old way of setting up the Daikin HVAC platform.

    Can only be called when a user accidentally mentions the platform in their
    config. But even in that case it would have been ignored.
    """

async def async_setup_entry(hass, entry, async_add_entities):
    """Set up Daikin water tank entities."""
    for dev_id, device in hass.data[DAIKIN_DOMAIN][DAIKIN_DEVICES].items():
        device_model = device.daikin_data["deviceModel"]
        supported_management_point_types = {'domesticHotWaterTank', 'domesticHotWaterFlowThrough'}
        """ When the device has a domesticHotWaterTank we add a water heater """
        managementPoints = device.daikin_data.get("managementPoints", [])
        for management_point in managementPoints:
            management_point_type = management_point["managementPointType"]
            if  management_point_type in supported_management_point_types:
                async_add_entities([DaikinWaterTank(device)], update_before_add=True)
            else:
                _LOGGER.info("'%s' has not a tank management point, ignoring as water heater", management_point_type)

class DaikinWaterTank(WaterHeaterEntity):
    """Representation of a Daikin Water Tank."""

    def __init__(self, device):
        """Initialize the Water device."""
        _LOGGER.info("Initializing Daiking Altherma HotWaterTank...")
        self._device = device
        if self.supported_features & WaterHeaterEntityFeature.TARGET_TEMPERATURE:
            _LOGGER.debug("Tank temperature is settable")

    async def _set(self, settings):
        raise NotImplementedError

    @property
    def embedded_id(self):
        # Find the embedded id for the hot water tank we have to use
        supported_management_point_types = {'domesticHotWaterTank', 'domesticHotWaterFlowThrough'}

        for management_point in self._device.daikin_data["managementPoints"]:
            management_point_type = management_point["managementPointType"]
            if  management_point_type in supported_management_point_types:
                return management_point["embeddedId"]
        return None

    @property
    def hotwatertank_data(self):
        # Find the management point for the hot water tank
        supported_management_point_types = {'domesticHotWaterTank', 'domesticHotWaterFlowThrough'}

        for management_point in self._device.daikin_data["managementPoints"]:
            management_point_type = management_point["managementPointType"]
            if  management_point_type in supported_management_point_types:
                return management_point
        return None

    @property
    def domestic_hotwater_temperature(self):
        # Find the json dictionary for controlling the hot water temperature
        temp_control = self.hotwatertank_data["temperatureControl"]["value"]
        if temp_control:
            heating_mode = temp_control["operationModes"]["heating"]
            if heating_mode is not None:
                return heating_mode["setpoints"]["domesticHotWaterTemperature"]
        return None

    @property
    def available(self):
        """Return the availability of the underlying device."""
        return self._device.available

    @property
    def supported_features(self):
        sf = WaterHeaterEntityFeature.OPERATION_MODE
        # Only when we have a fixed setpointMode we can control the target
        # temperature of the tank
        dht = self.domestic_hotwater_temperature
        if dht:
            if dht["settable"] == True:
                sf |= WaterHeaterEntityFeature.TARGET_TEMPERATURE
        """Return the list of supported features."""
        return sf

    @property
    def name(self):
        """Return the name of the thermostat, if any."""
        return self._device.name

    @property
    def unique_id(self):
        """Return a unique ID."""
        devID = self._device.getId()
        return f"{devID}"

    @property
    def temperature_unit(self):
        """Return the unit of measurement which this thermostat uses."""
        return UnitOfTemperature.CELSIUS

    @property
    def current_temperature(self):
        """Return tank temperature."""
        ret = None
        hwtd = self.hotwatertank_data
        # Some Altherma versions don't provide a current temperature, there is no sensoryData
        sensoryData = hwtd.get("sensoryData")
        if sensoryData is not None:
            ret =  float(sensoryData["value"]["tankTemperature"]["value"])
            _LOGGER.debug("Device '%s' hot water tank current_temperature '%s'", self._device.name, ret)
        else:
            _LOGGER.debug("Device '%s' doesn't provide a current temperature", self._device.name)

        return ret

    @property
    def target_temperature(self):
        """Return the temperature we try to reach."""
        ret = None
        dht = self.domestic_hotwater_temperature
        if dht is not None:
            ret = float(dht["value"])
        _LOGGER.debug("Device '%s' hot water tank target_temperature '%s'", self._device.name, ret)
        return ret

    @property
    def extra_state_attributes(self):
        data = {}
        dht = self.domestic_hotwater_temperature
        if dht is not None:
            """Return the optional device state attributes."""
            data = {"target_temp_step": float(dht["stepValue"])}
        return data

    @property
    def min_temp(self):
        """Return the supported minimum value target temperature."""
        ret = None
        dht = self.domestic_hotwater_temperature
        if dht is not None:
            ret = float(dht["minValue"])
        _LOGGER.debug("Device '%s' hot water tank minimum_temperature '%s'", self._device.name, ret)
        return ret

    @property
    def max_temp(self):
        """Return the supported maximum value of target temperature."""
        ret = None
        dht = self.domestic_hotwater_temperature
        if dht is not None:
            ret = float(self.domestic_hotwater_temperature["maxValue"])
        _LOGGER.debug("Device '%s' hot water tank maximum temperature '%s'", self._device.name, ret)
        return ret

    async def async_set_tank_temperature(self, value):
        """Set new target temperature."""
        _LOGGER.debug("Device '%s' set tank temperature: %s", self._device.name, value)
        if self.current_operation == STATE_OFF:
            _LOGGER.debug("Device '%s' set tank temperature ignored because device is off", self._device.name)
            return None
        dht = self.domestic_hotwater_temperature
        if dht is not None:
            if dht["settable"] == False:
                _LOGGER.debug("Device '%s' set tank temperature ignored because tank temperature can't be set", self._device.name)
                return None
        res = await self._device.set_path(self._device.getId(), self.embedded_id, "temperatureControl", "/operationModes/heating/setpoints/domesticHotWaterTemperature", int(value))
        # When updating the value to the daikin cloud worked update our local cached version
        if res:
            dht = self.domestic_hotwater_temperature
            if dht is not None:
                dht["value"] = value

    async def async_set_tank_state(self, new_tank_state):
        """Set new tank state."""
        _LOGGER.debug("Set tank state: %s", new_tank_state)
        result = True

        # First determine the new settings for onOffMode/powerfulMode, we need these to set them to Daikin
        # and update our local cached version when succeeded
        onOffMode = ""
        powerfulMode = ""
        if new_tank_state == STATE_OFF:
            onOffMode = "off"
        if new_tank_state == STATE_PERFORMANCE:
            powerfulMode = "on"
            if self.current_operation == STATE_OFF:
                onOffMode = "on"
        if new_tank_state == STATE_HEAT_PUMP:
            if self.current_operation == STATE_PERFORMANCE:
                powerfulMode = "off"
            if self.current_operation == STATE_OFF:
                onOffMode = "on"

        # Only set the on/off to Daikin when we need to change it
        if onOffMode != "":
            result &= await self._device.set_path(self._device.getId(), self.embedded_id, "onOffMode", "", onOffMode)
        # Only set powerfulMode when it is set and supported by the device
        if (powerfulMode != "") and (STATE_PERFORMANCE in self.operation_list):
            result &= await self._device.set_path(self._device.getId(), self.embedded_id, "powerfulMode", "", powerfulMode)

        if result is False:
            _LOGGER.warning("Device '%s' invalid tank state: %s", self._device.name, new_tank_state)
        else:
            # Update local cached version
            hwtd = self.hotwatertank_data
            if onOffMode != "":
                hwtd["onOffMode"]["value"] = onOffMode
            if powerfulMode != "":
                pwf = hwtd.get("powerfulMode")
                if pwf is not None:
                    pwf["value"] = powerfulMode

        return result

    async def async_set_temperature(self, **kwargs):
        """Set new target temperature."""
        # The service climate.set_temperature can set the hvac_mode too, see
        # https://www.home-assistant.io/integrations/climate/#service-climateset_temperature
        # se we first set the hvac_mode, if provided, then the temperature.
        await self.async_set_tank_temperature(kwargs[ATTR_TEMPERATURE])

    @property
    def current_operation(self):
        """Return current operation ie. heat, cool, idle."""
        state = STATE_OFF
        hwtd = self.hotwatertank_data
        if hwtd["onOffMode"]["value"] == "on":
            state = STATE_HEAT_PUMP
            pwf = hwtd.get("powerfulMode")
            if pwf is not None:
                if pwf["value"] == "on":
                    state = STATE_PERFORMANCE
        _LOGGER.debug("Device '%s' hot water tank current mode '%s'", self._device.name, state)
        return state

    @property
    def operation_list(self):
        """Return the list of available operation modes."""
        states = [STATE_OFF, STATE_HEAT_PUMP]
        hwtd = self.hotwatertank_data
        pwf = hwtd.get("powerfulMode")
        if pwf is not None:
            if pwf["settable"] == True:
                states += [STATE_PERFORMANCE]
        _LOGGER.debug("Device '%s' hot water tank supports modes %s", self._device.name, states)
        return states

    async def async_set_operation_mode(self, operation_mode):
        """Set new target tank operation mode."""
        await self.async_set_tank_state(operation_mode)

    @property
    def device_info(self):
        """Return a device description for device registry."""
        return self._device.device_info()
