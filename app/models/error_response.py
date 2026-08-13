"""Public schema for every error response the API returns.

Kept alongside the other schemas' spirit (see app/schemas/rag.py) rather
than inline inside the exception handlers, because this shape is a public
API contract that any client parses — it deserves the same visibility as
a request/response schema, not just an implementation detail of how
errors happen to be built.
"""

from pydantic import BaseModel


class ErrorResponse(BaseModel):
    """Uniform error envelope returned for every failed request.

    `error` is a stable, machine-readable code a client can branch on
    (e.g. "invalid_credentials"). `message` is safe to show a human.
    `request_id` lets a reported error be matched back to the exact
    server-side log lines that explain what actually happened.
    """

    error: str
    message: str
    request_id: str | None = None