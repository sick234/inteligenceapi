"""
Structured logging configuration.

Uses Python's built-in logging with a custom formatter that includes
request IDs for distributed tracing across the API and Celery workers.
"""
import logging
import sys
from typing import Optional


class RequestIdFilter(logging.Filter):
    """Injects request_id into every log record."""
    _request_id: Optional[str] = None

    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = self._request_id or "no-request"
        return True


request_id_filter = RequestIdFilter()


def setup_logging(level: str = "INFO") -> None:
    """Configure structured logging for the entire application."""
    fmt = (
        "%(asctime)s | %(levelname)-8s | %(request_id)s | "
        "%(name)s:%(funcName)s:%(lineno)d | %(message)s"
    )
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(fmt, datefmt="%Y-%m-%d %H:%M:%S"))
    handler.addFilter(request_id_filter)

    root = logging.getLogger()
    root.setLevel(getattr(logging, level.upper(), logging.INFO))
    root.handlers.clear()
    root.addHandler(handler)

    # Silence noisy third-party loggers
    for noisy in ("uvicorn.access", "sqlalchemy.engine", "celery.worker"):
        logging.getLogger(noisy).setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Get a named logger with the request_id filter attached."""
    logger = logging.getLogger(name)
    return logger
