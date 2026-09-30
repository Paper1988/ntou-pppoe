from __future__ import annotations

from unittest.mock import MagicMock, patch

from ntou_pppoe.core.service import ConnectionService
from ntou_pppoe.core.state import ConnectionState
from ntou_pppoe.network.connectivity import NetworkHealthResult
from ntou_pppoe.network.pppoe import RasdialResult


def create_service() -> tuple[ConnectionService, MagicMock]:
    """Create a service with a mocked connection manager."""

    manager = MagicMock()

    manager.config = {
        "startup_delay": 5,
        "check_interval": 30,
    }

    manager.state = ConnectionState.STARTING

    manager.logger = MagicMock()

    manager.retry = MagicMock()
    manager.retry.attempt = 0
    manager.retry.can_retry.return_value = True

    service = ConnectionService(manager)

    return service, manager


def healthy_result() -> NetworkHealthResult:
    """Return a healthy network result."""

    return NetworkHealthResult(
        pppoe_ok=True,
        ipv4_ok=True,
        gateway_ok=True,
        dns_ok=True,
        https_ok=True,
    )


def unhealthy_result() -> NetworkHealthResult:
    """Return an unhealthy network result."""

    return NetworkHealthResult(
        pppoe_ok=True,
        ipv4_ok=True,
        gateway_ok=True,
        dns_ok=True,
        https_ok=False,
    )


def test_service_starts_and_stops_cleanly():
    """start() should initialize the connection and stop cleanly."""

    service, manager = create_service()

    manager.connect.return_value = RasdialResult(
        success=True,
        output="Connected.",
        return_code=0,
    )

    with (
        patch(
            "ntou_pppoe.core.service.time.sleep",
        ),
        patch.object(
            service,
            "_run_loop",
        ),
    ):
        service.start()

    assert service.running is False
    manager.connect.assert_called_once()
    manager.health_check.assert_not_called()


def test_start_waits_for_startup_delay():
    """start() should wait for the configured startup delay."""

    service, manager = create_service()

    manager.connect.return_value = RasdialResult(
        success=True,
        output="Connected.",
        return_code=0,
    )

    manager.health_check.return_value = healthy_result()

    with (
        patch(
            "ntou_pppoe.core.service.time.sleep",
        ) as sleep,
        patch.object(
            service,
            "_run_loop",
        ),
    ):
        service.start()

    sleep.assert_any_call(5)


def test_initial_connection_failure_does_not_crash_service():
    """An initial connection failure should be handled gracefully."""

    service, manager = create_service()

    manager.connect.return_value = RasdialResult(
        success=False,
        output="Connection failed.",
        return_code=628,
    )

    with (
        patch(
            "ntou_pppoe.core.service.time.sleep",
        ),
        patch.object(
            service,
            "_run_loop",
        ),
    ):
        service.start()

    assert service.running is False
    manager.health_check.assert_not_called()


def test_stop_is_idempotent():
    """stop() should be safe to call multiple times."""

    service, manager = create_service()

    service.running = True

    service.stop()
    service.stop()

    assert service.running is False
    manager.logger.info.assert_called_once_with("NTOU-PPPoE service stopped.")


def test_run_cycle_recovers_when_disconnected():
    """A disconnected service should attempt recovery."""

    service, manager = create_service()

    manager.state = ConnectionState.DISCONNECTED

    manager.recover.return_value = RasdialResult(
        success=True,
        output="Recovered.",
        return_code=0,
    )

    manager.health_check.return_value = healthy_result()

    service._run_cycle()

    manager.recover.assert_called_once()
    manager.health_check.assert_called_once()


def test_run_cycle_recovers_after_previous_retry():
    """A disconnected service with retries should recover."""

    service, manager = create_service()

    manager.state = ConnectionState.DISCONNECTED
    manager.retry.attempt = 1

    manager.recover.return_value = RasdialResult(
        success=True,
        output="Recovered.",
        return_code=0,
    )

    manager.health_check.return_value = healthy_result()

    service._run_cycle()

    manager.recover.assert_called_once()
    manager.connect.assert_not_called()
    manager.health_check.assert_called_once()


def test_run_cycle_checks_health_when_connected():
    """A connected service should perform a health check."""

    service, manager = create_service()

    manager.state = ConnectionState.CONNECTED
    manager.health_check.return_value = healthy_result()

    service._run_cycle()

    manager.health_check.assert_called_once()
    manager.recover.assert_not_called()


def test_run_cycle_recovers_when_health_check_fails():
    """A failed health check should trigger recovery."""

    service, manager = create_service()

    manager.state = ConnectionState.CONNECTED

    manager.health_check.return_value = unhealthy_result()

    manager.recover.return_value = RasdialResult(
        success=True,
        output="Recovered.",
        return_code=0,
    )

    service._run_cycle()

    assert manager.health_check.call_count == 2
    manager.recover.assert_called_once()


def test_run_cycle_recovers_from_error_state():
    """An error state should attempt recovery when retries remain."""

    service, manager = create_service()

    manager.state = ConnectionState.ERROR
    manager.retry.can_retry.return_value = True

    manager.recover.return_value = RasdialResult(
        success=True,
        output="Recovered.",
        return_code=0,
    )

    manager.health_check.return_value = healthy_result()

    service._run_cycle()

    manager.recover.assert_called_once()
    manager.health_check.assert_called_once()


def test_run_cycle_does_not_recover_when_error_has_no_retries():
    """An error state with no retries should remain untouched."""

    service, manager = create_service()

    manager.state = ConnectionState.ERROR
    manager.retry.can_retry.return_value = False

    service._run_cycle()

    manager.recover.assert_not_called()
    manager.health_check.assert_not_called()


def test_start_handles_keyboard_interrupt():
    """start() should gracefully handle Ctrl+C."""

    service, manager = create_service()

    manager.connect.return_value = RasdialResult(
        success=True,
        output="Connected.",
        return_code=0,
    )

    manager.health_check.return_value = healthy_result()

    def raise_keyboard_interrupt() -> None:
        raise KeyboardInterrupt

    with patch.object(
        service,
        "_run_loop",
        side_effect=raise_keyboard_interrupt,
    ):
        service.start()

    assert service.running is False
    manager.logger.info.assert_any_call("Shutdown requested by user.")


def test_start_handles_unexpected_errors():
    """start() should enter ERROR state on unexpected failures."""

    service, manager = create_service()

    manager.connect.side_effect = RuntimeError("Unexpected failure")

    with patch(
        "ntou_pppoe.core.service.time.sleep",
    ):
        service.start()

    assert service.running is False
    assert manager.state == ConnectionState.ERROR
    manager.logger.exception.assert_called_once_with("Unexpected error in service.")
