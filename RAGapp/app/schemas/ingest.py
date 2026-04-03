"""Pydantic models for the ingestion endpoint."""

from typing import Optional

from pydantic import BaseModel


class IngestResponse(BaseModel):
    """Response returned after successful document ingestion."""
    doc_id: str
    filename: str
    page_count: Optional[int] = None
    row_count: Optional[int] = None
    chunk_count: int
    status: str = "success"
