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

ATTR_PRESET_MODE = "preset_mode"
ATTR_OPERATION_MODE = "operation_mode"
ATTR_TARGET_ROOM_TEMPERATURE = "target_room_temperature"
ATTR_TARGET_LEAVINGWATER_OFFSET = "target_leavingwater_offset"
ATTR_TARGET_LEAVINGWATER_TEMPERATURE = "target_leavingwater_temperature"
ATTR_LEAVINGWATER_TEMPERATURE = "leavingWaterTemperature"
ATTR_OUTSIDE_TEMPERATURE = "outdoorTemperature"
ATTR_ROOM_TEMPERATURE = "roomTemperature"
ATTR_LEAVINGWATER_OFFSET = "leavingWaterOffset"

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
FAN_QUIET = "silent"

ENABLED_DEFAULT = "Enabled"
STATE_CLASS = "STATE"
ENTITY_CATEGORY = "ENTITY_CATEGORY"

# This maps the NAME as listed in the Daikin JSON data to:
# - DEVICE_CLASS: home assistant device class, see https://developers.home-assistant.io/docs/core/entity/sensor/#available-device-classes
# - UNIT_OF_MEASUREMENT:
# - ICON: Icon to be used
# - ENABLED_DEFAULT: Is the sensor enabled by default or not
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
    "heatExchangerTemperature": {
        CONF_DEVICE_CLASS: DEVICE_CLASS_TEMPERATURE,
        CONF_STATE_CLASS: None,
        CONF_UNIT_OF_MEASUREMENT: TEMP_CELSIUS,
        CONF_ICON: "",
        ENABLED_DEFAULT: True,
        ENTITY_CATEGORY: None,
    },
    "suctionTemperature": {
        CONF_DEVICE_CLASS: DEVICE_CLASS_TEMPERATURE,
        CONF_STATE_CLASS: None,
        CONF_UNIT_OF_MEASUREMENT: TEMP_CELSIUS,
        CONF_ICON: "",
        ENABLED_DEFAULT: True,
        ENTITY_CATEGORY: None,
    },
}

TIMEOUT = 60
