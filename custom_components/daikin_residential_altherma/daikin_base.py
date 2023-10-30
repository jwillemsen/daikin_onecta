"""Pydaikin base appliance, represent a Daikin device."""

import logging

from .device import DaikinResidentialDevice

from .const import(
    PRESET_BOOST,
    PRESET_TANK_ONOFF,
    PRESET_SETPOINT_MODE,
    ATTR_OUTSIDE_TEMPERATURE,
    ATTR_TARGET_ROOM_TEMPERATURE,
    ATTR_TARGET_LEAVINGWATER_OFFSET,
    ATTR_TARGET_LEAVINGWATER_TEMPERATURE,
    ATTR_STATE_OFF,
    ATTR_STATE_ON,
    ATTR_CONTROL_MODE,
    DAIKIN_CMD_SETS,
    ATTR_ON_OFF_CLIMATE,
    ATTR_ON_OFF_TANK,
    ATTR_OPERATION_MODE,
    ATTR_ENERGY_CONSUMPTION,
    ATTR_ENERGY_CONSUMPTION_TANK,
    SENSOR_PERIOD_WEEKLY,
    MP_CLIMATE,
)

from homeassistant.components.climate.const import (
    ATTR_PRESET_MODE,
    HVAC_MODE_COOL,
    HVAC_MODE_HEAT,
    HVAC_MODE_HEAT_COOL,
    HVAC_MODE_OFF,
    PRESET_AWAY,
    PRESET_COMFORT,
    PRESET_BOOST,
    PRESET_ECO,
    PRESET_NONE,
)

from homeassistant.components.water_heater import (
    STATE_PERFORMANCE,
    STATE_HEAT_PUMP,
    STATE_OFF,
)

_LOGGER = logging.getLogger(__name__)

HA_PRESET_TO_DAIKIN = {
    PRESET_AWAY: "holidayMode",
    PRESET_NONE: "off",
    PRESET_BOOST: "powerfulMode",
    PRESET_COMFORT: "comfortMode",
    PRESET_ECO: "econoMode",
    PRESET_TANK_ONOFF: "onOffMode",
}

DAIKIN_HVAC_TO_HA = {
    "cooling": HVAC_MODE_COOL,
    "heating": HVAC_MODE_HEAT,
    "heatingDay": HVAC_MODE_HEAT,
    "heatingNight": HVAC_MODE_HEAT,
    "auto": HVAC_MODE_HEAT_COOL,
    "off": HVAC_MODE_OFF,
}

class Appliance(DaikinResidentialDevice):  # pylint: disable=too-many-public-methods
    """Daikin main appliance class."""

    def __init__(self, jsonData, apiInstance):
        """Init the pydaikin appliance, representing one Daikin device."""
        super().__init__(jsonData, apiInstance)

    async def init(self):
        """Init status."""
        # Re-defined in all sub-classes
        raise NotImplementedError

    def getCommandSet(self, param):
        if param in HA_PRESET_TO_DAIKIN.values():
            def keyByVal(dict,v):
                for k, v in dict.items():
                    if v == param:
                        return v
                    else:
                        continue
                return None
            if keyByVal(HA_PRESET_TO_DAIKIN,"Tank") == param:
                cmd_set = DAIKIN_CMD_SETS[ATTR_ON_OFF_TANK].copy()
                cmd_set[1] = param
            else:
                cmd_set = DAIKIN_CMD_SETS[ATTR_PRESET_MODE].copy()
                cmd_set[1] = param
        else:
            if "@Tank" not in param:
                cmd_set = DAIKIN_CMD_SETS[param].copy()
            else:
                cmd_set = DAIKIN_CMD_SETS[param].copy()
                cmd_set[1] = cmd_set[1].replace("@Tank","")
        if "%operationMode%" in cmd_set[2]:
            operation_mode = self.getValue(ATTR_OPERATION_MODE)
            cmd_set[2] = cmd_set[2].replace("%operationMode%", operation_mode)
        return cmd_set

    def getData(self, param):
        """Get the current data of a data object."""
        try:
            cmd_set = self.getCommandSet(param)
            v = self.get_data(cmd_set[0], cmd_set[1], cmd_set[2])
            return v
        except:
            return None

    def getDataEC(self, param, mode, period):
        """Get the current data of a data object."""
        if param == "energy_consumption":
            cmd_set = self.getCommandSet(param)
            return self.get_data(cmd_set[0], cmd_set[1], r"{}/{}/{}".format(cmd_set[2],mode,period))
        if param == "energy_consumption_tank":
            cmd_set = self.getCommandSet(param)
            return self.get_data(cmd_set[0], cmd_set[1], r"{}/{}/{}".format(cmd_set[2],mode,period))
        return None


    def getValue(self, param):
        """Get the current value of a data object."""
        data = self.getData(param)
        if data is None:
            return None
        return data["value"]

    def getValidValues(self, param):
        """Get the valid values of a data object."""
        data = self.getData(param)
        if data is None:
            return None
        return data["values"]

    async def setValue(self, param, value):
        """Set the current value of a data object."""
        cmd_set = self.getCommandSet(param)
        return await self.set_data(cmd_set[0], cmd_set[1], cmd_set[2], value)

    @property
    def hvac_mode(self):
        """Return current HVAC mode."""
        mode = HVAC_MODE_OFF
        if self.getValue(ATTR_ON_OFF_CLIMATE) != ATTR_STATE_OFF:
            mode = self.getValue(ATTR_OPERATION_MODE)
        return DAIKIN_HVAC_TO_HA.get(mode, HVAC_MODE_HEAT_COOL)

    @property
    def hvac_modes(self):
        """Return the list of available HVAC modes."""
        modes = [HVAC_MODE_OFF]
        for mode in self.getValidValues(ATTR_OPERATION_MODE):
            ha_mode = DAIKIN_HVAC_TO_HA[mode]
            if ha_mode not in modes:
                modes.append(ha_mode)
        return modes

    async def async_set_hvac_mode(self, hvac_mode):
        """Set HVAC mode."""
        if hvac_mode == HVAC_MODE_OFF:
            return await self.setValue(ATTR_ON_OFF_CLIMATE, ATTR_STATE_OFF)
        else:
            if self.hvac_mode == HVAC_MODE_OFF:
                await self.setValue(ATTR_ON_OFF_CLIMATE, ATTR_STATE_ON)
            return await self.setValue(ATTR_OPERATION_MODE, hvac_mode)

    def support_preset_mode(self, mode):
        """Return True if the device supports preset mode."""
        mode = HA_PRESET_TO_DAIKIN[mode]
        mode_data = self.get_data(MP_CLIMATE, mode)
        return mode_data is not None

    def preset_mode_status(self, mode):
        """Return the preset mode status."""
        mode = HA_PRESET_TO_DAIKIN[mode]
        mode_data = self.get_data(MP_CLIMATE, mode)
        if mode_data is None:
            return False
        # With the Altherma the preset mode holidayMode contains enabled/startDate/endDate
        # so handle that we van have a dictionary here with a enabled
        if type(mode_data) == dict:
            if mode_data["/enabled"] == True:
                return ATTR_STATE_ON
        return mode_data

    async def set_preset_mode_status(self, mode, status):
        """Set the preset mode status."""
        mode = HA_PRESET_TO_DAIKIN[mode]
        if self.getData(mode) is None:
            return
        return await self.setValue(mode, status)

    @property
    def supports_cooling(self):
        availableOperationModes = self.getValidValues(ATTR_OPERATION_MODE)
        if "cooling" in availableOperationModes:
            return True
        else:
            return False

    async def async_set_temperature(self, value):
        """Set new target temperature."""
        availableOperationModes = self.getValidValues(ATTR_OPERATION_MODE)
        operationMode = self.getValue(ATTR_OPERATION_MODE)
        if operationMode not in availableOperationModes:
            return None

        # Check which controlMode is used to control the device
        controlMode = self.getValue(ATTR_CONTROL_MODE)

        if controlMode == "roomTemperature":
            return await self.setValue(ATTR_TARGET_ROOM_TEMPERATURE, value)
        if controlMode in ("leavingWaterTemperature", "externalRoomTemperature"):
            if self.getData(ATTR_TARGET_LEAVINGWATER_OFFSET) is not None:
                return await self.setValue(ATTR_TARGET_LEAVINGWATER_OFFSET, int(value))
            if self.getData(ATTR_TARGET_LEAVINGWATER_TEMPERATURE) is not None:
                return await self.setValue(ATTR_TARGET_LEAVINGWATER_TEMPERATURE, int(value))

        return None

    def energy_consumption(self, attribute, mode, period):
        #DAMIANO
        #def energy_consumption_domestic(self, mode, period):
        """Return the last hour heat power consumption of a given mode in kWh."""
        energy_data = [
            0 if v is None else v

            #damiano
            #for v in self.getData(ATTR_ENERGY_CONSUMPTION)[mode][period]
            # passo anche mode e period
            for v in self.getDataEC(attribute,mode,period)
        ]
        start_index = 7 if period == SENSOR_PERIOD_WEEKLY else 12
        return sum(energy_data[start_index:])

    async def set(self, settings):
        """Set settings on Daikin device."""
        raise NotImplementedError

