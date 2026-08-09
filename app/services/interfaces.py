"""Abstractions that decouple RagService from concrete implementations."""

from typing import Protocol
from langchain_core.documents import Document
from app.models.documents import StoredDocument
from app.schemas.rag import ProcessedDocument
from app.schemas.rag import AnswerResponse, UploadResponse


class PdfProcessorInterface(Protocol):
    """Contract for turning a stored PDF into indexable chunks."""

    def process(self, stored_document: StoredDocument) -> "ProcessedDocument":
        """Read a stored document and return chunks ready for indexing."""
        ...


class VectorStoreInterface(Protocol):
    """Contract for semantic storage and retrieval of document chunks."""

    def contains_document(self, document_id: str) -> bool:
        """Return whether a document already has indexed chunks."""
        ...

    def add(self, chunks: list[Document], document_id: str) -> int:
        """Add chunks with stable IDs so repeat indexing is safe."""
        ...

    def search(self, question: str, limit: int) -> list[Document]:
        """Retrieve the most semantically relevant chunks."""
        ...


# Interfaces for the three main use cases of the RAG service, which can be implemented separately if desired.
class IngestionServiceInterface(Protocol):
    """Contract for persisting and indexing an uploaded document."""

    def ingest(self, filename: str, content: bytes) -> UploadResponse:
        """Persist and index one uploaded PDF, skipping if already indexed."""
        ...


class RetrievalServiceInterface(Protocol):
    """Contract for semantic retrieval of relevant document chunks."""

    def retrieve(self, question: str, limit: int) -> list[Document]:
        """Return the most relevant chunks for a question."""
        ...


class AnswerGenerationServiceInterface(Protocol):
    """Contract for generating a grounded answer from retrieved context."""

    def generate(self, question: str, documents: list[Document]) -> AnswerResponse:
        """Produce an answer using only the supplied context documents."""
        ...