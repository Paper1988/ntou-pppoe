from __future__ import annotations

import time

from ntou_pppoe.config.loader import load_config
from ntou_pppoe.config.validator import validate_config
from ntou_pppoe.core.retry import RetryController
from ntou_pppoe.core.state import ConnectionState
from ntou_pppoe.network.connectivity import (
    ConnectivityChecker,
    NetworkHealthResult,
)
from ntou_pppoe.network.diagnostics import (
    NetworkDiagnostics,
    NetworkDiagnosticsCollector,
)
from ntou_pppoe.network.pppoe import PPPoEManager, RasdialResult
from ntou_pppoe.utils.logger import setup_logger


class ConnectionManager:
    """Coordinate PPPoE connection and network recovery."""

    def __init__(self):
        config = load_config()
        validate_config(config)

        self.config = config
        self.state = ConnectionState.STARTING

        self.logger = setup_logger()

        self.pppoe = PPPoEManager(
            connection_name=config["connection_name"],
            timeout=config["connect_timeout"],
        )

        health_config = config["health_check"]

        self.health_check_enabled = health_config["enabled"]

        if self.health_check_enabled:
            self.connectivity = ConnectivityChecker(
                dns_host=health_config["dns_host"],
                https_url=health_config["https_url"],
                timeout=health_config["timeout"],
            )
        else:
            self.connectivity = None

        self.diagnostics = NetworkDiagnosticsCollector()

        retry_config = config["retry"]

        self.retry = RetryController(
            initial_delay=retry_config["initial_delay"],
            max_delay=retry_config["max_delay"],
            max_attempts=retry_config["max_attempts"],
        )

    def connect(self) -> RasdialResult:
        """Attempt to connect to the PPPoE network."""

        self.state = ConnectionState.CONNECTING

        self.logger.info(
            "Connecting to PPPoE profile: %s",
            self.pppoe.connection_name,
        )

        result = self.pppoe.connect()

        if not result.success:
            self.state = ConnectionState.DISCONNECTED

            self.logger.warning(
                "PPPoE connection failed: %s",
                result.output,
            )

            return result

        if not self.pppoe.is_connected():
            self.state = ConnectionState.DISCONNECTED

            self.logger.warning(
                "RAS reported success, but PPPoE connection could not be verified.",
            )

            return RasdialResult(
                success=False,
                output=(
                    "RAS reported success, but the PPPoE "
                    "connection could not be verified."
                ),
                return_code=result.return_code,
            )

        self.state = ConnectionState.CONNECTED
        self.retry.reset()

        self.logger.info(
            "PPPoE connection established and verified.",
        )

        return result

    def disconnect(self) -> RasdialResult:
        """Disconnect the PPPoE network and update manager state."""

        self.logger.info(
            "Disconnecting PPPoE profile: %s",
            self.pppoe.connection_name,
        )

        result = self.pppoe.disconnect()

        if result.success:
            self.state = ConnectionState.DISCONNECTED
            self.retry.reset()

            self.logger.info(
                "PPPoE connection disconnected and verified.",
            )
        else:
            if self.pppoe.is_connected():
                self.state = ConnectionState.CONNECTED
            else:
                self.state = ConnectionState.DISCONNECTED

            self.logger.warning(
                "PPPoE disconnection failed: %s",
                result.output,
            )

        return result

    def health_check(self) -> NetworkHealthResult:
        """Check whether the network connection is healthy."""

        if not self.health_check_enabled:
            self.logger.info("Network health check is disabled.")

            return NetworkHealthResult(
                pppoe_ok=True,
                ipv4_ok=True,
                gateway_ok=True,
                dns_ok=True,
                https_ok=True,
            )

        pppoe_ok = self.pppoe.is_connected()
        connectivity = self.connectivity.check()
        diagnostics = self.diagnostics.collect()

        result = NetworkHealthResult(
            pppoe_ok=pppoe_ok,
            ipv4_ok=diagnostics.ipv4_address is not None,
            gateway_ok=diagnostics.default_gateway is not None,
            dns_ok=connectivity.dns_ok,
            https_ok=connectivity.https_ok,
        )

        if result.healthy:
            self.state = ConnectionState.CONNECTED
            self.retry.reset()

            self.logger.info(
                "Network health check passed. "
                "PPPoE=%s IPv4=%s Gateway=%s DNS=%s HTTPS=%s",
                result.pppoe_ok,
                result.ipv4_ok,
                result.gateway_ok,
                result.dns_ok,
                result.https_ok,
            )
        else:
            self.state = ConnectionState.DEGRADED

            self.logger.warning(
                "Network health check failed. "
                "PPPoE=%s IPv4=%s Gateway=%s DNS=%s HTTPS=%s",
                result.pppoe_ok,
                result.ipv4_ok,
                result.gateway_ok,
                result.dns_ok,
                result.https_ok,
            )

        return result

    def recover(self) -> RasdialResult:
        """Attempt to recover a degraded connection."""

        self.state = ConnectionState.RECOVERING

        if not self.retry.can_retry():
            self.state = ConnectionState.ERROR

            self.logger.error(
                "Maximum recovery attempts reached.",
            )

            return RasdialResult(
                success=False,
                output="Maximum recovery attempts reached.",
                return_code=-4,
            )

        delay = self.retry.next_delay()

        self.logger.info(
            "Recovery attempt %d. Waiting %.1f seconds.",
            self.retry.attempt,
            delay,
        )

        time.sleep(delay)

        was_connected = self.pppoe.is_connected()

        self.logger.info(
            "PPPoE connection before recovery: %s",
            was_connected,
        )

        disconnect_result = self.disconnect()

        if not disconnect_result.success:
            self.state = ConnectionState.DISCONNECTED

            self.logger.warning(
                "Failed to disconnect PPPoE before recovery: %s",
                disconnect_result.output,
            )

        if self.pppoe.is_connected():
            self.state = ConnectionState.DISCONNECTED

            self.logger.warning(
                "PPPoE connection is still active after disconnect.",
            )

            return RasdialResult(
                success=False,
                output=("PPPoE connection is still active after disconnect."),
                return_code=disconnect_result.return_code,
            )

        self.logger.info(
            "PPPoE connection successfully disconnected.",
        )

        connect_result = self.connect()

        if connect_result.success:
            self.logger.info(
                "Recovery attempt succeeded.",
            )
        else:
            self.state = ConnectionState.DISCONNECTED

            self.logger.warning(
                "Recovery attempt failed: %s",
                connect_result.output,
            )

        return connect_result

    def get_diagnostics(self) -> NetworkDiagnostics:
        """Return current network diagnostics."""

        diagnostics = self.diagnostics.collect()

        self.logger.info(
            "Diagnostics: IPv4=%s Gateway=%s DNS=%s",
            diagnostics.ipv4_address,
            diagnostics.default_gateway,
            diagnostics.dns_servers,
        )

        return diagnostics
