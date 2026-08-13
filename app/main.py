from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from langchain_ollama import ChatOllama

from app.api.routes import router
from app.api.auth_routes import router as auth_router
from app.api.middleware import RequestLoggingMiddleware
from app.core.config import Settings
from app.core.database import DatabaseConnectionProvider
from app.core.exception_handlers import register_exception_handlers
from app.core.logger import get_logger
from app.core.logging_config import configure_logging
from app.repositories.document_repository import DocumentRepository
from app.services.pdf_processor import PdfProcessor
from app.services.rag_service import RagService
from app.services.vector_store import VectorStore
from app.services.ingestion_service import IngestionService
from app.services.retrieval_service import RetrievalService
from app.services.answer_generation_service import AnswerGenerationService
from app.services.security.password_hasher import BcryptPasswordHasher
from app.services.security.token_service import JwtTokenService

logger = get_logger(__name__)

def build_rag_service(settings: Settings) -> RagService:
    logger.info(
        "building_rag_service",
        embedding_model=settings.embedding_model,
        ollama_model=settings.ollama_model,
        chroma_dir=str(settings.chroma_dir),
    )

    vector_store = VectorStore(settings)
    ingestion_service = IngestionService(
        repository = DocumentRepository(settings.data_dir / "uploads"),
        processor = PdfProcessor(settings.chunk_size, settings.chunk_overlap),
        vector_store = vector_store,   
    )

    retrieval_service = RetrievalService(vector_store=vector_store)


    model_args: dict[str, str] = {"model": settings.ollama_model}
    if settings.ollama_base_url:
        model_args["base_url"] = settings.ollama_base_url
    llm = ChatOllama(**model_args)
    answer_service = AnswerGenerationService(llm=llm)

    logger.info("Rag service built successfully")

    return RagService(
        ingestion_service=ingestion_service,
        retrieval_service=retrieval_service,
        answer_service=answer_service,
        retrieval_k=settings.retrieval_k,
    )


def create_database_lifespan(settings: Settings):
    """Build the lifespan hook responsible for the database's startup/shutdown.

    A closure (rather than a free function) is used so the lifespan callable
    — which FastAPI requires to accept only `app` as its argument — still has
    access to `settings` without needing a second global lookup.

    Connecting happens here, not in `create_app()` directly, because
    `DatabaseConnectionProvider.connect_with_retry()` is a coroutine and must
    be awaited before the app starts accepting traffic. If it raises (either
    because DATABASE_URL is missing, or because every retry attempt failed),
    the exception propagates out of the lifespan and FastAPI/uvicorn never
    finishes starting the application.
    """

    @asynccontextmanager
    async def lifespan(application: FastAPI) -> AsyncIterator[None]:
        db_provider = DatabaseConnectionProvider(settings)
        await db_provider.connect_with_retry()
        application.state.db_provider = db_provider
        logger.info("database_ready")

        yield

        await db_provider.dispose()
        logger.info("database_disposed")

    return lifespan


def create_app() -> FastAPI:
    settings = Settings.from_environment()

    configure_logging(settings)
    logger.info("application_starting", log_dir=str(settings.log_dir), log_level=settings.log_level)

    application = FastAPI(
        title="Multi-Document RAG API",
        version="0.1.0",
        lifespan=create_database_lifespan(settings),
    )

    application.state.rag_service = build_rag_service(settings)
    application.state.password_hasher = BcryptPasswordHasher()
    application.state.token_service = JwtTokenService(settings)
    application.add_middleware(RequestLoggingMiddleware)
    register_exception_handlers(application)
    application.include_router(router, prefix="/api/v1", tags=["rag"])
    application.include_router(auth_router, prefix="/api/v1/auth", tags=["auth"])

    logger.info("application_started", log_dir=str(settings.log_dir), log_level=settings.log_level)
    return application


app = create_app()