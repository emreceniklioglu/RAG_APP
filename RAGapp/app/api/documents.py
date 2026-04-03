"""Documents listing endpoint."""

from fastapi import APIRouter

from app.repositories import document_repository
from app.schemas.document import DocumentInfo, DocumentListResponse

router = APIRouter()


@router.get("/documents", response_model=DocumentListResponse)
async def list_documents() -> DocumentListResponse:
    """List all ingested documents with their metadata."""
    docs = document_repository.list_documents()
    return DocumentListResponse(
        total=len(docs),
        documents=[DocumentInfo(**doc) for doc in docs],
    )
