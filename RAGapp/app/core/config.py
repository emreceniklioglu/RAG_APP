"""
Application configuration loaded from environment variables.
Uses pydantic-settings for type-safe config with .env file support.
"""

from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Central configuration for the application."""

    # App
    APP_NAME: str = "RAG Backend"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # Paths
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent
    UPLOAD_DIR: Path = BASE_DIR / "data" / "uploads"
    CHROMA_DIR: Path = BASE_DIR / "data" / "chroma"
    METADATA_DIR: Path = BASE_DIR / "data" / "metadata"

    # Jina Embeddings
    JINA_API_KEY: str = ""
    JINA_MODEL: str = "jina-embeddings-v3"
    EMBEDDING_DIM: int = 1024

    # LLM (Google Gemini)
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.0-flash"

    # Chunking
    CHUNK_SIZE: int = 400  # target tokens per chunk
    CHUNK_OVERLAP: int = 50  # overlap tokens between chunks
    MIN_CHUNK_TOKENS: int = 20  # skip chunks shorter than this

    # Retrieval
    TOP_K: int = 5

    # ChromaDB
    CHROMA_COLLECTION: str = "documents"

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }


# Singleton settings instance
settings = Settings()

# Ensure data directories exist
settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
settings.CHROMA_DIR.mkdir(parents=True, exist_ok=True)
settings.METADATA_DIR.mkdir(parents=True, exist_ok=True)
