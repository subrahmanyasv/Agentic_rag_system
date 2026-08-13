"""Central mapping from domain exceptions to HTTP responses.

This is the ONLY place in the application that knows "InvalidCredentialsError
means 401." Domain and service code (see app/services/auth_exceptions.py)
deliberately raises plain exceptions with no HTTP knowledge, so that those
services stay usable from any future entry point (a CLI tool, a worker,
another API) without dragging FastAPI along. Routes, in turn, no longer
need try/except at all — see app/api/routes.py — because Starlette's
exception middleware catches everything that escapes a route and looks it
up here by exception type.

Adding a new mapped exception is a one-line addition to _EXCEPTION_MAP.
Anything NOT listed here falls through to the catch-all Exception handler,
which never leaks internal details to the caller (AGENTS.md #9) but always
logs the full error server-side (AGENTS.md #10).
"""

from dataclasses import dataclass

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
import structlog

from app.models.error_response import ErrorResponse
from app.core.logger import get_logger
from app.repositories.interfaces import EmailAlreadyRegisteredError
from app.services.auth_exceptions import InvalidCredentialsError, InvalidRefreshTokenError

logger = get_logger(__name__)


@dataclass(frozen=True, slots=True)
class _ErrorMapping:
    """One row of the exception -> HTTP response table."""

    status_code: int
    error_code: str


# The single source of truth for "which exception means which HTTP status."
# Ordering does not matter for correctness: Starlette resolves a raised
# exception's *exact* type first, then walks up its MRO (its chain of
# parent classes) until it finds a registered match — so a more specific
# entry here is always preferred over a more general one automatically.
_EXCEPTION_MAP: dict[type[Exception], _ErrorMapping] = {
    EmailAlreadyRegisteredError: _ErrorMapping(status.HTTP_409_CONFLICT, "email_already_registered"),
    InvalidCredentialsError: _ErrorMapping(status.HTTP_401_UNAUTHORIZED, "invalid_credentials"),
    InvalidRefreshTokenError: _ErrorMapping(status.HTTP_401_UNAUTHORIZED, "invalid_refresh_token"),
}


def _current_request_id() -> str | None:
    """Read the request_id already bound by RequestLoggingMiddleware.

    Reused rather than re-derived so the id in the error body always
    matches the id on every log line for this same request.
    """
    return structlog.contextvars.get_contextvars().get("request_id")


def _make_domain_exception_handler(mapping: _ErrorMapping):
    """Build a handler that turns one mapped domain exception into a
    JSON response. A factory, rather than one function per exception
    type, since every mapped case does the identical thing: use the
    exception's own (already safe, user-facing) message.
    """

    async def handler(request: Request, exc: Exception) -> JSONResponse:
        logger.info(
            "request_rejected",
            error_code=mapping.error_code,
            status_code=mapping.status_code,
            path=request.url.path,
        )
        body = ErrorResponse(
            error=mapping.error_code,
            message=str(exc),
            request_id=_current_request_id(),
        )
        return JSONResponse(status_code=mapping.status_code, content=body.model_dump())

    return handler


async def _validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Replace FastAPI's default validation error body with the same
    uniform envelope used everywhere else, instead of exposing its raw,
    implementation-specific error list to the client unchanged.
    """
    logger.info(
        "request_validation_failed",
        path=request.url.path,
        error_count=len(exc.errors()),
    )
    body = ErrorResponse(
        error="validation_error",
        message="The request could not be validated. Check the submitted fields.",
        request_id=_current_request_id(),
    )
    return JSONResponse(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, content=body.model_dump())


async def _unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Catch-all for every exception not explicitly mapped above.

    This is the safety net: it guarantees two things simultaneously that
    the reference Express implementation did not (see AGENTS.md #9, #10):
    - the client NEVER sees `str(exc)` or any other internal detail, and
    - the full exception is ALWAYS logged server-side, so nothing about
      an unexpected failure is ever silently lost.
    """
    logger.error(
        "unhandled_exception",
        path=request.url.path,
        error_type=type(exc).__name__,
        exc_info=exc,
    )
    body = ErrorResponse(
        error="internal_error",
        message="An unexpected error occurred. Please try again later.",
        request_id=_current_request_id(),
    )
    return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content=body.model_dump())


def register_exception_handlers(application: FastAPI) -> None:
    """Register every exception handler on the given app.

    Called exactly once, from the composition root (app/main.py), next
    to where the request-logging middleware is attached.
    """
    for exception_type, mapping in _EXCEPTION_MAP.items():
        application.add_exception_handler(exception_type, _make_domain_exception_handler(mapping))

    application.add_exception_handler(RequestValidationError, _validation_exception_handler)
    application.add_exception_handler(Exception, _unhandled_exception_handler)

    logger.info("exception_handlers_registered", mapped_exception_count=len(_EXCEPTION_MAP))