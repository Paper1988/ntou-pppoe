from __future__ import annotations

import ctypes
from unittest.mock import MagicMock, patch

from ntou_pppoe.network.pppoe import (
    RASCONNW,
    PPPoEManager,
)


def create_manager() -> PPPoEManager:
    """Create a PPPoE manager without requiring a real RAS API."""

    with patch("ntou_pppoe.network.pppoe.ctypes.WinDLL"):
        return PPPoEManager(
            connection_name="NTOU-PPPoE",
            timeout=1,
        )


def create_connection(
    entry_name: str,
) -> RASCONNW:
    """Create a fake RAS connection."""

    connection = RASCONNW()
    connection.dwSize = ctypes.sizeof(RASCONNW)
    connection.szEntryName = entry_name

    return connection


def test_find_connection_finds_matching_profile_after_buffer_resize():
    """_find_connection() should find the target among multiple connections."""

    manager = create_manager()

    other_connection = create_connection(
        "Other-Connection",
    )
    target_connection = create_connection(
        "NTOU-PPPoE",
    )

    fake_function = MagicMock()

    def fake_ras_enum(
        connection_buffer,
        buffer_size,
        connection_count,
    ):
        if connection_buffer is None:
            buffer_size._obj.value = ctypes.sizeof(RASCONNW) * 2
            connection_count._obj.value = 2
            return 603

        array = ctypes.cast(
            connection_buffer,
            ctypes.POINTER(RASCONNW),
        )

        array[0] = other_connection
        array[1] = target_connection

        buffer_size._obj.value = ctypes.sizeof(RASCONNW) * 2
        connection_count._obj.value = 2

        return 0

    fake_function.side_effect = fake_ras_enum

    manager._rasapi32.RasEnumConnectionsW = fake_function

    result = manager._find_connection()

    assert result is not None
    assert result.szEntryName == "NTOU-PPPoE"
    assert result.hrasconn == target_connection.hrasconn
