"""Global fixtures for myenergi integration."""
from typing import Any
from unittest.mock import patch

import pytest

from . import load_fixture_json

pytest_plugins = "pytest_homeassistant_custom_component"


@pytest.fixture(name="auto_enable_custom_integrations", autouse=True)

def auto_enable_custom_integrations(hass: Any, enable_custom_integrations: Any) -> None:  # noqa: F811
    """Enable custom integrations defined in the test dir."""


# This fixture is used to prevent HomeAssistant from attempting to create and dismiss persistent
# notifications. These calls would fail without this fixture since the persistent_notification
# integration is never loaded during a test.
@pytest.fixture(name="skip_notifications", autouse=True)
def skip_notifications_fixture():
    """Skip notification calls."""
    with patch("homeassistant.components.persistent_notification.async_create"), patch(
        "homeassistant.components.persistent_notification.async_dismiss"
    ):
        yield

# This fixture, when used, will result in calls to async_get_data to return None. To have the call
# return a value, we would add the `return_value=<VALUE_TO_RETURN>` parameter to the patch call.
@pytest.fixture(name="bypass_get_data")
def bypass_get_data_fixture():
    # """Mock data from client.fetch_data()"""
    # with patch(
    #     "pymyenergi.client.MyenergiClient.fetch_data",
    #     return_value=load_fixture_json("client"),
    # ), patch(
    #     "pymyenergi.zappi.Zappi.fetch_history_data",
    #     return_value=load_fixture_json("history_zappi"),
    # ), patch(
    #     "pymyenergi.eddi.Eddi.fetch_history_data",
    #     return_value=load_fixture_json("history_eddi"),
    # ):
        yield


# In this fixture, we are forcing calls to async_get_data to raise an Exception. This is useful
# for exception handling.
@pytest.fixture(name="error_on_get_data")
def error_get_data_fixture():
    """Simulate error when retrieving data from API."""
    with patch(
        "pymyenergi.client.MyenergiClient.refresh",
        side_effect=Exception,
    ):
        yield


# In this fixture, we are forcing calls to async_get_data to raise an Exception. This is useful
# for exception handling.
@pytest.fixture(name="auth_error_on_get_data")
def auth_error_get_data_fixture():
    """Simulate authentication error when retrieving data from API."""
    with patch(
        "pymyenergi.client.MyenergiClient.refresh",
        side_effect=WrongCredentials,
    ):
        yield


# In this fixture, we are forcing calls to async_get_data to raise an Exception. This is useful
# for exception handling.
@pytest.fixture(name="timeout_error_on_get_data")
def timeout_error_get_data_fixture():
    """Simulate authentication error when retrieving data from API."""
    with patch(
        "pymyenergi.client.MyenergiClient.refresh",
        side_effect=TimeoutException,
    ):
        yield


@pytest.fixture
def mock_zappi_set_charge_mode():
    """Return a mocked Zappi object."""
    with patch("pymyenergi.client.Zappi.set_charge_mode") as charge_mode:
        yield charge_mode


@pytest.fixture
def mock_eddi_set_operating_mode():
    """Return a mocked Eddi object."""
    with patch("pymyenergi.client.Eddi.set_operating_mode") as op_mode:
        yield op_mode


@pytest.fixture
def mock_zappi_start_boost():
    """Return a mocked Zappi object."""
    with patch("pymyenergi.client.Zappi.start_boost") as start_boost:
        yield start_boost


@pytest.fixture
def mock_eddi_manual_boost():
    """Return a mocked Eddi object."""
    with patch("pymyenergi.client.Eddi.manual_boost") as manual_boost:
        yield manual_boost


@pytest.fixture
def mock_zappi_start_smart_boost():
    """Return a mocked Zappi object."""
    with patch("pymyenergi.client.Zappi.start_smart_boost") as start_smart_boost:
        yield start_smart_boost


@pytest.fixture
def mock_zappi_set_green():
    """Return a mocked Zappi object."""
    with patch("pymyenergi.client.Zappi.set_minimum_green_level") as green_lvl:
        yield green_lvl


@pytest.fixture
def mock_eddi_heater():
    """Return a mocked eddi object."""
    with patch("pymyenergi.client.Eddi.set_heater_priority") as heater:
        yield heater


@pytest.fixture
def mock_eddi_device():
    """Return a mocked eddi object."""
    with patch("pymyenergi.client.Eddi.set_priority") as device:
        yield device


@pytest.fixture
def mock_zappi_stop_boost():
    """Return a mocked Zappi object."""
    with patch("pymyenergi.client.Zappi.stop_boost") as stop_boost:
        yield stop_boost


@pytest.fixture
def mock_zappi_unlock():
    """Return a mocked Zappi object."""
    with patch("pymyenergi.client.Zappi.unlock") as unlock:
        yield unlock
