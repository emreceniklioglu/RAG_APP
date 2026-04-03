"""RAG query endpoint."""

from fastapi import APIRouter, HTTPException

from app.core.logging import logger
from app.schemas.query import QueryRequest, QueryResponse
from app.services import query_service

router = APIRouter()


@router.post("/query", response_model=QueryResponse)
async def query_documents(request: QueryRequest) -> QueryResponse:
    """Query ingested documents using RAG.

    - Validates user role against RBAC config.
    - Embeds the question, retrieves relevant chunks.
    - Generates an LLM answer grounded in the retrieved context.
    """
    try:
        result = query_service.query_documents(
            question=request.question,
            user_role=request.user_role,
        )
        return QueryResponse(**result)
    except ValueError as e:
        # Invalid role or input validation
        logger.warning("Query validation error: %s", e)
        raise HTTPException(status_code=400, detail=str(e)) from e
    except RuntimeError as e:
        # API errors (embedding, LLM)
        logger.error("Query runtime error: %s", e)
        raise HTTPException(status_code=502, detail=str(e)) from e
    except Exception as e:
        logger.error("Unexpected query error: %s", e, exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Sorgu işlenirken beklenmeyen bir hata oluştu.",
        ) from e
