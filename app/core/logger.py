"""
Centralized logging module for the application.

Note:if the logging backend ever needs to change (e.g. swapping structlog for a hosted APM/observability SDK once this MVP becomes a real product), the change is isolated to this file and `logging_config.py`. No call site anywhere else in the codebase needs to be touched.
"""

from typing import Any
import structlog


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """Return a bound logger scoped to the given module name.
    Callers should pass `__name__` so log lines can be traced back to
    their originating module.
    """
    return structlog.get_logger(name)


def bind_context(**kwargs: Any) -> None:
    """Attach key-value pairs to every subsequent log line on this context.

    Used by request-scoped middleware to propagate a `request_id` (and any
    other per-request metadata) into logs emitted deep inside services,
    without threading it explicitly through every function signature.
    """
    structlog.contextvars.bind_contextvars(**kwargs)


def clear_context() -> None:
    """Remove all bound context variables.

    Must be called at the end of every request. Context variables are
    task-scoped rather than automatically reset between ASGI requests, so
    skipping this would leak one request's request_id into the next.
    """
    structlog.contextvars.clear_contextvars()