"""Test the Daikin Onecta coordinator."""
from datetime import datetime
from datetime import time
from datetime import timedelta
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.daikin_onecta.const import DOMAIN
from custom_components.daikin_onecta.coordinator import OnectaDataUpdateCoordinator
from custom_components.daikin_onecta.coordinator import OnectaRuntimeData


@pytest.fixture
def mock_hass():
    """Return a mocked HomeAssistant instance."""
    hass = MagicMock(spec=HomeAssistant)
    return hass


@pytest.fixture
def mock_config_entry() -> MockConfigEntry:
    """Mock a config entry."""
    entry = MockConfigEntry(domain=DOMAIN, title="daikin_onecta", unique_id="12345")
    entry.runtime_data = OnectaRuntimeData(daikin_api=MagicMock(), coordinator={}, devices={})
    return entry


@pytest.fixture
def coordinator(mock_hass, mock_config_entry):
    """Return a coordinator with test options."""
    config_entry = mock_config_entry
    config_entry.add_to_hass(mock_hass)
    options = {
        "low_scan_interval": 30,  # minutes
        "high_scan_interval": 10,  # minutes
        "high_scan_start": "07:00:00",
        "low_scan_start": "22:00:00",
    }
    mock_hass.config_entries.async_update_entry(
        config_entry,
        data={**config_entry.data, **options},
    )
    return OnectaDataUpdateCoordinator(mock_hass, config_entry)


class TestOnectaDataUpdateCoordinator:
    """Test OnectaDataUpdateCoordinator class."""

    def test_in_between_normal_range(self, coordinator):
        """Time within a simple range not crossing midnight."""
        start = time(8, 0, 0)
        end = time(10, 0, 0)
        assert not coordinator.in_between(time(7, 0, 0), start, end)
        assert coordinator.in_between(time(8, 0, 0), start, end)
        assert coordinator.in_between(time(9, 0, 0), start, end)
        assert not coordinator.in_between(time(10, 0, 0), start, end)
        assert not coordinator.in_between(time(11, 0, 0), start, end)

    def test_in_between_overnight_range(self, coordinator):
        """Time within a range that crosses midnight."""
        start = time(22, 0, 0)
        end = time(7, 0, 0)
        assert coordinator.in_between(time(6, 0, 0), start, end)
        assert not coordinator.in_between(time(7, 0, 0), start, end)
        assert not coordinator.in_between(time(12, 0, 0), start, end)
        assert coordinator.in_between(time(22, 0, 0), start, end)
        assert coordinator.in_between(time(23, 0, 0), start, end)

    @patch("custom_components.daikin_onecta.coordinator.datetime")
    def test_high_scan_interval(self, mock_datetime, coordinator, mock_hass):
        """High scan interval should apply during high-frequency window."""
        mock_now = datetime(2023, 1, 1, 10, 0, 0)
        mock_datetime.now.return_value = mock_now
        mock_datetime.strptime.side_effect = datetime.strptime

        expected = timedelta(minutes=10)
        result = coordinator.determine_update_interval(mock_hass)
        assert result == expected

    @patch("custom_components.daikin_onecta.coordinator.datetime")
    def test_low_scan_interval(self, mock_datetime, coordinator, mock_hass):
        """Low scan interval should apply outside transition windows."""
        mock_now = datetime(2023, 1, 1, 23, 0, 0)
        mock_datetime.now.return_value = mock_now
        mock_datetime.strptime.side_effect = datetime.strptime

        with patch.object(coordinator, "in_between", side_effect=[False, False]):
            expected = timedelta(minutes=30)
            result = coordinator.determine_update_interval(mock_hass)
            assert result == expected

    @patch("custom_components.daikin_onecta.coordinator.datetime")
    @patch("custom_components.daikin_onecta.coordinator.random")
    def test_transition_period_randomization(self, mock_random, mock_datetime, coordinator, mock_hass):
        """During transition, interval is randomized between floor and low interval."""
        mock_now = datetime(2023, 1, 1, 22, 5, 0)
        mock_datetime.now.return_value = mock_now
        mock_datetime.strptime.side_effect = datetime.strptime
        mock_random.randint.return_value = 120  # 2 minutes

        with patch.object(coordinator, "in_between", side_effect=[False, True]):
            expected = timedelta(seconds=120)
            result = coordinator.determine_update_interval(mock_hass)
            assert result == expected
            mock_random.randint.assert_called_once_with(60, 1800)

    @patch("custom_components.daikin_onecta.coordinator.datetime")
    def test_rate_limit_exceeded(self, mock_datetime, coordinator, mock_hass, mock_config_entry):
        """When rate limit is exceeded, interval = retry_after + fallback (60s)."""
        mock_now = datetime(2023, 1, 1, 23, 0, 0)
        mock_datetime.now.return_value = mock_now
        mock_datetime.strptime.side_effect = datetime.strptime

        # Simulate daily rate limit reached
        mock_config_entry.runtime_data.daikin_api.rate_limits = {"remaining_day": 0, "retry_after": 3000}

        with patch.object(coordinator, "in_between", side_effect=[False, False]):
            expected = timedelta(seconds=3060)  # 3000 + 60
            result = coordinator.determine_update_interval(mock_hass)
            assert result == expected
