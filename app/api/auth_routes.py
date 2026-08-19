"""
FastAPI routes for authentication.

Every route does exactly three things: 
 - pull input out of the request
 - call AuthService 
 - shape the response. 

Defined routes: 
    - POST /signup: register a new user and start a session
    - POST /login: authenticate an existing user and start a session
    - POST /refresh: exchange a valid refresh token for a fresh token pair
    - POST /logout: end the current session
"""

from fastapi import APIRouter, Depends, Request, Response, status

from app.core.config import Settings
from app.core.dependencies import get_auth_service, get_settings
from app.schemas.auth import AccessTokenResponse, LoginRequest, MessageResponse, SignupRequest
from app.services.auth_exceptions import InvalidRefreshTokenError
from app.services.auth_service import AuthService

router = APIRouter()

_REFRESH_TOKEN_COOKIE = "refresh_token"


@router.post("/signup", response_model=AccessTokenResponse, status_code=status.HTTP_201_CREATED)
async def signup(
    payload: SignupRequest,
    response: Response,
    settings: Settings = Depends(get_settings),
    auth_service: AuthService = Depends(get_auth_service),
) -> AccessTokenResponse:
    """Register a new user and start a session.

    Raises EmailAlreadyRegisteredError (-> 409) if the email is taken;
    handled globally, not here.
    """
    tokens = await auth_service.signup(payload.email, payload.password)
    _set_refresh_cookie(response, tokens.refresh_token, settings)
    return AccessTokenResponse(access_token=tokens.access_token)


@router.post("/login", response_model=AccessTokenResponse)
async def login(
    payload: LoginRequest,
    response: Response,
    settings: Settings = Depends(get_settings),
    auth_service: AuthService = Depends(get_auth_service),
) -> AccessTokenResponse:
    """
    Authenticate a user and start a session.

    ==========================================================
    TODO: 
    - Adding redis caching the user instance with refresh token as key.
    - Adding rate limiting to prevent brute force attacks.
    ==========================================================
    """
    tokens = await auth_service.login(payload.email, payload.password)
    _set_refresh_cookie(response, tokens.refresh_token, settings)
    return AccessTokenResponse(access_token=tokens.access_token)


@router.post("/refresh", response_model=AccessTokenResponse)
async def refresh(
    request: Request,
    response: Response,
    settings: Settings = Depends(get_settings),
    auth_service: AuthService = Depends(get_auth_service),
) -> AccessTokenResponse:
    """
    Exchange a valid refresh token (from its cookie) for a fresh token pair.

    A missing cookie is treated identically to an invalid one — both
    raise InvalidRefreshTokenError (-> 401) — so a client can't
    distinguish "no session" from "session rejected."
    """
    raw_refresh_token = request.cookies.get(_REFRESH_TOKEN_COOKIE)
    if raw_refresh_token is None:
        raise InvalidRefreshTokenError("No refresh token was provided.")

    tokens = await auth_service.refresh(raw_refresh_token)
    _set_refresh_cookie(response, tokens.refresh_token, settings)
    return AccessTokenResponse(access_token=tokens.access_token)


@router.post("/logout", response_model=MessageResponse)
async def logout(
    request: Request,
    response: Response,
    auth_service: AuthService = Depends(get_auth_service),
) -> MessageResponse:
    """End the current session.

    Idempotent by design: calling this with no active session (no
    cookie present) is not an error — it simply confirms there is
    nothing to log out of, rather than forcing the client to first
    check whether a session exists.
    """
    raw_refresh_token = request.cookies.get(_REFRESH_TOKEN_COOKIE)
    if raw_refresh_token is not None:
        await auth_service.logout(raw_refresh_token)

    response.delete_cookie(_REFRESH_TOKEN_COOKIE)
    return MessageResponse(message="Logout successful.")


def _set_refresh_cookie(response: Response, refresh_token: str, settings: Settings) -> None:
    """Attach the refresh token as an httpOnly cookie, never in the body.

    httponly=True; prevents JavaScript from reading the cookie.
    samesite="strict"; mitigates CSRF; 
    secure=True; Sent only in HTTPS.
    
    lifetime is taken from the Settings instance, so it can be configured per environment.
    """
    response.set_cookie(
        key=_REFRESH_TOKEN_COOKIE,
        value=refresh_token,
        max_age=settings.refresh_token_expire_minutes * 60,
        httponly=True,
        secure=True,
        samesite="strict",
    )