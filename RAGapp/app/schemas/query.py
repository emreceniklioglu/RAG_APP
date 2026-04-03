"""Pydantic models for the query endpoint."""

from typing import Optional

from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    """Incoming query from a user."""
    question: str = Field(..., min_length=1, description="Sorulacak soru")
    user_role: str = Field(..., min_length=1, description="Kullanıcı rolü")


class SourceChunk(BaseModel):
    """A single source reference returned with the answer."""
    filename: str
    page_number: int
    chunk_excerpt: str
    score: float
    rerank_score: Optional[float] = None


class QueryResponse(BaseModel):
    """Response containing the generated answer and sources."""
    answer: str
    sources: list[SourceChunk]
