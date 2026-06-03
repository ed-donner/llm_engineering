#!/usr/bin/env python3
"""
Shared logging utilities for Deal Intel.
"""

import logging
import os
from typing import Optional

DEFAULT_FORMAT = "[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s"
DEFAULT_DATEFMT = "%Y-%m-%d %H:%M:%S %z"

def init_logger(name: str, level: Optional[str] = None) -> logging.Logger:
    """
    Initialize and return a logger with consistent formatting.
    Level can be overridden via env DEAL_INTEL_LOG_LEVEL.
    """
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger  # avoid duplicate handlers

    env_level = os.getenv("DEAL_INTEL_LOG_LEVEL", "INFO")
    level = level or env_level
    level_map = {
        "CRITICAL": logging.CRITICAL,
        "ERROR": logging.ERROR,
        "WARNING": logging.WARNING,
        "INFO": logging.INFO,
        "DEBUG": logging.DEBUG,
    }
    logger.setLevel(level_map.get(level.upper(), logging.INFO))

    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter(DEFAULT_FORMAT, datefmt=DEFAULT_DATEFMT))
    logger.addHandler(handler)
    return logger