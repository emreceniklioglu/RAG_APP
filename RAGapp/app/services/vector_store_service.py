"""ChromaDB vector store service.

Manages the ChromaDB collection for storing and querying document chunks.
Uses persistent storage so data survives restarts.
"""

from __future__ import annotations

from typing import Optional

import chromadb

from app.core.config import settings
from app.core.logging import logger

# Module-level ChromaDB client (singleton pattern)
_client: Optional[chromadb.PersistentClient] = None
_collection: Optional[chromadb.Collection] = None


def _get_collection() -> chromadb.Collection:
    """Get or create the ChromaDB collection (lazy singleton)."""
    global _client, _collection

    if _collection is None:
        _client = chromadb.PersistentClient(path=str(settings.CHROMA_DIR))
        _collection = _client.get_or_create_collection(
            name=settings.CHROMA_COLLECTION,
            metadata={"hnsw:space": "cosine"},
        )
        logger.info(
            "ChromaDB collection '%s' ready (%d items)",
            settings.CHROMA_COLLECTION,
            _collection.count(),
        )

    return _collection


def add_chunks(
    ids: list[str],
    embeddings: list[list[float]],
    documents: list[str],
    metadatas: list[dict],
) -> None:
    """Add chunk embeddings and metadata to the vector store.

    Args:
        ids: Unique IDs for each chunk.
        embeddings: Embedding vectors.
        documents: Original chunk texts.
        metadatas: Metadata dicts (doc_id, filename, page_number, department, etc.).
    """
    collection = _get_collection()

    # ChromaDB has a batch size limit; process in batches of 500
    batch_size = 500
    for i in range(0, len(ids), batch_size):
        end = i + batch_size
        collection.add(
            ids=ids[i:end],
            embeddings=embeddings[i:end],
            documents=documents[i:end],
            metadatas=metadatas[i:end],
        )

    logger.info("Added %d chunks to vector store", len(ids))


def query_chunks(
    query_embedding: list[float],
    departments: list[str],
    top_k: int = settings.TOP_K,
) -> dict:
    """Query the vector store for relevant chunks, filtered by department.

    Args:
        query_embedding: The embedded query vector.
        departments: List of departments to filter by (RBAC).
        top_k: Number of results to return.

    Returns:
        ChromaDB query result dict with ids, documents, metadatas, distances.
    """
    collection = _get_collection()

    where_filter = {"department": {"$in": departments}}

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
        where=where_filter,
        include=["documents", "metadatas", "distances"],
    )

    n_results = len(results["ids"][0]) if results["ids"] else 0
    logger.info(
        "Vector query returned %d results (departments=%s)", n_results, departments
    )
    return results


def find_by_file_hash(file_hash: str) -> Optional[dict]:
    """Check if any chunk with the given file_hash exists in the collection.

    Returns the metadata of the first matching chunk, or None if not found.
    Used for duplicate detection (B4) — queries ChromaDB metadata only.
    """
    collection = _get_collection()
    try:
        results = collection.get(
            where={"file_hash": {"$eq": file_hash}},
            limit=1,
            include=["metadatas"],
        )
        if results["ids"]:
            meta = results["metadatas"][0]
            logger.info(
                "Duplicate detected: file_hash=%s, doc_id=%s",
                file_hash[:16],
                meta.get("doc_id"),
            )
            return meta
    except Exception as e:
        # Collection may be empty or have no file_hash field yet — not a duplicate
        logger.debug("find_by_file_hash: %s", e)
    return None


def get_collection_count() -> int:
    """Return total number of chunks in the collection."""
    return _get_collection().count()


def delete_by_doc_id(doc_id: str) -> None:
    """Delete all chunks for a given document."""
    collection = _get_collection()
    collection.delete(where={"doc_id": doc_id})
    logger.info("Deleted chunks for doc_id=%s", doc_id)
