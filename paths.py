from __future__ import annotations

import sys
from pathlib import Path


def get_base_path() -> Path:
    """
    Return the base directory for assets and writable files.

    Works both in development and in PyInstaller builds.
    """
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


BASE_PATH = get_base_path()
SETTINGS_PATH = BASE_PATH / "settings.json"
MAPS_DIR = BASE_PATH / "maps"
SCREENSHOTS_DIR = BASE_PATH / "screenshots"