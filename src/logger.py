"""
Centralized logging setup for AIMO.
All modules call get_logger(__name__) to get their named logger.
Writes to logs/aimo.log (DEBUG+) and stdout (INFO+).
"""

import logging
import os
from pathlib import Path

_LOG_DIR = Path(__file__).parent.parent / "logs"
_LOG_DIR.mkdir(exist_ok=True)

_FMT = logging.Formatter(
    "%(asctime)s [%(name)s] %(levelname)s — %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

_file_handler = logging.FileHandler(_LOG_DIR / "aimo.log", encoding="utf-8")
_file_handler.setLevel(logging.DEBUG)
_file_handler.setFormatter(_FMT)

_stream_handler = logging.StreamHandler()
_stream_handler.setLevel(logging.INFO)
_stream_handler.setFormatter(_FMT)


def get_logger(name: str) -> logging.Logger:
    """Returns a named logger with file + stream handlers (idempotent)."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(logging.DEBUG)
        logger.addHandler(_file_handler)
        logger.addHandler(_stream_handler)
        logger.propagate = False
    return logger
