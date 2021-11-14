"""Support for Daikin AirBase zones."""
from homeassistant.helpers.entity import ToggleEntity

from .daikin_base import Appliance

from .const import (
    DOMAIN as DAIKIN_DOMAIN,
    DAIKIN_DEVICES,
    DAIKIN_SWITCHES,
    DAIKIN_SWITCHES_ICONS,
    SWITCH_DEFAULT_ICON,
    ATTR_STATE_OFF,
    ATTR_STATE_ON,
    #PRESET_STREAMER,
    PRESET_BOOST,
    PRESET_TANK_ONOFF,
)

# DAMIANO
import logging
_LOGGER = logging.getLogger(__name__)


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Old way of setting up the platform.

    Can only be called when a user accidentally mentions the platform in their
    config. But even in that case it would have been ignored.
    """


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up Daikin climate based on config_entry."""
    for dev_id, device in hass.data[DAIKIN_DOMAIN][DAIKIN_DEVICES].items():
        switches = DAIKIN_SWITCHES
        
        for switch in switches:
            
            if device.support_preset_mode(switch):
                print("DAMIANO Adding Switch {}".format(switch))
                async_add_entities([DaikinSwitch(device, switch)])
            


class DaikinSwitch(ToggleEntity):
    """Representation of a switch."""

    def __init__(self, device: Appliance, switch_id: str):
        """Initialize the zone."""
        self._device = device
        #DAMIANO
        self._switch_id = switch_id
        if switch_id in DAIKIN_SWITCHES:
            subname = device.managementPoints["domesticHotWaterTank"]["name"]["value"]
            #self._name = f"{device.name}-{} {switch_id}".format(subname)
            self._name = "{} {} {}".format(self._device.name,subname,switch_id)
        else:
            self._name = f"{device.name} {switch_id}"

    @property
    def available(self):
        """Return the availability of the underlying device."""
        return self._device.available

    @property
    def unique_id(self):
        """Return a unique ID."""
        devID = self._device.getId()
        return f"{devID}-{self._switch_id}"

    @property
    def icon(self):
        """Icon to use in the frontend, if any."""
 
        return DAIKIN_SWITCHES_ICONS[self._switch_id]
    @property
    def name(self):
        """Return the name of the switch."""
        return self._name

    @property
    def is_on(self):
        """Return the state of the switch."""
        return self._device.preset_mode_status(self._switch_id) == ATTR_STATE_ON

    @property
    def device_info(self):
        """Return a device description for device registry."""
        return self._device.device_info()

    async def async_update(self):
        """Retrieve latest state."""
        print("DAMIANO {}: ASINC UPDATE SWITCH".format(self))
        await self._device.api.async_update()

    async def async_turn_on(self, **kwargs):
        """Turn the zone on."""
        print("DAMIANO {}: SWITCH TO {}".format(self._switch_id, ATTR_STATE_ON))
        await self._device.set_preset_mode_status(self._switch_id, ATTR_STATE_ON)

    async def async_turn_off(self, **kwargs):
        """Turn the zone off."""
        print("DAMIANO {} SWITCH TO: {}".format(self._switch_id, ATTR_STATE_ON))
        await self._device.set_preset_mode_status(self._switch_id, ATTR_STATE_OFF)
