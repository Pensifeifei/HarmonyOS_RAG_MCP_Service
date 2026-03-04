"""
Global logging configuration.

Provides a ``get_logger`` factory that returns consistently configured
loggers throughout the application.  The log level is driven by the
``LOG_LEVEL`` environment variable (defaults to INFO).
"""

from __future__ import annotations

import logging
import os
import sys


# Read log level early — before ``config.py`` to avoid circular imports.
_LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

# Common format:  [2026-03-04 18:00:00] [INFO] [module_name] message
_LOG_FORMAT = "[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s"
_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# Configure the root logger once.
logging.basicConfig(
    level=getattr(logging, _LOG_LEVEL, logging.INFO),
    format=_LOG_FORMAT,
    datefmt=_DATE_FORMAT,
    handlers=[logging.StreamHandler(sys.stderr)],
)


def get_logger(name: str) -> logging.Logger:
    """Return a named logger with the project-wide configuration.

    Args:
        name: Logger name, typically ``__name__`` of the calling module.

    Returns:
        A configured ``logging.Logger`` instance.
    """
    return logging.getLogger(name)
