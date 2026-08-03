"""Use-case services for ingestion and grounded question answering."""

from langchain_ollama import ChatOllama

from app.core.config import Settings
from app.models.documents import StoredDocument
from app.repositories.document_repository import DocumentRepository
from app.schemas.rag import AnswerResponse, Source, UploadResponse
from app.services.interfaces import PdfProcessorInterface, VectorStoreInterface


class RagService:
    """Coordinates document ingestion, retrieval, and Ollama generation."""

    def __init__(self, settings: Settings, repository: DocumentRepository, processor: PdfProcessorInterface, vector_store: VectorStoreInterface) -> None:
        self._settings = settings
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

    def answer(self, question: str) -> AnswerResponse:
        """Retrieve context and have the local model answer only from it."""
        documents = self._vector_store.search(question, self._settings.retrieval_k)
        if not documents:
            return AnswerResponse(answer="I could not find relevant information in the uploaded documents.", sources=[])
        context = "\n\n".join(f"[Source {index + 1}]\n{document.page_content}" for index, document in enumerate(documents))
        prompt = (
            "Answer the question using only the supplied document context. "
            "If the answer is not in the context, say so plainly. Do not invent facts.\n\n"
            f"Context:\n{context}\n\nQuestion: {question}"
        )
        model_args: dict[str, str] = {"model": self._settings.ollama_model}
        if self._settings.ollama_base_url:
            model_args["base_url"] = self._settings.ollama_base_url
        response = ChatOllama(**model_args).invoke(prompt)
        sources = [Source(
            document_id=str(document.metadata["document_id"]), filename=str(document.metadata["filename"]),
            page=int(document.metadata["page"]), excerpt=document.page_content[:500],
        ) for document in documents]
        return AnswerResponse(answer=str(response.content), sources=sources)
