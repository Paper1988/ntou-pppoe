from __future__ import annotations

import socket
import urllib.error
import urllib.request
from dataclasses import dataclass


@dataclass(frozen=True)
class ConnectivityResult:
    """Result of Internet connectivity checks."""

    dns_ok: bool
    https_ok: bool

    @property
    def healthy(self) -> bool:
        """Return whether all Internet checks passed."""
        return self.dns_ok and self.https_ok


@dataclass(frozen=True)
class NetworkHealthResult:
    """Complete result of a network health check."""

    pppoe_ok: bool
    ipv4_ok: bool
    gateway_ok: bool
    dns_ok: bool
    https_ok: bool

    @property
    def healthy(self) -> bool:
        """Return whether all network health checks passed."""
        return (
            self.pppoe_ok
            and self.ipv4_ok
            and self.gateway_ok
            and self.dns_ok
            and self.https_ok
        )


class ConnectivityChecker:
    """Perform basic Internet connectivity checks."""

    def __init__(
        self,
        dns_host: str,
        https_url: str,
        timeout: float = 5,
    ):
        self.dns_host = dns_host
        self.https_url = https_url
        self.timeout = timeout

    def check_dns(self) -> bool:
        """Check whether DNS resolution is working."""
        try:
            socket.gethostbyname(self.dns_host)
            return True
        except (socket.gaierror, OSError):
            return False

    def check_https(self) -> bool:
        """Check whether an HTTPS request can reach the Internet."""
        try:
            request = urllib.request.Request(
                self.https_url,
                method="HEAD",
            )

            with urllib.request.urlopen(
                request,
                timeout=self.timeout,
            ):
                return True

        except (urllib.error.URLError, OSError):
            return False

    def check(self) -> ConnectivityResult:
        """Run all Internet connectivity checks."""
        dns_ok = self.check_dns()

        if not dns_ok:
            return ConnectivityResult(
                dns_ok=False,
                https_ok=False,
            )

        https_ok = self.check_https()

        return ConnectivityResult(
            dns_ok=True,
            https_ok=https_ok,
        )
