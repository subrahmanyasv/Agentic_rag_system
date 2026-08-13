"""Public API schemas for authentication."""

from pydantic import BaseModel, EmailStr, Field


class SignupRequest(BaseModel):
    """Payload to register a new user."""

    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class LoginRequest(BaseModel):
    """Payload to authenticate an existing user."""

    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class AccessTokenResponse(BaseModel):
    """What every successful auth endpoint returns in the response body.

    The refresh token is deliberately never included here — it only ever
    travels as an httpOnly cookie (see app/api/auth_routes.py), so it's
    unreachable from JavaScript and never logged as part of a JSON body.
    """

    access_token: str
    token_type: str = "bearer"


class MessageResponse(BaseModel):
    """Simple confirmation body for endpoints with no token to return."""

    message: str