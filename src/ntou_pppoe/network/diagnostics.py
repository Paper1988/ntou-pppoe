from __future__ import annotations

import socket
import subprocess
from dataclasses import dataclass


@dataclass(frozen=True)
class NetworkDiagnostics:
    """Diagnostic information about the current network state."""

    ipv4_address: str | None
    default_gateway: str | None
    dns_servers: tuple[str, ...]


class NetworkDiagnosticsCollector:
    """Collect basic network information from Windows."""

    def collect(self) -> NetworkDiagnostics:
        """Collect the current network diagnostics."""
        return NetworkDiagnostics(
            ipv4_address=self._get_ipv4_address(),
            default_gateway=self._get_default_gateway(),
            dns_servers=self._get_dns_servers(),
        )

    def _get_ipv4_address(self) -> str | None:
        """Return the local IPv4 address used for outbound traffic."""
        try:
            with socket.socket(
                socket.AF_INET,
                socket.SOCK_DGRAM,
            ) as sock:
                sock.connect(("8.8.8.8", 80))
                return sock.getsockname()[0]
        except OSError:
            return None

    def _get_default_gateway(self) -> str | None:
        """Return the current default gateway."""
        try:
            result = subprocess.run(
                ["route", "print", "0.0.0.0"],
                capture_output=True,
                text=True,
                encoding="mbcs",
                errors="replace",
                timeout=10,
                check=False,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
        except (FileNotFoundError, OSError, subprocess.TimeoutExpired):
            return None

        for line in result.stdout.splitlines():
            parts = line.split()

            if len(parts) < 4:
                continue

            if parts[0] == "0.0.0.0" and parts[1] == "0.0.0.0":
                gateway = parts[2]

                if gateway != "On-link":
                    return gateway

        return None

    def _get_dns_servers(self) -> tuple[str, ...]:
        """Return DNS servers configured on the system."""
        try:
            result = subprocess.run(
                [
                    "powershell",
                    "-NoProfile",
                    "-Command",
                    (
                        "Get-DnsClientServerAddress "
                        "-AddressFamily IPv4 | "
                        "Select-Object -ExpandProperty ServerAddresses"
                    ),
                ],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=10,
                check=False,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
        except (FileNotFoundError, OSError, subprocess.TimeoutExpired):
            return ()

        servers = tuple(
            line.strip() for line in result.stdout.splitlines() if line.strip()
        )

        return servers
