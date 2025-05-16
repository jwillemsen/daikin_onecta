"""Test the Daikin Onecta coordinator."""
from datetime import datetime, time, timedelta
from unittest.mock import MagicMock, patch

import pytest
from homeassistant.core import HomeAssistant

from custom_components.daikin_onecta.const import DAIKIN_API, DOMAIN
from custom_components.daikin_onecta.coordinator import OnectaDataUpdateCoordinator


@pytest.fixture
def mock_hass():
    """Return a mocked HomeAssistant instance."""
    hass = MagicMock(spec=HomeAssistant)
    hass.data = {DOMAIN: {DAIKIN_API: MagicMock()}}
    hass.data[DOMAIN][DAIKIN_API].rate_limits = {"remaining_day": 100, "retry_after": 0}
    return hass


@pytest.fixture
def coordinator(mock_hass):
    """Return a coordinator with test options."""
    config_entry = MagicMock()
    config_entry.options = {
        "low_scan_interval": 30,   # minutes
        "high_scan_interval": 10,  # minutes
        "high_scan_start": "07:00:00",
        "low_scan_start": "22:00:00",
    }
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
        """High scan interval should apply during high‐frequency window."""
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
            mock_random.randint.assert_called_once_with(1, 1800)

    @patch("custom_components.daikin_onecta.coordinator.datetime")
    def test_rate_limit_exceeded(self, mock_datetime, coordinator, mock_hass):
        """When rate limit is exceeded, interval = retry_after + fallback (60s)."""
        mock_now = datetime(2023, 1, 1, 23, 0, 0)
        mock_datetime.now.return_value = mock_now
        mock_datetime.strptime.side_effect = datetime.strptime

        # Simulate daily rate limit reached
        mock_hass.data[DOMAIN][DAIKIN_API].rate_limits = {"remaining_day": 0, "retry_after": 300}

        with patch.object(coordinator, "in_between", side_effect=[False, False]):
            expected = timedelta(seconds=360)  # 300 + 60
            result = coordinator.determine_update_interval(mock_hass)
            assert result == expected