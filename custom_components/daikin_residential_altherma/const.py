"""Constants for Daikin Residential Controller."""

from homeassistant.const import (
    CONF_DEVICE_CLASS,
    CONF_TOKEN,
    CONF_ICON,
    CONF_NAME,
    CONF_TYPE,
    CONF_UNIT_OF_MEASUREMENT,
    DEVICE_CLASS_TEMPERATURE,
    ENERGY_KILO_WATT_HOUR,
    TEMP_CELSIUS,
)

DOMAIN = "daikin_residential_altherma"

CONF_TOKENSET = CONF_TOKEN + "set"

DAIKIN_DATA = "daikin_data"
DAIKIN_API = "daikin_api"
DAIKIN_DEVICES = "daikin_devices"
DAIKIN_DISCOVERY_NEW = "daikin_discovery_new_{}"

# MANAGEMENT POINTS
MP_CLIMATE = "climateControlMainZone"
MP_GATEWAY = "gateway" # NEW
MP_DOMESTIC_HWT = "domesticHotWaterTank"
MP_INDOOR_UNIT = "indoorUnitHydro"
MP_OUDOOR_UNIT = "outdoorUnit"
MP_USER_INTERFACE = "userInterface"

# DATA POINTS
DP_ON_OFF_CLIMATE = "onOffMode"
DP_ON_OFF_TANK = "onOffMode"
DP_OPERATION_MODE = "operationMode"
DP_SENSORS = "sensoryData"
DP_TEMPERATURE = "temperatureControl"
DP_CONSUMPTION = "consumptionData"

# DAMIANO HEAT PUMP ALTHERMA

#ATTR_ON_OFF = "on_off"
ATTR_ON_OFF_CLIMATE = "on_off_climate"
ATTR_ON_OFF_TANK = "on_off_tank"
ATTR_PRESET_MODE = "preset_mode"
ATTR_OPERATION_MODE = "operation_mode"
ATTR_TARGET_ROOM_TEMPERATURE = "target_room_temperature"
ATTR_LEAVINGWATER_TEMPERATURE = "leavingWaterTemperature"
ATTR_OUTSIDE_TEMPERATURE = "outdoorTemperature"
ATTR_ROOM_TEMPERATURE = "roomTemperature"
ATTR_TANK_TEMPERATURE = "tankTemperature"
ATTR_ENERGY_CONSUMPTION = "energy_consumption"
ATTR_ENERGY_CONSUMPTION_TANK = "energy_consumption_tank"
ATTR_COOL_ENERGY = "cool_energy"
ATTR_HEAT_ENERGY = "heat_energy"
ATTR_HEAT_TANK_ENERGY = "heat_tank_energy"

DAIKIN_CMD_SETS = {
    #ATTR_ON_OFF: [MP_CLIMATE, DP_ON_OFF, "onOffMode"],
    ATTR_ON_OFF_CLIMATE: [MP_CLIMATE, DP_ON_OFF_CLIMATE, ""],
    ATTR_ON_OFF_TANK: [MP_DOMESTIC_HWT, DP_ON_OFF_TANK, ""],
    ATTR_PRESET_MODE: [MP_CLIMATE, "", ""],
    ATTR_OPERATION_MODE: [MP_CLIMATE, DP_OPERATION_MODE, ""],
    ATTR_OUTSIDE_TEMPERATURE: [MP_CLIMATE, DP_SENSORS, "/outdoorTemperature"],
    ATTR_ROOM_TEMPERATURE: [MP_CLIMATE, DP_SENSORS, "/roomTemperature"],
    ATTR_LEAVINGWATER_TEMPERATURE: [MP_CLIMATE, DP_SENSORS, "/leavingWaterTemperature"], # "/roomTemperature"
    ATTR_TANK_TEMPERATURE: [MP_DOMESTIC_HWT, DP_SENSORS, "/tankTemperature"],
    ATTR_TARGET_ROOM_TEMPERATURE: [
        MP_CLIMATE,
        DP_TEMPERATURE,
        "/operationModes/%operationMode%/setpoints/roomTemperature",
    ],
    ATTR_ENERGY_CONSUMPTION: [MP_CLIMATE, DP_CONSUMPTION, "/electrical"],
    ATTR_ENERGY_CONSUMPTION_TANK: [MP_DOMESTIC_HWT, DP_CONSUMPTION, "/electrical"]
}

ATTR_STATE_ON = "on"
ATTR_STATE_OFF = "off"

PRESET_BOOST= "boost"
PRESET_TANK_ONOFF= "ACS_state"
PRESET_SETPOINT_MODE = "setpointMode"
# DAMIANO
DAIKIN_SWITCHES = [PRESET_BOOST,PRESET_TANK_ONOFF,] #PRESET_SETPOINT_MODE
DAIKIN_SWITCHES_ICONS ={PRESET_BOOST:'mdi:bike-fast',PRESET_TANK_ONOFF: 'mdi:bathtub-outline',PRESET_SETPOINT_MODE:'mdi:thermometer-lines'}
SWITCH_DEFAULT_ICON = "hass:air-filter"

SENSOR_TYPE_TEMPERATURE = "temperature"
SENSOR_TYPE_POWER = "power"
SENSOR_TYPE_ENERGY = "energy"
SENSOR_TYPE_INFO = "info"
SENSOR_PERIOD_DAILY = "d"
SENSOR_PERIOD_WEEKLY = "w"
SENSOR_PERIOD_YEARLY = "m"
SENSOR_PERIODS = {
    SENSOR_PERIOD_DAILY: "Daily",
    SENSOR_PERIOD_WEEKLY: "Weekly",
    SENSOR_PERIOD_YEARLY: "Yearly",
}

SENSOR_TYPES = {
    ATTR_LEAVINGWATER_TEMPERATURE: {
        CONF_NAME: "Leaving Water Temperature",
        CONF_TYPE: SENSOR_TYPE_TEMPERATURE,
        CONF_DEVICE_CLASS: DEVICE_CLASS_TEMPERATURE,
        CONF_UNIT_OF_MEASUREMENT: TEMP_CELSIUS,
    },
    ATTR_OUTSIDE_TEMPERATURE: {
        CONF_NAME: "Outside Temperature",
        CONF_TYPE: SENSOR_TYPE_TEMPERATURE,
        CONF_DEVICE_CLASS: DEVICE_CLASS_TEMPERATURE,
        CONF_UNIT_OF_MEASUREMENT: TEMP_CELSIUS,
    },
    ATTR_ROOM_TEMPERATURE: {
        CONF_NAME: "Room Temperature",
        CONF_TYPE: SENSOR_TYPE_TEMPERATURE,
        CONF_DEVICE_CLASS: DEVICE_CLASS_TEMPERATURE,
        CONF_UNIT_OF_MEASUREMENT: TEMP_CELSIUS,
    },
    ATTR_TANK_TEMPERATURE: {
        CONF_NAME: "Tank Temperature",
        CONF_TYPE: SENSOR_TYPE_TEMPERATURE,
        CONF_ICON: "mdi:bathtub-outline",
        CONF_DEVICE_CLASS: DEVICE_CLASS_TEMPERATURE,
        CONF_UNIT_OF_MEASUREMENT: TEMP_CELSIUS,
    },
    ATTR_COOL_ENERGY: {
        CONF_NAME: "Cool Energy Consumption",
        CONF_TYPE: SENSOR_TYPE_ENERGY,
        CONF_ICON: "mdi:snowflake",
        CONF_UNIT_OF_MEASUREMENT: ENERGY_KILO_WATT_HOUR,
    },
    ATTR_HEAT_ENERGY: {
        CONF_NAME: "Heat Energy Consumption",
        CONF_TYPE: SENSOR_TYPE_ENERGY,
        CONF_ICON: "mdi:waves-arrow-up",
        CONF_UNIT_OF_MEASUREMENT: ENERGY_KILO_WATT_HOUR,
    },
    ATTR_HEAT_TANK_ENERGY: {
        CONF_NAME: "Heat Tank Energy Consumption",
        CONF_TYPE: SENSOR_TYPE_ENERGY,
        CONF_ICON: "mdi:bathtub-outline",
        CONF_UNIT_OF_MEASUREMENT: ENERGY_KILO_WATT_HOUR,
    },
}

CONF_UUID = "uuid"

KEY_MAC = "mac"
KEY_IP = "ip"

TIMEOUT = 60
