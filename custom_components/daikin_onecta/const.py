"""Constants for Daikin Oncecta."""
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
COORDINATOR = "coordinator"

OAUTH2_AUTHORIZE = "https://idp.onecta.daikineurope.com/v1/oidc/authorize"
OAUTH2_TOKEN = "https://idp.onecta.daikineurope.com/v1/oidc/token"

DAIKIN_DATA = "daikin_data"
DAIKIN_API = "daikin_api"
DAIKIN_DEVICES = "daikin_devices"
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

# This maps the NAME as listed in the Daikin JSON data to:
# - DEVICE_CLASS: home assistant device class, see
#   https://developers.home-assistant.io/docs/core/entity/sensor/#available-device-classes
# - UNIT_OF_MEASUREMENT:
# - ICON: Icon to be used
# - ENABLED_DEFAULT: Is the sensor enabled by default or not
VALUE_SENSOR_MAPPING = {
    "controlMode": {
        CONF_DEVICE_CLASS: None,
        CONF_STATE_CLASS: None,
        CONF_UNIT_OF_MEASUREMENT: None,
        CONF_ICON: "mdi:alphabetical",
        ENABLED_DEFAULT: True,
        ENTITY_CATEGORY: None,
    },
    "onOffMode": {
        CONF_DEVICE_CLASS: None,
        CONF_STATE_CLASS: None,
        CONF_UNIT_OF_MEASUREMENT: None,
        CONF_ICON: "mdi:toggle-switch-variant",
        ENABLED_DEFAULT: True,
        ENTITY_CATEGORY: None,
    },
    "operationMode": {
        CONF_DEVICE_CLASS: None,
        CONF_STATE_CLASS: None,
        CONF_UNIT_OF_MEASUREMENT: None,
        CONF_ICON: "mdi:alphabetical",
        ENABLED_DEFAULT: True,
        ENTITY_CATEGORY: None,
    },
    "airPurificationMode": {
        CONF_DEVICE_CLASS: None,
        CONF_STATE_CLASS: None,
        CONF_UNIT_OF_MEASUREMENT: None,
        CONF_ICON: "mdi:alphabetical",
        ENABLED_DEFAULT: True,
        ENTITY_CATEGORY: None,
    },
    "setpointMode": {
        CONF_DEVICE_CLASS: None,
        CONF_STATE_CLASS: None,
        CONF_UNIT_OF_MEASUREMENT: None,
        CONF_ICON: "mdi:alphabetical",
        ENABLED_DEFAULT: True,
        ENTITY_CATEGORY: None,
    },
    "heatupMode": {
        CONF_DEVICE_CLASS: None,
        CONF_STATE_CLASS: None,
        CONF_UNIT_OF_MEASUREMENT: None,
        CONF_ICON: "mdi:alphabetical",
        ENABLED_DEFAULT: True,
        ENTITY_CATEGORY: None,
    },
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
        CONF_DEVICE_CLASS: SensorDeviceClass.SIGNAL_STRENGTH,
        CONF_STATE_CLASS: SensorStateClass.MEASUREMENT,
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
        CONF_DEVICE_CLASS: BinarySensorDeviceClass.PROBLEM,
        CONF_STATE_CLASS: None,
        CONF_UNIT_OF_MEASUREMENT: None,
        CONF_ICON: "mdi:information-outline",
        ENABLED_DEFAULT: True,
        ENTITY_CATEGORY: EntityCategory.DIAGNOSTIC,
    },
    "isInWarningState": {
        CONF_DEVICE_CLASS: BinarySensorDeviceClass.PROBLEM,
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
        CONF_DEVICE_CLASS: BinarySensorDeviceClass.PROBLEM,
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
        CONF_DEVICE_CLASS: BinarySensorDeviceClass.PROBLEM,
        CONF_STATE_CLASS: None,
        CONF_UNIT_OF_MEASUREMENT: None,
        CONF_ICON: "mdi:information-outline",
        ENABLED_DEFAULT: True,
        ENTITY_CATEGORY: EntityCategory.DIAGNOSTIC,
    },
    "isInCautionState": {
        CONF_DEVICE_CLASS: BinarySensorDeviceClass.PROBLEM,
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
        CONF_DEVICE_CLASS: SensorDeviceClass.TEMPERATURE,
        CONF_STATE_CLASS: SensorStateClass.MEASUREMENT,
        CONF_UNIT_OF_MEASUREMENT: UnitOfTemperature.CELSIUS,
        CONF_ICON: "",
        ENABLED_DEFAULT: True,
        ENTITY_CATEGORY: None,
    },
    "outdoorTemperature": {
        CONF_DEVICE_CLASS: SensorDeviceClass.TEMPERATURE,
        CONF_STATE_CLASS: SensorStateClass.MEASUREMENT,
        CONF_UNIT_OF_MEASUREMENT: UnitOfTemperature.CELSIUS,
        CONF_ICON: "",
        ENABLED_DEFAULT: True,
        ENTITY_CATEGORY: None,
    },
    "leavingWaterTemperature": {
        CONF_DEVICE_CLASS: SensorDeviceClass.TEMPERATURE,
        CONF_STATE_CLASS: SensorStateClass.MEASUREMENT,
        CONF_UNIT_OF_MEASUREMENT: UnitOfTemperature.CELSIUS,
        CONF_ICON: "",
        ENABLED_DEFAULT: True,
        ENTITY_CATEGORY: None,
    },
    "tankTemperature": {
        CONF_DEVICE_CLASS: SensorDeviceClass.TEMPERATURE,
        CONF_STATE_CLASS: SensorStateClass.MEASUREMENT,
        CONF_UNIT_OF_MEASUREMENT: UnitOfTemperature.CELSIUS,
        CONF_ICON: "mdi:bathtub-outline",
        ENABLED_DEFAULT: True,
        ENTITY_CATEGORY: None,
    },
    "heatExchangerTemperature": {
        CONF_DEVICE_CLASS: SensorDeviceClass.TEMPERATURE,
        CONF_STATE_CLASS: SensorStateClass.MEASUREMENT,
        CONF_UNIT_OF_MEASUREMENT: UnitOfTemperature.CELSIUS,
        CONF_ICON: "",
        ENABLED_DEFAULT: True,
        ENTITY_CATEGORY: None,
    },
    "suctionTemperature": {
        CONF_DEVICE_CLASS: SensorDeviceClass.TEMPERATURE,
        CONF_STATE_CLASS: SensorStateClass.MEASUREMENT,
        CONF_UNIT_OF_MEASUREMENT: UnitOfTemperature.CELSIUS,
        CONF_ICON: "",
        ENABLED_DEFAULT: True,
        ENTITY_CATEGORY: None,
    },
    "deltaD": {
        CONF_DEVICE_CLASS: SensorDeviceClass.TEMPERATURE,
        CONF_STATE_CLASS: SensorStateClass.MEASUREMENT,
        CONF_UNIT_OF_MEASUREMENT: UnitOfTemperature.CELSIUS,
        CONF_ICON: "",
        ENABLED_DEFAULT: True,
        ENTITY_CATEGORY: None,
    },
    "dryKeepSetting": {
        CONF_DEVICE_CLASS: None,
        CONF_STATE_CLASS: None,
        CONF_UNIT_OF_MEASUREMENT: None,
        CONF_ICON: "mdi:water-percent",
        ENABLED_DEFAULT: True,
        ENTITY_CATEGORY: None,
    },
    "streamerMode": {
        CONF_DEVICE_CLASS: None,
        CONF_STATE_CLASS: None,
        CONF_UNIT_OF_MEASUREMENT: None,
        CONF_ICON: "hass:air-filter",
        ENABLED_DEFAULT: True,
        ENTITY_CATEGORY: None,
    },
    "powerfulMode": {
        CONF_DEVICE_CLASS: None,
        CONF_STATE_CLASS: None,
        CONF_UNIT_OF_MEASUREMENT: None,
        CONF_ICON: "mdi:rocket-launch",
        ENABLED_DEFAULT: True,
        ENTITY_CATEGORY: None,
    },
    "econoMode": {
        CONF_DEVICE_CLASS: None,
        CONF_STATE_CLASS: None,
        CONF_UNIT_OF_MEASUREMENT: None,
        CONF_ICON: "mdi:leaf",
        ENABLED_DEFAULT: True,
        ENTITY_CATEGORY: None,
    },
    "fanMotorRotationSpeed": {
        CONF_DEVICE_CLASS: None,
        CONF_STATE_CLASS: SensorStateClass.MEASUREMENT,
        CONF_UNIT_OF_MEASUREMENT: REVOLUTIONS_PER_MINUTE,
        CONF_ICON: "mdi:fan",
        ENABLED_DEFAULT: True,
        ENTITY_CATEGORY: None,
    },
    "ipAddress": {
        CONF_DEVICE_CLASS: None,
        CONF_STATE_CLASS: None,
        CONF_UNIT_OF_MEASUREMENT: None,
        CONF_ICON: "mdi:ip-network",
        ENABLED_DEFAULT: True,
        ENTITY_CATEGORY: EntityCategory.DIAGNOSTIC,
    },
    "name": {
        CONF_DEVICE_CLASS: None,
        CONF_STATE_CLASS: None,
        CONF_UNIT_OF_MEASUREMENT: None,
        CONF_ICON: "mdi:information-outline",
        ENABLED_DEFAULT: True,
        ENTITY_CATEGORY: EntityCategory.DIAGNOSTIC,
    },
    "modelInfo": {
        CONF_DEVICE_CLASS: None,
        CONF_STATE_CLASS: None,
        CONF_UNIT_OF_MEASUREMENT: None,
        CONF_ICON: "mdi:information-outline",
        ENABLED_DEFAULT: True,
        ENTITY_CATEGORY: EntityCategory.DIAGNOSTIC,
    },
    "dateTime": {
        CONF_DEVICE_CLASS: None,
        CONF_STATE_CLASS: None,
        CONF_UNIT_OF_MEASUREMENT: None,
        CONF_ICON: "mdi:information-outline",
        ENABLED_DEFAULT: True,
        ENTITY_CATEGORY: EntityCategory.DIAGNOSTIC,
    },
    "miconId": {
        CONF_DEVICE_CLASS: None,
        CONF_STATE_CLASS: None,
        CONF_UNIT_OF_MEASUREMENT: None,
        CONF_ICON: "mdi:information-outline",
        ENABLED_DEFAULT: True,
        ENTITY_CATEGORY: EntityCategory.DIAGNOSTIC,
    },
    "regionCode": {
        CONF_DEVICE_CLASS: None,
        CONF_STATE_CLASS: None,
        CONF_UNIT_OF_MEASUREMENT: None,
        CONF_ICON: "mdi:information-outline",
        ENABLED_DEFAULT: True,
        ENTITY_CATEGORY: EntityCategory.DIAGNOSTIC,
    },
    "errorCode": {
        CONF_DEVICE_CLASS: None,
        CONF_STATE_CLASS: None,
        CONF_UNIT_OF_MEASUREMENT: None,
        CONF_ICON: "mdi:information-outline",
        ENABLED_DEFAULT: True,
        ENTITY_CATEGORY: EntityCategory.DIAGNOSTIC,
    },
    "timeZone": {
        CONF_DEVICE_CLASS: None,
        CONF_STATE_CLASS: None,
        CONF_UNIT_OF_MEASUREMENT: None,
        CONF_ICON: "mdi:information-outline",
        ENABLED_DEFAULT: True,
        ENTITY_CATEGORY: EntityCategory.DIAGNOSTIC,
    },
    "roomHumidity": {
        CONF_DEVICE_CLASS: SensorDeviceClass.HUMIDITY,
        CONF_STATE_CLASS: SensorStateClass.MEASUREMENT,
        CONF_UNIT_OF_MEASUREMENT: PERCENTAGE,
        CONF_ICON: "mdi:water-percent",
        ENABLED_DEFAULT: True,
        ENTITY_CATEGORY: None,
    },
    "pm1Concentration": {
        CONF_DEVICE_CLASS: SensorDeviceClass.PM1,
        CONF_STATE_CLASS: SensorStateClass.MEASUREMENT,
        CONF_UNIT_OF_MEASUREMENT: CONCENTRATION_MICROGRAMS_PER_CUBIC_METER,
        CONF_ICON: "mdi:blur",
        ENABLED_DEFAULT: True,
        ENTITY_CATEGORY: None,
    },
    "pm25Concentration": {
        CONF_DEVICE_CLASS: SensorDeviceClass.PM25,
        CONF_STATE_CLASS: SensorStateClass.MEASUREMENT,
        CONF_UNIT_OF_MEASUREMENT: CONCENTRATION_MICROGRAMS_PER_CUBIC_METER,
        CONF_ICON: "mdi:blur",
        ENABLED_DEFAULT: True,
        ENTITY_CATEGORY: None,
    },
    "pm10Concentration": {
        CONF_DEVICE_CLASS: SensorDeviceClass.PM10,
        CONF_STATE_CLASS: SensorStateClass.MEASUREMENT,
        CONF_UNIT_OF_MEASUREMENT: CONCENTRATION_MICROGRAMS_PER_CUBIC_METER,
        CONF_ICON: "mdi:blur",
        ENABLED_DEFAULT: True,
        ENTITY_CATEGORY: None,
    },
}
