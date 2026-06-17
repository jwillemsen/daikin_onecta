import json
import logging
from datetime import datetime
from datetime import timedelta

from homeassistant.helpers.device_registry import CONNECTION_NETWORK_MAC
from homeassistant.helpers.device_registry import DeviceInfo

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

# How long to keep watching for a silent revert after a successful PATCH.
# After this period we stop checking the pending write to avoid false positives
# caused by legitimate user changes via the wired controller or the Onecta app.
REVERT_CHECK_TTL = timedelta(minutes=5)


class DaikinOnectaDevice:
    """Class to represent and control one Daikin Onecta Device."""

    def __init__(self, jsonData, apiInstance):
        """Initialize a new Daikin Onecta Device."""
        self.api = apiInstance
        # get name from climateControl
        self.daikin_data = jsonData
        self.id = self.daikin_data["id"]
        self.name = self.daikin_data["deviceModel"]
        # Successful PATCH writes for which we have not yet observed the
        # resulting value via a coordinator refresh. Used to warn the user
        # when the Daikin cloud, gateway or wired master controller silently
        # reverts a change.
        self._pending_writes: list[dict] = []

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

    def setJsonData(self, desc):
        """Overwrite the json data for this device."""
        self.daikin_data = desc
        _LOGGER.info("Device '%s' received new data from the Daikin cloud, isCloudConnectionUp '%s'", self.name, self.available)
        self._check_pending_writes()

    def _read_value(self, embedded_id, data_point, data_point_path):
        """Return the current value at the given characteristic path, or None.

        The characteristic value is stored under ``managementPoint[data_point]["value"]``.
        For nested writes (``data_point_path`` like ``/operationModes/auto/fanSpeed/currentMode``)
        we walk that path inside the characteristic value and read the final ``value`` field.
        """
        for management_point in self.daikin_data.get("managementPoints", []):
            if management_point.get("embeddedId") != embedded_id:
                continue
            characteristic = management_point.get(data_point)
            if characteristic is None:
                return None
            if not data_point_path:
                return characteristic.get("value")
            node = characteristic.get("value")
            for segment in data_point_path.strip("/").split("/"):
                if not isinstance(node, dict):
                    return None
                node = node.get(segment)
                if node is None:
                    return None
            if isinstance(node, dict):
                return node.get("value")
            return node
        return None

    def _check_pending_writes(self):
        """Warn when a previously accepted PATCH has been reverted by the cloud/unit."""
        if not self._pending_writes:
            return
        now = datetime.now()
        remaining: list[dict] = []
        for pending in self._pending_writes:
            if now - pending["set_at"] > REVERT_CHECK_TTL:
                # Stop watching expired entries silently.
                continue
            actual = self._read_value(pending["embedded_id"], pending["data_point"], pending["data_point_path"])
            if actual is None:
                # Value not present yet in the new payload, keep watching.
                remaining.append(pending)
                continue
            if actual == pending["value"]:
                # The write took effect, stop watching this entry.
                continue
            _LOGGER.warning(
                "Device '%s' value at %s/%s%s was set to '%s' but the Daikin cloud now reports '%s'. "
                "The unit, gateway or a wired master controller (for example a BRC1H) most likely reverted "
                "the change. Check the master controller's operation mode lock / cool-heat selection setting.",
                self.name,
                pending["embedded_id"],
                pending["data_point"],
                pending["data_point_path"] or "",
                pending["value"],
                actual,
            )
            # Warn only once per pending write, then drop it.
        self._pending_writes = remaining

    async def patch(self, id, embeddedId, dataPoint, dataPointPath, value):
        setPath = "/v1/gateway-devices/" + id + "/management-points/" + embeddedId + "/characteristics/" + dataPoint
        setBody = {"value": value}
        if dataPointPath:
            setBody["path"] = dataPointPath
        setOptions = json.dumps(setBody)

        _LOGGER.info("Path: " + setPath + " , options: %s", setOptions)

        res = await self.api.doBearerRequest("PATCH", setPath, setOptions)

        _LOGGER.info("Result: {}".format(res))

        if res is True:
            self._pending_writes.append(
                {
                    "embedded_id": embeddedId,
                    "data_point": dataPoint,
                    "data_point_path": dataPointPath,
                    "value": value,
                    "set_at": datetime.now(),
                }
            )

        return res

    async def post(self, id, embeddedId, dataPoint, value):
        setPath = "/v1/gateway-devices/" + id + "/management-points/" + embeddedId + "/" + dataPoint
        setOptions = json.dumps(value)

        _LOGGER.info("Path: " + setPath + " , options: %s", setOptions)

        res = await self.api.doBearerRequest("POST", setPath, setOptions)

        _LOGGER.info("Result: {}".format(res))

        return res

    async def put(self, id, embeddedId, dataPoint, value=None):
        setPath = "/v1/gateway-devices/" + id + "/management-points/" + embeddedId + "/" + dataPoint
        setOptions = None
        if value is not None:
            setOptions = json.dumps(value)

        _LOGGER.info("Path: " + setPath + " , options: %s", setOptions)

        res = await self.api.doBearerRequest("PUT", setPath, setOptions)

        _LOGGER.info("Result: {}".format(res))

        return res
