from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


class ConfigError(Exception):
    """Raised when the configuration cannot be loaded."""

DEFAULT_CONFIG: dict[str, Any] = {
    "connection_name": "NTOU-PPPoE",
    "startup_delay": 5,
    "check_interval": 30,
    "connect_timeout": 30,
    "health_check": {
        "enabled": True,
        "dns_host": "example.com",
        "https_url": "https://www.example.com",
        "timeout": 5,
    },
    "retry": {
        "initial_delay": 5,
        "max_delay": 60,
        "max_attempts": 5,
    },
}


def create_default_config(path: Path) -> None:
    """Write a template config.json so first-time users have something to edit."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        json.dump(DEFAULT_CONFIG, file, indent=4, ensure_ascii=False)

def get_project_root() -> Path:
    """Return the base directory that contains the config/ folder."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parents[3]


def get_config_path() -> Path:
    """Return the path to config/config.json."""
    return get_project_root() / "config" / "config.json"


def load_config(path: Path | None = None) -> dict[str, Any]:
    """Load the application configuration from a JSON file."""
    config_path = path or get_config_path()

    if not config_path.exists():
        if path is None:
            create_default_config(config_path)
            raise ConfigError(
                f"找不到設定檔,已自動建立範本:{config_path}\n"
                f"請打開它,把 connection_name 改成你的 Windows PPPoE "
                f"連線名稱後,再執行一次。"
            )
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
