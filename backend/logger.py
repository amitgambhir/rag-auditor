"""Structured JSON logger with per-request context propagation."""
from __future__ import annotations
import json
import logging
from contextvars import ContextVar

# Populated by the HTTP middleware; available everywhere in the call stack
request_id_var: ContextVar[str] = ContextVar("request_id", default="-")

# Standard LogRecord attributes we never want in the JSON payload
_STANDARD_ATTRS = frozenset({
    "args", "created", "exc_info", "exc_text", "filename", "funcName",
    "levelname", "levelno", "lineno", "message", "module", "msecs",
    "msg", "name", "pathname", "process", "processName", "relativeCreated",
    "stack_info", "thread", "threadName", "taskName",
})


class _JSONFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict = {
            "ts": self.formatTime(record, "%Y-%m-%dT%H:%M:%SZ"),
            "level": record.levelname,
            "logger": record.name,
            "request_id": request_id_var.get("-"),
            "msg": record.getMessage(),
        }
        # Merge any extra= fields that aren't standard LogRecord attrs
        for key, val in record.__dict__.items():
            if key not in _STANDARD_ATTRS and not key.startswith("_") and key not in payload:
                payload[key] = val
        if record.exc_info:
            payload["exc"] = self.formatException(record.exc_info)
        return json.dumps(payload, default=str)


def configure_logging(level: str = "INFO") -> None:
    handler = logging.StreamHandler()
    handler.setFormatter(_JSONFormatter())
    logging.root.handlers = [handler]
    logging.root.setLevel(level)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
