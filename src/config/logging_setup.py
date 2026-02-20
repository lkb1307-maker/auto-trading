from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from .constants import DEFAULT_LOG_FILE


def configure_logging(level_name: str = "INFO") -> logging.Logger:
    logger = logging.getLogger("auto_trader")
    logger.setLevel(getattr(logging, level_name.upper(), logging.INFO))
    logger.propagate = False

    if logger.handlers:
        return logger

    log_path = Path(DEFAULT_LOG_FILE)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)s | %(name)s | %(module)s | %(message)s"
    )

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    file_handler = RotatingFileHandler(log_path, maxBytes=1_000_000, backupCount=3)
    file_handler.setFormatter(formatter)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger
