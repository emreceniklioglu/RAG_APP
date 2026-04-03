"""FastAPI application factory.

Creates and configures the FastAPI app with all API routes
and a global exception handler for consistent error responses.
"""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.api import documents, health, ingest, query
from app.core.config import settings
from app.core.logging import logger


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description="Mini RAG backend for querying internal company documents.",
    )

    # Register API routes under /api prefix
    app.include_router(health.router, prefix="/api", tags=["Health"])
    app.include_router(ingest.router, prefix="/api", tags=["Ingestion"])
    app.include_router(query.router, prefix="/api", tags=["Query"])
    app.include_router(documents.router, prefix="/api", tags=["Documents"])

    # Global exception handler — never expose raw stack traces
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.error("Unhandled exception: %s", exc, exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"detail": "Sunucuda beklenmeyen bir hata oluştu."},
        )

    @app.on_event("startup")
    async def startup_event() -> None:
        logger.info(
            "%s v%s started", settings.APP_NAME, settings.APP_VERSION
        )

    return app


app = create_app()
