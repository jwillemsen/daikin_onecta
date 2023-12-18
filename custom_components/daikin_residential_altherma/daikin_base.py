"""Pydaikin base appliance, represent a Daikin device."""

import logging

from .device import DaikinResidentialDevice

_LOGGER = logging.getLogger(__name__)

class Appliance(DaikinResidentialDevice):
    """Daikin main appliance class."""

    def __init__(self, jsonData, apiInstance):
        """Init the pydaikin appliance, representing one Daikin device."""
        super().__init__(jsonData, apiInstance)

    async def init(self):
        """Init status."""
        # Re-defined in all sub-classes
        raise NotImplementedError

    async def set(self, settings):
        """Set settings on Daikin device."""
        raise NotImplementedError

