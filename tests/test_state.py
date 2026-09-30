from __future__ import annotations

from unittest.mock import MagicMock, patch

from ntou_pppoe.core.manager import ConnectionManager
from ntou_pppoe.core.state import ConnectionState
from ntou_pppoe.network.pppoe import RasdialResult


def create_manager() -> ConnectionManager:
    """Create a connection manager without loading real configuration."""

    with (
        patch(
            "ntou_pppoe.core.manager.load_config",
            return_value={
                "connection_name": "NTOU-PPPoE",
                "startup_delay": 0,
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
            },
        ),
        patch(
            "ntou_pppoe.core.manager.validate_config",
        ),
        patch(
            "ntou_pppoe.core.manager.setup_logger",
        ),
    ):
        return ConnectionManager()


def test_initial_state_is_starting():
    """The manager should start in STARTING state."""

    manager = create_manager()

    assert manager.state == ConnectionState.STARTING


def test_successful_connect_transitions_to_connected():
    """A successful verified connection should enter CONNECTED."""

    manager = create_manager()

    manager.pppoe.connect = MagicMock(
        return_value=RasdialResult(
            success=True,
            output="PPPoE connection established.",
            return_code=0,
        )
    )

    manager.pppoe.is_connected = MagicMock(
        return_value=True,
    )

    result = manager.connect()

    assert result.success is True
    assert manager.state == ConnectionState.CONNECTED


def test_failed_connect_transitions_to_disconnected():
    """A failed connection should enter DISCONNECTED."""

    manager = create_manager()

    manager.pppoe.connect = MagicMock(
        return_value=RasdialResult(
            success=False,
            output="Connection failed.",
            return_code=628,
        )
    )

    result = manager.connect()

    assert result.success is False
    assert manager.state == ConnectionState.DISCONNECTED


def test_successful_disconnect_transitions_to_disconnected():
    """A successful disconnect should enter DISCONNECTED."""

    manager = create_manager()
    manager.state = ConnectionState.CONNECTED

    manager.pppoe.disconnect = MagicMock(
        return_value=RasdialResult(
            success=True,
            output="PPPoE connection disconnected.",
            return_code=0,
        )
    )

    result = manager.disconnect()

    assert result.success is True
    assert manager.state == ConnectionState.DISCONNECTED


def test_failed_disconnect_keeps_connected_state_when_connection_remains():
    """A failed disconnect should remain CONNECTED if still active."""

    manager = create_manager()
    manager.state = ConnectionState.CONNECTED

    manager.pppoe.disconnect = MagicMock(
        return_value=RasdialResult(
            success=False,
            output="Disconnect failed.",
            return_code=6,
        )
    )

    manager.pppoe.is_connected = MagicMock(
        return_value=True,
    )

    result = manager.disconnect()

    assert result.success is False
    assert manager.state == ConnectionState.CONNECTED


def test_failed_disconnect_enters_disconnected_when_connection_is_gone():
    """A failed operation with no active connection should enter DISCONNECTED."""

    manager = create_manager()
    manager.state = ConnectionState.CONNECTED

    manager.pppoe.disconnect = MagicMock(
        return_value=RasdialResult(
            success=False,
            output="Disconnect failed.",
            return_code=-4,
        )
    )

    manager.pppoe.is_connected = MagicMock(
        return_value=False,
    )

    result = manager.disconnect()

    assert result.success is False
    assert manager.state == ConnectionState.DISCONNECTED


def test_healthy_check_transitions_to_connected():
    """A fully healthy network should enter CONNECTED."""

    manager = create_manager()

    manager.pppoe.is_connected = MagicMock(
        return_value=True,
    )

    manager.connectivity.check = MagicMock(
        return_value=MagicMock(
            dns_ok=True,
            https_ok=True,
        )
    )

    manager.diagnostics.collect = MagicMock(
        return_value=MagicMock(
            ipv4_address="118.167.200.241",
            default_gateway="26.0.0.1",
        )
    )

    result = manager.health_check()

    assert result.healthy is True
    assert manager.state == ConnectionState.CONNECTED


def test_unhealthy_check_transitions_to_degraded():
    """A failed health check should enter DEGRADED."""

    manager = create_manager()

    manager.pppoe.is_connected = MagicMock(
        return_value=False,
    )

    manager.connectivity.check = MagicMock(
        return_value=MagicMock(
            dns_ok=False,
            https_ok=False,
        )
    )

    manager.diagnostics.collect = MagicMock(
        return_value=MagicMock(
            ipv4_address=None,
            default_gateway=None,
        )
    )

    result = manager.health_check()

    assert result.healthy is False
    assert manager.state == ConnectionState.DEGRADED


def test_recovery_success_transitions_to_connected():
    """Successful recovery should end in CONNECTED."""

    manager = create_manager()
    manager.state = ConnectionState.DEGRADED

    manager.pppoe.is_connected = MagicMock(
        side_effect=[
            True,
            False,
            True,
        ]
    )

    manager.pppoe.disconnect = MagicMock(
        return_value=RasdialResult(
            success=True,
            output="PPPoE connection disconnected.",
            return_code=0,
        )
    )

    manager.pppoe.connect = MagicMock(
        return_value=RasdialResult(
            success=True,
            output="PPPoE connection established.",
            return_code=0,
        )
    )

    with patch(
        "ntou_pppoe.core.manager.time.sleep",
    ):
        result = manager.recover()

    assert result.success is True
    assert manager.state == ConnectionState.CONNECTED


def test_recovery_limit_transitions_to_error():
    """Exhausted recovery attempts should enter ERROR."""

    manager = create_manager()

    manager.retry._attempt = manager.retry.max_attempts

    result = manager.recover()

    assert result.success is False
    assert manager.state == ConnectionState.ERROR
