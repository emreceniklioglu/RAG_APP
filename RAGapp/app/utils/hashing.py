"""Hashing utilities for generating deterministic document and chunk IDs."""

import hashlib


def generate_doc_id(filename: str, content_hash: str) -> str:
    """Generate a unique document ID from filename and content hash."""
    raw = f"{filename}:{content_hash}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


def generate_chunk_id(doc_id: str, page_number: int, chunk_index: int) -> str:
    """Generate a unique chunk ID within a document."""
    raw = f"{doc_id}:p{page_number}:c{chunk_index}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


def hash_content(content: str) -> str:
    """Return a SHA-256 hash of text content."""
    return hashlib.sha256(content.encode()).hexdigest()[:32]


def hash_file_bytes(data: bytes) -> str:
    """Return the full SHA-256 hex digest of raw file bytes.

    Used for duplicate detection (B4) — computed before any processing.
    """
    return hashlib.sha256(data).hexdigest()
