import datetime
import logging
import json

from homeassistant.util import Throttle

from homeassistant.helpers.device_registry import CONNECTION_NETWORK_MAC
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

class DaikinResidentialDevice:
    """Class to represent and control one Daikin Residential Device."""

    def __init__(self, jsonData, apiInstance):
        """Initialize a new Daikin Residential Device."""
        self.api = apiInstance
        self.setJsonData(jsonData)
        # get name from climateControl
        self._available = True
        self.daikin_data = jsonData
        self.name = self.daikin_data["deviceModel"]

        managementPoints = self.daikin_data.get("managementPoints", [])
        for management_point in managementPoints:
            management_point_type = management_point["managementPointType"]
            if management_point_type == "climateControl":
                self.name = management_point["name"]["value"]

        _LOGGER.info("Initialized Daikin Residential Device '%s' (id %s)", self.name, self.getId())

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        try:
            return self.daikin_data["isCloudConnectionUp"]["value"]
        except Exception:
            return False

    def device_info(self):
        """Return a device description for device registry."""
        mac_add = ""
        model = ""
        sw_vers = ""
        name = ""
        supported_management_point_types = {'gateway'}
        managementPoints = self.daikin_data.get("managementPoints", [])
        for management_point in managementPoints:
            management_point_type = management_point["managementPointType"]
            if  management_point_type in supported_management_point_types:
                mac_add = management_point["macAddress"]["value"]
                model = management_point["modelInfo"]["value"]
                sw_vers = management_point["firmwareVersion"]["value"]
            if management_point_type == "climateControl":
                name = management_point["name"]["value"]

        return {
            "identifiers": {
                # Serial numbers are unique identifiers within a specific domain
                (DOMAIN, self.getId())
            },
            "connections": {
                (CONNECTION_NETWORK_MAC, mac_add)
            },
            "manufacturer": "Daikin",
            "model": model,
            "name": name,
            "sw_version": sw_vers.replace("_", "."),
        }

    def setJsonData(self, desc):
        """Set a device description and parse/traverse data structure."""
        self.daikin_data = desc

    def daikin_data(self):
        return self.daikin_data

    def getId(self):
        """Get Daikin Device UUID."""
        return self.daikin_data["id"]

    def getName(self):
        managementPoints = self.daikin_data.get("managementPoints", [])
        for management_point in managementPoints:
            management_point_type = management_point["managementPointType"]
            if management_point_type == "climateControl":
                self.name = management_point["name"]["value"]
        return self.name

    def getDescription(self):
        """Get the original Daikin Device Description."""
        return self.daikin_data

    def getLastUpdated(self):
        """Get the timestamp when data were last updated."""
        return self.daikin_data["lastUpdateReceived"]

    async def set_path(self, id, embeddedId, dataPoint, dataPointPath, value):
        setPath = (
            "/v1/gateway-devices/"
            + id
            + "/management-points/"
            + embeddedId
            + "/characteristics/"
            + dataPoint
        )
        setBody = {"value": value}
        if dataPointPath != "":
            setBody["path"] = dataPointPath
        setOptions = {"method": "PATCH", "json": json.dumps(setBody)}

        _LOGGER.info("Path: " + setPath + " , options: %s", setOptions)

        res = await self.api.doBearerRequest(setPath, setOptions)
        _LOGGER.debug("RES IS {}".format(res))

        return res
