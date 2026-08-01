"""Domain objects used by document processing."""

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class StoredDocument:
    """A durable copy of an uploaded PDF."""

    document_id: str
    original_name: str
    path: Path
    sha256: str
