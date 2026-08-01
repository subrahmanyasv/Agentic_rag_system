"""Public API schemas."""

from pydantic import BaseModel, Field


class UploadResponse(BaseModel):
    """Result for a processed upload."""

    document_id: str
    filename: str
    chunks_indexed: int
    already_indexed: bool = False


class QuestionRequest(BaseModel):
    """A question submitted against the knowledge base."""

    question: str = Field(min_length=1, max_length=10_000)


class Source(BaseModel):
    """A document fragment used to support an answer."""

    document_id: str
    filename: str
    page: int
    excerpt: str


class AnswerResponse(BaseModel):
    """An answer generated solely from retrieved context."""

    answer: str
    sources: list[Source]
