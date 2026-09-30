from __future__ import annotations

from unittest.mock import MagicMock, patch

from ntou_pppoe.core.manager import ConnectionManager
from ntou_pppoe.core.state import ConnectionState
from ntou_pppoe.network.connectivity import ConnectivityResult
from ntou_pppoe.network.diagnostics import NetworkDiagnostics
from ntou_pppoe.network.pppoe import RasdialResult


def create_manager(
    *,
    health_check_enabled: bool = False,
) -> ConnectionManager:
    """Create a ConnectionManager with a test configuration."""

    health_check = {
        "enabled": health_check_enabled,
    }

    if health_check_enabled:
        health_check.update(
            {
                "dns_host": "example.com",
                "https_url": "https://www.example.com",
                "timeout": 5,
            }
        )

    config = {
        "connection_name": "NTOU-PPPoE",
        "startup_delay": 5,
        "check_interval": 30,
        "connect_timeout": 30,
        "health_check": health_check,
        "retry": {
            "initial_delay": 5,
            "max_delay": 60,
            "max_attempts": 5,
        },
    }

    with (
        patch(
            "ntou_pppoe.core.manager.load_config",
            return_value=config,
        ),
        patch(
            "ntou_pppoe.core.manager.PPPoEManager",
        ),
        patch(
            "ntou_pppoe.core.manager.setup_logger",
        ),
        patch(
            "ntou_pppoe.core.manager.ConnectivityChecker",
        ),
        patch(
            "ntou_pppoe.core.manager.NetworkDiagnosticsCollector",
        ),
    ):
        manager = ConnectionManager()

    return manager


def test_manager_can_initialize_with_health_check_disabled():
    """Manager should initialize when health checks are disabled."""

    manager = create_manager()

    assert manager.health_check_enabled is False
    assert manager.connectivity is None


def test_manager_initializes_connectivity_when_health_check_enabled():
    """Manager should create ConnectivityChecker when health checks are enabled."""

    with (
        patch(
            "ntou_pppoe.core.manager.load_config",
            return_value={
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
            },
        ),
        patch(
            "ntou_pppoe.core.manager.PPPoEManager",
        ),
        patch(
            "ntou_pppoe.core.manager.setup_logger",
        ),
        patch(
            "ntou_pppoe.core.manager.ConnectivityChecker",
        ) as connectivity_checker,
    ):
        manager = ConnectionManager()

    connectivity_checker.assert_called_once_with(
        dns_host="example.com",
        https_url="https://www.example.com",
        timeout=5,
    )

    assert manager.health_check_enabled is True
    assert manager.connectivity is connectivity_checker.return_value


def test_health_check_returns_healthy_when_disabled():
    """Disabled health checks should return a healthy result."""

    manager = create_manager()

    result = manager.health_check()

    assert result.healthy is True
    assert result.pppoe_ok is True
    assert result.ipv4_ok is True
    assert result.gateway_ok is True
    assert result.dns_ok is True
    assert result.https_ok is True


def test_health_check_marks_connection_healthy():
    """A fully healthy connection should become CONNECTED."""

    manager = create_manager(
        health_check_enabled=True,
    )

    manager.connectivity.check.return_value = ConnectivityResult(
        dns_ok=True,
        https_ok=True,
    )

    manager.diagnostics.collect.return_value = NetworkDiagnostics(
        ipv4_address="192.168.1.100",
        default_gateway="192.168.1.1",
        dns_servers=("8.8.8.8",),
    )

    manager.pppoe.is_connected.return_value = True

    manager.retry.next_delay()

    result = manager.health_check()

    assert result.healthy is True
    assert manager.state == ConnectionState.CONNECTED
    assert manager.retry.attempt == 0


def test_health_check_marks_connection_degraded_when_unhealthy():
    """An unhealthy connection should become DEGRADED."""

    manager = create_manager(
        health_check_enabled=True,
    )

    manager.connectivity.check.return_value = ConnectivityResult(
        dns_ok=True,
        https_ok=False,
    )

    manager.diagnostics.collect.return_value = NetworkDiagnostics(
        ipv4_address="192.168.1.100",
        default_gateway="192.168.1.1",
        dns_servers=("8.8.8.8",),
    )

    manager.pppoe.is_connected.return_value = True

    result = manager.health_check()

    assert result.healthy is False
    assert result.pppoe_ok is True
    assert result.ipv4_ok is True
    assert result.gateway_ok is True
    assert result.dns_ok is True
    assert result.https_ok is False
    assert manager.state == ConnectionState.DEGRADED


def test_health_check_marks_degraded_when_pppoe_is_disconnected():
    """A disconnected PPPoE session should make health check fail."""

    manager = create_manager(
        health_check_enabled=True,
    )

    manager.pppoe.is_connected.return_value = False

    manager.connectivity.check.return_value = ConnectivityResult(
        dns_ok=True,
        https_ok=True,
    )

    manager.diagnostics.collect.return_value = NetworkDiagnostics(
        ipv4_address="192.168.1.100",
        default_gateway="192.168.1.1",
        dns_servers=("8.8.8.8",),
    )

    result = manager.health_check()

    assert result.healthy is False
    assert result.pppoe_ok is False
    assert result.ipv4_ok is True
    assert result.gateway_ok is True
    assert result.dns_ok is True
    assert result.https_ok is True
    assert manager.state == ConnectionState.DEGRADED


def test_health_check_marks_degraded_when_ipv4_is_missing():
    """A missing IPv4 address should make health check fail."""

    manager = create_manager(
        health_check_enabled=True,
    )

    manager.pppoe.is_connected.return_value = True

    manager.connectivity.check.return_value = ConnectivityResult(
        dns_ok=True,
        https_ok=True,
    )

    manager.diagnostics.collect.return_value = NetworkDiagnostics(
        ipv4_address=None,
        default_gateway="192.168.1.1",
        dns_servers=("8.8.8.8",),
    )

    result = manager.health_check()

    assert result.healthy is False
    assert result.pppoe_ok is True
    assert result.ipv4_ok is False
    assert result.gateway_ok is True
    assert result.dns_ok is True
    assert result.https_ok is True
    assert manager.state == ConnectionState.DEGRADED


def test_health_check_marks_degraded_when_gateway_is_missing():
    """A missing gateway should make health check fail."""

    manager = create_manager(
        health_check_enabled=True,
    )

    manager.pppoe.is_connected.return_value = True

    manager.connectivity.check.return_value = ConnectivityResult(
        dns_ok=True,
        https_ok=True,
    )

    manager.diagnostics.collect.return_value = NetworkDiagnostics(
        ipv4_address="192.168.1.100",
        default_gateway=None,
        dns_servers=("8.8.8.8",),
    )

    result = manager.health_check()

    assert result.healthy is False
    assert result.pppoe_ok is True
    assert result.ipv4_ok is True
    assert result.gateway_ok is False
    assert result.dns_ok is True
    assert result.https_ok is True
    assert manager.state == ConnectionState.DEGRADED


def test_health_check_marks_degraded_when_dns_fails():
    """A failed DNS check should make health check fail."""

    manager = create_manager(
        health_check_enabled=True,
    )

    manager.pppoe.is_connected.return_value = True

    manager.connectivity.check.return_value = ConnectivityResult(
        dns_ok=False,
        https_ok=False,
    )

    manager.diagnostics.collect.return_value = NetworkDiagnostics(
        ipv4_address="192.168.1.100",
        default_gateway="192.168.1.1",
        dns_servers=("8.8.8.8",),
    )

    result = manager.health_check()

    assert result.healthy is False
    assert result.pppoe_ok is True
    assert result.ipv4_ok is True
    assert result.gateway_ok is True
    assert result.dns_ok is False
    assert result.https_ok is False
    assert manager.state == ConnectionState.DEGRADED


def test_connect_requires_connection_verification():
    """A successful RAS dial should still require verification."""

    manager = create_manager()

    manager.pppoe.connect.return_value = RasdialResult(
        success=True,
        output="PPPoE connection established.",
        return_code=0,
    )
    manager.pppoe.is_connected.return_value = False

    result = manager.connect()

    assert result.success is False
    assert result.return_code == 0
    assert "could not be verified" in result.output
    assert manager.state == ConnectionState.DISCONNECTED


def test_connect_marks_connection_connected_after_verification():
    """A verified PPPoE connection should become CONNECTED."""

    manager = create_manager()

    manager.pppoe.connect.return_value = RasdialResult(
        success=True,
        output="PPPoE connection established.",
        return_code=0,
    )
    manager.pppoe.is_connected.return_value = True

    manager.retry.next_delay()

    result = manager.connect()

    assert result.success is True
    assert manager.state == ConnectionState.CONNECTED
    assert manager.retry.attempt == 0


def test_connect_marks_disconnected_when_pppoe_connect_fails():
    """A failed PPPoE connection should become DISCONNECTED."""

    manager = create_manager()

    manager.pppoe.connect.return_value = RasdialResult(
        success=False,
        output="RasDialW failed with error 628.",
        return_code=628,
    )

    result = manager.connect()

    assert result.success is False
    assert result.return_code == 628
    assert manager.state == ConnectionState.DISCONNECTED


def test_disconnect_marks_connection_disconnected():
    """A successful disconnect should become DISCONNECTED."""

    manager = create_manager()

    manager.state = ConnectionState.CONNECTED

    manager.pppoe.disconnect.return_value = RasdialResult(
        success=True,
        output="PPPoE connection disconnected.",
        return_code=0,
    )

    manager.retry.next_delay()

    result = manager.disconnect()

    assert result.success is True
    assert manager.state == ConnectionState.DISCONNECTED
    assert manager.retry.attempt == 0


def test_disconnect_failure_keeps_connected_when_connection_remains():
    """A failed disconnect should remain CONNECTED if still active."""

    manager = create_manager()

    manager.state = ConnectionState.CONNECTED

    manager.pppoe.disconnect.return_value = RasdialResult(
        success=False,
        output="RasHangUpW failed with error 6.",
        return_code=6,
    )
    manager.pppoe.is_connected.return_value = True

    result = manager.disconnect()

    assert result.success is False
    assert result.return_code == 6
    assert manager.state == ConnectionState.CONNECTED


def test_disconnect_failure_enters_disconnected_when_connection_is_gone():
    """A failed disconnect should become DISCONNECTED if already gone."""

    manager = create_manager()

    manager.state = ConnectionState.CONNECTED

    manager.pppoe.disconnect.return_value = RasdialResult(
        success=False,
        output="Connection disappeared during disconnect.",
        return_code=6,
    )
    manager.pppoe.is_connected.return_value = False

    result = manager.disconnect()

    assert result.success is False
    assert result.return_code == 6
    assert manager.state == ConnectionState.DISCONNECTED


def test_recover_succeeds_after_disconnect_and_reconnect():
    """Recovery should disconnect and reconnect successfully."""

    manager = create_manager()

    manager.state = ConnectionState.DEGRADED

    manager.pppoe.is_connected.side_effect = [
        True,
        False,
        True,
    ]

    manager.pppoe.disconnect.return_value = RasdialResult(
        success=True,
        output="PPPoE connection disconnected.",
        return_code=0,
    )

    manager.pppoe.connect.return_value = RasdialResult(
        success=True,
        output="PPPoE connection established.",
        return_code=0,
    )

    with patch(
        "ntou_pppoe.core.manager.time.sleep",
    ) as sleep:
        result = manager.recover()

    assert result.success is True
    assert manager.state == ConnectionState.CONNECTED
    assert manager.retry.attempt == 0

    sleep.assert_called_once_with(5)


def test_recover_fails_when_maximum_attempts_are_reached():
    """Recovery should enter ERROR when retries are exhausted."""

    manager = create_manager()

    for _ in range(5):
        manager.retry.next_delay()

    result = manager.recover()

    assert result.success is False
    assert result.return_code == -4
    assert result.output == "Maximum recovery attempts reached."
    assert manager.state == ConnectionState.ERROR


def test_recover_fails_when_connection_remains_after_disconnect():
    """Recovery should fail if PPPoE remains active after disconnect."""

    manager = create_manager()

    manager.state = ConnectionState.DEGRADED

    manager.pppoe.is_connected.return_value = True

    manager.pppoe.disconnect.return_value = RasdialResult(
        success=True,
        output="PPPoE connection disconnected.",
        return_code=0,
    )

    with patch(
        "ntou_pppoe.core.manager.time.sleep",
    ):
        result = manager.recover()

    assert result.success is False
    assert manager.state == ConnectionState.DISCONNECTED
    assert "still active after disconnect" in result.output


def test_recover_continues_when_disconnect_reports_failure_but_connection_is_gone():
    """Recovery should continue if disconnect fails but connection is gone."""

    manager = create_manager()

    manager.state = ConnectionState.DEGRADED

    manager.pppoe.is_connected.side_effect = [
        True,  # recover()：原本有連線
        False,  # disconnect()：確認已經斷線
        False,  # recover()：確認斷線後再 reconnect
        True,  # connect()：確認重新連線成功
    ]

    manager.pppoe.disconnect.return_value = RasdialResult(
        success=False,
        output="RasHangUpW failed with error 6.",
        return_code=6,
    )

    manager.pppoe.connect.return_value = RasdialResult(
        success=True,
        output="PPPoE connection established.",
        return_code=0,
    )

    with patch(
        "ntou_pppoe.core.manager.time.sleep",
    ):
        result = manager.recover()

    assert result.success is True
    assert manager.state == ConnectionState.CONNECTED


def test_get_diagnostics_returns_current_network_information():
    """get_diagnostics() should return collected diagnostics."""

    manager = create_manager()

    diagnostics = NetworkDiagnostics(
        ipv4_address="192.168.1.100",
        default_gateway="192.168.1.1",
        dns_servers=("8.8.8.8", "1.1.1.1"),
    )

    manager.diagnostics.collect.return_value = diagnostics

    result = manager.get_diagnostics()

    assert result == diagnostics
    manager.diagnostics.collect.assert_called_once()
