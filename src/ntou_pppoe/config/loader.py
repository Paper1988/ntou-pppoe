from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class ConfigError(Exception):
    """Raised when the configuration cannot be loaded."""


def get_project_root() -> Path:
    """Return the project root directory."""
    return Path(__file__).resolve().parents[3]


def get_config_path() -> Path:
    """Return the path to config/config.json."""
    return get_project_root() / "config" / "config.json"


def load_config(path: Path | None = None) -> dict[str, Any]:
    """Load the application configuration from a JSON file."""
    config_path = path or get_config_path()

    if not config_path.exists():
        raise ConfigError(f"Configuration file not found: {config_path}")

    if not config_path.is_file():
        raise ConfigError(f"Configuration path is not a file: {config_path}")

    try:
        with config_path.open("r", encoding="utf-8") as file:
            config = json.load(file)
    except json.JSONDecodeError as exc:
        raise ConfigError(f"Invalid JSON in configuration file: {exc}") from exc
    except OSError as exc:
        raise ConfigError(f"Unable to read configuration file: {exc}") from exc

    if not isinstance(config, dict):
        raise ConfigError("Configuration root must be a JSON object.")

    return config
