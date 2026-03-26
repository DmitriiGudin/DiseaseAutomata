from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any, Dict


SETTINGS_PATH = Path("settings.json")

REQUIRED_KEYS = {
    "GRID_WIDTH": int,
    "GRID_HEIGHT": int,
    "CELL_SIZE": int,
    "alpha": (int, float),
    "beta": (int, float),
    "gamma": (int, float),
    "FPS": int,
}


def _validate_section(name: str, data: Dict[str, Any]) -> None:
    """
    Validate one settings section ('default' or 'current').
    """
    for key, expected_type in REQUIRED_KEYS.items():
        if key not in data:
            raise ValueError(f"Missing key '{key}' in settings section '{name}'.")

        if not isinstance(data[key], expected_type):
            raise ValueError(
                f"Key '{key}' in section '{name}' must have type {expected_type}, "
                f"got {type(data[key])}."
            )

    if data["GRID_WIDTH"] <= 0:
        raise ValueError("GRID_WIDTH must be positive.")
    if data["GRID_HEIGHT"] <= 0:
        raise ValueError("GRID_HEIGHT must be positive.")
    if data["CELL_SIZE"] <= 0:
        raise ValueError("CELL_SIZE must be positive.")
    if data["FPS"] <= 0:
        raise ValueError("FPS must be positive.")

    for prob_key in ("alpha", "beta", "gamma"):
        if not (0.0 <= float(data[prob_key]) <= 1.0):
            raise ValueError(f"{prob_key} must lie in [0, 1].")


def validate_settings(payload: Dict[str, Any]) -> None:
    """
    Validate the full settings payload.
    """
    if "default" not in payload:
        raise ValueError("settings.json is missing the 'default' section.")
    if "current" not in payload:
        raise ValueError("settings.json is missing the 'current' section.")

    if not isinstance(payload["default"], dict):
        raise ValueError("'default' must be an object.")
    if not isinstance(payload["current"], dict):
        raise ValueError("'current' must be an object.")

    _validate_section("default", payload["default"])
    _validate_section("current", payload["current"])


def load_settings_file() -> Dict[str, Any]:
    """
    Load and validate the full settings JSON.
    """
    if not SETTINGS_PATH.exists():
        raise FileNotFoundError(
            f"Could not find {SETTINGS_PATH}. Create it before running the project."
        )

    with SETTINGS_PATH.open("r", encoding="utf-8") as f:
        payload = json.load(f)

    validate_settings(payload)
    return payload


def save_settings_file(payload: Dict[str, Any]) -> None:
    """
    Validate and save the full settings JSON.
    """
    validate_settings(payload)

    with SETTINGS_PATH.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)


def get_current_settings() -> Dict[str, Any]:
    """
    Return a copy of the current runtime settings.
    """
    payload = load_settings_file()
    return copy.deepcopy(payload["current"])


def get_default_settings() -> Dict[str, Any]:
    """
    Return a copy of the default settings.
    """
    payload = load_settings_file()
    return copy.deepcopy(payload["default"])


def reset_current_to_default() -> None:
    """
    Replace current settings with the default settings.
    """
    payload = load_settings_file()
    payload["current"] = copy.deepcopy(payload["default"])
    save_settings_file(payload)


def update_current_settings(updates: Dict[str, Any]) -> None:
    """
    Update the current settings with the provided values.
    """
    payload = load_settings_file()
    current = copy.deepcopy(payload["current"])

    for key, value in updates.items():
        if key not in REQUIRED_KEYS:
            raise ValueError(f"Unknown settings key: {key}")
        current[key] = value

    _validate_section("current", current)
    payload["current"] = current
    save_settings_file(payload)