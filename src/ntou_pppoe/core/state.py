from __future__ import annotations

from enum import Enum


class ConnectionState(Enum):
    """Possible states of the PPPoE connection manager."""

    STARTING = "starting"
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    DEGRADED = "degraded"
    RECOVERING = "recovering"
    ERROR = "error"
