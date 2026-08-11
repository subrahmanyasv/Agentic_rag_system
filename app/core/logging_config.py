"""Structlog + stdlib rotating-file-handler wiring.

This module owns all logging *configuration*: processors, JSON rendering, handlers, and rotation policy. Application code never touches any of this directly — it only ever calls `app.core.logger.get_logger()`.

Together with `app.core.logger`, this is the single place that would need to change if the logging backend is ever swapped (e.g. for a hosted observability platform once this project moves past MVP).
"""

import logging
import logging.handlers
import sys
from pathlib import Path
import structlog

from app.core.config import Settings

# Processors shared between structlog-originated and stdlib-originated log
# records, so both end up rendered identically in the JSON output.
_SHARED_PROCESSORS = [
    structlog.contextvars.merge_contextvars,
    structlog.stdlib.add_logger_name,
    structlog.stdlib.add_log_level,
    structlog.processors.TimeStamper(fmt="iso", utc=True),
    structlog.processors.StackInfoRenderer(),
    structlog.processors.format_exc_info,
]


def configure_logging(settings: Settings) -> None:
    """Configure structlog and the stdlib handlers it delegates to.

    Must be called exactly once, before the FastAPI app is created and
    before any `get_logger()` call is made elsewhere.
    """
    settings.log_dir.mkdir(parents=True, exist_ok=True)

    structlog.configure(
        processors=_SHARED_PROCESSORS + [structlog.stdlib.ProcessorFormatter.wrap_for_formatter],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    json_formatter = structlog.stdlib.ProcessorFormatter(
        processor=structlog.processors.JSONRenderer(),
        foreign_pre_chain=_SHARED_PROCESSORS,
    )

    _configure_root_logger(json_formatter, settings)
    _configure_access_logger(json_formatter, settings)
    _quiet_third_party_loggers()


def _configure_root_logger(formatter: logging.Formatter, settings: Settings) -> None:
    """Domain/application events -> stdout + app.log + error.log."""
    root_logger = logging.getLogger()
    root_logger.setLevel(settings.log_level)
    root_logger.handlers.clear()

    root_logger.addHandler(_stream_handler(formatter))
    root_logger.addHandler(_rotating_file_handler(
        settings.log_dir / "app.log", formatter, settings, min_level=logging.INFO,
    ))
    root_logger.addHandler(_rotating_file_handler(
        settings.log_dir / "error.log", formatter, settings, min_level=logging.ERROR,
    ))


def _configure_access_logger(formatter: logging.Formatter, settings: Settings) -> None:
    """HTTP request/response events -> stdout + access.log.

    Kept as a separate, non-propagating logger ("access") so per-request
    lines don't interleave with domain event lines inside app.log.
    """
    access_logger = logging.getLogger("access")
    access_logger.propagate = False
    access_logger.setLevel(logging.INFO)
    access_logger.handlers.clear()

    access_logger.addHandler(_stream_handler(formatter))
    access_logger.addHandler(_rotating_file_handler(
        settings.log_dir / "access.log", formatter, settings, min_level=logging.INFO,
    ))


def _quiet_third_party_loggers() -> None:
    """Prevent chatty dependencies from drowning out application events."""
    for noisy_logger_name in ("httpx", "httpcore", "chromadb", "sentence_transformers", "urllib3"):
        logging.getLogger(noisy_logger_name).setLevel(logging.WARNING)


def _stream_handler(formatter: logging.Formatter) -> logging.Handler:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    return handler


def _rotating_file_handler(
    path: Path, formatter: logging.Formatter, settings: Settings, min_level: int,
) -> logging.Handler:
    handler = logging.handlers.RotatingFileHandler(
        filename=str(path),
        maxBytes=settings.log_max_bytes,
        backupCount=settings.log_backup_count,
        encoding="utf-8",
    )
    handler.setFormatter(formatter)
    handler.setLevel(min_level)
    return handler