from __future__ import annotations

import time

from ntou_pppoe.core.manager import ConnectionManager
from ntou_pppoe.core.state import ConnectionState


class ConnectionService:
    """Run the PPPoE connection manager as a long-running service."""

    def __init__(self, manager: ConnectionManager):
        self.manager = manager
        self.running = False

    def start(self) -> None:
        """Start the connection monitoring loop."""
        self.running = True

        self.manager.logger.info("NTOU-PPPoE service started.")

        try:
            startup_delay = self.manager.config["startup_delay"]

            if startup_delay > 0:
                self.manager.logger.info(
                    "Waiting %.1f seconds before startup.",
                    startup_delay,
                )
                time.sleep(startup_delay)

            self._initialize_connection()
            self._run_loop()
        except KeyboardInterrupt:
            self.manager.logger.info("Shutdown requested by user.")
        except Exception:
            self.manager.state = ConnectionState.ERROR

            self.manager.logger.exception("Unexpected error in service.")
        finally:
            self.stop()

    def stop(self) -> None:
        """Stop the connection monitoring loop."""
        if not self.running:
            return

        self.running = False

        self.manager.logger.info("NTOU-PPPoE service stopped.")

    def _initialize_connection(self) -> None:
        """Establish the initial PPPoE connection."""
        self.manager.state = ConnectionState.STARTING

        self.manager.logger.info("Initializing PPPoE connection.")

        result = self.manager.connect()

        if result.success:
            return

        self.manager.state = ConnectionState.DISCONNECTED

        self.manager.logger.warning(
            "Initial PPPoE connection failed. Automatic recovery will be attempted."
        )

    def _run_loop(self) -> None:
        """Run the main monitoring loop."""
        while self.running:
            self._run_cycle()

            if not self.running:
                break

            time.sleep(
                self.manager.config["check_interval"],
            )

    def _run_cycle(self) -> None:
        """Run one connection monitoring cycle."""

        if self.manager.state == ConnectionState.ERROR:
            if not self.manager.retry.can_retry():
                self.manager.logger.warning(
                    "Recovery attempts exhausted. "
                    "Waiting before starting a new recovery cycle."
                )

                self.manager.retry.reset()
                self.manager.state = ConnectionState.DISCONNECTED

                return

            result = self.manager.recover()

            if result.success:
                self.manager.health_check()

            return

        if self.manager.state == ConnectionState.DISCONNECTED:
            result = self.manager.recover()

            if result.success:
                self.manager.health_check()

            return

        health = self.manager.health_check()

        if health.healthy:
            return

        result = self.manager.recover()

        if result.success:
            self.manager.health_check()
