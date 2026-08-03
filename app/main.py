from fastapi import FastAPI
from app.api.routes import router
from app.core.config import Settings
from app.repositories.document_repository import DocumentRepository
from app.services.pdf_processor import PdfProcessor
from app.services.rag_service import RagService
from app.services.vector_store import VectorStore


def build_rag_service(settings: Settings) -> RagService:
    """Wire concrete dependencies into a RagService (composition root)."""
    return RagService(
        settings=settings,
        repository=DocumentRepository(settings.data_dir / "uploads"),
        processor=PdfProcessor(settings.chunk_size, settings.chunk_overlap),
        vector_store=VectorStore(settings),
    )


def create_app() -> FastAPI:
    application = FastAPI(title="Multi-Document RAG API", version="0.1.0")
    settings = Settings.from_environment()
    application.state.rag_service = build_rag_service(settings)
    application.include_router(router, prefix="/api/v1", tags=["rag"])
    return application


app = create_app()