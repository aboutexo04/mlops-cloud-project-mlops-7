"""Central logging configuration for pipeline modules."""

from __future__ import annotations

import logging
import sys


def configure_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """Return a logger with a standard configuration."""

    logger = logging.getLogger(name)

    # 이미 핸들러가 있으면 중복 추가하지 않음
    if logger.handlers:
        return logger

    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(formatter)

    logger.addHandler(handler)
    logger.setLevel(level)
    logger.propagate = False

    return logger


__all__ = ["configure_logger"]
