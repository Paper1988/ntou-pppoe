from __future__ import annotations

import subprocess
from unittest.mock import patch

from ntou_pppoe.network.diagnostics import (
    NetworkDiagnostics,
    NetworkDiagnosticsCollector,
)


def create_collector() -> NetworkDiagnosticsCollector:
    """Create a diagnostics collector."""

    return NetworkDiagnosticsCollector()


def test_collect_returns_all_diagnostics():
    """collect() should return IPv4, gateway, and DNS information."""

    collector = create_collector()

    with (
        patch.object(
            collector,
            "_get_ipv4_address",
            return_value="118.167.200.241",
        ),
        patch.object(
            collector,
            "_get_default_gateway",
            return_value="26.0.0.1",
        ),
        patch.object(
            collector,
            "_get_dns_servers",
            return_value=(
                "168.95.192.1",
                "168.95.1.1",
            ),
        ),
    ):
        result = collector.collect()

    assert result == NetworkDiagnostics(
        ipv4_address="118.167.200.241",
        default_gateway="26.0.0.1",
        dns_servers=(
            "168.95.192.1",
            "168.95.1.1",
        ),
    )


def test_ipv4_address_returns_outbound_address():
    """IPv4 detection should return the socket's local address."""

    collector = create_collector()

    fake_socket = patch(
        "ntou_pppoe.network.diagnostics.socket.socket",
    )

    with fake_socket as socket_class:
        socket_instance = socket_class.return_value.__enter__.return_value
        socket_instance.getsockname.return_value = (
            "118.167.200.241",
            12345,
        )

        result = collector._get_ipv4_address()

    assert result == "118.167.200.241"
    socket_instance.connect.assert_called_once_with(
        ("8.8.8.8", 80),
    )


def test_ipv4_address_returns_none_on_socket_error():
    """IPv4 detection should return None when socket access fails."""

    collector = create_collector()

    with patch(
        "ntou_pppoe.network.diagnostics.socket.socket",
        side_effect=OSError("Network unavailable"),
    ):
        result = collector._get_ipv4_address()

    assert result is None


def test_default_gateway_is_parsed_from_route_output():
    """Gateway detection should parse the default route."""

    collector = create_collector()

    route_output = """
===========================================================================
Interface List
 10...00 00 00 00 00 00 ......Ethernet
===========================================================================
IPv4 Route Table
===========================================================================
Active Routes:
Network Destination        Netmask          Gateway       Interface
          0.0.0.0          0.0.0.0          26.0.0.1     118.167.200.241
        127.0.0.0        255.0.0.0          On-link       127.0.0.1
===========================================================================
"""

    completed = subprocess.CompletedProcess(
        args=["route", "print", "0.0.0.0"],
        returncode=0,
        stdout=route_output,
        stderr="",
    )

    with patch(
        "ntou_pppoe.network.diagnostics.subprocess.run",
        return_value=completed,
    ):
        result = create_collector()._get_default_gateway()

    assert result == "26.0.0.1"


def test_default_gateway_ignores_on_link_route():
    """An On-link default route should not be returned as a gateway."""

    route_output = """
0.0.0.0          0.0.0.0          On-link       118.167.200.241
"""

    completed = subprocess.CompletedProcess(
        args=["route", "print", "0.0.0.0"],
        returncode=0,
        stdout=route_output,
        stderr="",
    )

    with patch(
        "ntou_pppoe.network.diagnostics.subprocess.run",
        return_value=completed,
    ):
        result = create_collector()._get_default_gateway()

    assert result is None


def test_default_gateway_returns_none_when_command_fails():
    """Gateway detection should return None when route fails."""

    completed = subprocess.CompletedProcess(
        args=["route", "print", "0.0.0.0"],
        returncode=1,
        stdout="",
        stderr="Route failed",
    )

    with patch(
        "ntou_pppoe.network.diagnostics.subprocess.run",
        return_value=completed,
    ):
        result = create_collector()._get_default_gateway()

    assert result is None


def test_default_gateway_returns_none_when_command_is_missing():
    """Gateway detection should handle a missing route command."""

    with patch(
        "ntou_pppoe.network.diagnostics.subprocess.run",
        side_effect=FileNotFoundError,
    ):
        result = create_collector()._get_default_gateway()

    assert result is None


def test_default_gateway_returns_none_on_timeout():
    """Gateway detection should handle command timeouts."""

    with patch(
        "ntou_pppoe.network.diagnostics.subprocess.run",
        side_effect=subprocess.TimeoutExpired(
            cmd="route",
            timeout=10,
        ),
    ):
        result = create_collector()._get_default_gateway()

    assert result is None


def test_dns_servers_are_parsed_from_powershell_output():
    """DNS detection should return configured IPv4 DNS servers."""

    powershell_output = """
168.95.192.1
168.95.1.1
172.20.10.1
"""

    completed = subprocess.CompletedProcess(
        args=["powershell"],
        returncode=0,
        stdout=powershell_output,
        stderr="",
    )

    with patch(
        "ntou_pppoe.network.diagnostics.subprocess.run",
        return_value=completed,
    ):
        result = create_collector()._get_dns_servers()

    assert result == (
        "168.95.192.1",
        "168.95.1.1",
        "172.20.10.1",
    )


def test_dns_servers_ignore_empty_lines():
    """DNS detection should ignore blank output lines."""

    powershell_output = """
168.95.192.1

168.95.1.1

"""

    completed = subprocess.CompletedProcess(
        args=["powershell"],
        returncode=0,
        stdout=powershell_output,
        stderr="",
    )

    with patch(
        "ntou_pppoe.network.diagnostics.subprocess.run",
        return_value=completed,
    ):
        result = create_collector()._get_dns_servers()

    assert result == (
        "168.95.192.1",
        "168.95.1.1",
    )


def test_dns_servers_return_empty_tuple_when_command_fails():
    """DNS detection should return an empty tuple on failure."""

    completed = subprocess.CompletedProcess(
        args=["powershell"],
        returncode=1,
        stdout="",
        stderr="PowerShell failed",
    )

    with patch(
        "ntou_pppoe.network.diagnostics.subprocess.run",
        return_value=completed,
    ):
        result = create_collector()._get_dns_servers()

    assert result == ()


def test_dns_servers_return_empty_tuple_when_command_is_missing():
    """DNS detection should handle a missing PowerShell command."""

    with patch(
        "ntou_pppoe.network.diagnostics.subprocess.run",
        side_effect=FileNotFoundError,
    ):
        result = create_collector()._get_dns_servers()

    assert result == ()


def test_dns_servers_return_empty_tuple_on_timeout():
    """DNS detection should handle PowerShell timeouts."""

    with patch(
        "ntou_pppoe.network.diagnostics.subprocess.run",
        side_effect=subprocess.TimeoutExpired(
            cmd="powershell",
            timeout=10,
        ),
    ):
        result = create_collector()._get_dns_servers()

    assert result == ()
