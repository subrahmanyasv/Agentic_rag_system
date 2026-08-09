"""Generates grounded answers from retrieved context using the LLM."""

from langchain_core.documents import Document
from langchain_ollama import ChatOllama
from app.schemas.rag import AnswerResponse, Source


class AnswerGenerationService:
    """Builds a grounded prompt and invokes the LLM to answer a question."""

    def __init__(self, llm: ChatOllama) -> None:
        self._llm = llm

    def generate(self, question: str, documents: list[Document]) -> AnswerResponse:
        """Produce an answer using only the supplied context documents."""
        if not documents:
            return AnswerResponse(answer="I could not find relevant information in the uploaded documents.", sources=[])
        context = "\n\n".join(f"[Source {index + 1}]\n{document.page_content}" for index, document in enumerate(documents))
        prompt = (
            "Answer the question using only the supplied document context. "
            "If the answer is not in the context, say so plainly. Do not invent facts.\n\n"
            f"Context:\n{context}\n\nQuestion: {question}"
        )
        response = self._llm.invoke(prompt)
        sources = [Source(
            document_id=str(document.metadata["document_id"]), filename=str(document.metadata["filename"]),
            page=int(document.metadata["page"]), excerpt=document.page_content[:500],
        ) for document in documents]
        return AnswerResponse(answer=str(response.content), sources=sources)