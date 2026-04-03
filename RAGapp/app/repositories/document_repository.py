"""Document metadata repository.

Stores document metadata as JSON files in the metadata directory.
This avoids needing a database for the MVP while keeping data persistent.
"""

from __future__ import annotations

import json
from pathlib import Path

from app.core.config import settings
from app.core.logging import logger


def _metadata_path(doc_id: str) -> Path:
    """Return the file path for a document's metadata."""
    return settings.METADATA_DIR / f"{doc_id}.json"


def save_document(metadata: dict) -> None:
    """Save document metadata to disk.

    Args:
        metadata: Dict containing doc_id, filename, department, page_count,
                  chunk_count, ingested_at.
    """
    path = _metadata_path(metadata["doc_id"])
    path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
    logger.info("Saved metadata for doc_id=%s", metadata["doc_id"])


def get_document(doc_id: str) -> dict | None:
    """Load document metadata by ID. Returns None if not found."""
    path = _metadata_path(doc_id)
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def list_documents() -> list[dict]:
    """List all stored document metadata, sorted by ingestion time."""
    documents: list[dict] = []
    for path in settings.METADATA_DIR.glob("*.json"):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            documents.append(data)
        except (json.JSONDecodeError, KeyError) as e:
            logger.warning("Skipping corrupt metadata file %s: %s", path.name, e)

    documents.sort(key=lambda d: d.get("ingested_at", ""), reverse=True)
    return documents


def document_exists(doc_id: str) -> bool:
    """Check if a document with the given ID already exists."""
    return _metadata_path(doc_id).exists()
