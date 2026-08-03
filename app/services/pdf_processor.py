"""PDF extraction and semantic chunk preparation."""

from dataclasses import dataclass
from pypdf import PdfReader
from pypdf.errors import PdfReadError
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.models.documents import StoredDocument
from app.schemas.rag import ProcessedDocument


class PdfProcessor:
    """Extracts page text; PDF text includes table content where extractable."""

    def __init__(self, chunk_size: int, chunk_overlap: int) -> None:
        self._splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size, chunk_overlap=chunk_overlap, separators=["\n\n", "\n", ". ", " ", ""]
        )

    def process(self, stored_document: StoredDocument) -> ProcessedDocument:
        """Read each PDF page and return chunks annotated with source metadata."""
        try:
            reader = PdfReader(str(stored_document.path))
        except PdfReadError as error:
            raise ValueError("The uploaded file is not a readable PDF.") from error
        page_documents: list[Document] = []
        for page_number, page in enumerate(reader.pages, start=1):
            try:
                # Layout mode retains columns and table-like structures where the
                # PDF contains selectable text.
                text = page.extract_text(extraction_mode="layout") or ""
            except TypeError:  # Compatibility with older pypdf versions.
                text = page.extract_text() or ""
            if text.strip():
                page_documents.append(Document(
                    page_content=text,
                    metadata={
                        "document_id": stored_document.document_id,
                        "filename": stored_document.original_name,
                        "page": page_number,
                        "sha256": stored_document.sha256,
                    },
                ))
        if not page_documents:
            raise ValueError("The PDF contains no extractable text. Scanned/image-only PDFs require OCR support.")
        return ProcessedDocument(chunks=self._splitter.split_documents(page_documents))
