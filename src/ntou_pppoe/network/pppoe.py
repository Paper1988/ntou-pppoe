from __future__ import annotations

import ctypes
import time
from ctypes import wintypes
from dataclasses import dataclass
from pathlib import Path

RAS_MAX_ENTRY_NAME = 256
RAS_MAX_PHONE_NUMBER = 128
RAS_MAX_CALLBACK_NUMBER = 128
RAS_MAX_DEVICE_TYPE = 16
RAS_MAX_DEVICE_NAME = 128
UNLEN = 256
PWLEN = 256
DNLEN = 15
RASCS_DISCONNECTED = 0
RASCS_Connected = 8192


class GUID(ctypes.Structure):
    """Windows GUID structure."""

    _pack_ = 4

    _fields_ = [
        ("Data1", wintypes.DWORD),
        ("Data2", wintypes.WORD),
        ("Data3", wintypes.WORD),
        ("Data4", ctypes.c_ubyte * 8),
    ]


class LUID(ctypes.Structure):
    """Windows LUID structure."""

    _pack_ = 4

    _fields_ = [
        ("LowPart", wintypes.DWORD),
        ("HighPart", wintypes.LONG),
    ]


class RASDIALPARAMSW(ctypes.Structure):
    """Windows RAS dial parameters."""

    _fields_ = [
        ("dwSize", wintypes.DWORD),
        (
            "szEntryName",
            wintypes.WCHAR * (RAS_MAX_ENTRY_NAME + 1),
        ),
        (
            "szPhoneNumber",
            wintypes.WCHAR * (RAS_MAX_PHONE_NUMBER + 1),
        ),
        (
            "szCallbackNumber",
            wintypes.WCHAR * (RAS_MAX_CALLBACK_NUMBER + 1),
        ),
        (
            "szUserName",
            wintypes.WCHAR * (UNLEN + 1),
        ),
        (
            "szPassword",
            wintypes.WCHAR * (PWLEN + 1),
        ),
        (
            "szDomain",
            wintypes.WCHAR * (DNLEN + 1),
        ),
        ("dwSubEntry", wintypes.DWORD),
        ("dwCallbackId", ctypes.c_size_t),
        ("dwIfIndex", wintypes.DWORD),
    ]


class RASCONNW(ctypes.Structure):
    """Windows active RAS connection information."""

    _pack_ = 4

    _fields_ = [
        ("dwSize", wintypes.DWORD),
        ("hrasconn", ctypes.c_void_p),
        (
            "szEntryName",
            wintypes.WCHAR * (RAS_MAX_ENTRY_NAME + 1),
        ),
        (
            "szDeviceType",
            wintypes.WCHAR * (RAS_MAX_DEVICE_TYPE + 1),
        ),
        (
            "szDeviceName",
            wintypes.WCHAR * (RAS_MAX_DEVICE_NAME + 1),
        ),
        (
            "szPhonebook",
            wintypes.WCHAR * 260,
        ),
        ("dwSubEntry", wintypes.DWORD),
        ("guidEntry", GUID),
        ("dwFlags", wintypes.DWORD),
        ("luid", LUID),
        ("guidCorrelationId", GUID),
    ]


@dataclass(frozen=True)
class RasdialResult:
    """Result returned by a RAS operation."""

    success: bool
    output: str
    return_code: int


class PPPoEManager:
    """Manage a Windows PPPoE connection through the RAS API."""

    def __init__(
        self,
        connection_name: str,
        timeout: float = 30,
    ):
        self.connection_name = connection_name
        self.timeout = timeout

        self._rasapi32 = ctypes.WinDLL(
            "rasapi32.dll",
        )

        self._connection_handle: ctypes.c_void_p | None = None

    def connect(self) -> RasdialResult:
        """Connect to the configured PPPoE profile."""

        try:
            if self.is_connected():
                return RasdialResult(
                    success=True,
                    output=("PPPoE connection is already active."),
                    return_code=0,
                )

            pbk_path = self._get_pbk_path()

            if not pbk_path.is_file():
                return RasdialResult(
                    success=False,
                    output=(f"RAS phonebook not found: {pbk_path}"),
                    return_code=-1,
                )

            params = self._get_dial_params(
                pbk_path,
            )

            return self._ras_dial(params)

        except OSError as exc:
            return RasdialResult(
                success=False,
                output=f"Failed to load RAS API: {exc}",
                return_code=-2,
            )
        except Exception as exc:
            return RasdialResult(
                success=False,
                output=f"Unexpected RAS error: {exc}",
                return_code=-3,
            )

    def disconnect(self) -> RasdialResult:
        """Disconnect the configured PPPoE profile."""

        try:
            connection = self._find_connection()

            if connection is None:
                self._connection_handle = None

                return RasdialResult(
                    success=True,
                    output=("PPPoE connection is already disconnected."),
                    return_code=0,
                )

            result = self._ras_hang_up(
                connection.hrasconn,
            )

            if result != 0:
                return RasdialResult(
                    success=False,
                    output=(f"RasHangUpW failed with error {result}."),
                    return_code=result,
                )

            self._connection_handle = None

            if not self._wait_for_disconnect():
                return RasdialResult(
                    success=False,
                    output=(
                        "PPPoE disconnect requested, "
                        "but the connection is still active "
                        f"after {self.timeout:.1f} seconds."
                    ),
                    return_code=-4,
                )

            return RasdialResult(
                success=True,
                output="PPPoE connection disconnected.",
                return_code=0,
            )

        except OSError as exc:
            return RasdialResult(
                success=False,
                output=(f"Failed to access RAS API: {exc}"),
                return_code=-1,
            )
        except Exception as exc:
            return RasdialResult(
                success=False,
                output=f"Unexpected RAS error: {exc}",
                return_code=-2,
            )

    def is_connected(self) -> bool:
        """Return whether the configured PPPoE profile is connected."""

        try:
            connection = self._find_connection()

            if connection is None:
                self._connection_handle = None
                return False

            self._connection_handle = connection.hrasconn
            return True

        except (OSError, RuntimeError):
            self._connection_handle = None
            return False

    def _get_connect_status(
        self,
        connection_handle: ctypes.c_void_p,
    ) -> int | None:
        """Return the current RAS connection state."""

        function = self._rasapi32.RasGetConnectStatusW

        function.argtypes = [
            ctypes.c_void_p,
            ctypes.c_void_p,
        ]

        function.restype = wintypes.DWORD

        class RASCONNSTATUSW(ctypes.Structure):
            _fields_ = [
                ("dwSize", wintypes.DWORD),
                ("rasconnstate", wintypes.DWORD),
                ("dwError", wintypes.DWORD),
                ("szDeviceType", wintypes.WCHAR * (RAS_MAX_DEVICE_TYPE + 1)),
                ("szDeviceName", wintypes.WCHAR * (RAS_MAX_DEVICE_NAME + 1)),
                ("szPhoneNumber", wintypes.WCHAR * (RAS_MAX_PHONE_NUMBER + 1)),
            ]

        status = RASCONNSTATUSW()
        status.dwSize = ctypes.sizeof(RASCONNSTATUSW)

        result = function(
            connection_handle,
            ctypes.byref(status),
        )

        if result != 0:
            return None

        return status.rasconnstate

    def _wait_for_connect(self) -> bool:
        """Wait until the PPPoE connection becomes active."""

        deadline = time.monotonic() + self.timeout

        while time.monotonic() < deadline:
            if self.is_connected():
                return True

            time.sleep(0.25)

        return self.is_connected()

    def _wait_for_disconnect(self) -> bool:
        """Wait until the PPPoE connection is fully released."""

        deadline = time.monotonic() + self.timeout

        while time.monotonic() < deadline:
            connection = self._find_connection()

            if connection is None:
                # RAS has removed the connection from its active list.
                # Give RasMan a short settling period before another dial.
                time.sleep(0.5)

                return self._find_connection() is None

            status = self._get_connect_status(
                connection.hrasconn,
            )

            if status is None:
                time.sleep(0.25)
                continue

            if status == RASCS_DISCONNECTED:
                time.sleep(0.5)

                if self._find_connection() is None:
                    return True

            time.sleep(0.25)

        return self._find_connection() is None

    def _get_pbk_path(self) -> Path:
        """Return the current user's RAS phonebook path."""

        return (
            Path.home()
            / "AppData"
            / "Roaming"
            / "Microsoft"
            / "Network"
            / "Connections"
            / "Pbk"
            / "rasphone.pbk"
        )

    def _get_dial_params(
        self,
        pbk_path: Path,
    ) -> RASDIALPARAMSW:
        """Load saved dial parameters from the RAS phonebook."""

        function = self._rasapi32.RasGetEntryDialParamsW

        function.argtypes = [
            ctypes.c_wchar_p,
            ctypes.POINTER(RASDIALPARAMSW),
            ctypes.POINTER(wintypes.BOOL),
        ]

        function.restype = wintypes.DWORD

        params = RASDIALPARAMSW()
        params.dwSize = ctypes.sizeof(
            RASDIALPARAMSW,
        )
        params.szEntryName = self.connection_name

        password_was_returned = wintypes.BOOL(False)

        result = function(
            str(pbk_path),
            ctypes.byref(params),
            ctypes.byref(password_was_returned),
        )

        if result != 0:
            raise RuntimeError(f"RasGetEntryDialParamsW failed: {result}")

        return params

    def _ras_dial(
        self,
        params: RASDIALPARAMSW,
    ) -> RasdialResult:
        """Dial the PPPoE connection using the RAS API."""

        function = self._rasapi32.RasDialW

        function.argtypes = [
            ctypes.c_void_p,
            ctypes.c_wchar_p,
            ctypes.POINTER(RASDIALPARAMSW),
            wintypes.DWORD,
            ctypes.c_void_p,
            ctypes.POINTER(ctypes.c_void_p),
        ]

        function.restype = wintypes.DWORD

        connection_handle = ctypes.c_void_p()

        result = function(
            None,
            None,
            ctypes.byref(params),
            0,
            None,
            ctypes.byref(connection_handle),
        )

        if result == 756:
            for _ in range(3):
                time.sleep(0.5)

                if self.is_connected():
                    self._connection_handle = connection_handle

                    return RasdialResult(
                        success=True,
                        output="PPPoE connection established.",
                        return_code=0,
                    )

                result = function(
                    None,
                    None,
                    ctypes.byref(params),
                    0,
                    None,
                    ctypes.byref(connection_handle),
                )

                if result != 756:
                    break

        if result != 0:
            return RasdialResult(
                success=False,
                output=(f"RasDialW failed with error {result}."),
                return_code=result,
            )

        self._connection_handle = connection_handle

        if not self._wait_for_connect():
            return RasdialResult(
                success=False,
                output=(
                    "RasDialW reported success, "
                    "but the PPPoE connection could not "
                    f"be verified within {self.timeout:.1f} seconds."
                ),
                return_code=-4,
            )

        return RasdialResult(
            success=True,
            output="PPPoE connection established.",
            return_code=0,
        )

    def _find_connection(
        self,
    ) -> RASCONNW | None:
        """Find the active RAS connection for this profile."""

        function = self._rasapi32.RasEnumConnectionsW

        function.argtypes = [
            ctypes.POINTER(RASCONNW),
            ctypes.POINTER(wintypes.DWORD),
            ctypes.POINTER(wintypes.DWORD),
        ]

        function.restype = wintypes.DWORD

        buffer_size = wintypes.DWORD(0)
        connection_count = wintypes.DWORD(0)

        result = function(
            None,
            ctypes.byref(buffer_size),
            ctypes.byref(connection_count),
        )

        if result != 603:
            if result == 0 and connection_count.value == 0:
                return None

            raise RuntimeError(f"RasEnumConnectionsW failed: {result}")

        if buffer_size.value == 0:
            return None

        buffer = ctypes.create_string_buffer(
            buffer_size.value,
        )

        connection_array = ctypes.cast(
            buffer,
            ctypes.POINTER(RASCONNW),
        )

        connection_array[0].dwSize = ctypes.sizeof(
            RASCONNW,
        )

        result = function(
            connection_array,
            ctypes.byref(buffer_size),
            ctypes.byref(connection_count),
        )

        if result != 0:
            raise RuntimeError(f"RasEnumConnectionsW failed: {result}")

        for index in range(connection_count.value):
            connection = connection_array[index]

            if connection.szEntryName == self.connection_name:
                return connection

        return None

    def _ras_hang_up(
        self,
        connection_handle: ctypes.c_void_p,
    ) -> int:
        """Hang up an active RAS connection."""

        function = self._rasapi32.RasHangUpW

        function.argtypes = [
            ctypes.c_void_p,
        ]

        function.restype = wintypes.DWORD

        return function(connection_handle)
