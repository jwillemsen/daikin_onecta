"""Constants for Daikin Residential Controller."""

from homeassistant.const import (
    CONF_DEVICE_CLASS,
    CONF_TOKEN,
    CONF_ICON,
    CONF_NAME,
    CONF_TYPE,
    CONF_UNIT_OF_MEASUREMENT,
    DEVICE_CLASS_TEMPERATURE,
    DEVICE_CLASS_ENERGY,
    DEVICE_CLASS_SIGNAL_STRENGTH,
    ENERGY_KILO_WATT_HOUR,
    TEMP_CELSIUS,
    PERCENTAGE,
    SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
)

DOMAIN = "daikin_residential_altherma"

CONF_TOKENSET = CONF_TOKEN + "set"

DAIKIN_DATA = "daikin_data"
DAIKIN_API = "daikin_api"
DAIKIN_DEVICES = "daikin_devices"
DAIKIN_DISCOVERY_NEW = "daikin_discovery_new_{}"

# MANAGEMENT POINTS
MP_CLIMATE = "climateControlMainZone"
MP_GATEWAY = "gateway"
MP_DOMESTIC_HWT = "domesticHotWaterTank"
MP_INDOOR_UNIT = "indoorUnitHydro"
MP_OUDOOR_UNIT = "outdoorUnit"
MP_USER_INTERFACE = "userInterface"

# DATA POINTS
DP_ON_OFF_MODE = "onOffMode"
DP_TANK_POWERFUL_MODE = "powerfulMode"
DP_TANK_TEMPERATURECONTROL = "temperatureControl"

DP_ON_OFF_CLIMATE = "onOffMode"
DP_ON_OFF_TANK = "onOffMode"
DP_OPERATION_MODE = "operationMode"
DP_SENSORS = "sensoryData"
DP_TEMPERATURE = "temperatureControl"
DP_CONSUMPTION = "consumptionData"
DP_CONTROL_MODE = "controlMode"
DP_WIFI_STRENGTH = "wifiConnectionStrength"
DP_WIFI_SSID = "wifiConnectionSSID"
DP_LOCAL_SSID = "ssid"
DP_MAC_ADDRESS = "macAddress"
DP_SERIAL_NUMBER = "serialNumber"

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
ATTR_LEAVINGWATER_OFFSET = "leavingWaterOffset"
ATTR_TANK_TEMPERATURE = "tankTemperature"
ATTR_ENERGY_CONSUMPTION = "energy_consumption"
ATTR_ENERGY_CONSUMPTION_TANK = "energy_consumption_tank"
ATTR_COOL_ENERGY = "cool_energy"
ATTR_HEAT_ENERGY = "heat_energy"
ATTR_HEAT_TANK_ENERGY = "heat_tank_energy"
ATTR_SETPOINT_MODE = "setpointMode"
ATTR_TANK_SETPOINT_MODE = "@TanksetpointMode"
ATTR_CONTROL_MODE = "controlMode"

ATTR_TANK_ON_OFF = "tank_on_off"
ATTR_TANK_POWERFUL = "powerfulMode"
ATTR_TANK_STATE_HEAT_PUMP = "on"
ATTR_TANK_TARGET_TEMPERATURE = "targetTemperature"
ATTR_TANK_MODE = "tank_mode"
ATTR_TANK_MODE_SET = "tank_state"
ATTR_TANK_STATE_OFF = "off"
ATTR_TANK_STATE_PERFOMANCE = "powerfulMode"

ATTR_IS_HOLIDAY_MODE_ACTIVE = "isHolidayModeActive"
ATTR_IS_IN_EMERGENCY_STATE = "isInEmergencyState"
ATTR_IS_IN_ERROR_STATE = "isInErrorState"
ATTR_IS_IN_INSTALLER_STATE = "isInInstallerState"
ATTR_IS_IN_WARNING_STATE = "isInWarningState"
ATTR_ERROR_CODE = "errorCode"

ATTR_TANK_HEATUP_MODE = "heatupMode"
ATTR_TANK_IS_HOLIDAY_MODE_ACTIVE = "@TankisHolidayModeActive"
ATTR_TANK_IS_IN_EMERGENCY_STATE = "@TankisInEmergencyState"
ATTR_TANK_IS_IN_ERROR_STATE = "@TankisInErrorState"
ATTR_TANK_IS_IN_INSTALLER_STATE = "@TankisInInstallerState"
ATTR_TANK_IS_IN_WARNING_STATE = "@TankisInWarningState"
ATTR_TANK_IS_POWERFUL_MODE_ACTIVE = "isPowerfulModeActive"
ATTR_TANK_ERROR_CODE = "@TankErrorCode"

ATTR_WIFI_STRENGTH = "wifi_strength"
ATTR_WIFI_SSID = "wifi_ssid"
ATTR_LOCAL_SSID = "local_ssid"
ATTR_MAC_ADDRESS = "mac_address"
ATTR_SERIAL_NUMBER = "serial_number"

DAIKIN_CMD_SETS = {
    #ATTR_ON_OFF: [MP_CLIMATE, DP_ON_OFF, "onOffMode"],
    ATTR_ON_OFF_CLIMATE: [MP_CLIMATE, DP_ON_OFF_CLIMATE, ""],
    ATTR_ON_OFF_TANK: [MP_DOMESTIC_HWT, DP_ON_OFF_TANK, ""],
    ATTR_PRESET_MODE: [MP_CLIMATE, "", ""],
    ATTR_OPERATION_MODE: [MP_CLIMATE, DP_OPERATION_MODE, ""],
    ATTR_OUTSIDE_TEMPERATURE: [MP_CLIMATE, DP_SENSORS, "/outdoorTemperature"],
    ATTR_ROOM_TEMPERATURE: [MP_CLIMATE, DP_SENSORS, "/roomTemperature"],
    ATTR_LEAVINGWATER_OFFSET: [MP_CLIMATE, DP_TEMPERATURE, "/operationModes/%operationMode%/setpoints/leavingWaterOffset"],
    ATTR_LEAVINGWATER_TEMPERATURE: [MP_CLIMATE, DP_SENSORS, "/leavingWaterTemperature"], # "/roomTemperature"
    ATTR_TANK_TEMPERATURE: [MP_DOMESTIC_HWT, DP_SENSORS, "/tankTemperature"],
    ATTR_TARGET_ROOM_TEMPERATURE: [
        MP_CLIMATE,
        DP_TEMPERATURE,
        "/operationModes/%operationMode%/setpoints/roomTemperature",
    ],
    ATTR_ENERGY_CONSUMPTION: [MP_CLIMATE, DP_CONSUMPTION, "/electrical"],
    ATTR_ENERGY_CONSUMPTION_TANK: [MP_DOMESTIC_HWT, DP_CONSUMPTION, "/electrical"],
    ATTR_SETPOINT_MODE: [MP_CLIMATE, "setpointMode", ""],
    ATTR_TANK_SETPOINT_MODE: [MP_DOMESTIC_HWT, "@TanksetpointMode", ""],
    ATTR_CONTROL_MODE: [MP_CLIMATE, DP_CONTROL_MODE, ""],
    # FLAG HEAT PUMP
    ATTR_IS_HOLIDAY_MODE_ACTIVE: [MP_CLIMATE, "isHolidayModeActive", ""],
    ATTR_IS_IN_EMERGENCY_STATE: [MP_CLIMATE, "isInEmergencyState", ""],
    ATTR_IS_IN_ERROR_STATE: [MP_CLIMATE, "isInErrorState", ""],
    ATTR_IS_IN_INSTALLER_STATE: [MP_CLIMATE, "isInInstallerState", ""],
    ATTR_IS_IN_WARNING_STATE: [MP_CLIMATE, "isInWarningState", ""],
    ATTR_ERROR_CODE: [MP_CLIMATE, "errorCode", ""],
    #  FLAG HOT WATER TANK
    ATTR_TANK_HEATUP_MODE: [MP_DOMESTIC_HWT, "heatupMode", ""],
    ATTR_TANK_IS_HOLIDAY_MODE_ACTIVE: [MP_DOMESTIC_HWT, "@TankisHolidayModeActive", ""],
    ATTR_TANK_IS_IN_EMERGENCY_STATE: [MP_DOMESTIC_HWT, "@TankisInEmergencyState", ""],
    ATTR_TANK_IS_IN_ERROR_STATE: [MP_DOMESTIC_HWT, "@TankisInErrorState", ""],
    ATTR_TANK_IS_IN_INSTALLER_STATE: [MP_DOMESTIC_HWT, "@TankisInInstallerState", ""],
    ATTR_TANK_IS_IN_WARNING_STATE: [MP_DOMESTIC_HWT, "@TankisInWarningState", ""],
    ATTR_TANK_IS_POWERFUL_MODE_ACTIVE: [MP_DOMESTIC_HWT, "isPowerfulModeActive", ""],
    ATTR_TANK_ERROR_CODE: [MP_DOMESTIC_HWT, "errorCode", ""],
    ATTR_TANK_TARGET_TEMPERATURE: [MP_DOMESTIC_HWT, DP_TANK_TEMPERATURECONTROL, "/operationModes/heating/setpoints/domesticHotWaterTemperature"],
    #  Gateway settings
    ATTR_WIFI_STRENGTH: [MP_GATEWAY, DP_WIFI_STRENGTH, ""],
    ATTR_WIFI_SSID: [MP_GATEWAY, DP_WIFI_SSID, ""],
    ATTR_LOCAL_SSID: [MP_GATEWAY, DP_LOCAL_SSID, ""],
    ATTR_MAC_ADDRESS: [MP_GATEWAY, DP_MAC_ADDRESS, ""],
    ATTR_SERIAL_NUMBER: [MP_GATEWAY, DP_SERIAL_NUMBER, ""],
    ATTR_TANK_ON_OFF: [MP_DOMESTIC_HWT, DP_ON_OFF_MODE, ""],
    ATTR_TANK_POWERFUL: [MP_DOMESTIC_HWT, DP_TANK_POWERFUL_MODE, ""],
}

ATTR_STATE_ON = "on"
ATTR_STATE_OFF = "off"
SWITCH_TANK_TANK_ONOFF = "onOffMode"
SWITCH_POWERFUL_ONOFF = "powerfulMode"

PRESET_BOOST= "boost"
PRESET_TANK_ONOFF= "Tank"
PRESET_SETPOINT_MODE = "setpointMode"
DAIKIN_SWITCHES = [PRESET_BOOST,PRESET_TANK_ONOFF] #PRESET_SETPOINT_MODE ,SWITCH_TANK_TANK_ONOFF,SWITCH_POWERFUL_ONOFF,
DAIKIN_SWITCHES_ICONS ={PRESET_BOOST:'mdi:bike-fast',PRESET_TANK_ONOFF: 'mdi:bathtub-outline',PRESET_SETPOINT_MODE:'mdi:thermometer-lines'}
SWITCH_DEFAULT_ICON = "hass:air-filter"

SENSOR_TYPE_TEMPERATURE = "temperature"
SENSOR_TYPE_POWER = "power"
SENSOR_TYPE_ENERGY = "energy"
SENSOR_TYPE_INFO = None
SENSOR_TYPE_GATEWAY_DIAGNOSTIC = "gateway_diagnostic"
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
    ATTR_LEAVINGWATER_OFFSET: {
        CONF_NAME: "Leaving Water Offset",
        CONF_TYPE: SENSOR_TYPE_TEMPERATURE,
        CONF_ICON: "mdi:cursor-pointer",
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
        CONF_DEVICE_CLASS: DEVICE_CLASS_ENERGY,
        CONF_UNIT_OF_MEASUREMENT: ENERGY_KILO_WATT_HOUR,
    },
    ATTR_HEAT_ENERGY: {
        CONF_NAME: "Heat Energy Consumption",
        CONF_TYPE: SENSOR_TYPE_ENERGY,
        CONF_ICON: "mdi:fire",
        CONF_DEVICE_CLASS: DEVICE_CLASS_ENERGY,
        CONF_UNIT_OF_MEASUREMENT: ENERGY_KILO_WATT_HOUR,
    },
    ATTR_HEAT_TANK_ENERGY: {
        CONF_NAME: "Heat Tank Energy Consumption",
        CONF_TYPE: SENSOR_TYPE_ENERGY,
        CONF_ICON: "mdi:bathtub-outline",
        CONF_DEVICE_CLASS: DEVICE_CLASS_ENERGY,
        CONF_UNIT_OF_MEASUREMENT: ENERGY_KILO_WATT_HOUR,
    },
    ATTR_SETPOINT_MODE: {
        CONF_NAME: "Info Setpoint Mode",
        CONF_TYPE: None,
        CONF_ICON: "mdi:information-outline",
        CONF_UNIT_OF_MEASUREMENT: " ",
    },
    ATTR_TANK_SETPOINT_MODE: {
        CONF_NAME: "Info Tank Setpoint Mode",
        CONF_TYPE: None,
        CONF_ICON: "mdi:information-outline",
        CONF_UNIT_OF_MEASUREMENT: " ",
    },
    ATTR_CONTROL_MODE: {
        CONF_NAME: "Info Control Mode",
        CONF_TYPE: None,
        CONF_ICON: "mdi:information-outline",
        #CONF_DEVICE_CLASS: DEVICE_CLASS_ENERGY,
        CONF_UNIT_OF_MEASUREMENT: " ",
    },
    ATTR_IS_HOLIDAY_MODE_ACTIVE: {
        CONF_NAME: "Info is Holiday Mode Active",
        CONF_TYPE: None,
        CONF_ICON: "mdi:information-outline",
        #CONF_DEVICE_CLASS: DEVICE_CLASS_ENERGY,
        CONF_UNIT_OF_MEASUREMENT: " ",
    },
    ATTR_IS_IN_EMERGENCY_STATE: {
        CONF_NAME: "Info is In Emergency State",
        CONF_TYPE: None,
        CONF_ICON: "mdi:information-outline",
        #CONF_DEVICE_CLASS: DEVICE_CLASS_ENERGY,
        CONF_UNIT_OF_MEASUREMENT: " ",
    },
    ATTR_IS_IN_ERROR_STATE: {
        CONF_NAME: "Info is In Error State",
        CONF_TYPE: None,
        CONF_ICON: "mdi:information-outline",
        #CONF_DEVICE_CLASS: DEVICE_CLASS_ENERGY,
        CONF_UNIT_OF_MEASUREMENT: " ",
    },
    ATTR_IS_IN_INSTALLER_STATE: {
        CONF_NAME: "Info is In Installer State",
        CONF_TYPE: None,
        CONF_ICON: "mdi:information-outline",
        #CONF_DEVICE_CLASS: DEVICE_CLASS_ENERGY,
        CONF_UNIT_OF_MEASUREMENT: " ",
    },
    ATTR_IS_IN_WARNING_STATE: {
        CONF_NAME: "Info is In Warning State",
        CONF_TYPE: None,
        CONF_ICON: "mdi:information-outline",
        #CONF_DEVICE_CLASS: DEVICE_CLASS_ENERGY,
        CONF_UNIT_OF_MEASUREMENT: " ",
    },
    ATTR_ERROR_CODE: {
        CONF_NAME: "Info Error Code",
        CONF_TYPE: None,
        CONF_ICON: "mdi:information-outline",
        #CONF_DEVICE_CLASS: DEVICE_CLASS_ENERGY,
        CONF_UNIT_OF_MEASUREMENT: " ",
    },
    ATTR_TANK_HEATUP_MODE:{
        CONF_NAME: "Info heatupMode",
        CONF_TYPE: None,
        CONF_ICON: "mdi:information-outline",
        #CONF_DEVICE_CLASS: DEVICE_CLASS_ENERGY,
        CONF_UNIT_OF_MEASUREMENT: " ",
    },
    ATTR_TANK_IS_HOLIDAY_MODE_ACTIVE: {
        CONF_NAME: "Info Tank is Holiday Mode Active",
        CONF_TYPE: None,
        CONF_ICON: "mdi:information-outline",
        #CONF_DEVICE_CLASS: DEVICE_CLASS_ENERGY,
        CONF_UNIT_OF_MEASUREMENT: " ",
    },
    ATTR_TANK_IS_IN_EMERGENCY_STATE: {
        CONF_NAME: "Info Tank is In Emergency State",
        CONF_TYPE: None,
        CONF_ICON: "mdi:information-outline",
        #CONF_DEVICE_CLASS: DEVICE_CLASS_ENERGY,
        CONF_UNIT_OF_MEASUREMENT: " ",
    },
    ATTR_TANK_IS_IN_ERROR_STATE: {
        CONF_NAME: "Info Tank is In Error State",
        CONF_TYPE: None,
        CONF_ICON: "mdi:information-outline",
        #CONF_DEVICE_CLASS: DEVICE_CLASS_ENERGY,
        CONF_UNIT_OF_MEASUREMENT: " ",
    },
    ATTR_TANK_IS_IN_INSTALLER_STATE: {
        CONF_NAME: "Info Tank is In Installer State",
        CONF_TYPE: None,
        CONF_ICON: "mdi:information-outline",
        #CONF_DEVICE_CLASS: DEVICE_CLASS_ENERGY,
        CONF_UNIT_OF_MEASUREMENT: " ",
    },
    ATTR_TANK_IS_IN_WARNING_STATE: {
        CONF_NAME: "Info Tank is In Warning State",
        CONF_TYPE: None,
        CONF_ICON: "mdi:information-outline",
        #CONF_DEVICE_CLASS: DEVICE_CLASS_ENERGY,
        CONF_UNIT_OF_MEASUREMENT: " ",
    },
    ATTR_TANK_IS_POWERFUL_MODE_ACTIVE: {
        CONF_NAME: "Info Tank is Powerful Mode Active",
        CONF_TYPE: None,
        CONF_ICON: "mdi:information-outline",
        #CONF_DEVICE_CLASS: DEVICE_CLASS_ENERGY,
        CONF_UNIT_OF_MEASUREMENT: " ",
    },
        ATTR_TANK_ERROR_CODE: {
        CONF_NAME: "Info Tank Error Code",
        CONF_TYPE: None,
        CONF_ICON: "mdi:information-outline",
        #CONF_DEVICE_CLASS: DEVICE_CLASS_ENERGY,
        CONF_UNIT_OF_MEASUREMENT: " ",
    },
    ATTR_WIFI_STRENGTH: {
        CONF_NAME: "WiFi Strength",
        CONF_TYPE: SENSOR_TYPE_GATEWAY_DIAGNOSTIC,
        CONF_DEVICE_CLASS: DEVICE_CLASS_SIGNAL_STRENGTH,
        CONF_UNIT_OF_MEASUREMENT: SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
    },
    ATTR_WIFI_SSID: {
        CONF_NAME: "WiFi SSID",
        CONF_TYPE: SENSOR_TYPE_GATEWAY_DIAGNOSTIC,
        CONF_ICON: "mdi:access-point-network",
        CONF_DEVICE_CLASS: None,
        CONF_UNIT_OF_MEASUREMENT: None,
    },
    ATTR_LOCAL_SSID: {
        CONF_NAME: "Internal SSID",
        CONF_TYPE: SENSOR_TYPE_GATEWAY_DIAGNOSTIC,
        CONF_DEVICE_CLASS: None,
        CONF_UNIT_OF_MEASUREMENT: None,
    },
    ATTR_MAC_ADDRESS: {
        CONF_NAME: "Mac Address",
        CONF_TYPE: SENSOR_TYPE_GATEWAY_DIAGNOSTIC,
        CONF_DEVICE_CLASS: None,
        CONF_UNIT_OF_MEASUREMENT: None,
    },
    ATTR_SERIAL_NUMBER: {
        CONF_NAME: "Serial Number",
        CONF_TYPE: SENSOR_TYPE_GATEWAY_DIAGNOSTIC,
        CONF_ICON: "mdi:numeric",
        CONF_DEVICE_CLASS: None,
        CONF_UNIT_OF_MEASUREMENT: None,
    },
    ATTR_TANK_TARGET_TEMPERATURE: {
        CONF_NAME: "Tank target tempeature",
        CONF_TYPE: SENSOR_TYPE_TEMPERATURE,
        CONF_ICON: "mdi:bathtub-outline",
        CONF_DEVICE_CLASS: DEVICE_CLASS_TEMPERATURE,
        CONF_UNIT_OF_MEASUREMENT: TEMP_CELSIUS,
    },
}

CONF_UUID = "uuid"

KEY_MAC = "mac"
KEY_IP = "ip"

TIMEOUT = 60

