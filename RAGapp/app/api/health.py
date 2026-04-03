"""Health check endpoint."""

from fastapi import APIRouter

from app.core.config import settings
from app.services import vector_store_service

router = APIRouter()


@router.get("/health")
def health_check() -> dict:
    """Return service health status and basic metadata."""
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "vector_store_chunks": vector_store_service.get_collection_count(),
    }
