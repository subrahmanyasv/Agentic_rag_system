"""
Database engine, connection pool, and session provisioning.

This module owns exactly two responsibilities:
1. Connecting to the database with retry-on-startup, so the application
   refuses to boot if the database is unreachable or misconfigured.
2. Handing out short-lived, per-request sessions borrowed from a
   long-lived connection pool.

Nothing above this module (services, routes) should import SQLAlchemy
directly.
"""

import asyncio
from contextlib import asynccontextmanager
from typing import AsyncIterator

from sqlalchemy.exc import OperationalError
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import Settings
from app.core.logger import get_logger

logger = get_logger(__name__)


class DatabaseConfigurationError(ValueError):
    """Raised when required database configuration is missing or invalid.

    Kept as a distinct type (rather than a bare ValueError) so callers in
    main.py can, if ever needed, distinguish "misconfigured" failures from
    "unreachable" ones without string-matching an error message.
    """


class DatabaseConnectionProvider:
    """
    Owns the database engine (connection pool) for the app's lifetime.
    Built exactly once in the composition root (app/main.py) and stored on
    app.state.
    Sessions, by contrast, are borrowed per request via `session()` and
    always closed at the end of that request — see app/core/dependencies.py.
    """

    def __init__(self, settings: Settings) -> None:
        """
        Validate configuration and create the engine + session factory.
        Does not open a network connection yet — engine creation is lazy
        in SQLAlchemy. The pool is only actually exercised once
        `connect_with_retry()` or `session()` is used. Configuration
        validation, however, happens immediately and unconditionally.
        """
        self._validate_database_url(settings.database_url)

        self._retries = settings.db_connection_retries
        self._backoff_seconds = settings.db_retry_backoff_seconds
        self._dialect = self._extract_dialect(settings.database_url)

        self._engine: AsyncEngine = create_async_engine(
            settings.database_url,
            pool_size=settings.db_pool_size,
            max_overflow=settings.db_pool_max_overflow,
        )
        self._session_factory = async_sessionmaker(
            bind=self._engine,
            expire_on_commit=False,
        )

        logger.info(
            "database_provider_initialized",
            dialect=self._dialect,
            pool_size=settings.db_pool_size,
            max_overflow=settings.db_pool_max_overflow,
            configured_retries=self._retries,
        )

    def _validate_database_url(self, database_url: str | None) -> None:
        """
        Fail loudly and immediately if no database URL was configured.
        """
        if not database_url or not database_url.strip():
            logger.error(
                "database_url_not_configured",
                hint="Set DATABASE_URL in the environment (see .env.example).",
            )
            raise DatabaseConfigurationError(
                "DATABASE_URL is not set. The application cannot start "
                "without a database connection string."
            )


    @staticmethod
    def _extract_dialect(database_url: str) -> str:
        """
        Return only the scheme (e.g. 'postgresql+asyncpg') for logging.
        Used so log lines can identify which database backend is in use
        without ever writing the credentials portion of the DSN to logs.
        """
        return database_url.split("://", maxsplit=1)[0]
    

    async def connect_with_retry(self) -> None:
        """
        Attempt to connect up to `db_connection_retries` times.
        Runs exactly once, at application startup, from the lifespan hook
        in app/main.py. If every attempt fails, the final exception is
        re-raised so the application never finishes starting up — this
        propagation is what satisfies "the app should not start if the
        database connection failed."
        """
        for attempt in range(1, self._retries + 1):
            try:
                async with self._engine.connect():
                    logger.info(
                        "database_connected",
                        dialect=self._dialect,
                        attempt=attempt,
                        attempts_allowed=self._retries,
                    )
                    return
            except OperationalError as error:
                is_final_attempt = attempt == self._retries
                logger.warning(
                    "database_connect_attempt_failed",
                    dialect=self._dialect,
                    attempt=attempt,
                    attempts_allowed=self._retries,
                    error_type=type(error).__name__,
                    final_attempt=is_final_attempt,
                )
                if is_final_attempt:
                    logger.error(
                        "database_connect_exhausted",
                        dialect=self._dialect,
                        attempts_made=self._retries,
                    )
                    raise
                backoff = self._backoff_seconds * attempt
                await asyncio.sleep(backoff)

    @asynccontextmanager
    async def session(self) -> AsyncIterator[AsyncSession]:
        """Borrow one session from the pool for the caller's scope.

        Intended to be used exactly once per request, via the
        `get_db_session` FastAPI dependency. The session — and the
        underlying pooled connection it holds — is always released on
        exit, whether the caller's code succeeds or raises.
        """
        session = self._session_factory()
        try:
            yield session
        finally:
            await session.close()

    async def dispose(self) -> None:
        """Close all pooled connections. Called once, on app shutdown."""
        await self._engine.dispose()
        logger.info("database_disposed", dialect=self._dialect)