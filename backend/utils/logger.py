"""
Centralized logging setup using loguru.

Import `logger` from this module anywhere in the backend instead of
calling `print()` or configuring `logging` per-file.
"""
import sys

from loguru import logger as _logger

from config.settings import get_config

_config = get_config()

_logger.remove()
_logger.add(
    sys.stdout,
    level=_config.log_level,
    format=(
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{module}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
        "<level>{message}</level>"
    ),
    colorize=True,
)
_logger.add(
    "logs/app.log",
    rotation="10 MB",
    retention="7 days",
    level=_config.log_level,
    enqueue=True,
)

logger = _logger
