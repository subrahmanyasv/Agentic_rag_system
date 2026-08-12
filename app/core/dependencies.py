"""Composition root: builds and provides application-wide services."""

from fastapi import Request, Depends
from typing import AsyncIterator
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.rag_service import RagService
from app.services.auth_service import AuthService
from app.services.security.password_hasher import PasswordHasherInterface
from app.services.security.token_service import TokenServiceInterface
from app.repositories.interfaces import UserRepositoryInterface
from app.repositories.postgres_user_repository import PostgresUserRepository


def get_rag_service(request: Request) -> RagService:
    """Resolve the RagService instance stored on app startup."""
    return request.app.state.rag_service

async def get_db_session(request: Request) -> AsyncIterator[AsyncSession]:
    async with request.app.state.db_provider.session() as session:
        yield session

def get_password_hasher(request: Request) -> PasswordHasherInterface:
       return request.app.state.password_hasher

def get_token_service(request: Request) -> TokenServiceInterface:
       return request.app.state.token_service

async def get_user_repository(
    session: AsyncSession = Depends(get_db_session),
) -> UserRepositoryInterface:
    return PostgresUserRepository(session)

async def get_auth_service(
    user_repository: UserRepositoryInterface = Depends(get_user_repository),
   password_hasher: PasswordHasherInterface = Depends(get_password_hasher),
   token_service: TokenServiceInterface = Depends(get_token_service),
) -> AuthService:
   return AuthService(user_repository, password_hasher, token_service)