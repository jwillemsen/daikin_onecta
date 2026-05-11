"""Support for Daikin firmware update entities."""
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
# point.


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Daikin update entities from a config entry."""
    onecta_data: OnectaRuntimeData = config_entry.runtime_data
    coordinator = onecta_data.coordinator

    entities: list[DaikinFirmwareUpdateEntity] = []
    supported_management_point_types = {
        "gateway",
        "userInterface",
    }

    for device in onecta_data.devices.values():
        for mp_type in supported_management_point_types:
            management_point = _get_management_point(device, mp_type)
            if management_point is not None:
                firmware_update_supported = _get_value(management_point, "isFirmwareUpdateSupported")
                if firmware_update_supported is not True:
                    _LOGGER.debug(
                        "Device %s %s has no isFirmwareUpdateSupported, skipping update entity",
                        mp_type,
                        device.name,
                    )
                    continue

                entities.append(DaikinFirmwareUpdateEntity(coordinator, device, management_point, mp_type))

    async_add_entities(entities)


def _get_management_point(device: DaikinOnectaDevice, mp_type: str) -> dict | None:
    """Return the gateway management point dict, or None if absent."""
    for mp in device.daikin_data.get("managementPoints", []):
        if mp.get("managementPointType") == mp_type:
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
        management_point_type: str,
    ) -> None:
        """Initialise the update entity."""
        super().__init__(coordinator)
        self._device = device
        self._coordinator = coordinator
        self._management_point_type = management_point_type
        mpt = management_point_type[0].upper() + management_point_type[1:]
        self._attr_device_info = {
            "identifiers": {(DOMAIN, self._device.id + self._management_point_type)},
            "name": self._device.name + " " + mpt,
            "via_device": (DOMAIN, self._device.id),
        }
        self._device.fill_device_info(self._attr_device_info, management_point_type)
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
        self._attr_unique_id = f"{device.id}_{management_point_type}_firmware_update"

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
        return self._latest_version

    @property
    def release_url(self) -> str | None:
        """Point users to the Daikin support site for firmware info."""
        return self._release_url

    @property
    def release_summary(self) -> str | None:
        """Brief hint that the mobile app is used to apply updates."""
        return self._release_summary

    @property
    def in_progress(self) -> bool | None:
        """Is the update in progress."""
        return self._in_progress

    async def async_install(self, version: str | None, backup: bool, **kwargs: Any) -> None:
        """Trigger a firmware update via the Daikin Onecta cloud API."""
        if self._firmware_id is None:
            _LOGGER.error(
                "Cannot install firmware for %s: no firmware ID available",
                self._device.name,
            )
            return

        _LOGGER.debug(
            "Requesting firmware update for %s, firmware id %s",
            self._device.name,
            self._firmware_id,
        )

        self._in_progress = True
        self.async_write_ha_state()

        result = await self._device.put(self._device.id, self._management_point_type, f"firmware/{self._firmware_id}", "")

        if not result:
            _LOGGER.error("Failed to trigger firmware update for %s", self._device.name)
            self._in_progress = False
            self.async_write_ha_state()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _update_from_management_point(self, management_point: dict) -> None:
        """Pull the latest values out of a gateway management point dict."""
        self._installed_version: str | None = _get_value(management_point, "firmwareVersion")
        self._is_update_supported: bool = bool(_get_value(management_point, "isFirmwareUpdateSupported"))
        self._latest_version = None
        self._release_url = None
        self._release_summary = None
        self._firmware_id = None
        self._in_progress = False
        self._attr_supported_features = UpdateEntityFeature.INSTALL

        firmwareUpdate = management_point.get("firmwareUpdate")
        if firmwareUpdate is not None:
            firmwareUpdateValue = firmwareUpdate.get("value")
            if firmwareUpdateValue is not None:
                self._latest_version = firmwareUpdateValue.get("version")
                self._release_url = None
                self._release_summary = firmwareUpdateValue.get("description")
                self._firmware_id = firmwareUpdateValue.get("id")
        firmwareUpdateStatus = management_point.get("firmwareUpdateStatus")
        if firmwareUpdateStatus is not None:
            firmwareUpdateStatusValue = firmwareUpdateStatus.get("value")
            if firmwareUpdateStatusValue is not None:
                self._in_progress = firmwareUpdateStatusValue == "in-progress"
                self._attr_supported_features |= UpdateEntityFeature.PROGRESS

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        mp = _get_management_point(self._device, self._management_point_type)
        if mp is not None:
            self._update_from_management_point(mp)
        self.async_write_ha_state()
