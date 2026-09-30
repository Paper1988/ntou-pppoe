from __future__ import annotations

from unittest.mock import MagicMock, patch

from ntou_pppoe.cli import create_parser, run_command
from ntou_pppoe.core.state import ConnectionState
from ntou_pppoe.network.connectivity import NetworkHealthResult
from ntou_pppoe.network.diagnostics import NetworkDiagnostics
from ntou_pppoe.network.pppoe import RasdialResult


def create_manager() -> MagicMock:
    """Create a mocked connection manager."""

    manager = MagicMock()

    manager.pppoe.connection_name = "NTOU-PPPoE"
    manager.state = ConnectionState.CONNECTED
    manager.retry.attempt = 0

    manager.config = {
        "startup_delay": 5,
        "check_interval": 30,
    }

    return manager


def healthy_result() -> NetworkHealthResult:
    """Return a healthy network result."""

    return NetworkHealthResult(
        pppoe_ok=True,
        ipv4_ok=True,
        gateway_ok=True,
        dns_ok=True,
        https_ok=True,
    )


def diagnostics_result() -> NetworkDiagnostics:
    """Return sample network diagnostics."""

    return NetworkDiagnostics(
        ipv4_address="118.167.200.241",
        default_gateway="26.0.0.1",
        dns_servers=(
            "168.95.192.1",
            "168.95.1.1",
        ),
    )


def test_parser_accepts_all_commands():
    """The CLI parser should accept all supported commands."""

    parser = create_parser()

    for command in [
        "start",
        "connect",
        "disconnect",
        "status",
        "diagnose",
    ]:
        args = parser.parse_args([command])

        assert args.command == command


def test_connect_command():
    """connect should connect, check health, and render the dashboard."""

    manager = create_manager()

    manager.connect.return_value = RasdialResult(
        success=True,
        output="PPPoE connection established.",
        return_code=0,
    )

    with (
        patch(
            "ntou_pppoe.cli.ConnectionManager",
            return_value=manager,
        ),
        patch(
            "ntou_pppoe.cli.Dashboard",
        ) as dashboard_class,
    ):
        run_command("connect")

    manager.connect.assert_called_once()
    manager.health_check.assert_called_once()
    manager.get_diagnostics.assert_called_once()

    dashboard_class.return_value.render.assert_called_once_with(
        profile_name="NTOU-PPPoE",
        state=ConnectionState.CONNECTED,
        health=manager.health_check.return_value,
        diagnostics=manager.get_diagnostics.return_value,
        retry_attempt=0,
    )


def test_connect_command_prints_error_on_failure():
    """connect should print the failure output."""

    manager = create_manager()

    manager.connect.return_value = RasdialResult(
        success=False,
        output="RasDialW failed with error 628.",
        return_code=628,
    )

    with (
        patch(
            "ntou_pppoe.cli.ConnectionManager",
            return_value=manager,
        ),
        patch(
            "ntou_pppoe.cli.Dashboard",
        ),
        patch(
            "builtins.print",
        ) as print_mock,
    ):
        run_command("connect")

    print_mock.assert_any_call()
    print_mock.assert_any_call(
        "RasDialW failed with error 628.",
    )


def test_disconnect_command():
    """disconnect should disconnect and render the dashboard."""

    manager = create_manager()

    manager.disconnect.return_value = RasdialResult(
        success=True,
        output="PPPoE connection disconnected.",
        return_code=0,
    )

    with (
        patch(
            "ntou_pppoe.cli.ConnectionManager",
            return_value=manager,
        ),
        patch(
            "ntou_pppoe.cli.Dashboard",
        ) as dashboard_class,
    ):
        run_command("disconnect")

    manager.disconnect.assert_called_once()

    dashboard_class.return_value.render.assert_called_once_with(
        profile_name="NTOU-PPPoE",
        state=ConnectionState.CONNECTED,
        retry_attempt=0,
    )


def test_disconnect_command_prints_error_on_failure():
    """disconnect should print the failure output."""

    manager = create_manager()

    manager.disconnect.return_value = RasdialResult(
        success=False,
        output="RasHangUpW failed with error 6.",
        return_code=6,
    )

    with (
        patch(
            "ntou_pppoe.cli.ConnectionManager",
            return_value=manager,
        ),
        patch(
            "ntou_pppoe.cli.Dashboard",
        ),
        patch(
            "builtins.print",
        ) as print_mock,
    ):
        run_command("disconnect")

    print_mock.assert_any_call()
    print_mock.assert_any_call(
        "RasHangUpW failed with error 6.",
    )


def test_status_command():
    """status should run health and diagnostics checks."""

    manager = create_manager()

    manager.health_check.return_value = healthy_result()
    manager.get_diagnostics.return_value = diagnostics_result()

    with (
        patch(
            "ntou_pppoe.cli.ConnectionManager",
            return_value=manager,
        ),
        patch(
            "ntou_pppoe.cli.Dashboard",
        ) as dashboard_class,
    ):
        run_command("status")

    manager.health_check.assert_called_once()
    manager.get_diagnostics.assert_called_once()

    dashboard_class.return_value.render.assert_called_once_with(
        profile_name="NTOU-PPPoE",
        state=ConnectionState.CONNECTED,
        health=healthy_result(),
        diagnostics=diagnostics_result(),
        retry_attempt=0,
    )


def test_diagnose_command():
    """diagnose should collect and render diagnostics."""

    manager = create_manager()

    manager.get_diagnostics.return_value = diagnostics_result()

    with (
        patch(
            "ntou_pppoe.cli.ConnectionManager",
            return_value=manager,
        ),
        patch(
            "ntou_pppoe.cli.Dashboard",
        ) as dashboard_class,
    ):
        run_command("diagnose")

    manager.get_diagnostics.assert_called_once()
    manager.health_check.assert_not_called()

    dashboard_class.return_value.render.assert_called_once_with(
        profile_name="NTOU-PPPoE",
        state=ConnectionState.CONNECTED,
        diagnostics=diagnostics_result(),
        retry_attempt=0,
    )


def test_start_command():
    """start should create and run the connection service."""

    manager = create_manager()

    with (
        patch(
            "ntou_pppoe.cli.ConnectionManager",
            return_value=manager,
        ),
        patch(
            "ntou_pppoe.cli.Dashboard",
        ),
        patch(
            "ntou_pppoe.cli.ConnectionService",
        ) as service_class,
    ):
        run_command("start")

    service_class.assert_called_once_with(manager)
    service_class.return_value.start.assert_called_once()


def test_run_command_returns_zero_on_success():
    """A successful command should return exit code 0."""

    manager = create_manager()

    manager.connect.return_value = RasdialResult(
        success=True,
        output="PPPoE connection established.",
        return_code=0,
    )

    with (
        patch(
            "ntou_pppoe.cli.ConnectionManager",
            return_value=manager,
        ),
        patch(
            "ntou_pppoe.cli.Dashboard",
        ),
    ):
        result = run_command("connect")

    assert result == 0


def test_run_command_returns_nonzero_on_connect_failure():
    """A failed connect command should return a non-zero exit code."""

    manager = create_manager()

    manager.connect.return_value = RasdialResult(
        success=False,
        output="RasDialW failed with error 628.",
        return_code=628,
    )

    with (
        patch(
            "ntou_pppoe.cli.ConnectionManager",
            return_value=manager,
        ),
        patch(
            "ntou_pppoe.cli.Dashboard",
        ),
        patch(
            "builtins.print",
        ),
    ):
        result = run_command("connect")

    assert result == 628


def test_run_command_returns_nonzero_on_disconnect_failure():
    """A failed disconnect command should return a non-zero exit code."""

    manager = create_manager()

    manager.disconnect.return_value = RasdialResult(
        success=False,
        output="RasHangUpW failed with error 6.",
        return_code=6,
    )

    with (
        patch(
            "ntou_pppoe.cli.ConnectionManager",
            return_value=manager,
        ),
        patch(
            "ntou_pppoe.cli.Dashboard",
        ),
        patch(
            "builtins.print",
        ),
    ):
        result = run_command("disconnect")

    assert result == 6


def test_run_command_returns_zero_for_diagnose():
    """A successful diagnostic command should return exit code 0."""

    manager = create_manager()

    manager.get_diagnostics.return_value = diagnostics_result()

    with (
        patch(
            "ntou_pppoe.cli.ConnectionManager",
            return_value=manager,
        ),
        patch(
            "ntou_pppoe.cli.Dashboard",
        ),
    ):
        result = run_command("diagnose")

    assert result == 0
