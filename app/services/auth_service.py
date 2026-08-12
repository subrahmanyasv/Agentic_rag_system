"""Orchestrates signup, login, refresh, and logout.

Built fresh per request (see app/core/dependencies.py) because it
transitively holds UserRepositoryInterface, which is bound to a
request-scoped session. Contains no SQL, no JWT internals, and no
bcrypt calls directly — those are delegated to its collaborators.
"""

from app.core.logger import get_logger
from app.models.token import TokenPair
from app.repositories.interfaces import EmailAlreadyRegisteredError, UserRepositoryInterface
from app.services.auth_exceptions import InvalidCredentialsError, InvalidRefreshTokenError
from app.services.security.password_hasher import PasswordHasherInterface
from app.services.security.token_service import (
    InvalidTokenError,
    TokenExpiredError,
    TokenServiceInterface,
)

logger = get_logger(__name__)


class AuthService:
    def __init__(
        self,
        user_repository: UserRepositoryInterface,
        password_hasher: PasswordHasherInterface,
        token_service: TokenServiceInterface,
    ) -> None:
        self._user_repository = user_repository
        self._password_hasher = password_hasher
        self._token_service = token_service

    async def signup(self, email: str, plain_password: str) -> TokenPair:
        """Create a new user and return a fresh token pair.

        Raises EmailAlreadyRegisteredError if the email is already taken
        (propagated from the repository; the route translates it to 409).
        """
        hashed_password = self._password_hasher.hash(plain_password)
        user = await self._user_repository.create(email=email, hashed_password=hashed_password)

        logger.info("user_signed_up", user_id=str(user.id))
        return self._issue_token_pair(user_id=user.id)

    async def login(self, email: str, plain_password: str) -> TokenPair:
        """Verify credentials and return a fresh token pair.

        Raises InvalidCredentialsError for both a nonexistent email and a
        wrong password — identical error, on purpose (see auth_exceptions.py).
        """
        user = await self._user_repository.get_by_email(email)
        if user is None or not self._password_hasher.verify(plain_password, user.hashed_password):
            logger.warning("login_failed", email=email)
            raise InvalidCredentialsError("Invalid email or password.")

        if not user.is_active:
            logger.warning("login_rejected_inactive_user", user_id=str(user.id))
            raise InvalidCredentialsError("Invalid email or password.")

        logger.info("user_logged_in", user_id=str(user.id))
        return self._issue_token_pair(user_id=user.id)

    async def refresh(self, raw_refresh_token: str) -> TokenPair:
        """Verify a refresh token and issue a new token pair.

        NOTE: with no server-side refresh-token store yet, this only
        confirms the token is structurally valid and unexpired — it
        cannot detect a token that was previously logged out. This
        closes once the Redis-backed store is added.
        """
        try:
            user_id = self._token_service.decode_refresh_token(raw_refresh_token)
        except (TokenExpiredError, InvalidTokenError) as error:
            logger.warning("refresh_token_invalid", reason=type(error).__name__)
            raise InvalidRefreshTokenError("Invalid or expired refresh token.") from error

        user = await self._user_repository.get_by_id(user_id)
        if user is None or not user.is_active:
            logger.warning("refresh_rejected_unknown_or_inactive_user", user_id=str(user_id))
            raise InvalidRefreshTokenError("Invalid or expired refresh token.")

        logger.info("token_refreshed", user_id=str(user.id))
        return self._issue_token_pair(user_id=user.id)

    async def logout(self, raw_refresh_token: str) -> None:
        """Currently a no-op with respect to server-side state.

        There is nowhere yet to record that a refresh token is dead —
        that requires the Redis-backed store planned as the next
        requirement. Until then, logout only has effect if the client
        discards its tokens; the server cannot force revocation.
        """
        logger.warning(
            "logout_called_without_revocation_store",
            detail="Refresh token was not server-side revoked; no store exists yet.",
        )

    def _issue_token_pair(self, user_id) -> TokenPair:
        access_token = self._token_service.create_access_token(user_id)
        refresh_token = self._token_service.create_refresh_token(user_id)
        return TokenPair(access_token=access_token, refresh_token=refresh_token)