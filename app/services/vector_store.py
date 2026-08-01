"""Chroma vector index adapter."""

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings

from app.core.config import Settings


class VectorStore:
    """Persistent semantic index backed by ChromaDB."""

    def __init__(self, settings: Settings) -> None:
        settings.chroma_dir.mkdir(parents=True, exist_ok=True)
        embeddings = HuggingFaceEmbeddings(model_name=settings.embedding_model)
        self._store = Chroma(
            collection_name=settings.collection_name,
            persist_directory=str(settings.chroma_dir),
            embedding_function=embeddings,
        )

    def contains_document(self, document_id: str) -> bool:
        """Return whether a document already has indexed chunks."""
        return bool(self._store.get(where={"document_id": document_id}, limit=1).get("ids"))

    def add(self, chunks: list[Document], document_id: str) -> int:
        """Add chunks with stable IDs so repeat indexing is safe."""
        ids = [f"{document_id}-{index}" for index in range(len(chunks))]
        self._store.add_documents(chunks, ids=ids)
        return len(chunks)

    def search(self, question: str, limit: int) -> list[Document]:
        """Retrieve the most semantically relevant chunks."""
        return self._store.similarity_search(question, k=limit)
