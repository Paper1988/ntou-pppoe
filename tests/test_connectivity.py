from __future__ import annotations

from unittest.mock import patch

from ntou_pppoe.network.connectivity import (
    ConnectivityChecker,
    ConnectivityResult,
    NetworkHealthResult,
)


def create_checker() -> ConnectivityChecker:
    """Create a connectivity checker with test settings."""

    return ConnectivityChecker(
        dns_host="example.com",
        https_url="https://example.com",
        timeout=5,
    )


def test_dns_check_succeeds_when_resolution_works():
    """DNS check should succeed when hostname resolution works."""

    checker = create_checker()

    with patch(
        "ntou_pppoe.network.connectivity.socket.gethostbyname",
        return_value="93.184.216.34",
    ):
        assert checker.check_dns() is True


def test_dns_check_fails_when_resolution_fails():
    """DNS check should fail when hostname resolution fails."""

    checker = create_checker()

    with patch(
        "ntou_pppoe.network.connectivity.socket.gethostbyname",
        side_effect=OSError("DNS failure"),
    ):
        assert checker.check_dns() is False


def test_dns_check_fails_on_gaierror():
    """DNS check should handle socket resolution errors."""

    checker = create_checker()

    with patch(
        "ntou_pppoe.network.connectivity.socket.gethostbyname",
        side_effect=__import__("socket").gaierror,
    ):
        assert checker.check_dns() is False


def test_https_check_succeeds():
    """HTTPS check should succeed when the request works."""

    checker = create_checker()

    with patch(
        "ntou_pppoe.network.connectivity.urllib.request.urlopen",
    ) as urlopen:
        urlopen.return_value.__enter__.return_value = object()

        assert checker.check_https() is True


def test_https_check_fails_on_url_error():
    """HTTPS check should fail on URL errors."""

    checker = create_checker()

    with patch(
        "ntou_pppoe.network.connectivity.urllib.request.urlopen",
        side_effect=__import__("urllib").error.URLError("Connection failed"),
    ):
        assert checker.check_https() is False


def test_https_check_fails_on_os_error():
    """HTTPS check should fail on operating system errors."""

    checker = create_checker()

    with patch(
        "ntou_pppoe.network.connectivity.urllib.request.urlopen",
        side_effect=OSError("Network failure"),
    ):
        assert checker.check_https() is False


def test_check_returns_both_results_when_healthy():
    """check() should report successful DNS and HTTPS checks."""

    checker = create_checker()

    with (
        patch.object(
            checker,
            "check_dns",
            return_value=True,
        ),
        patch.object(
            checker,
            "check_https",
            return_value=True,
        ),
    ):
        result = checker.check()

    assert result == ConnectivityResult(
        dns_ok=True,
        https_ok=True,
    )


def test_check_skips_https_when_dns_fails():
    """HTTPS should not be checked when DNS resolution fails."""

    checker = create_checker()

    with (
        patch.object(
            checker,
            "check_dns",
            return_value=False,
        ),
        patch.object(
            checker,
            "check_https",
        ) as check_https,
    ):
        result = checker.check()

    assert result == ConnectivityResult(
        dns_ok=False,
        https_ok=False,
    )

    check_https.assert_not_called()


def test_connectivity_result_is_healthy_only_when_both_checks_pass():
    """ConnectivityResult should require DNS and HTTPS."""

    assert (
        ConnectivityResult(
            dns_ok=True,
            https_ok=True,
        ).healthy
        is True
    )

    assert (
        ConnectivityResult(
            dns_ok=True,
            https_ok=False,
        ).healthy
        is False
    )

    assert (
        ConnectivityResult(
            dns_ok=False,
            https_ok=True,
        ).healthy
        is False
    )

    assert (
        ConnectivityResult(
            dns_ok=False,
            https_ok=False,
        ).healthy
        is False
    )


def test_network_health_result_is_healthy_when_all_checks_pass():
    """NetworkHealthResult should be healthy when every check passes."""

    result = NetworkHealthResult(
        pppoe_ok=True,
        ipv4_ok=True,
        gateway_ok=True,
        dns_ok=True,
        https_ok=True,
    )

    assert result.healthy is True


def test_network_health_result_is_unhealthy_when_pppoe_fails():
    """A PPPoE failure should make the network unhealthy."""

    result = NetworkHealthResult(
        pppoe_ok=False,
        ipv4_ok=True,
        gateway_ok=True,
        dns_ok=True,
        https_ok=True,
    )

    assert result.healthy is False


def test_network_health_result_is_unhealthy_when_ipv4_fails():
    """An IPv4 failure should make the network unhealthy."""

    result = NetworkHealthResult(
        pppoe_ok=True,
        ipv4_ok=False,
        gateway_ok=True,
        dns_ok=True,
        https_ok=True,
    )

    assert result.healthy is False


def test_network_health_result_is_unhealthy_when_gateway_fails():
    """A gateway failure should make the network unhealthy."""

    result = NetworkHealthResult(
        pppoe_ok=True,
        ipv4_ok=True,
        gateway_ok=False,
        dns_ok=True,
        https_ok=True,
    )

    assert result.healthy is False


def test_network_health_result_is_unhealthy_when_dns_fails():
    """A DNS failure should make the network unhealthy."""

    result = NetworkHealthResult(
        pppoe_ok=True,
        ipv4_ok=True,
        gateway_ok=True,
        dns_ok=False,
        https_ok=True,
    )

    assert result.healthy is False


def test_network_health_result_is_unhealthy_when_https_fails():
    """An HTTPS failure should make the network unhealthy."""

    result = NetworkHealthResult(
        pppoe_ok=True,
        ipv4_ok=True,
        gateway_ok=True,
        dns_ok=True,
        https_ok=False,
    )

    assert result.healthy is False
