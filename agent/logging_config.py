"""Structured logging with event_id and job_id correlation."""

from __future__ import annotations

import json
import logging
import sys
from typing import Any


class CorrelatedFormatter(logging.Formatter):
    """JSON formatter that includes event_id and job_id in every log line."""

    def format(self, record: logging.LogRecord) -> str:
        log_entry: dict[str, Any] = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Attach correlation IDs if present on the record
        event_id = getattr(record, "event_id", None)
        job_id = getattr(record, "job_id", None)

        if event_id is not None:
            log_entry["event_id"] = str(event_id)
        if job_id is not None:
            log_entry["job_id"] = str(job_id)

        if record.exc_info and not record.exc_text:
            record.exc_text = self.formatException(record.exc_info)
        if record.exc_text:
            log_entry["exception"] = record.exc_text

        return json.dumps(log_entry)


def setup_logging(*, level: int = logging.INFO) -> logging.Logger:
    """Configure the root agent logger with JSON-formatted, correlated output.

    Returns the configured logger instance.
    """
    logger = logging.getLogger("agent")
    logger.setLevel(level)

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stderr)
        handler.setFormatter(CorrelatedFormatter())
        logger.addHandler(handler)

    return logger


def get_logger(name: str) -> logging.Logger:
    """Get a child logger under the ``agent`` namespace."""
    return logging.getLogger(f"agent.{name}")
