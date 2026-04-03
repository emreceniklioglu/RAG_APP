"""Pydantic models for the documents listing endpoint."""

from typing import Optional

from pydantic import BaseModel


class DocumentInfo(BaseModel):
    """Metadata for a single ingested document."""
    doc_id: str
    filename: str
    department: str
    page_count: Optional[int] = None
    row_count: Optional[int] = None
    chunk_count: int
    ingested_at: str
    file_hash: Optional[str] = None


class DocumentListResponse(BaseModel):
    """Response listing all ingested documents."""
    total: int
    documents: list[DocumentInfo]
