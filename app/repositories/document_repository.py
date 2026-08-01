"""Durable filesystem storage for original uploads."""

from hashlib import sha256
from pathlib import Path
import re

from app.models.documents import StoredDocument


class DocumentRepository:
    """Stores content-addressed PDFs without overwriting previous uploads."""

    def __init__(self, upload_directory: Path) -> None:
        self._upload_directory = upload_directory
        self._upload_directory.mkdir(parents=True, exist_ok=True)

    def save(self, filename: str, content: bytes) -> tuple[StoredDocument, bool]:
        """Persist an upload and report whether its bytes already existed."""
        digest = sha256(content).hexdigest()
        safe_name = re.sub(r"[^A-Za-z0-9._-]", "_", Path(filename).name) or "document.pdf"
        document_id = digest[:24]
        path = self._upload_directory / f"{document_id}_{safe_name}"
        existed = path.exists()
        if not existed:
            path.write_bytes(content)
        return StoredDocument(document_id, safe_name, path, digest), existed
