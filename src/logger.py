"""
Centralised logging setup for the automated trading system.

Usage:
    from src.logger import get_logger
    log = get_logger(__name__)
    log.info("message")

Two handlers are attached to every logger:
  • RotatingFileHandler  — DEBUG+  → logs/trading_system.log  (5 MB × 5 files)
  • StreamHandler        — INFO+   → stdout

Child loggers (e.g. get_logger("trading_system.portfolio")) inherit both
handlers automatically via the root "trading_system" logger.
"""

import logging
import logging.handlers
import os

_ROOT     = "trading_system"
_LOG_DIR  = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs")
_LOG_FILE = os.path.join(_LOG_DIR, "trading_system.log")

_FILE_FMT = logging.Formatter(
    "%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
_CONSOLE_FMT = logging.Formatter("%(levelname)-8s  %(message)s")


def _setup_root() -> logging.Logger:
    root = logging.getLogger(_ROOT)
    if root.handlers:
        return root

    root.setLevel(logging.DEBUG)
    os.makedirs(_LOG_DIR, exist_ok=True)

    fh = logging.handlers.RotatingFileHandler(
        _LOG_FILE, maxBytes=5 * 1024 * 1024, backupCount=5, encoding="utf-8"
    )
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(_FILE_FMT)

    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(_CONSOLE_FMT)

    root.addHandler(fh)
    root.addHandler(ch)
    root.propagate = False
    return root


def get_logger(name: str = _ROOT) -> logging.Logger:
    """Return a logger that writes to both log file and console.

    Pass __name__ (or any dot-separated name prefixed with 'trading_system')
    to get a child logger that inherits both handlers.
    """
    _setup_root()
    if not name.startswith(_ROOT):
        name = f"{_ROOT}.{name}"
    return logging.getLogger(name)
