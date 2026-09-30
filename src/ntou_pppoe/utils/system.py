from __future__ import annotations

import os
import platform


def is_windows() -> bool:
    """Return whether the application is running on Windows."""
    return platform.system() == "Windows"


def is_admin() -> bool:
    """Return whether the current process has administrator privileges."""
    if not is_windows():
        return False

    try:
        import ctypes

        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except (AttributeError, OSError):
        return False


def get_process_id() -> int:
    """Return the current process ID."""
    return os.getpid()
