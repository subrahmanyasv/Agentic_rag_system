"""Composition root: builds and provides application-wide services."""

from fastapi import Request
from app.services.rag_service import RagService


def get_rag_service(request: Request) -> RagService:
    """Resolve the RagService instance stored on app startup."""
    return request.app.state.rag_service