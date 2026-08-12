"""Configuration loaded from environment variables."""

from dataclasses import dataclass
from pathlib import Path
import os
from dotenv import load_dotenv


@dataclass(frozen=True, slots=True)
class Settings:
    """Runtime settings for the RAG service."""

    data_dir: Path
    chroma_dir: Path
    collection_name: str
    embedding_model: str
    ollama_model: str
    ollama_base_url: str | None
    chunk_size: int
    chunk_overlap: int
    retrieval_k: int

    log_dir: Path
    log_level: str
    log_max_bytes: int
    log_backup_count: int

    database_url: str | None = None
    db_connection_retries: int = 5
    db_retry_backoff_seconds: int = 1.0
    db_pool_size: int = 5
    db_pool_max_overflow: int = 10

    jwt_secret_key: str | None = None
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_minutes: int = 60 * 24 * 7  # 7 days

    @classmethod
    def from_environment(cls) -> "Settings":
        """Create settings using environment variables and safe MVP defaults."""
        load_dotenv(Path(__file__).resolve().parents[2] / ".env")
        data_dir = Path(os.getenv("RAG_DATA_DIR", "data")).resolve()
        return cls(
            data_dir=data_dir,
            chroma_dir=Path(os.getenv("CHROMA_PERSIST_DIRECTORY", str(data_dir / "chroma"))).resolve(),
            collection_name=os.getenv("CHROMA_COLLECTION_NAME", "documents"),
            embedding_model=os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2"),
            ollama_model=os.getenv("OLLAMA_MODEL", "llama3.2"),
            ollama_base_url=os.getenv("OLLAMA_BASE_URL") or None,
            chunk_size=int(os.getenv("CHUNK_SIZE", "1000")),
            chunk_overlap=int(os.getenv("CHUNK_OVERLAP", "150")),
            retrieval_k=int(os.getenv("RETRIEVAL_K", "4")),
            log_dir=Path(os.getenv("LOG_DIR", str(data_dir / "logs"))).resolve(),
            log_level=os.getenv("LOG_LEVEL", "INFO").upper(),
            log_max_bytes=int(os.getenv("LOG_MAX_BYTES", str(10 * 1024 * 1024))),  
            log_backup_count=int(os.getenv("LOG_BACKUP_COUNT", "5")),

            database_url=os.getenv("DATABASE_URL") or None,
            db_connection_retries=int(os.getenv("DB_CONNECTION_RETRIES", "5")),
            db_retry_backoff_seconds=float(os.getenv("DB_RETRY_BACKOFF_SECONDS", "1.0")),
            db_pool_size=int(os.getenv("DB_POOL_SIZE", "5")),
            db_pool_max_overflow=int(os.getenv("DB_POOL_MAX_OVERFLOW", "10")),

            jwt_secret_key=os.getenv("JWT_SECRET_KEY") or None,
            jwt_algorithm=os.getenv("JWT_ALGORITHM", "HS256"),
            access_token_expire_minutes=int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30")),
            refresh_token_expire_minutes=int(os.getenv("REFRESH_TOKEN_EXPIRE_MINUTES", str(60 * 24 * 7)))
        )
