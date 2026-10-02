"""Install test and integration requirements."""

import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "custom_components" / "daikin_onecta" / "manifest.json"


def main() -> None:
    """Install requirements needed to test the integration."""
    subprocess.run(
        [
            sys.executable,
            "-m",
            "pip",
            "install",
            "-r",
            str(ROOT / "requirements_test.txt"),
        ],
        check=True,
    )

    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    requirements = manifest.get("requirements", [])
    if requirements:
        subprocess.run(
            [sys.executable, "-m", "pip", "install", *requirements],
            check=True,
        )


if __name__ == "__main__":
    main()
