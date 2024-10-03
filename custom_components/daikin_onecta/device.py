import json
import logging

from homeassistant.helpers.device_registry import CONNECTION_NETWORK_MAC

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

        _LOGGER.info("Initialized Daikin Onecta Device '%s' (id %s)", self.name, self.id)

    @property
    def available(self) -> bool:
        result = False
        icu = self.daikin_data.get("isCloudConnectionUp")
        if icu is not None:
            result = icu["value"]
        return result

    def device_info(self):
        """Return a device description for device registry."""
        mac_add = ""
        model = ""
        sw_vers = ""
        model_id = self.daikin_data.get("deviceModel")
        supported_management_point_types = {"gateway"}
        management_points = self.daikin_data.get("managementPoints", [])
        for management_point in management_points:
            management_point_type = management_point["managementPointType"]
            if management_point_type in supported_management_point_types:
                mp = management_point.get("macAddress")
                if mp is not None:
                    mac_add = mp["value"]
                mi = management_point.get("modelInfo")
                if mi is not None:
                    model = mi["value"]
                fw = management_point.get("firmwareVersion")
                if fw is not None:
                    sw_vers = fw["value"]

        return {
            "identifiers": {
                # Serial numbers are unique identifiers within a specific domain
                (DOMAIN, self.id)
            },
            "connections": {(CONNECTION_NETWORK_MAC, mac_add)},
            "manufacturer": "Daikin",
            "model": model,
            "name": self.name,
            "model_id": model_id,
            "sw_version": sw_vers.replace("_", "."),
        }

    "Helper to merge the json, prevents invalid reads when other threads are reading the daikin_data"

    def merge_json(self, a: dict, b: dict, path=[]):
        for key in b:
            if key in a:
                if isinstance(a[key], dict) and isinstance(b[key], dict):
                    self.merge_json(a[key], b[key], path + [str(key)])
                else:
                    a[key] = b[key]
            else:
                a[key] = b[key]
        return a

    def setJsonData(self, desc):
        """Set a device description and parse/traverse data structure."""
        self.merge_json(self.daikin_data, desc)

    async def patch(self, id, embeddedId, dataPoint, dataPointPath, value):
        setPath = "/v1/gateway-devices/" + id + "/management-points/" + embeddedId + "/characteristics/" + dataPoint
        setBody = {"value": value}
        if dataPointPath:
            setBody["path"] = dataPointPath
        setOptions = json.dumps(setBody)

        _LOGGER.info("Path: " + setPath + " , options: %s", setOptions)

        res = await self.api.doBearerRequest("PATCH", setPath, setOptions)
        _LOGGER.debug("RES IS {}".format(res))

        return res

    async def post(self, id, embeddedId, dataPoint, value):
        setPath = "/v1/gateway-devices/" + id + "/management-points/" + embeddedId + "/" + dataPoint
        setOptions = json.dumps(value)

        _LOGGER.info("Path: " + setPath + " , options: %s", setOptions)

        res = await self.api.doBearerRequest("POST", setPath, setOptions)
        _LOGGER.debug("RES IS {}".format(res))

        return res

    async def put(self, id, embeddedId, dataPoint, value):
        setPath = "/v1/gateway-devices/" + id + "/management-points/" + embeddedId + "/" + dataPoint
        setOptions = json.dumps(value)

        _LOGGER.info("Path: " + setPath + " , options: %s", setOptions)

        res = await self.api.doBearerRequest("PUT", setPath, setOptions)
        _LOGGER.debug("RES IS {}".format(res))

        return res
