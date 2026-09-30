from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path


def get_project_root() -> Path:
    """Return the project root directory."""
    return Path(__file__).resolve().parents[3]


def get_log_path() -> Path:
    """Return the application log path."""
    return get_project_root() / "logs" / "ntou-pppoe.log"


def setup_logger() -> logging.Logger:
    """Create and configure the application logger."""
    logger = logging.getLogger("ntou_pppoe")

    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)

    log_path = get_log_path()
    log_path.parent.mkdir(parents=True, exist_ok=True)

    handler = RotatingFileHandler(
        log_path,
        maxBytes=5 * 1024 * 1024,
        backupCount=3,
        encoding="utf-8",
    )

    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger
