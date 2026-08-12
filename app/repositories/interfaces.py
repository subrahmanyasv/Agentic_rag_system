"""Abstractions that decouple services (e.g. AuthService) from concrete
persistence implementations.

Mirrors the pattern already established in app/services/interfaces.py:
all repository contracts live together in one file, and concrete classes
satisfy them structurally (via Python's Protocol) rather than through an
explicit `implements` declaration.
"""

from typing import Protocol
import uuid

from app.models.user import User


class UserRepositoryInterface(Protocol):
    """Contract for reading and writing user records.

    Deliberately narrow (per ISP) — only the operations AuthService
    actually needs. Returns plain `User` dataclasses, never ORM objects,
    so callers never depend on SQLAlchemy or hold a reference that
    outlives the request-scoped session.
    """

    async def get_by_email(self, email: str) -> User | None:
        """Return the user with this email, or None if none exists."""
        ...

    async def get_by_id(self, user_id: uuid.UUID) -> User | None:
        """Return the user with this id, or None if none exists."""
        ...

    async def create(self, email: str, hashed_password: str) -> User:
        """Persist a new user and return the created record.

        Raises EmailAlreadyRegisteredError if the email is already in use.
        Callers are responsible for hashing the password before calling
        this — the repository never hashes or validates passwords itself.
        """
        ...


class EmailAlreadyRegisteredError(Exception):
    """Raised when attempting to create a user with a duplicate email.

    Defined here rather than in the ORM/database layer so callers (e.g.
    AuthService) can catch it without importing anything SQLAlchemy-specific.
    """