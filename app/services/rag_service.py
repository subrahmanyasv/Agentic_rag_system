"""Thin orchestrator that delegates ingestion, retrieval, and generation."""

from app.schemas.rag import AnswerResponse, UploadResponse
from app.services.interfaces import (
    AnswerGenerationServiceInterface,
    IngestionServiceInterface,
    RetrievalServiceInterface,
)


class RagService:
    """Coordinates ingestion, retrieval, and answer generation services."""

    def __init__(
        self,
        ingestion_service: IngestionServiceInterface,
        retrieval_service: RetrievalServiceInterface,
        answer_service: AnswerGenerationServiceInterface,
        retrieval_k: int,
    ) -> None:
        self._ingestion_service = ingestion_service
        self._retrieval_service = retrieval_service
        self._answer_service = answer_service
        self._retrieval_k = retrieval_k

    def ingest(self, filename: str, content: bytes) -> UploadResponse:
        """Persist and index one uploaded PDF."""
        return self._ingestion_service.ingest(filename, content)

    def answer(self, question: str) -> AnswerResponse:
        """Retrieve context and have the LLM answer only from it."""
        documents = self._retrieval_service.retrieve(question, self._retrieval_k)
        return self._answer_service.generate(question, documents)