"""Pydaikin base appliance, represent a Daikin device."""
import logging

from .device import DaikinOnectaDevice

_LOGGER = logging.getLogger(__name__)


class Appliance(DaikinOnectaDevice):
    """Daikin main appliance class."""

    def __init__(self, jsonData, apiInstance):
        """Init the pydaikin appliance, representing one Daikin device."""
        super().__init__(jsonData, apiInstance)
