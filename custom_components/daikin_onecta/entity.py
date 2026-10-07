"""Shared entity helpers for Daikin Onecta."""

from typing import Any, override

from homeassistant.helpers.device_registry import CONNECTION_NETWORK_MAC, DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN


def gateway_device_info(device: Any) -> DeviceInfo:
    """Build Home Assistant device metadata for a gateway."""
    connections = set()
    if mac_address := device.device.mac_address:
        connections.add((CONNECTION_NETWORK_MAC, mac_address))

    info = DeviceInfo(
        identifiers={(DOMAIN, device.id)},
        connections=connections,
        name=device.name,
        model_id=device.device.device_model,
        manufacturer="Daikin",
    )
    if (embedded_id := device.gateway_embedded_id) is not None:
        _add_management_point_metadata(info, device, embedded_id)
    return info


def management_point_device_info(device: Any, embedded_id: str, management_point_type: str) -> DeviceInfo:
    """Build Home Assistant device metadata for a management point."""
    assert device.ha_device_id is not None
    info = DeviceInfo(
        identifiers={(DOMAIN, device.id + embedded_id)},
        name=f"{device.name} {management_point_type[0].upper() + management_point_type[1:]}",
        via_device_id=device.ha_device_id,
        manufacturer="Daikin",
    )
    _add_management_point_metadata(info, device, embedded_id)
    return info


def _add_management_point_metadata(info: DeviceInfo, device: Any, embedded_id: str) -> None:
    """Add model, serial, and firmware data from a management point."""
    if (point := device.management_point(embedded_id)) is None:
        return
    if point.version is not None:
        info["sw_version"] = point.version
    if point.model is not None:
        info["model"] = point.model
    if point.serial is not None:
        info["serial_number"] = point.serial


class DaikinEntity(CoordinatorEntity):
    """Base entity backed by a Daikin gateway device."""

    def __init__(self, device: Any, coordinator, embedded_id: str | None = None, management_point_type: str | None = None) -> None:
        """Initialize shared coordinator and device state."""
        super().__init__(coordinator)
        self._device = device
        self._embedded_id = embedded_id
        self._attr_device_info = (
            gateway_device_info(device)
            if embedded_id is None
            else management_point_device_info(device, embedded_id, management_point_type or "Gateway")
        )

    @property
    @override
    def available(self) -> bool:
        """Return whether the coordinator and Daikin device are available."""
        return super().available and self._device.available
