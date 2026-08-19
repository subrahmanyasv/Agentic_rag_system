"""Issuing and verifying JWTs.

Refresh tokens are, for now, purely stateless (signature + expiry only) —
there is deliberately no server-side store yet. Revocation/rotation will
be added once the Redis-backed refresh-token cache is built (next
requirement after auth). Until then, `decode_refresh_token` can confirm
a token is well-formed and unexpired, but NOT that it hasn't been logged
out / revoked — that guarantee doesn't exist yet.
"""

import uuid
from datetime import datetime, timedelta, timezone
from typing import Protocol

import jwt

from app.core.config import Settings


class TokenExpiredError(Exception):
    """Raised when a token's signature is valid but it has expired."""


class InvalidTokenError(Exception):
    """Raised when a token is malformed, has a bad signature, or is
    otherwise unusable — distinct from simply being expired."""


class TokenServiceInterface(Protocol):
    def create_access_token(self, user_id: uuid.UUID) -> str: ...
    def create_refresh_token(self, user_id: uuid.UUID) -> str: ...
    def decode_access_token(self, token: str) -> uuid.UUID:
        """Return the user_id encoded in a valid access token.

        Raises TokenExpiredError or InvalidTokenError.
        """
        ...

    def decode_refresh_token(self, token: str) -> uuid.UUID:
        """Return the user_id encoded in a valid refresh token.

        Raises TokenExpiredError or InvalidTokenError. Confirms the
        token is well-formed and unexpired ONLY — see module docstring
        on why revocation is not yet enforced here.
        """
        ...


class JwtTokenService:
    """Stateless — no DB, no session. Built once at startup and shared
    across every request via app.state, same as PasswordHasherInterface.
    """

    _ACCESS_TOKEN_TYPE = "access"
    _REFRESH_TOKEN_TYPE = "refresh"

    def __init__(self, settings: Settings) -> None:
        self._secret_key = settings.jwt_secret_key
        self._algorithm = settings.jwt_algorithm
        self._access_token_expire = timedelta(minutes=settings.access_token_expire_minutes)
        self._refresh_token_expire = timedelta(minutes=settings.refresh_token_expire_minutes)

    def create_access_token(self, user_id: uuid.UUID) -> str:
        return self._encode(user_id, self._ACCESS_TOKEN_TYPE, self._access_token_expire)

    def create_refresh_token(self, user_id: uuid.UUID) -> str:
        return self._encode(user_id, self._REFRESH_TOKEN_TYPE, self._refresh_token_expire)

    def decode_access_token(self, token: str) -> uuid.UUID:
        return self._decode(token, expected_type=self._ACCESS_TOKEN_TYPE)

    def decode_refresh_token(self, token: str) -> uuid.UUID:
        return self._decode(token, expected_type=self._REFRESH_TOKEN_TYPE)

    def _encode(self, user_id: uuid.UUID, token_type: str, expires_in: timedelta) -> str:
        now = datetime.now(timezone.utc)
        payload = {
            "sub": str(user_id),
            "type": token_type,
            "iat": now,
            "exp": now + expires_in,
        }
        return jwt.encode(payload, self._secret_key, algorithm=self._algorithm)

    def _decode(self, token: str, expected_type: str) -> uuid.UUID:
        try:
            payload = jwt.decode(token, self._secret_key, algorithms=[self._algorithm])
        except jwt.ExpiredSignatureError as error:
            raise TokenExpiredError("Token has expired.") from error
        except jwt.InvalidTokenError as error:
            raise InvalidTokenError("Token is malformed or has an invalid signature.") from error

        if payload.get("type") != expected_type:
            raise InvalidTokenError(
                f"Expected a '{expected_type}' token but received '{payload.get('type')}'."
            )

        try:
            return uuid.UUID(payload["sub"])
        except (KeyError, ValueError) as error:
            raise InvalidTokenError("Token payload is missing a valid subject.") from error