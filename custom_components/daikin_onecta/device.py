import json
import logging

from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.device_registry import CONNECTION_NETWORK_MAC
from homeassistant.helpers.device_registry import DeviceInfo

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


class DaikinOnectaDevice:
    """Class to represent and control one Daikin Onecta Device."""

    def __init__(self, jsonData, apiInstance):
        """Initialize a new Daikin Onecta Device."""
        self.api = apiInstance
        # get name from climateControl
        self.daikin_data = jsonData
        self.id = self.daikin_data["id"]
        self.name = self.daikin_data["deviceModel"]

        management_points = self.daikin_data.get("managementPoints", [])
        for management_point in management_points:
            if management_point["managementPointType"] == "climateControl":
                name = management_point["name"]["value"]
                if name:
                    self.name = name

        # Populated by async_register_ha_device() before any entity platform is set
        # up. Sub-entities (per-management-point devices in sensor/water_heater/
        # select/binary_sensor/switch/update) use this as via_device_id to link back
        # to this gateway device: the older via_device=(DOMAIN, identifier) form is
        # deprecated because identifiers are no longer guaranteed globally unique.
        self.ha_device_id: str | None = None

        _LOGGER.info("Initialized Daikin Onecta Device '%s' (id %s)", self.name, self.id)

    @property
    def available(self) -> bool:
        result = False
        icu = self.daikin_data.get("isCloudConnectionUp")
        if icu is not None:
            result = icu["value"]
        return result

    def fill_device_info(self, device_info, management_point_type):
        manufacturer = {"manufacturer": "Daikin"}
        device_info.update(**manufacturer)
        management_points = self.daikin_data.get("managementPoints", [])
        for management_point in management_points:
            if management_point_type == management_point["managementPointType"]:
                mp = management_point.get("eepromVersion")
                if mp is not None:
                    v = {"sw_version": mp["value"]}
                    device_info.update(**v)
                mp = management_point.get("modelInfo")
                if mp is not None:
                    v = {"model": mp["value"]}
                    device_info.update(**v)
                mp = management_point.get("firmwareVersion")
                if mp is not None:
                    v = {"sw_version": mp["value"]}
                    device_info.update(**v)
                mp = management_point.get("serialNumber")
                if mp is not None:
                    v = {"serial_number": mp["value"]}
                    device_info.update(**v)
                mp = management_point.get("softwareVersion")
                if mp is not None:
                    v = {"sw_version": mp["value"]}
                    device_info.update(**v)

    def device_info(self) -> DeviceInfo:
        """Return a device description for device registry."""
        mac_add = ""
        devicemodel = self.daikin_data.get("deviceModel")
        supported_management_point_types = {"gateway"}
        management_points = self.daikin_data.get("managementPoints", [])
        for management_point in management_points:
            management_point_type = management_point["managementPointType"]
            if management_point_type in supported_management_point_types:
                mp = management_point.get("macAddress")
                if mp is not None:
                    mac_add = mp["value"]

        info = DeviceInfo(
            identifiers={
                # Serial numbers are unique identifiers within a specific domain
                (DOMAIN, self.id)
            },
            connections={(CONNECTION_NETWORK_MAC, mac_add)},
            name=self.name,
            model_id=devicemodel,
        )

        self.fill_device_info(info, "gateway")

        return info

    def async_register_ha_device(self, hass: HomeAssistant, config_entry) -> None:
        """Eagerly create/update this device in the device registry.

        Called once from the coordinator, before any entity platform is set up
        (platforms are forwarded concurrently, so entity __init__ order across
        platforms can't be relied on). This guarantees self.ha_device_id is
        already populated by the time any platform builds a sub-device's
        DeviceInfo with via_device_id=self.ha_device_id.
        """
        device_registry = dr.async_get(hass)
        entry = device_registry.async_get_or_create(
            config_entry_id=config_entry.entry_id,
            **self.device_info(),
        )
        self.ha_device_id = entry.id

    def setJsonData(self, desc):
        """Overwrite the json data for this device."""
        self.daikin_data = desc
        _LOGGER.debug("Device '%s' received new data from the Daikin cloud, isCloudConnectionUp '%s'", self.name, self.available)

    async def patch(self, id, embeddedId, dataPoint, dataPointPath, value):
        setPath = "/v1/gateway-devices/" + id + "/management-points/" + embeddedId + "/characteristics/" + dataPoint
        setBody = {"value": value}
        if dataPointPath:
            setBody["path"] = dataPointPath
        setOptions = json.dumps(setBody)

        _LOGGER.debug("Path: %s , options: %s", setPath, setOptions)

        res = await self.api.doBearerRequest("PATCH", setPath, setOptions)

        _LOGGER.debug(f"Result: {res}")

        return res

    async def post(self, id, embeddedId, dataPoint, value):
        setPath = "/v1/gateway-devices/" + id + "/management-points/" + embeddedId + "/" + dataPoint
        setOptions = json.dumps(value)

        _LOGGER.debug("Path: %s , options: %s", setPath, setOptions)

        res = await self.api.doBearerRequest("POST", setPath, setOptions)

        _LOGGER.debug(f"Result: {res}")

        return res

    async def put(self, id, embeddedId, dataPoint, value=None):
        setPath = "/v1/gateway-devices/" + id + "/management-points/" + embeddedId + "/" + dataPoint
        setOptions = None
        if value is not None:
            setOptions = json.dumps(value)

        _LOGGER.debug("Path: %s , options: %s", setPath, setOptions)

        res = await self.api.doBearerRequest("PUT", setPath, setOptions)

        _LOGGER.debug(f"Result: {res}")

        return res
