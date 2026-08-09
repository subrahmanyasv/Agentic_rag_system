"""Coordinates persistence, chunking, and indexing of uploaded PDFs."""

from app.repositories.document_repository import DocumentRepository
from app.schemas.rag import UploadResponse
from app.services.interfaces import PdfProcessorInterface, VectorStoreInterface


class IngestionService:
    """Persists an upload and indexes it, skipping documents already indexed."""

    def __init__(self, repository: DocumentRepository, processor: PdfProcessorInterface, vector_store: VectorStoreInterface) -> None:
        self._repository = repository
        self._processor = processor
        self._vector_store = vector_store

    def ingest(self, filename: str, content: bytes) -> UploadResponse:
        """Persist and index one uploaded PDF."""
        stored_document, _ = self._repository.save(filename, content)
        if self._vector_store.contains_document(stored_document.document_id):
            return UploadResponse(document_id=stored_document.document_id, filename=stored_document.original_name, chunks_indexed=0, already_indexed=True)
        processed = self._processor.process(stored_document)
        count = self._vector_store.add(processed.chunks, stored_document.document_id)
        return UploadResponse(document_id=stored_document.document_id, filename=stored_document.original_name, chunks_indexed=count)