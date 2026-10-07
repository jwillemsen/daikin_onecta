"""Represent Daikin Onecta gateway devices."""

import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr, entity_registry as er

from daikin_onecta.models import GatewayDevice

from .const import DOMAIN
from .daikin_api import DaikinApi
from .entity import gateway_device_info

_LOGGER = logging.getLogger(__name__)


class DaikinOnectaDevice:
    """Class to represent and control one Daikin Onecta Device."""

    def __init__(self, device: GatewayDevice, apiInstance: DaikinApi) -> None:
        """Initialize a new Daikin Onecta Device."""
        self.api = apiInstance
        # get name from climateControl
        self.device = device
        self.id: str = device.id
        self.name: str = device.display_name

        # Populated by async_register_ha_device() before any entity platform is set
        # up. Sub-entities (per-management-point devices in sensor/water_heater/
        # select/binary_sensor/switch/update) use this as via_device_id to link back
        # to this gateway device: the older via_device=(DOMAIN, identifier) form is
        # deprecated because identifiers are no longer guaranteed globally unique.
        self.ha_device_id: str | None = None
        self._is_present_in_cloud = True

        _LOGGER.info("Initialized Daikin Onecta Device '%s' (id %s)", self.name, self.id)

    @property
    def available(self) -> bool:
        """Return whether the device is connected to the Daikin cloud."""
        return self._is_present_in_cloud and self.device.available

    def management_point(self, embedded_id: str):
        """Return a management point by embedded id."""
        return self.device.management_point(embedded_id)

    @property
    def gateway_embedded_id(self) -> str | None:
        """Return the embedded ID of the gateway management point."""
        return self.device.gateway_embedded_id

    def async_register_ha_device(self, hass: HomeAssistant, config_entry: ConfigEntry) -> None:
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
            **gateway_device_info(self),
        )
        self.ha_device_id = entry.id

    def set_device_data(self, device: GatewayDevice) -> None:
        """Overwrite the typed and compatibility data for this device."""
        self.device = device
        self.name = device.display_name
        self._is_present_in_cloud = True
        _LOGGER.debug(
            "Device '%s' received new data from the Daikin cloud, isCloudConnectionUp '%s'",
            self.name,
            self.available,
        )

    def mark_unavailable(self) -> None:
        """Mark the device unavailable after it is absent from a cloud response."""
        self._is_present_in_cloud = False


def migrate_legacy_subdevice_identifiers(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    devices: dict[str, DaikinOnectaDevice],
) -> None:
    """Migrate type-based subdevice identifiers to embedded management-point IDs.

    Legacy versions could represent only one management point of a given type.
    Preserve that device registry entry for the first matching point, while
    later same-type points receive their own identifiers when entities are set
    up.
    """
    device_registry = dr.async_get(hass)
    for device in devices.values():
        management_points_by_type: dict[str, list[Any]] = {}
        for management_point in device.device.management_points:
            management_points_by_type.setdefault(management_point.management_point_type, []).append(management_point)

        for management_point_type, management_points in management_points_by_type.items():
            legacy_identifier = (DOMAIN, device.id + management_point_type)
            registry_entry = device_registry.async_get_device_by_identifier(legacy_identifier, config_entry.entry_id)
            if registry_entry is None:
                continue

            embedded_identifier = (DOMAIN, device.id + management_points[0].embedded_id)
            identifiers = set(registry_entry.identifiers)
            identifiers.discard(legacy_identifier)
            identifiers.add(embedded_identifier)
            device_registry.async_update_device(registry_entry.id, new_identifiers=identifiers)


def _migrate_type_based_entity_unique_id(
    device: DaikinOnectaDevice,
    unique_id: str,
    points_by_type: dict[str, list[Any]],
) -> str | None:
    """Return an embedded-ID unique ID for a type-based legacy ID."""
    for management_point_type, points in points_by_type.items():
        old_prefix = f"{device.id}_{management_point_type}_"
        if unique_id.startswith(old_prefix):
            return f"{device.id}_{points[0].embedded_id}_{unique_id.removeprefix(old_prefix)}"
    return None


def _legacy_entity_unique_id(
    device: DaikinOnectaDevice,
    entry: Any,
    points_by_type: dict[str, list[Any]],
) -> str | None:
    """Return the embedded-ID equivalent of a legacy entity unique ID."""
    if entry.domain in {"binary_sensor", "select", "switch", "update"}:
        return _migrate_type_based_entity_unique_id(device, entry.unique_id, points_by_type)

    if entry.domain == "climate":
        climate_points = points_by_type.get("climateControl", [])
        old_prefix = f"{device.id}_"
        if climate_points and entry.unique_id.startswith(old_prefix):
            suffix = entry.unique_id.removeprefix(old_prefix)
            if any(suffix.startswith(f"{point.embedded_id}_") for point in climate_points):
                return None
            return f"{device.id}_{climate_points[-1].embedded_id}_{suffix}"

    if entry.domain == "water_heater" and entry.unique_id == device.id:
        for management_point_type in ("domesticHotWaterTank", "domesticHotWaterFlowThrough"):
            if points := points_by_type.get(management_point_type):
                return f"{device.id}_{points[0].embedded_id}"

    return None


def migrate_legacy_entity_unique_ids(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    devices: dict[str, DaikinOnectaDevice],
) -> None:
    """Migrate per-management-point entity IDs to use embedded IDs.

    Management-point types are not unique on multi-zone systems.  Keep the
    existing entity registry entry for the first matching point, matching the
    legacy platform setup behavior, so users retain their entity IDs, history,
    and customizations.
    """
    entity_registry = er.async_get(hass)
    entries = er.async_entries_for_config_entry(entity_registry, config_entry.entry_id)

    for device in devices.values():
        points_by_type: dict[str, list[Any]] = {}
        for management_point in device.device.management_points:
            points_by_type.setdefault(management_point.management_point_type, []).append(management_point)

        for entry in entries:
            if entry.platform != DOMAIN:
                continue
            new_unique_id = _legacy_entity_unique_id(device, entry, points_by_type)

            if new_unique_id is None or entity_registry.async_get_entity_id(entry.domain, DOMAIN, new_unique_id) is not None:
                continue
            entity_registry.async_update_entity(entry.entity_id, new_unique_id=new_unique_id)
