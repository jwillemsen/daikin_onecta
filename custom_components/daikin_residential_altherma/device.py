import datetime
import logging
import json

from homeassistant.util import Throttle

from homeassistant.helpers.device_registry import CONNECTION_NETWORK_MAC
from .const import DOMAIN


MIN_TIME_BETWEEN_UPDATES = datetime.timedelta(seconds=2)


_LOGGER = logging.getLogger(__name__)


class DaikinResidentialDevice:
    """Class to represent and control one Daikin Residential Device."""

    def __init__(self, jsonData, apiInstance):
        """Initialize a new Daikin Residential Device."""
        self.api = apiInstance
        self.setJsonData(jsonData)
        self.name = self.getName()
        self._available = True
        self.daikin_data = jsonData

        _LOGGER.info("Initialized Daikin Residential Device '%s' (id %s)", self.name, self.getId())

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        try:
            return self.desc["isCloudConnectionUp"]["value"]
        except Exception:
            return False

    def device_info(self):
        """Return a device description for device registry."""
        mac_add = self.get_value("gateway", "macAddress")
        model = self.get_value("gateway", "modelInfo")
        sw_vers = self.get_value("gateway", "firmwareVersion")
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
            "name": self.get_value("climateControl", "name"),
            "sw_version": sw_vers.replace("_", "."),
        }

    """
     * Helper method to traverse the Device object returned
     * by Daikin cloud for subPath datapoints
     *
     * @param {object} obj Object to traverse
     * @param {object} data Data object where all data are collected
     * @param {string} [pathPrefix] remember the path when traversing through structure
     * @returns {object} collected data
    """

    def _traverseDatapointStructure(self, obj, data={}, pathPrefix=""):
        """Helper method to traverse the Device object returned
        by Daikin cloud for subPath datapoints."""
        for key in obj.keys():
            if type(obj[key]) is not dict:
                data[pathPrefix + "/" + key] = obj[key]
            else:
                subKeys = obj[key].keys()
                if (
                    key == "meta"
                    or "value" in subKeys
                    or "settable" in subKeys
                    or "unit" in subKeys
                ):
                    # we found end leaf
                    # print('FINAL ' + pathPrefix + '/' + key)
                    data[pathPrefix + "/" + key] = obj[key]
                elif type(obj[key]) == dict:
                    # go one level deeper
                    # print('   found ' + key)
                    newPath = pathPrefix + "/" + key
                    self._traverseDatapointStructure(obj[key], data, newPath)
                else:
                    _LOGGER.error("SOMETHING IS WRONG WITH KEY %s", key)
        return data

    def setJsonData(self, desc):
        """Set a device description and parse/traverse data structure."""
        self.desc = desc
        self.daikin_data = desc
        # re-map some data for more easy access
        self.managementPoints = {}
        dataPoints = {}

        for mp in self.desc["managementPoints"]:
            # # Damiano deccommentato
            #print('AAAA: [{}] [{}]'.format(mp['managementPointType'], mp))
            #_LOGGER.debug('AAAA: [{}] [{}]'.format(mp['managementPointType'], mp))

            dataPoints = {}
            for key in mp.keys():
                dataPoints[key] = {}
                if mp[key] is None:
                    continue
                if type(mp[key]) != dict:
                    dataPoints[key] = mp[key]
                    continue
                if type(mp[key]["value"]) != dict or (
                    len(mp[key]["value"]) == 1 and "enabled" in mp[key]["value"]
                ):
                    dataPoints[key] = mp[key]
                else:
                    # DAMIANO decommentato
                    #print('TRAVERSE ' + key + ': ' + json.dumps(dataPoints[key]));
                    dataPoints[key] = self._traverseDatapointStructure(
                        mp[key]["value"], {}
                    )
                    #_LOGGER.warning('TRAVERSE ' + key + ': ' + json.dumps(dataPoints[key]));
                    dataPoints[key] = self._traverseDatapointStructure(
                        mp[key]["value"], {}
                    )

            self.managementPoints[mp["managementPointType"]] = dataPoints

        # Damiano decommentati
        #print('MPS FOUND: [{}]'.format(self.managementPoints))
        #print('MPS FOUND: [{}]'.format(self.managementPoints.keys()))
        #_LOGGER.warning('MPS FOUND: [{}]'.format(self.managementPoints))
        #_LOGGER.warning('MPS FOUND: [{}]'.format(self.managementPoints.keys()))

    def daikin_data(self):
        return self.daikin_data

    def getId(self):
        """Get Daikin Device UUID."""
        return self.desc["id"]

    def getName(self):
        """Get Daikin Device UUID."""
        return self.desc["deviceModel"]

    def getDescription(self):
        """Get the original Daikin Device Description."""
        return self.desc

    def getLastUpdated(self):
        """Get the timestamp when data were last updated."""
        _LOGGER.info("DAMIANO {}: LAST UPDATE DEVICE".format(self))
        return self.desc["lastUpdateReceived"]

    """
     * Get a current data object (includes value and meta information).
     * Without any parameter the full internal data structure is returned and
     * can be further detailed by sending parameters
     *
     * @param {string} [managementPoint] Management point name
     * @param {string} [dataPoint] Datapoint name for management point
     * @param {string} [dataPointPath] further detailed datapoints with subpath data
     * @returns {object|null} Data object
    """

    def get_data(self, managementPoint=None, dataPoint=None, dataPointPath=""):
        """Get a current data object (includes value and meta information)."""
        if managementPoint is None:
            # return all data
            return self.managementPoints

        # DAMIANO control_mode
        if dataPoint == "controlMode" and dataPointPath == "":
            # return data from one managementPoint and dataPoint
            return self.managementPoints[managementPoint][dataPoint]

        # DAMIANO setpoint_mode
        if dataPoint == "setpointMode" and dataPointPath == "":
            # return data from one managementPoint and dataPoint
            return self.managementPoints[managementPoint][dataPoint]

        # DAMIANO temperatureControl
        #if dataPoint == "temperatureControl":
            # return data from one managementPoint and dataPoint
            #print("aaa")
            #return self.managementPoints[managementPoint][dataPoint]

        # DAMIANO heatupMode
        if dataPoint == "heatupMode" and dataPointPath == "":
            # return data from one managementPoint and dataPoint
            return self.managementPoints[managementPoint][dataPoint]

        if managementPoint not in self.managementPoints:
            #print("DAMIANO MNGP device.py managementPoint = %s",managementPoint)
            return None

        if dataPoint is None:
            # return data from one managementPoint
            return self.managementPoints[managementPoint]

        if dataPoint not in self.managementPoints[managementPoint]:
            #_LOGGER.warning("DAMIANO DP device.py dataPoint = %s",dataPoint)
            return None

        if dataPointPath == "":
            # return data from one managementPoint and dataPoint
            return self.managementPoints[managementPoint][dataPoint]

        if dataPointPath not in self.managementPoints[managementPoint][dataPoint]:
            return None

        return self.managementPoints[managementPoint][dataPoint][dataPointPath]

    def get_value(self, managementPoint=None, dataPoint=None, dataPointPath=""):
        """Get the current value of a data object."""
        _LOGGER.info("Device '{}' get the current value of: '{}-{}-{}'".format(self.name,managementPoint,dataPoint,dataPointPath))
        data = self.get_data(managementPoint, dataPoint, dataPointPath)
        if data is None:
            return None
        return data["value"]

    def get_valid_values(self, managementPoint=None, dataPoint=None, dataPointPath=""):
        """Get a list of the accepted values of a data object."""
        data = self.get_data(managementPoint, dataPoint, dataPointPath)
        if data is None:
            return None
        return data["values"]

    @Throttle(MIN_TIME_BETWEEN_UPDATES)
    async def updateData(self):
        """Update the data of self device from the cloud."""
        return
        # TODO: Enhance self method to also allow to get some partial data
        # like only one managementPoint or such; needs checking how to request
        _LOGGER.info("DEV UPDATE " + self.name)
        desc = await self.api.doBearerRequest("/v1/gateway-devices/" + self.getId())
        self.setJsonData(desc)
        _LOGGER.info("DEVICE: " + self.name)
        _LOGGER.info(
            "    temp: inner "
            + str(self.get_value("climateControl", "sensoryData", "/roomTemperature"))
            + " outer "
            + str(
                self.get_value("climateControl", "sensoryData", "/outdoorTemperature")
            )
        )
        _LOGGER.info(
            "    current mode: "
            + str(self.get_value("climateControl", "operationMode"))
            + "  "
            + str(self.get_value("climateControl", "onOffMode"))
        )
        _LOGGER.info(
            "    target temp: "
            + str(
                self.get_value(
                    "climateControl",
                    "temperatureControl",
                    "/operationModes/cooling/setpoints/roomTemperature",
                )
            )
        )
        _LOGGER.info(
            "    FAN: mode [{}] speed [{}]\n".format(
                self.get_value(
                    "climateControl",
                    "fanControl",
                    "/operationModes/auto/fanSpeed/currentMode",
                ),
                self.get_value(
                    "climateControl",
                    "fanControl",
                    "/operationModes/auto/fanSpeed/modes/fixed",
                ),
            )
        )
        return True

    def _validateData(self, dataPoint, descr, value):
        """Validates a value that should be sent to the Daikin Device."""

        if "value" not in descr:  # and not 'settable' in descr:
            raise Exception("Value can not be set without dataPointPath")

        if "settable" not in descr or not descr["settable"]:
            raise Exception("Data point " + dataPoint + " is not writable")

        if "stepValue" in descr and type(descr["stepValue"]) != type(value):
            raise Exception(
                "Type of value ("
                + str(type(value))
                + ") is not the expected type ("
                + str(type(descr["value"]))
                + ")"
            )

        if (
            "values" in descr
            and isinstance(descr["values"], list)
            and value not in descr["values"]
        ):
            raise Exception(
                "Value ("
                + str(value)
                + ") is not in the list of allowed values: "
                + "/".join(map(str, descr["values"]))
            )

        if (
            "maxLength" in descr
            and type(descr["maxLength"]) == int
            and type(value) == str
            and len(value) > descr["maxLength"]
        ):
            raise Exception(
                "Length of value ("
                + str(len(value))
                + ") is greater than the allowed "
                + str(descr["maxLength"])
                + " characters"
            )

        if (
            "minValue" in descr
            and type(descr["minValue"]) == int
            and type(value) in (int, float)
            and float(value) < descr["minValue"]
        ):
            raise Exception(
                "Value ("
                + str(value)
                + ") must not be smaller than "
                + str(descr["minValue"])
            )

        if (
            "maxValue" in descr
            and type(descr["maxValue"]) == int
            and type(value) in (int, float)
            and float(value) > descr["maxValue"]
        ):
            raise Exception(
                "Value ("
                + str(value)
                + ") must not be bigger than "
                + str(descr["maxValue"])
            )

        # TODO add more validations for stepValue(number)

    """
     * Set a datapoint on this device
     *
     * @param {string} managementPoint Management point name
     * @param {string} dataPoint Datapoint name for management point
     * @param {string} [dataPointPath] further detailed datapoints with subpath data
     * @param {number|string} value Value to set
     * @returns {Promise<Object|boolean>} should return a true - or if a body
     * is returned the body object (can this happen?)
    """

    async def set_data(self, managementPoint, dataPoint, dataPointPath="", value=None):
        """Set a datapoint on this device."""
        if value is None:
            value = dataPointPath
            dataPointPath = ""

        if dataPoint not in self.managementPoints[managementPoint].keys() or (
            dataPointPath != ""
            and dataPointPath
            not in self.managementPoints[managementPoint][dataPoint].keys()
        ):
            raise Exception(
                "Please provide a valid datapoint definition "
                "that exists in the data structure"
            )

        dataPointDef = (
            self.managementPoints[managementPoint][dataPoint][dataPointPath]
            if dataPointPath != ""
            else self.managementPoints[managementPoint][dataPoint]
        )
        _LOGGER.debug(
            "Trying to validate `%s` for %s with description: %s",
            str(value),
            dataPoint,
            format(dataPointDef),
        )

        embeddedId = self.managementPoints[managementPoint]['embeddedId']
        _LOGGER.debug(
            "Management point `%s` has embeddedId '%s'",
            managementPoint,
            embeddedId,
        )

        try:
            self._validateData(dataPoint + dataPointPath, dataPointDef, value)
        except Exception as error:
            _LOGGER.error("FAILED to validate set_data params: %s", format(error))
            return

        setPath = (
            "/v1/gateway-devices/"
            + self.getId()
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
        if res is True:
            self.get_data(managementPoint, dataPoint, dataPointPath)["value"] = value

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
#        if res is True:
# JWI TODO
#            self.get_data(managementPoint, dataPoint, dataPointPath)["value"] = value
