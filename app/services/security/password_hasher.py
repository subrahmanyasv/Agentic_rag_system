"""Password hashing, isolated behind an interface so the hashing scheme
(bcrypt today, argon2 tomorrow) can change without touching AuthService.
"""

from typing import Protocol

from passlib.context import CryptContext


class PasswordHasherInterface(Protocol):
    def hash(self, plain_password: str) -> str:
        """Return a salted hash of the given plaintext password."""
        ...

    def verify(self, plain_password: str, hashed_password: str) -> bool:
        """Return True if plain_password matches the given hash."""
        ...


class BcryptPasswordHasher:
    """Bcrypt-backed implementation.

    Stateless — no DB, no session. Safe to construct once at application
    startup and share across every request via app.state, the same way
    VectorStore is shared today.
    """

    def __init__(self) -> None:
        self._context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    def hash(self, plain_password: str) -> str:
        return self._context.hash(plain_password)

    def verify(self, plain_password: str, hashed_password: str) -> bool:
        return self._context.verify(plain_password, hashed_password)