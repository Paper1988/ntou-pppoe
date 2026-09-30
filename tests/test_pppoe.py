from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

from ntou_pppoe.network.pppoe import (
    RASDIALPARAMSW,
    PPPoEManager,
    RasdialResult,
)


def create_manager() -> PPPoEManager:
    """Create a PPPoE manager without requiring a real RAS API."""

    with patch("ntou_pppoe.network.pppoe.ctypes.WinDLL"):
        return PPPoEManager(
            connection_name="NTOU-PPPoE",
            timeout=1,
        )


def test_connect_returns_success_when_already_connected():
    """connect() should not dial an already active connection."""

    manager = create_manager()

    manager.is_connected = MagicMock(
        return_value=True,
    )

    result = manager.connect()

    assert result == RasdialResult(
        success=True,
        output="PPPoE connection is already active.",
        return_code=0,
    )


def test_connect_fails_when_phonebook_is_missing():
    """connect() should fail when the RAS phonebook does not exist."""

    manager = create_manager()

    manager.is_connected = MagicMock(
        return_value=False,
    )

    with patch.object(
        manager,
        "_get_pbk_path",
        return_value=Path("missing.pbk"),
    ):
        result = manager.connect()

    assert result.success is False
    assert result.return_code == -1
    assert "phonebook not found" in result.output


def test_connect_fails_when_dial_params_cannot_be_loaded():
    """connect() should report an error when dial parameters fail."""

    manager = create_manager()

    manager.is_connected = MagicMock(
        return_value=False,
    )

    with (
        patch.object(
            manager,
            "_get_pbk_path",
            return_value=Path("rasphone.pbk"),
        ),
        patch.object(
            Path,
            "is_file",
            return_value=True,
        ),
        patch.object(
            manager,
            "_get_dial_params",
            side_effect=RuntimeError("RasGetEntryDialParamsW failed: 623"),
        ),
    ):
        result = manager.connect()

    assert result.success is False
    assert result.return_code == -3
    assert "Unexpected RAS error" in result.output


def test_ras_dial_reports_api_error():
    """_ras_dial() should return the RAS API error code."""

    manager = create_manager()

    fake_function = MagicMock(
        return_value=628,
    )

    manager._rasapi32.RasDialW = fake_function

    params = RASDIALPARAMSW()
    params.dwSize = 1

    result = manager._ras_dial(params)

    assert result == RasdialResult(
        success=False,
        output="RasDialW failed with error 628.",
        return_code=628,
    )


def test_ras_dial_requires_connection_verification():
    """RasDialW success is not enough without connection verification."""

    manager = create_manager()

    fake_function = MagicMock(
        return_value=0,
    )

    manager._rasapi32.RasDialW = fake_function
    manager.is_connected = MagicMock(
        return_value=False,
    )

    params = RASDIALPARAMSW()
    params.dwSize = 1

    with patch.object(
        manager,
        "_wait_for_connect",
        return_value=False,
    ):
        result = manager._ras_dial(params)

    assert result.success is False
    assert result.return_code == -4
    assert "could not be verified" in result.output


def test_ras_dial_succeeds_after_connection_verification():
    """A verified RAS connection should return success."""

    manager = create_manager()

    fake_function = MagicMock(
        return_value=0,
    )

    manager._rasapi32.RasDialW = fake_function

    params = RASDIALPARAMSW()
    params.dwSize = 1

    with patch.object(
        manager,
        "_wait_for_connect",
        return_value=True,
    ):
        result = manager._ras_dial(params)

    assert result == RasdialResult(
        success=True,
        output="PPPoE connection established.",
        return_code=0,
    )


def test_disconnect_is_idempotent():
    """disconnect() should succeed when already disconnected."""

    manager = create_manager()

    manager._find_connection = MagicMock(
        return_value=None,
    )

    result = manager.disconnect()

    assert result == RasdialResult(
        success=True,
        output="PPPoE connection is already disconnected.",
        return_code=0,
    )


def test_disconnect_reports_hangup_error():
    """disconnect() should report RasHangUpW failures."""

    manager = create_manager()

    connection = MagicMock()
    connection.hrasconn = MagicMock()

    manager._find_connection = MagicMock(
        return_value=connection,
    )

    manager._ras_hang_up = MagicMock(
        return_value=6,
    )

    result = manager.disconnect()

    assert result == RasdialResult(
        success=False,
        output="RasHangUpW failed with error 6.",
        return_code=6,
    )


def test_disconnect_requires_completion_verification():
    """disconnect() should fail if the connection remains active."""

    manager = create_manager()

    connection = MagicMock()
    connection.hrasconn = MagicMock()

    manager._find_connection = MagicMock(
        return_value=connection,
    )

    manager._ras_hang_up = MagicMock(
        return_value=0,
    )

    with patch.object(
        manager,
        "_wait_for_disconnect",
        return_value=False,
    ):
        result = manager.disconnect()

    assert result.success is False
    assert result.return_code == -4
    assert "still active" in result.output


def test_disconnect_succeeds_after_completion_verification():
    """disconnect() should succeed after the connection disappears."""

    manager = create_manager()

    connection = MagicMock()
    connection.hrasconn = MagicMock()

    manager._find_connection = MagicMock(
        return_value=connection,
    )

    manager._ras_hang_up = MagicMock(
        return_value=0,
    )

    with patch.object(
        manager,
        "_wait_for_disconnect",
        return_value=True,
    ):
        result = manager.disconnect()

    assert result == RasdialResult(
        success=True,
        output="PPPoE connection disconnected.",
        return_code=0,
    )


def test_is_connected_returns_false_without_connection():
    """is_connected() should return false when no connection exists."""

    manager = create_manager()

    manager._find_connection = MagicMock(
        return_value=None,
    )

    assert manager.is_connected() is False


def test_is_connected_returns_true_for_matching_profile():
    """is_connected() should recognize the configured profile."""

    manager = create_manager()

    connection = MagicMock()
    connection.hrasconn = MagicMock()

    manager._find_connection = MagicMock(
        return_value=connection,
    )

    assert manager.is_connected() is True


def test_is_connected_handles_ras_errors():
    """is_connected() should safely handle RAS enumeration errors."""

    manager = create_manager()

    manager._find_connection = MagicMock(
        side_effect=RuntimeError("RasEnumConnectionsW failed: 632"),
    )

    assert manager.is_connected() is False
