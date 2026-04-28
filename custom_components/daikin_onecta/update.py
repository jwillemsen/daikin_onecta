"""Support for Daikin firmware update entities."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import CONF_STATE_CLASS
from homeassistant.components.update import UpdateEntity
from homeassistant.components.update import UpdateEntityFeature
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_DEVICE_CLASS
from homeassistant.const import CONF_ICON
from homeassistant.const import CONF_UNIT_OF_MEASUREMENT
from homeassistant.core import callback
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .const import ENABLED_DEFAULT
from .const import ENTITY_CATEGORY
from .const import TRANSLATION_KEY
from .const import VALUE_SENSOR_MAPPING
from .coordinator import OnectaDataUpdateCoordinator
from .coordinator import OnectaRuntimeData
from .device import DaikinOnectaDevice

_LOGGER = logging.getLogger(__name__)

# The Daikin Onecta cloud API exposes firmware info on the "gateway" management
# point.  The relevant characteristics are:
#   firmwareVersion       – currently installed version string
#   isFirmwareUpdateSupported – whether the gateway hardware supports OTA updates


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Daikin update entities from a config entry."""
    onecta_data: OnectaRuntimeData = config_entry.runtime_data
    coordinator = onecta_data.coordinator

    entities: list[DaikinFirmwareUpdateEntity] = []

    for dev_id, device in onecta_data.devices.items():
        gateway_mp = _get_gateway_management_point(device)
        if gateway_mp is None:
            _LOGGER.debug(
                "Device %s has no gateway management point, skipping update entity",
                device.name,
            )
            continue

        firmware_update_supported = _get_value(gateway_mp, "isFirmwareUpdateSupported")
        if firmware_update_supported is None:
            _LOGGER.debug(
                "Device %s gateway has no isFirmwareUpdateSupported, skipping update entity",
                device.name,
            )
            continue

        entities.append(DaikinFirmwareUpdateEntity(coordinator, device, gateway_mp))

    async_add_entities(entities)


def _get_gateway_management_point(device: DaikinOnectaDevice) -> dict | None:
    """Return the gateway management point dict, or None if absent."""
    for mp in device.daikin_data.get("managementPoints", []):
        if mp.get("managementPointType") == "gateway":
            return mp
    return None


def _get_value(mp: dict, characteristic: str) -> Any:
    """Safely read .value from a management point characteristic."""
    char = mp.get(characteristic)
    if not isinstance(char, dict):
        return None
    return char.get("value")


class DaikinFirmwareUpdateEntity(CoordinatorEntity, UpdateEntity):
    """Represents the gateway firmware for a single Daikin device."""

    def __init__(
        self,
        coordinator: OnectaDataUpdateCoordinator,
        device: DaikinOnectaDevice,
        gateway_mp: dict,
    ) -> None:
        """Initialise the update entity."""
        super().__init__(coordinator)
        self._device = device
        self._coordinator = coordinator
        self._attr_supported_features = UpdateEntityFeature(0)
        self._attr_has_entity_name = True
        sensor_settings = VALUE_SENSOR_MAPPING.get("FirmwareUpdate")
        self._attr_icon = sensor_settings[CONF_ICON]
        self._attr_device_class = sensor_settings[CONF_DEVICE_CLASS]
        self._attr_entity_registry_enabled_default = sensor_settings[ENABLED_DEFAULT]
        self._attr_state_class = sensor_settings[CONF_STATE_CLASS]
        self._attr_entity_category = sensor_settings[ENTITY_CATEGORY]
        self._attr_native_unit_of_measurement = sensor_settings[CONF_UNIT_OF_MEASUREMENT]
        self._attr_translation_key = sensor_settings[TRANSLATION_KEY]

        # Unique ID: <device_id>_firmware_update
        self._attr_unique_id = f"{device.id}_firmware_update"

        # Link to the HA device
        self._attr_device_info = {
            "identifiers": {(DOMAIN, self._device.id + "gateway")},
            "name": self._device.name + " " + "gateway",
            "via_device": (DOMAIN, self._device.id),
        }
        self._device.fill_device_info(self._attr_device_info, "gateway")

        # Populate initial state
        self._update_from_management_point(gateway_mp)

    # ------------------------------------------------------------------
    # UpdateEntity properties
    # ------------------------------------------------------------------

    @property
    def installed_version(self) -> str | None:
        """Return the currently installed firmware version."""
        return self._installed_version

    @property
    def latest_version(self) -> str | None:
        """Return the latest known firmware version."""
        return None

    @property
    def release_url(self) -> str | None:
        """Point users to the Daikin support site for firmware info."""
        return None

    @property
    def release_summary(self) -> str | None:
        """Brief hint that the mobile app is used to apply updates."""
        return None

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _update_from_management_point(self, gateway_mp: dict) -> None:
        """Pull the latest values out of a gateway management point dict."""
        self._installed_version: str | None = _get_value(gateway_mp, "firmwareVersion")
        self._is_update_supported: bool = bool(_get_value(gateway_mp, "isFirmwareUpdateSupported"))

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        gateway_mp = _get_gateway_management_point(self._device)
        if gateway_mp is not None:
            self._update_from_management_point(gateway_mp)
        self.async_write_ha_state()
