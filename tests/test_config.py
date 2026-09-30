import pytest

from ntou_pppoe.config.validator import (
    ConfigValidationError,
    validate_config,
)


def create_valid_config() -> dict:
    """Return a valid test configuration."""

    return {
        "connection_name": "NTOU-PPPoE",
        "startup_delay": 5,
        "check_interval": 30,
        "connect_timeout": 30,
        "health_check": {
            "enabled": True,
            "dns_host": "example.com",
            "https_url": "https://example.com",
            "timeout": 5,
        },
        "retry": {
            "initial_delay": 5,
            "max_delay": 60,
            "max_attempts": 5,
        },
    }


def test_valid_config_passes():
    """A valid configuration should pass validation."""

    config = create_valid_config()

    validate_config(config)


def test_non_dict_config_fails():
    """The configuration root must be a dictionary."""

    with pytest.raises(ConfigValidationError):
        validate_config([])


def test_missing_connection_name_fails():
    """connection_name is required."""

    config = create_valid_config()
    del config["connection_name"]

    with pytest.raises(ConfigValidationError):
        validate_config(config)


def test_empty_connection_name_fails():
    """connection_name cannot be empty."""

    config = create_valid_config()
    config["connection_name"] = "   "

    with pytest.raises(ConfigValidationError):
        validate_config(config)


def test_non_positive_startup_delay_fails():
    """startup_delay must be positive."""

    config = create_valid_config()
    config["startup_delay"] = 0

    with pytest.raises(ConfigValidationError):
        validate_config(config)


def test_non_positive_check_interval_fails():
    """check_interval must be positive."""

    config = create_valid_config()
    config["check_interval"] = -1

    with pytest.raises(ConfigValidationError):
        validate_config(config)


def test_non_positive_connect_timeout_fails():
    """connect_timeout must be positive."""

    config = create_valid_config()
    config["connect_timeout"] = 0

    with pytest.raises(ConfigValidationError):
        validate_config(config)


def test_invalid_health_check_type_fails():
    """health_check must be a dictionary."""

    config = create_valid_config()
    config["health_check"] = True

    with pytest.raises(ConfigValidationError):
        validate_config(config)


def test_invalid_health_check_enabled_type_fails():
    """health_check.enabled must be boolean."""

    config = create_valid_config()
    config["health_check"]["enabled"] = "true"

    with pytest.raises(ConfigValidationError):
        validate_config(config)


def test_empty_dns_host_fails_when_health_check_enabled():
    """dns_host cannot be empty when health checks are enabled."""

    config = create_valid_config()
    config["health_check"]["dns_host"] = ""

    with pytest.raises(ConfigValidationError):
        validate_config(config)


def test_invalid_https_url_fails_when_health_check_enabled():
    """https_url must use HTTP or HTTPS."""

    config = create_valid_config()
    config["health_check"]["https_url"] = "ftp://example.com"

    with pytest.raises(ConfigValidationError):
        validate_config(config)


def test_non_positive_health_timeout_fails():
    """Health check timeout must be positive."""

    config = create_valid_config()
    config["health_check"]["timeout"] = 0

    with pytest.raises(ConfigValidationError):
        validate_config(config)


def test_health_check_details_are_optional_when_disabled():
    """Health check details are not required when disabled."""

    config = create_valid_config()
    config["health_check"] = {
        "enabled": False,
    }

    validate_config(config)


def test_retry_initial_delay_greater_than_max_delay_fails():
    """Initial retry delay cannot exceed max delay."""

    config = create_valid_config()
    config["retry"]["initial_delay"] = 100
    config["retry"]["max_delay"] = 60

    with pytest.raises(ConfigValidationError):
        validate_config(config)


def test_non_positive_retry_max_delay_fails():
    """Retry max delay must be positive."""

    config = create_valid_config()
    config["retry"]["max_delay"] = 0

    with pytest.raises(ConfigValidationError):
        validate_config(config)


def test_non_positive_retry_initial_delay_fails():
    """Retry initial delay must be positive."""

    config = create_valid_config()
    config["retry"]["initial_delay"] = -1

    with pytest.raises(ConfigValidationError):
        validate_config(config)


def test_non_positive_retry_max_attempts_fails():
    """Retry max attempts must be a positive integer."""

    config = create_valid_config()
    config["retry"]["max_attempts"] = 0

    with pytest.raises(ConfigValidationError):
        validate_config(config)


def test_boolean_retry_max_attempts_fails():
    """Boolean values must not be accepted as max attempts."""

    config = create_valid_config()
    config["retry"]["max_attempts"] = True

    with pytest.raises(ConfigValidationError):
        validate_config(config)
