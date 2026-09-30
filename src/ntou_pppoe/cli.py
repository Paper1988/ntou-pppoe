from __future__ import annotations

import argparse

from ntou_pppoe.core.manager import ConnectionManager
from ntou_pppoe.core.service import ConnectionService
from ntou_pppoe.network.connectivity import NetworkHealthResult
from ntou_pppoe.ui.dashboard import Dashboard


def create_parser() -> argparse.ArgumentParser:
    """Create the command-line argument parser."""

    parser = argparse.ArgumentParser(
        prog="ntou-pppoe",
        description="NTOU PPPoE connection manager.",
    )

    parser.add_argument(
        "command",
        choices=[
            "start",
            "connect",
            "disconnect",
            "status",
            "diagnose",
        ],
        help="Command to execute.",
    )

    return parser


def _print_error(
    operation: str,
    output: str,
    return_code: int,
) -> None:
    """Print a consistent CLI error message."""

    print()
    print(f"❌ {operation} failed")
    print()

    if return_code > 0:
        print(f"Error code: {return_code}")

    if output:
        print(output)


def _print_health_failure(
    health: NetworkHealthResult,
) -> None:
    """Print the checks that failed during a health check."""

    checks = [
        ("PPPoE", health.pppoe_ok),
        ("IPv4", health.ipv4_ok),
        ("Gateway", health.gateway_ok),
        ("DNS", health.dns_ok),
        ("HTTPS", health.https_ok),
    ]

    failed_checks = [name for name, passed in checks if not passed]

    if not failed_checks:
        return

    print()
    print("⚠ Network health check failed")
    print("Failed checks: " + ", ".join(failed_checks))


def run_command(command: str) -> int:
    """Execute a CLI command and return its exit code."""

    manager = ConnectionManager()
    dashboard = Dashboard()

    if command == "start":
        service = ConnectionService(manager)
        service.start()
        return 0

    if command == "connect":
        result = manager.connect()

        if not result.success:
            dashboard.render(
                profile_name=manager.pppoe.connection_name,
                state=manager.state,
                retry_attempt=manager.retry.attempt,
            )

            _print_error(
                "PPPoE connection",
                result.output,
                result.return_code,
            )

            return result.return_code or 1

        health = manager.health_check()
        diagnostics = manager.get_diagnostics()

        dashboard.render(
            profile_name=manager.pppoe.connection_name,
            state=manager.state,
            health=health,
            diagnostics=diagnostics,
            retry_attempt=manager.retry.attempt,
        )

        if not health.healthy:
            _print_health_failure(health)

        return 0 if health.healthy else 1

    if command == "disconnect":
        result = manager.disconnect()

        dashboard.render(
            profile_name=manager.pppoe.connection_name,
            state=manager.state,
            retry_attempt=manager.retry.attempt,
        )

        if not result.success:
            _print_error(
                "PPPoE disconnection",
                result.output,
                result.return_code,
            )

            return result.return_code or 1

        return 0

    if command == "status":
        health = manager.health_check()
        diagnostics = manager.get_diagnostics()

        dashboard.render(
            profile_name=manager.pppoe.connection_name,
            state=manager.state,
            health=health,
            diagnostics=diagnostics,
            retry_attempt=manager.retry.attempt,
        )

        if not health.healthy:
            _print_health_failure(health)

        return 0 if health.healthy else 1

    if command == "diagnose":
        diagnostics = manager.get_diagnostics()

        dashboard.render(
            profile_name=manager.pppoe.connection_name,
            state=manager.state,
            diagnostics=diagnostics,
            retry_attempt=manager.retry.attempt,
        )

        return 0

    return 1


def main() -> int:
    """CLI entry point."""

    parser = create_parser()
    args = parser.parse_args()

    return run_command(args.command)
