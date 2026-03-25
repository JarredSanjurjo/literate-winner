"""Structured logging helpers."""

from __future__ import annotations

import logging


DEFAULT_LOG_FORMAT = "%(asctime)s %(levelname)s %(name)s %(message)s"


def configure_logging(level: str = "INFO") -> logging.Logger:
    """Configure and return the application logger."""

    logging.basicConfig(level=getattr(logging, level.upper(), logging.INFO), format=DEFAULT_LOG_FORMAT)
    return logging.getLogger("ai_workflow")
