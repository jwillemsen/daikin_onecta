"""Tests for daikin_onecta integration."""
from __future__ import annotations

import json
import logging
from typing import Any
from unittest.mock import Mock
from unittest.mock import patch

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.daikin_onecta import DOMAIN


TEST_CONFIG_ENTRY_ID = "77889900af"


def load_fixture_json(name):
    with open(f"tests/fixtures/{name}.json") as json_file:
        data = json.load(json_file)
        return data


