"""Tests that setup translations match the OAuth2 config flow."""
import json
from pathlib import Path

import pytest

COMPONENT = Path(__file__).resolve().parents[1] / "custom_components" / "daikin_onecta"
TRANSLATIONS = COMPONENT / "translations"
STRINGS = COMPONENT / "strings.json"

# Abort reasons used by this integration and the HA OAuth2 flow helper
REQUIRED_ABORT_KEYS = {
    "already_configured",
    "invalid_token",
    "wrong_account",
    "unknown",
    "oauth_error",
    "oauth_failed",
    "oauth_implementation_unavailable",
    "oauth_timeout",
    "oauth_unauthorized",
    "missing_configuration",
    "authorize_url_timeout",
    "no_url_available",
    "user_rejected_authorize",
    "reauth_successful",
}

# These translations are currently incomplete in Lokalise. Keep the exact
# expected gaps here so the test fails as soon as the translations are
# updated, reminding us to remove the temporary exception.
TEMPORARY_TRANSLATION_GAPS = {
    "da.json": {
        "missing_abort_keys": {"invalid_token", "unknown", "wrong_account"},
        "missing_reauth_description": True,
    },
    "es.json": {
        "missing_abort_keys": {"invalid_token", "unknown", "wrong_account"},
        "missing_reauth_description": True,
    },
    "pt.json": {
        "missing_abort_keys": {"invalid_token", "unknown", "wrong_account"},
        "missing_reauth_description": True,
    },
}

REQUIRED_STEPS = {"pick_implementation", "reauth_confirm"}


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _translation_files() -> list[Path]:
    return sorted(TRANSLATIONS.glob("*.json"))


@pytest.mark.parametrize("path", _translation_files(), ids=lambda p: p.name)
def test_config_translations_are_oauth2(path: Path) -> None:
    """Setup translations must describe OAuth2, not email/password login."""
    data = _load(path)
    config = data["config"]

    steps = set(config["step"])
    assert REQUIRED_STEPS.issubset(steps), f"{path.name} missing steps: {REQUIRED_STEPS - steps}"
    assert "user" not in steps, f"{path.name} still has obsolete email/password user step"

    gaps = TEMPORARY_TRANSLATION_GAPS.get(path.name)

    abort = set(config["abort"])
    missing = REQUIRED_ABORT_KEYS - abort
    if gaps is not None:
        expected_missing = gaps["missing_abort_keys"]
        assert missing == expected_missing, (
            f"{path.name} temporary translation exception is outdated: "
            f"expected missing {expected_missing}, found {missing}; "
            "update the translations test exception"
        )
    else:
        assert not missing, f"{path.name} missing abort keys: {missing}"

    reauth = config["step"]["reauth_confirm"]
    if gaps is not None and gaps["missing_reauth_description"]:
        assert "description" not in reauth, f"{path.name} now has a reauth description; remove the temporary " "translation exception"
    else:
        assert "description" in reauth
        assert "Daikin Onecta" in reauth["description"] or "daikin" in reauth["description"].lower()

    assert "title" in reauth


def test_strings_json_config_is_oauth2() -> None:
    """strings.json is the English source and must match the OAuth2 flow."""
    data = _load(STRINGS)
    config = data["config"]

    assert REQUIRED_STEPS.issubset(set(config["step"]))
    assert "user" not in config["step"]
    assert REQUIRED_ABORT_KEYS.issubset(set(config["abort"]))

    pick = config["step"]["pick_implementation"]
    assert "oauth2_pick_implementation" in pick["title"]
    assert "implementation" in pick.get("data", {})
