"""
NOTE: This is a temporary file to hold domain exceptions for AuthService. It is deliberately

**************************************
IMPLEMENT GLOBAL EXCEPTION HANDLING IN LATER SPRINTS
**************************************

Domain exceptions for AuthService.

Plain Python exceptions, deliberately free of any HTTP-status knowledge —
routes are responsible for translating these into the correct
HTTPException, keeping AuthService unaware of FastAPI entirely.
"""


class InvalidCredentialsError(Exception):
    """Raised for both 'no such user' and 'wrong password'.

    Deliberately a single, identical error for both cases — the caller
    should never be able to distinguish which one occurred, to avoid
    leaking which emails are registered.
    """


class InvalidRefreshTokenError(Exception):
    """Raised when a refresh token is malformed, expired, or otherwise
    unusable. See token_service.py's module docstring: this currently
    cannot detect a token that was explicitly logged out, since there is
    no server-side store yet — only structural/expiry validity.
    """