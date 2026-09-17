"""Regression tests for Daikin climate HVAC mode discovery."""
from unittest.mock import MagicMock

from homeassistant.components.climate.const import HVACMode

from custom_components.daikin_onecta.climate import DaikinClimate
from custom_components.daikin_onecta.device import DaikinOnectaDevice


def test_hvac_modes_when_operation_mode_reported_not_settable() -> None:
    """Expose advertised HVAC modes even when Daikin reports read-only metadata."""
    device_data = {
        "id": "test-device",
        "deviceModel": "test-model",
        "managementPoints": [
            {
                "managementPointType": "climateControl",
                "name": {"value": "Test climate"},
                "operationMode": {
                    "settable": False,
                    "value": "cooling",
                    "values": ["cooling", "heating", "dry", "fanOnly", "auto"],
                },
            }
        ],
    }

    device = DaikinOnectaDevice(device_data, MagicMock())
    climate = MagicMock(spec=DaikinClimate)
    climate.operation_mode.return_value = device.daikin_data["managementPoints"][0]["operationMode"]

    assert DaikinClimate.get_hvac_modes(climate) == [
        HVACMode.OFF,
        HVACMode.COOL,
        HVACMode.HEAT,
        HVACMode.DRY,
        HVACMode.FAN_ONLY,
        HVACMode.HEAT_COOL,
    ]
