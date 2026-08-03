"""Abstractions that decouple RagService from concrete implementations."""

from typing import Protocol
from langchain_core.documents import Document
from app.models.documents import StoredDocument
from app.schemas.rag import ProcessedDocument


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