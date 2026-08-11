"""FastAPI routes with no embedded business logic."""

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from app.schemas.rag import AnswerResponse, QuestionRequest, UploadResponse
from app.services.rag_service import RagService
from app.core.dependencies import get_rag_service
from app.core.logger import get_logger


router = APIRouter()
logger = get_logger(__name__)

@router.get("/health")
def health_check() -> dict[str, str]:
    """Provide a lightweight liveness endpoint."""
    return {"status": "ok"}


@router.post("/documents", response_model=list[UploadResponse], status_code=status.HTTP_201_CREATED)
async def upload_documents(files: list[UploadFile] = File(...), service: RagService = Depends(get_rag_service)) -> list[UploadResponse]:
    """Upload and incrementally index one or more PDF documents."""
    results: list[UploadResponse] = []
    for upload in files:
        if not upload.filename or not upload.filename.lower().endswith(".pdf"):
            raise HTTPException(status_code=400, detail="Only PDF files are supported.")
        content = await upload.read()
        if not content:
            raise HTTPException(status_code=400, detail=f"{upload.filename} is empty.")
        try:
            results.append(service.ingest(upload.filename, content))
        except (ValueError, OSError) as error:
            logger.warning("document_upload_rejected", filename=upload.filename, reason=str(error))
            raise HTTPException(status_code=422, detail=str(error)) from error
    return results


@router.post("/questions", response_model=AnswerResponse)
def ask_question(request: QuestionRequest, service: RagService = Depends(get_rag_service)) -> AnswerResponse:
    """Answer a question from all indexed documents."""
    try:
        return service.answer(request.question)
    except Exception as error:
        logger.error("question_answering_failed", question_length=len(request.question), error_type=type(error).__name__)
        raise HTTPException(status_code=503, detail="The local language model is unavailable.") from error
