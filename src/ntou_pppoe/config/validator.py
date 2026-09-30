from __future__ import annotations

from typing import Any


class ConfigValidationError(Exception):
    """Raised when the configuration is invalid."""


def _require_type(
    config: dict[str, Any],
    key: str,
    expected_type: type | tuple[type, ...],
) -> Any:
    if key not in config:
        raise ConfigValidationError(f"Missing required configuration: {key}")

    value = config[key]

    if not isinstance(value, expected_type):
        raise ConfigValidationError(f"'{key}' must be of type {expected_type}")

    return value


def _require_positive_integer(
    value: Any,
    key: str,
) -> None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ConfigValidationError(f"'{key}' must be a number")

    if value <= 0:
        raise ConfigValidationError(f"'{key}' must be greater than 0")


def validate_config(config: dict[str, Any]) -> None:
    """Validate the application configuration."""

    if not isinstance(config, dict):
        raise ConfigValidationError("Configuration root must be a JSON object.")

    connection_name = _require_type(
        config,
        "connection_name",
        str,
    )

    if not connection_name.strip():
        raise ConfigValidationError("'connection_name' cannot be empty")

    startup_delay = _require_type(
        config,
        "startup_delay",
        (int, float),
    )
    _require_positive_integer(
        startup_delay,
        "startup_delay",
    )

    check_interval = _require_type(
        config,
        "check_interval",
        (int, float),
    )
    _require_positive_integer(
        check_interval,
        "check_interval",
    )

    connect_timeout = _require_type(
        config,
        "connect_timeout",
        (int, float),
    )
    _require_positive_integer(
        connect_timeout,
        "connect_timeout",
    )

    health_check = _require_type(
        config,
        "health_check",
        dict,
    )

    enabled = _require_type(
        health_check,
        "enabled",
        bool,
    )

    if enabled:
        dns_host = _require_type(
            health_check,
            "dns_host",
            str,
        )

        if not dns_host.strip():
            raise ConfigValidationError("'health_check.dns_host' cannot be empty")

        https_url = _require_type(
            health_check,
            "https_url",
            str,
        )

        if not https_url.startswith(("http://", "https://")):
            raise ConfigValidationError(
                "'health_check.https_url' must start with 'http://' or 'https://'"
            )

        health_timeout = _require_type(
            health_check,
            "timeout",
            (int, float),
        )
        _require_positive_integer(
            health_timeout,
            "health_check.timeout",
        )

    retry = _require_type(
        config,
        "retry",
        dict,
    )

    initial_delay = _require_type(
        retry,
        "initial_delay",
        (int, float),
    )
    _require_positive_integer(
        initial_delay,
        "retry.initial_delay",
    )

    max_delay = _require_type(
        retry,
        "max_delay",
        (int, float),
    )
    _require_positive_integer(
        max_delay,
        "retry.max_delay",
    )

    if initial_delay > max_delay:
        raise ConfigValidationError(
            "'retry.initial_delay' cannot be greater than 'retry.max_delay'"
        )

    max_attempts = _require_type(
        retry,
        "max_attempts",
        int,
    )

    if isinstance(max_attempts, bool) or max_attempts <= 0:
        raise ConfigValidationError("'retry.max_attempts' must be a positive integer")
