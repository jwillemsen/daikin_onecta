"""Tests for daikin_onecta integration."""
from __future__ import annotations

import json


def load_fixture_json(name):
    with open(f"tests/fixtures/{name}.json") as json_file:
        data = json.load(json_file)
        return data
