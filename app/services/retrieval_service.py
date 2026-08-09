"""Performs semantic search against the vector store."""

from langchain_core.documents import Document
from app.services.interfaces import VectorStoreInterface


class RetrievalService:
    """Retrieves the most relevant document chunks for a question."""

    def __init__(self, vector_store: VectorStoreInterface) -> None:
        self._vector_store = vector_store

    def retrieve(self, question: str, limit: int) -> list[Document]:
        """Return the most semantically relevant chunks."""
        return self._vector_store.search(question, limit)