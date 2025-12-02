"""Constants for Daikin Onecta."""
from homeassistant.components.binary_sensor import BinarySensorDeviceClass
from homeassistant.components.sensor import CONF_STATE_CLASS
from homeassistant.components.sensor import SensorDeviceClass
from homeassistant.components.sensor import SensorStateClass
from homeassistant.const import CONCENTRATION_MICROGRAMS_PER_CUBIC_METER
from homeassistant.const import CONF_DEVICE_CLASS
from homeassistant.const import CONF_ICON
from homeassistant.const import CONF_UNIT_OF_MEASUREMENT
from homeassistant.const import PERCENTAGE
from homeassistant.const import REVOLUTIONS_PER_MINUTE
from homeassistant.const import SIGNAL_STRENGTH_DECIBELS_MILLIWATT
from homeassistant.const import UnitOfTemperature
from homeassistant.helpers.entity import EntityCategory


DOMAIN = "daikin_onecta"

OAUTH2_AUTHORIZE = "https://idp.onecta.daikineurope.com/v1/oidc/authorize"
OAUTH2_TOKEN = "https://idp.onecta.daikineurope.com/v1/oidc/token"

DAIKIN_API_URL = "https://api.onecta.daikineurope.com"

SCHEDULE_OFF = "off"

FANMODE_FIXED = "fixed"

SENSOR_PERIOD_DAILY = "d"
SENSOR_PERIOD_WEEKLY = "w"
SENSOR_PERIOD_YEARLY = "m"
SENSOR_PERIODS = {
    SENSOR_PERIOD_DAILY: "Daily",
    SENSOR_PERIOD_WEEKLY: "Weekly",
    SENSOR_PERIOD_YEARLY: "Yearly",
}

ENABLED_DEFAULT = "Enabled"
STATE_CLASS = "STATE"
ENTITY_CATEGORY = "ENTITY_CATEGORY"
TRANSLATION_KEY = "TranslationKey"

# This maps the NAME as listed in the Daikin JSON data to:
# - DEVICE_CLASS: home assistant device class, see
#   https://developers.home-assistant.io/docs/core/entity/sensor/#available-device-classes
# - UNIT_OF_MEASUREMENT:
# - ICON: Icon to be used
# - ENABLED_DEFAULT: Is the sensor enabled by default or not
# - TRANSLATION_KEY: Translation key
VALUE_SENSOR_MAPPING = {
    "schedule": {
        CONF_DEVICE_CLASS: None,
        CONF_STATE_CLASS: None,
        CONF_UNIT_OF_MEASUREMENT: None,
        CONF_ICON: "mdi:calendar-clock",
        ENABLED_DEFAULT: True,
        ENTITY_CATEGORY: None,
        TRANSLATION_KEY: "schedule",
    },
    "controlMode": {
        CONF_DEVICE_CLASS: None,
        CONF_STATE_CLASS: None,
        CONF_UNIT_OF_MEASUREMENT: None,
        CONF_ICON: "mdi:alphabetical",
        ENABLED_DEFAULT: True,
        ENTITY_CATEGORY: None,
        TRANSLATION_KEY: "controlmode",
    },
    "onOffMode": {
        CONF_DEVICE_CLASS: None,
        CONF_STATE_CLASS: None,
        CONF_UNIT_OF_MEASUREMENT: None,
        CONF_ICON: "mdi:toggle-switch-variant",
        ENABLED_DEFAULT: True,
        ENTITY_CATEGORY: None,
        TRANSLATION_KEY: "onoffmode",
    },
    "operationMode": {
        CONF_DEVICE_CLASS: None,
        CONF_STATE_CLASS: None,
        CONF_UNIT_OF_MEASUREMENT: None,
        CONF_ICON: "mdi:alphabetical",
        ENABLED_DEFAULT: True,
        ENTITY_CATEGORY: None,
        TRANSLATION_KEY: "operationmode",
    },
    "airPurificationMode": {
        CONF_DEVICE_CLASS: None,
        CONF_STATE_CLASS: None,
        CONF_UNIT_OF_MEASUREMENT: None,
        CONF_ICON: "mdi:alphabetical",
        ENABLED_DEFAULT: True,
        ENTITY_CATEGORY: None,
        TRANSLATION_KEY: "airpurificationmode",
    },
    "setpointMode": {
        CONF_DEVICE_CLASS: None,
        CONF_STATE_CLASS: None,
        CONF_UNIT_OF_MEASUREMENT: None,
        CONF_ICON: "mdi:alphabetical",
        ENABLED_DEFAULT: True,
        ENTITY_CATEGORY: None,
        TRANSLATION_KEY: "setpointmode",
    },
    "heatupMode": {
        CONF_DEVICE_CLASS: None,
        CONF_STATE_CLASS: None,
        CONF_UNIT_OF_MEASUREMENT: None,
        CONF_ICON: "mdi:alphabetical",
        ENABLED_DEFAULT: True,
        ENTITY_CATEGORY: None,
        TRANSLATION_KEY: "heatupmode",
    },
    "wifiConnectionSSID": {
        CONF_DEVICE_CLASS: None,
        CONF_STATE_CLASS: None,
        CONF_UNIT_OF_MEASUREMENT: None,
        CONF_ICON: "mdi:access-point-network",
        ENABLED_DEFAULT: True,
        ENTITY_CATEGORY: EntityCategory.DIAGNOSTIC,
        TRANSLATION_KEY: "wificonnectionssid",
    },
    "wifiConnectionStrength": {
        CONF_DEVICE_CLASS: SensorDeviceClass.SIGNAL_STRENGTH,
        CONF_STATE_CLASS: SensorStateClass.MEASUREMENT,
        CONF_UNIT_OF_MEASUREMENT: SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
        CONF_ICON: "mdi:wifi",
        ENABLED_DEFAULT: True,
        ENTITY_CATEGORY: EntityCategory.DIAGNOSTIC,
        TRANSLATION_KEY: "wificonnectionstrength",
    },
    "ssid": {
        CONF_DEVICE_CLASS: None,
        CONF_STATE_CLASS: None,
        CONF_UNIT_OF_MEASUREMENT: None,
        CONF_ICON: "mdi:access-point-network",
        ENABLED_DEFAULT: True,
        ENTITY_CATEGORY: EntityCategory.DIAGNOSTIC,
        TRANSLATION_KEY: "ssid",
    },
    "isHolidayModeActive": {
        CONF_DEVICE_CLASS: None,
        CONF_STATE_CLASS: None,
        CONF_UNIT_OF_MEASUREMENT: None,
        CONF_ICON: "mdi:information-outline",
        ENABLED_DEFAULT: True,
        ENTITY_CATEGORY: EntityCategory.DIAGNOSTIC,
        TRANSLATION_KEY: "isholidaymodeactive",
    },
    "isInErrorState": {
        CONF_DEVICE_CLASS: BinarySensorDeviceClass.PROBLEM,
        CONF_STATE_CLASS: None,
        CONF_UNIT_OF_MEASUREMENT: None,
        CONF_ICON: "mdi:information-outline",
        ENABLED_DEFAULT: True,
        ENTITY_CATEGORY: EntityCategory.DIAGNOSTIC,
        TRANSLATION_KEY: "isinerrorstate",
    },
    "isInWarningState": {
        CONF_DEVICE_CLASS: BinarySensorDeviceClass.PROBLEM,
        CONF_STATE_CLASS: None,
        CONF_UNIT_OF_MEASUREMENT: None,
        CONF_ICON: "mdi:information-outline",
        ENABLED_DEFAULT: True,
        ENTITY_CATEGORY: EntityCategory.DIAGNOSTIC,
        TRANSLATION_KEY: "isinwarningstate",
    },
    "isInInstallerState": {
        CONF_DEVICE_CLASS: None,
        CONF_STATE_CLASS: None,
        CONF_UNIT_OF_MEASUREMENT: None,
        CONF_ICON: "mdi:information-outline",
        ENABLED_DEFAULT: True,
        ENTITY_CATEGORY: EntityCategory.DIAGNOSTIC,
        TRANSLATION_KEY: "isininstallerstate",
    },
    "isInEmergencyState": {
        CONF_DEVICE_CLASS: BinarySensorDeviceClass.PROBLEM,
        CONF_STATE_CLASS: None,
        CONF_UNIT_OF_MEASUREMENT: None,
        CONF_ICON: "mdi:information-outline",
        ENABLED_DEFAULT: True,
        ENTITY_CATEGORY: EntityCategory.DIAGNOSTIC,
        TRANSLATION_KEY: "isinemergencystate",
    },
    "isPowerfulModeActive": {
        CONF_DEVICE_CLASS: None,
        CONF_STATE_CLASS: None,
        CONF_UNIT_OF_MEASUREMENT: None,
        CONF_ICON: "mdi:information-outline",
        ENABLED_DEFAULT: True,
        ENTITY_CATEGORY: EntityCategory.DIAGNOSTIC,
        TRANSLATION_KEY: "ispowerfulmodeactive",
    },
    "isCoolHeatMaster": {
        CONF_DEVICE_CLASS: None,
        CONF_STATE_CLASS: None,
        CONF_UNIT_OF_MEASUREMENT: None,
        CONF_ICON: "mdi:information-outline",
        ENABLED_DEFAULT: True,
        ENTITY_CATEGORY: EntityCategory.DIAGNOSTIC,
        TRANSLATION_KEY: "iscoolheatmaster",
    },
    "isInModeConflict": {
        CONF_DEVICE_CLASS: BinarySensorDeviceClass.PROBLEM,
        CONF_STATE_CLASS: None,
        CONF_UNIT_OF_MEASUREMENT: None,
        CONF_ICON: "mdi:information-outline",
        ENABLED_DEFAULT: True,
        ENTITY_CATEGORY: EntityCategory.DIAGNOSTIC,
        TRANSLATION_KEY: "isinmodeconflict",
    },
    "isInCautionState": {
        CONF_DEVICE_CLASS: BinarySensorDeviceClass.PROBLEM,
        CONF_STATE_CLASS: None,
        CONF_UNIT_OF_MEASUREMENT: None,
        CONF_ICON: "mdi:information-outline",
        ENABLED_DEFAULT: True,
        ENTITY_CATEGORY: EntityCategory.DIAGNOSTIC,
        TRANSLATION_KEY: "isincautionstate",
    },
    "isLockFunctionEnabled": {
        CONF_DEVICE_CLASS: None,
        CONF_STATE_CLASS: None,
        CONF_UNIT_OF_MEASUREMENT: None,
        CONF_ICON: "mdi:information-outline",
        ENABLED_DEFAULT: True,
        ENTITY_CATEGORY: EntityCategory.DIAGNOSTIC,
        TRANSLATION_KEY: "islockfunctionenabled",
    },
    "ledEnabled": {
        CONF_DEVICE_CLASS: None,
        CONF_STATE_CLASS: None,
        CONF_UNIT_OF_MEASUREMENT: None,
        CONF_ICON: "mdi:information-outline",
        ENABLED_DEFAULT: True,
        ENTITY_CATEGORY: EntityCategory.DIAGNOSTIC,
        TRANSLATION_KEY: "ledenabled",
    },
    "isFirmwareUpdateSupported": {
        CONF_DEVICE_CLASS: None,
        CONF_STATE_CLASS: None,
        CONF_UNIT_OF_MEASUREMENT: None,
        CONF_ICON: "mdi:information-outline",
        ENABLED_DEFAULT: True,
        ENTITY_CATEGORY: EntityCategory.DIAGNOSTIC,
        TRANSLATION_KEY: "isfirmwareupdatesupported",
    },
    "daylightSavingTimeEnabled": {
        CONF_DEVICE_CLASS: None,
        CONF_STATE_CLASS: None,
        CONF_UNIT_OF_MEASUREMENT: None,
        CONF_ICON: "mdi:information-outline",
        ENABLED_DEFAULT: True,
        ENTITY_CATEGORY: EntityCategory.DIAGNOSTIC,
        TRANSLATION_KEY: "daylightsavingtimeenabled",
    },
    "roomTemperature": {
        CONF_DEVICE_CLASS: SensorDeviceClass.TEMPERATURE,
        CONF_STATE_CLASS: SensorStateClass.MEASUREMENT,
        CONF_UNIT_OF_MEASUREMENT: UnitOfTemperature.CELSIUS,
        CONF_ICON: "",
        ENABLED_DEFAULT: True,
        ENTITY_CATEGORY: None,
        TRANSLATION_KEY: "roomtemperature",
    },
    "outdoorTemperature": {
        CONF_DEVICE_CLASS: SensorDeviceClass.TEMPERATURE,
        CONF_STATE_CLASS: SensorStateClass.MEASUREMENT,
        CONF_UNIT_OF_MEASUREMENT: UnitOfTemperature.CELSIUS,
        CONF_ICON: "",
        ENABLED_DEFAULT: True,
        ENTITY_CATEGORY: None,
        TRANSLATION_KEY: "outdoortemperature",
    },
    "leavingWaterTemperature": {
        CONF_DEVICE_CLASS: SensorDeviceClass.TEMPERATURE,
        CONF_STATE_CLASS: SensorStateClass.MEASUREMENT,
        CONF_UNIT_OF_MEASUREMENT: UnitOfTemperature.CELSIUS,
        CONF_ICON: "",
        ENABLED_DEFAULT: True,
        ENTITY_CATEGORY: None,
        TRANSLATION_KEY: "leavingwatertemperature",
    },
    "leavingWaterOffset": {
        CONF_DEVICE_CLASS: SensorDeviceClass.TEMPERATURE,
        CONF_STATE_CLASS: SensorStateClass.MEASUREMENT,
        CONF_UNIT_OF_MEASUREMENT: UnitOfTemperature.CELSIUS,
        CONF_ICON: "",
        ENABLED_DEFAULT: True,
        ENTITY_CATEGORY: None,
        TRANSLATION_KEY: "leavingwateroffset",
    },
    "calculatedLeavingWaterTemperature": {
        CONF_DEVICE_CLASS: SensorDeviceClass.TEMPERATURE,
        CONF_STATE_CLASS: SensorStateClass.MEASUREMENT,
        CONF_UNIT_OF_MEASUREMENT: UnitOfTemperature.CELSIUS,
        CONF_ICON: "",
        ENABLED_DEFAULT: True,
        ENTITY_CATEGORY: None,
        TRANSLATION_KEY: "calculatedleavingwatertemperature",
    },
    "tankTemperature": {
        CONF_DEVICE_CLASS: SensorDeviceClass.TEMPERATURE,
        CONF_STATE_CLASS: SensorStateClass.MEASUREMENT,
        CONF_UNIT_OF_MEASUREMENT: UnitOfTemperature.CELSIUS,
        CONF_ICON: "mdi:bathtub-outline",
        ENABLED_DEFAULT: True,
        ENTITY_CATEGORY: None,
        TRANSLATION_KEY: "tanktemperature",
    },
    "heatExchangerTemperature": {
        CONF_DEVICE_CLASS: SensorDeviceClass.TEMPERATURE,
        CONF_STATE_CLASS: SensorStateClass.MEASUREMENT,
        CONF_UNIT_OF_MEASUREMENT: UnitOfTemperature.CELSIUS,
        CONF_ICON: "",
        ENABLED_DEFAULT: True,
        ENTITY_CATEGORY: None,
        TRANSLATION_KEY: "heatexchangertemperature",
    },
    "suctionTemperature": {
        CONF_DEVICE_CLASS: SensorDeviceClass.TEMPERATURE,
        CONF_STATE_CLASS: SensorStateClass.MEASUREMENT,
        CONF_UNIT_OF_MEASUREMENT: UnitOfTemperature.CELSIUS,
        CONF_ICON: "",
        ENABLED_DEFAULT: True,
        ENTITY_CATEGORY: None,
        TRANSLATION_KEY: "suctiontemperature",
    },
    "deltaD": {
        CONF_DEVICE_CLASS: SensorDeviceClass.TEMPERATURE,
        CONF_STATE_CLASS: SensorStateClass.MEASUREMENT,
        CONF_UNIT_OF_MEASUREMENT: UnitOfTemperature.CELSIUS,
        CONF_ICON: "",
        ENABLED_DEFAULT: True,
        ENTITY_CATEGORY: None,
        TRANSLATION_KEY: "deltad",
    },
    "dryKeepSetting": {
        CONF_DEVICE_CLASS: None,
        CONF_STATE_CLASS: None,
        CONF_UNIT_OF_MEASUREMENT: None,
        CONF_ICON: "mdi:water-percent",
        ENABLED_DEFAULT: True,
        ENTITY_CATEGORY: None,
        TRANSLATION_KEY: "drykeepsetting",
    },
    "streamerMode": {
        CONF_DEVICE_CLASS: None,
        CONF_STATE_CLASS: None,
        CONF_UNIT_OF_MEASUREMENT: None,
        CONF_ICON: "hass:air-filter",
        ENABLED_DEFAULT: True,
        ENTITY_CATEGORY: None,
        TRANSLATION_KEY: "streamermode",
    },
    "powerfulMode": {
        CONF_DEVICE_CLASS: None,
        CONF_STATE_CLASS: None,
        CONF_UNIT_OF_MEASUREMENT: None,
        CONF_ICON: "mdi:rocket-launch",
        ENABLED_DEFAULT: True,
        ENTITY_CATEGORY: None,
        TRANSLATION_KEY: "powerfulmode",
    },
    "econoMode": {
        CONF_DEVICE_CLASS: None,
        CONF_STATE_CLASS: None,
        CONF_UNIT_OF_MEASUREMENT: None,
        CONF_ICON: "mdi:leaf",
        ENABLED_DEFAULT: True,
        ENTITY_CATEGORY: None,
        TRANSLATION_KEY: "economode",
    },
    "fanMotorRotationSpeed": {
        CONF_DEVICE_CLASS: None,
        CONF_STATE_CLASS: SensorStateClass.MEASUREMENT,
        CONF_UNIT_OF_MEASUREMENT: REVOLUTIONS_PER_MINUTE,
        CONF_ICON: "mdi:fan",
        ENABLED_DEFAULT: True,
        ENTITY_CATEGORY: None,
        TRANSLATION_KEY: "fanmotorrotationspeed",
    },
    "ipAddress": {
        CONF_DEVICE_CLASS: None,
        CONF_STATE_CLASS: None,
        CONF_UNIT_OF_MEASUREMENT: None,
        CONF_ICON: "mdi:ip-network",
        ENABLED_DEFAULT: True,
        ENTITY_CATEGORY: EntityCategory.DIAGNOSTIC,
        TRANSLATION_KEY: "ipaddress",
    },
    "dateTime": {
        CONF_DEVICE_CLASS: None,
        CONF_STATE_CLASS: None,
        CONF_UNIT_OF_MEASUREMENT: None,
        CONF_ICON: "mdi:information-outline",
        ENABLED_DEFAULT: True,
        ENTITY_CATEGORY: EntityCategory.DIAGNOSTIC,
        TRANSLATION_KEY: "datetime",
    },
    "regionCode": {
        CONF_DEVICE_CLASS: None,
        CONF_STATE_CLASS: None,
        CONF_UNIT_OF_MEASUREMENT: None,
        CONF_ICON: "mdi:information-outline",
        ENABLED_DEFAULT: True,
        ENTITY_CATEGORY: EntityCategory.DIAGNOSTIC,
        TRANSLATION_KEY: "regioncode",
    },
    "errorCode": {
        CONF_DEVICE_CLASS: None,
        CONF_STATE_CLASS: None,
        CONF_UNIT_OF_MEASUREMENT: None,
        CONF_ICON: "mdi:information-outline",
        ENABLED_DEFAULT: True,
        ENTITY_CATEGORY: EntityCategory.DIAGNOSTIC,
        TRANSLATION_KEY: "errorcode",
    },
    "timeZone": {
        CONF_DEVICE_CLASS: None,
        CONF_STATE_CLASS: None,
        CONF_UNIT_OF_MEASUREMENT: None,
        CONF_ICON: "mdi:information-outline",
        ENABLED_DEFAULT: True,
        ENTITY_CATEGORY: EntityCategory.DIAGNOSTIC,
        TRANSLATION_KEY: "timezone",
    },
    "roomHumidity": {
        CONF_DEVICE_CLASS: SensorDeviceClass.HUMIDITY,
        CONF_STATE_CLASS: SensorStateClass.MEASUREMENT,
        CONF_UNIT_OF_MEASUREMENT: PERCENTAGE,
        CONF_ICON: "mdi:water-percent",
        ENABLED_DEFAULT: True,
        ENTITY_CATEGORY: None,
        TRANSLATION_KEY: "roomhumidity",
    },
    "pm1Concentration": {
        CONF_DEVICE_CLASS: SensorDeviceClass.PM1,
        CONF_STATE_CLASS: SensorStateClass.MEASUREMENT,
        CONF_UNIT_OF_MEASUREMENT: CONCENTRATION_MICROGRAMS_PER_CUBIC_METER,
        CONF_ICON: "mdi:blur",
        ENABLED_DEFAULT: True,
        ENTITY_CATEGORY: None,
        TRANSLATION_KEY: "pm1concentration",
    },
    "pm25Concentration": {
        CONF_DEVICE_CLASS: SensorDeviceClass.PM25,
        CONF_STATE_CLASS: SensorStateClass.MEASUREMENT,
        CONF_UNIT_OF_MEASUREMENT: CONCENTRATION_MICROGRAMS_PER_CUBIC_METER,
        CONF_ICON: "mdi:blur",
        ENABLED_DEFAULT: True,
        ENTITY_CATEGORY: None,
        TRANSLATION_KEY: "pm25concentration",
    },
    "pm10Concentration": {
        CONF_DEVICE_CLASS: SensorDeviceClass.PM10,
        CONF_STATE_CLASS: SensorStateClass.MEASUREMENT,
        CONF_UNIT_OF_MEASUREMENT: CONCENTRATION_MICROGRAMS_PER_CUBIC_METER,
        CONF_ICON: "mdi:blur",
        ENABLED_DEFAULT: True,
        ENTITY_CATEGORY: None,
        TRANSLATION_KEY: "pm10concentration",
    },
}
