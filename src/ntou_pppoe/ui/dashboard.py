from __future__ import annotations

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from ntou_pppoe.core.state import ConnectionState
from ntou_pppoe.network.connectivity import NetworkHealthResult
from ntou_pppoe.network.diagnostics import NetworkDiagnostics


class Dashboard:
    """Render the NTOU PPPoE terminal dashboard."""

    def __init__(self, console: Console | None = None):
        self.console = console or Console()

    def render(
        self,
        *,
        profile_name: str,
        state: ConnectionState,
        health: NetworkHealthResult | None = None,
        diagnostics: NetworkDiagnostics | None = None,
        retry_attempt: int = 0,
    ) -> None:
        """Render the current connection status."""

        state_label, state_style = self._get_state_display(state)

        table = Table.grid(
            padding=(0, 1),
            expand=False,
        )

        table.add_column(
            style="bold",
            width=12,
        )
        table.add_column(
            width=34,
        )

        table.add_row(
            "Status",
            f"[{state_style}]● {state_label}[/{state_style}]",
        )

        table.add_row(
            "Profile",
            profile_name,
        )

        table.add_row(
            "IPv4",
            (
                diagnostics.ipv4_address
                if diagnostics and diagnostics.ipv4_address
                else "[dim]Unknown[/dim]"
            ),
        )

        table.add_row(
            "Gateway",
            (
                diagnostics.default_gateway
                if diagnostics and diagnostics.default_gateway
                else "[dim]Unknown[/dim]"
            ),
        )

        dns_value = (
            ", ".join(diagnostics.dns_servers)
            if diagnostics and diagnostics.dns_servers
            else None
        )

        table.add_row(
            "DNS",
            dns_value or "[dim]Unknown[/dim]",
        )

        if health is not None:
            table.add_section()

            checks = [
                ("PPPoE", health.pppoe_ok),
                ("IPv4", health.ipv4_ok),
                ("Gateway", health.gateway_ok),
                ("DNS", health.dns_ok),
                ("HTTPS", health.https_ok),
            ]

            passed = sum(ok for _, ok in checks)

            health_style = "green" if health.healthy else "red"

            table.add_row(
                "Health",
                (
                    f"[{health_style}]"
                    f"{self._health_bar(passed)}"
                    f"[/{health_style}] "
                    f"{passed}/5"
                ),
            )

            table.add_row(
                "Checks",
                self._format_checks(checks),
            )
        else:
            table.add_section()

            table.add_row(
                "Health",
                "[dim]Not checked[/dim]",
            )

        table.add_row(
            "Retry",
            str(retry_attempt),
        )

        title = "[bold cyan]NTOU PPPoE[/bold cyan] [dim]Manager[/dim]"

        panel = Panel(
            table,
            title=title,
            border_style=state_style,
            expand=False,
            padding=(1, 1),
        )

        self.console.print(panel)

    @staticmethod
    def _health_bar(passed: int) -> str:
        """Return a compact health indicator."""

        return "█" * passed + "░" * (5 - passed)

    @staticmethod
    def _format_checks(
        checks: list[tuple[str, bool]],
    ) -> str:
        """Return a compact representation of health checks."""

        return " ".join(
            f"[{'green' if ok else 'red'}]"
            f"{'✓' if ok else '✗'}"
            f"[/{'green' if ok else 'red'}]"
            for _, ok in checks
        )

    @staticmethod
    def _get_state_display(
        state: ConnectionState,
    ) -> tuple[str, str]:
        """Return the display label and Rich style for a state."""

        states = {
            ConnectionState.STARTING: ("Starting", "cyan"),
            ConnectionState.DISCONNECTED: ("Disconnected", "red"),
            ConnectionState.CONNECTING: ("Connecting", "yellow"),
            ConnectionState.CONNECTED: ("Connected", "green"),
            ConnectionState.DEGRADED: ("Degraded", "yellow"),
            ConnectionState.RECOVERING: ("Recovering", "yellow"),
            ConnectionState.ERROR: ("Error", "red"),
        }

        return states.get(
            state,
            ("Unknown", "white"),
        )
