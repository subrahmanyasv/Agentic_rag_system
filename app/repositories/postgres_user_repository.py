"""Postgres-backed implementation of UserRepositoryInterface.

Built fresh per request from a request-scoped AsyncSession (see
app/core/dependencies.py) — never cached or shared across requests,
since it holds a reference to a session that is closed at the end of
each request.
"""

import uuid

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.orm.user import User as UserOrm
from app.models.user import User
from app.repositories.interfaces import EmailAlreadyRegisteredError


class PostgresUserRepository:
    """Reads and writes user records via SQLAlchemy, translating ORM rows
    into plain `User` dataclasses before returning them.

    Translation happens here, not upstream, so nothing above the
    repository layer ever touches a SQLAlchemy-mapped object — this is
    what keeps AuthService free to work with plain data regardless of
    which database or ORM sits underneath.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_email(self, email: str) -> User | None:
        """Return the user with this email, or None if none exists."""
        statement = select(UserOrm).where(UserOrm.email == email)
        result = await self._session.execute(statement)
        orm_user = result.scalar_one_or_none()
        return self._to_domain(orm_user) if orm_user is not None else None

    async def get_by_id(self, user_id: uuid.UUID) -> User | None:
        """Return the user with this id, or None if none exists."""
        orm_user = await self._session.get(UserOrm, user_id)
        return self._to_domain(orm_user) if orm_user is not None else None

    async def create(self, email: str, hashed_password: str) -> User:
        """Persist a new user and return the created record.

        Relies on the unique constraint on users.email (set up in the
        ORM model / migration) rather than a separate pre-check query,
        to avoid a race between "check email is free" and "insert" under
        concurrent signups.
        """
        orm_user = UserOrm(email=email, hashed_password=hashed_password)
        self._session.add(orm_user)
        try:
            await self._session.commit()
        except IntegrityError as error:
            await self._session.rollback()
            raise EmailAlreadyRegisteredError(
                f"A user with email '{email}' is already registered."
            ) from error
        await self._session.refresh(orm_user)
        return self._to_domain(orm_user)

    @staticmethod
    def _to_domain(orm_user: UserOrm) -> User:
        """Convert an ORM row into a plain, session-independent dataclass."""
        return User(
            id=orm_user.id,
            email=orm_user.email,
            hashed_password=orm_user.hashed_password,
            is_active=orm_user.is_active,
            created_at=orm_user.created_at,
        )