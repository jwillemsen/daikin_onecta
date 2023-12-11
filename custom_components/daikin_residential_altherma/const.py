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

from homeassistant.components.sensor import (
    CONF_STATE_CLASS,
    STATE_CLASS_MEASUREMENT,
)

from homeassistant.helpers.entity import (
    EntityCategory
)

DOMAIN = "daikin_residential_altherma"

CONF_TOKENSET = CONF_TOKEN + "set"

DAIKIN_DATA = "daikin_data"
DAIKIN_API = "daikin_api"
DAIKIN_DEVICES = "daikin_devices"
DAIKIN_DISCOVERY_NEW = "daikin_discovery_new_{}"

# MANAGEMENT POINTS
MP_CLIMATE = "climateControl"
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
ATTR_TARGET_LEAVINGWATER_OFFSET = "target_leavingwater_offset"
ATTR_TARGET_LEAVINGWATER_TEMPERATURE = "target_leavingwater_temperature"
ATTR_LEAVINGWATER_TEMPERATURE = "leavingWaterTemperature"
ATTR_OUTSIDE_TEMPERATURE = "outdoorTemperature"
ATTR_ROOM_TEMPERATURE = "roomTemperature"
ATTR_LEAVINGWATER_OFFSET = "leavingWaterOffset"
ATTR_TANK_TEMPERATURE = "tankTemperature"
ATTR_COOL_ENERGY = "cool_energy"
ATTR_HEAT_ENERGY = "heat_energy"
ATTR_HEAT_TANK_ENERGY = "heat_tank_energy"
ATTR_SETPOINT_MODE = "setpointMode"
ATTR_CONTROL_MODE = "controlMode"

ATTR_TANK_TARGET_TEMPERATURE = "targetTemperature"

ATTR_WIFI_SSID = "wifi_ssid"
ATTR_LOCAL_SSID = "local_ssid"

ATTR_STATE_ON = "on"
ATTR_STATE_OFF = "off"

SENSOR_TYPE_TEMPERATURE = "temperature"
SENSOR_TYPE_POWER = "power"
SENSOR_TYPE_ENERGY = "energy"
SENSOR_PERIOD_DAILY = "d"
SENSOR_PERIOD_WEEKLY = "w"
SENSOR_PERIOD_YEARLY = "m"
SENSOR_PERIODS = {
    SENSOR_PERIOD_DAILY: "Daily",
    SENSOR_PERIOD_WEEKLY: "Weekly",
    SENSOR_PERIOD_YEARLY: "Yearly",
}

FAN_FIXED = "fixed"
FAN_QUIET = "Silence"

ENABLED_DEFAULT = "Enabled"
STATE_CLASS = "STATE"
ENTITY_CATEGORY = "ENTITY_CATEGORY"

# This maps the NAME as listed in the Daikin JSON data to:
# - NAME: Postfix for the sensor name
# - DEVICE_CLASS: home assistant device class, see https://developers.home-assistant.io/docs/core/entity/sensor/#available-device-classes
# - UNIT_OF_MEASUREMENT:
# - ICON: Icon to be used
VALUE_SENSOR_MAPPING = {
    "serialNumber": {
        CONF_DEVICE_CLASS: None,
        CONF_STATE_CLASS: None,
        CONF_UNIT_OF_MEASUREMENT: None,
        CONF_ICON: "mdi:numeric",
        ENABLED_DEFAULT: True,
        ENTITY_CATEGORY: EntityCategory.DIAGNOSTIC,
    },
    "wifiConnectionSSID": {
        CONF_DEVICE_CLASS: None,
        CONF_STATE_CLASS: None,
        CONF_UNIT_OF_MEASUREMENT: None,
        CONF_ICON: "mdi:access-point-network",
        ENABLED_DEFAULT: True,
        ENTITY_CATEGORY: EntityCategory.DIAGNOSTIC,
    },
    "wifiConnectionStrength": {
        CONF_DEVICE_CLASS: DEVICE_CLASS_SIGNAL_STRENGTH,
        CONF_STATE_CLASS: STATE_CLASS_MEASUREMENT,
        CONF_UNIT_OF_MEASUREMENT: SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
        CONF_ICON: "mdi:wifi",
        ENABLED_DEFAULT: True,
        ENTITY_CATEGORY: EntityCategory.DIAGNOSTIC,
    },
    "ssid": {
        CONF_DEVICE_CLASS: None,
        CONF_STATE_CLASS: None,
        CONF_UNIT_OF_MEASUREMENT: None,
        CONF_ICON: "mdi:access-point-network",
        ENABLED_DEFAULT: True,
        ENTITY_CATEGORY: EntityCategory.DIAGNOSTIC,
    },
    "isHolidayModeActive": {
        CONF_DEVICE_CLASS: None,
        CONF_STATE_CLASS: None,
        CONF_UNIT_OF_MEASUREMENT: None,
        CONF_ICON: "mdi:information-outline",
        ENABLED_DEFAULT: True,
        ENTITY_CATEGORY: EntityCategory.DIAGNOSTIC,
    },
    "isInErrorState": {
        CONF_DEVICE_CLASS: None,
        CONF_STATE_CLASS: None,
        CONF_UNIT_OF_MEASUREMENT: None,
        CONF_ICON: "mdi:information-outline",
        ENABLED_DEFAULT: True,
        ENTITY_CATEGORY: EntityCategory.DIAGNOSTIC,
    },
    "isInWarningState": {
        CONF_DEVICE_CLASS: None,
        CONF_STATE_CLASS: None,
        CONF_UNIT_OF_MEASUREMENT: None,
        CONF_ICON: "mdi:information-outline",
        ENABLED_DEFAULT: True,
        ENTITY_CATEGORY: EntityCategory.DIAGNOSTIC,
    },
    "isInInstallerState": {
        CONF_DEVICE_CLASS: None,
        CONF_STATE_CLASS: None,
        CONF_UNIT_OF_MEASUREMENT: None,
        CONF_ICON: "mdi:information-outline",
        ENABLED_DEFAULT: True,
        ENTITY_CATEGORY: EntityCategory.DIAGNOSTIC,
    },
    "isInEmergencyState": {
        CONF_DEVICE_CLASS: None,
        CONF_STATE_CLASS: None,
        CONF_UNIT_OF_MEASUREMENT: None,
        CONF_ICON: "mdi:information-outline",
        ENABLED_DEFAULT: True,
        ENTITY_CATEGORY: EntityCategory.DIAGNOSTIC,
    },
    "isPowerfulModeActive": {
        CONF_DEVICE_CLASS: None,
        CONF_STATE_CLASS: None,
        CONF_UNIT_OF_MEASUREMENT: None,
        CONF_ICON: "mdi:information-outline",
        ENABLED_DEFAULT: True,
        ENTITY_CATEGORY: EntityCategory.DIAGNOSTIC,
    },
    "isCoolHeatMaster": {
        CONF_DEVICE_CLASS: None,
        CONF_STATE_CLASS: None,
        CONF_UNIT_OF_MEASUREMENT: None,
        CONF_ICON: "mdi:information-outline",
        ENABLED_DEFAULT: True,
        ENTITY_CATEGORY: EntityCategory.DIAGNOSTIC,
    },
    "isInModeConflict": {
        CONF_DEVICE_CLASS: None,
        CONF_STATE_CLASS: None,
        CONF_UNIT_OF_MEASUREMENT: None,
        CONF_ICON: "mdi:information-outline",
        ENABLED_DEFAULT: True,
        ENTITY_CATEGORY: EntityCategory.DIAGNOSTIC,
    },
    "isInCautionState": {
        CONF_DEVICE_CLASS: None,
        CONF_STATE_CLASS: None,
        CONF_UNIT_OF_MEASUREMENT: None,
        CONF_ICON: "mdi:information-outline",
        ENABLED_DEFAULT: True,
        ENTITY_CATEGORY: EntityCategory.DIAGNOSTIC,
    },
    "isLockFunctionEnabled": {
        CONF_DEVICE_CLASS: None,
        CONF_STATE_CLASS: None,
        CONF_UNIT_OF_MEASUREMENT: None,
        CONF_ICON: "mdi:information-outline",
        ENABLED_DEFAULT: True,
        ENTITY_CATEGORY: EntityCategory.DIAGNOSTIC,
    },
    "ledEnabled": {
        CONF_DEVICE_CLASS: None,
        CONF_STATE_CLASS: None,
        CONF_UNIT_OF_MEASUREMENT: None,
        CONF_ICON: "mdi:information-outline",
        ENABLED_DEFAULT: True,
        ENTITY_CATEGORY: EntityCategory.DIAGNOSTIC,
    },
    "iconId": {
        CONF_DEVICE_CLASS: None,
        CONF_STATE_CLASS: None,
        CONF_UNIT_OF_MEASUREMENT: None,
        CONF_ICON: "mdi:information-outline",
        ENABLED_DEFAULT: True,
        ENTITY_CATEGORY: EntityCategory.DIAGNOSTIC,
    },
    "firmwareVersion": {
        CONF_DEVICE_CLASS: None,
        CONF_STATE_CLASS: None,
        CONF_UNIT_OF_MEASUREMENT: None,
        CONF_ICON: "mdi:information-outline",
        ENABLED_DEFAULT: True,
        ENTITY_CATEGORY: EntityCategory.DIAGNOSTIC,
    },
    "eepromVersion": {
        CONF_DEVICE_CLASS: None,
        CONF_STATE_CLASS: None,
        CONF_UNIT_OF_MEASUREMENT: None,
        CONF_ICON: "mdi:information-outline",
        ENABLED_DEFAULT: True,
        ENTITY_CATEGORY: EntityCategory.DIAGNOSTIC,
    },
    "softwareVersion": {
        CONF_DEVICE_CLASS: None,
        CONF_STATE_CLASS: None,
        CONF_UNIT_OF_MEASUREMENT: None,
        CONF_ICON: "mdi:information-outline",
        ENABLED_DEFAULT: True,
        ENTITY_CATEGORY: EntityCategory.DIAGNOSTIC,
    },
    "isFirmwareUpdateSupported": {
        CONF_DEVICE_CLASS: None,
        CONF_STATE_CLASS: None,
        CONF_UNIT_OF_MEASUREMENT: None,
        CONF_ICON: "mdi:information-outline",
        ENABLED_DEFAULT: True,
        ENTITY_CATEGORY: EntityCategory.DIAGNOSTIC,
    },
    "daylightSavingTimeEnabled": {
        CONF_DEVICE_CLASS: None,
        CONF_STATE_CLASS: None,
        CONF_UNIT_OF_MEASUREMENT: None,
        CONF_ICON: "mdi:information-outline",
        ENABLED_DEFAULT: True,
        ENTITY_CATEGORY: EntityCategory.DIAGNOSTIC,
    },
    "macAddress": {
        CONF_DEVICE_CLASS: None,
        CONF_STATE_CLASS: None,
        CONF_UNIT_OF_MEASUREMENT: None,
        CONF_ICON: "mdi:information-outline",
        ENABLED_DEFAULT: True,
        ENTITY_CATEGORY: EntityCategory.DIAGNOSTIC,
    },
    "roomTemperature": {
        CONF_DEVICE_CLASS: DEVICE_CLASS_TEMPERATURE,
        CONF_STATE_CLASS: None,
        CONF_UNIT_OF_MEASUREMENT: TEMP_CELSIUS,
        CONF_ICON: "",
        ENABLED_DEFAULT: True,
        ENTITY_CATEGORY: None,
    },
    "outdoorTemperature": {
        CONF_DEVICE_CLASS: DEVICE_CLASS_TEMPERATURE,
        CONF_STATE_CLASS: None,
        CONF_UNIT_OF_MEASUREMENT: TEMP_CELSIUS,
        CONF_ICON: "",
        ENABLED_DEFAULT: True,
        ENTITY_CATEGORY: None,
    },
    "leavingWaterTemperature": {
        CONF_DEVICE_CLASS: DEVICE_CLASS_TEMPERATURE,
        CONF_STATE_CLASS: None,
        CONF_UNIT_OF_MEASUREMENT: TEMP_CELSIUS,
        CONF_ICON: "",
        ENABLED_DEFAULT: True,
        ENTITY_CATEGORY: None,
    },
    "tankTemperature": {
        CONF_DEVICE_CLASS: DEVICE_CLASS_TEMPERATURE,
        CONF_STATE_CLASS: None,
        CONF_UNIT_OF_MEASUREMENT: TEMP_CELSIUS,
        CONF_ICON: "mdi:bathtub-outline",
        ENABLED_DEFAULT: True,
        ENTITY_CATEGORY: None,
    },
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
    ATTR_TANK_TARGET_TEMPERATURE: {
        CONF_NAME: "Tank Target temperature",
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
    ATTR_OPERATION_MODE: {
        CONF_NAME: "Operation Mode",
        CONF_TYPE: None,
        CONF_ICON: "mdi:information-outline",
        CONF_UNIT_OF_MEASUREMENT: " ",
    },
    ATTR_SETPOINT_MODE: {
        CONF_NAME: "Info Setpoint Mode",
        CONF_TYPE: None,
        CONF_ICON: "mdi:information-outline",
        CONF_UNIT_OF_MEASUREMENT: " ",
    },
    ATTR_CONTROL_MODE: {
        CONF_NAME: "Info Control Mode",
        CONF_TYPE: None,
        CONF_ICON: "mdi:information-outline",
        CONF_UNIT_OF_MEASUREMENT: " ",
    },
}

CONF_UUID = "uuid"

KEY_MAC = "mac"
KEY_IP = "ip"

TIMEOUT = 60

