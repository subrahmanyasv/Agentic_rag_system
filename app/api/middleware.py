"""HTTP-layer request logging middleware."""

import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import ASGIApp

from app.core.logger import bind_context, clear_context, get_logger

_access_logger = get_logger("access")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Logs one structured line per request to access.log.

    A request_id (reused from the `x-request-id` header if the caller
    supplied one, otherwise freshly generated) is bound into the logging
    context for the lifetime of the request. Any log line emitted by
    services further down the call stack automatically carries it too,
    which is what makes it possible to trace everything that happened
    for a single request across app.log, access.log, and error.log.
    """

    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        request_id = request.headers.get("x-request-id", str(uuid.uuid4()))
        bind_context(request_id=request_id)
        start = time.perf_counter()
        try:
            response = await call_next(request)
        except Exception:
            duration_ms = round((time.perf_counter() - start) * 1000, 2)
            _access_logger.error(
                "request_failed",
                method=request.method,
                path=request.url.path,
                duration_ms=duration_ms,
            )
            raise
        else:
            duration_ms = round((time.perf_counter() - start) * 1000, 2)
            _access_logger.info(
                "request_completed",
                method=request.method,
                path=request.url.path,
                status_code=response.status_code,
                duration_ms=duration_ms,
            )
            response.headers["x-request-id"] = request_id
            return response
        finally:
            clear_context()