"""Document ingestion endpoint.

Accepts PDF, CSV, and XLSX files.
Implements B4 (duplicate detection via file_hash in ChromaDB).
Returns the ingestion result synchronously.
"""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.logging import logger
from app.schemas.ingest import IngestResponse
from app.services import ingestion_service, vector_store_service
from app.utils.hashing import hash_file_bytes

router = APIRouter()

# Allowed MIME types -> category mapping
MIME_MAP: dict[str, str] = {
    "application/pdf": "pdf",
    "text/csv": "csv",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": "xlsx",
    "application/vnd.ms-excel": "xlsx",
}

# Extension fallback
EXT_MAP: dict[str, str] = {
    ".pdf": "pdf",
    ".csv": "csv",
    ".xlsx": "xlsx",
    ".xls": "xlsx",
}


def _detect_file_type(filename: str, content_type: str | None) -> str:
    """Detect file type by MIME type first, then by extension.

    Returns 'pdf', 'csv', or 'xlsx'.
    Raises HTTPException 400 for unsupported types.
    """
    if content_type and content_type in MIME_MAP:
        return MIME_MAP[content_type]

    ext = Path(filename).suffix.lower()
    if ext in EXT_MAP:
        return EXT_MAP[ext]

    raise HTTPException(
        status_code=400,
        detail="Desteklenmeyen dosya formatı. Kabul edilen formatlar: PDF, CSV, XLSX",
    )


@router.post("/ingest", response_model=IngestResponse)
async def ingest_document(
    file: UploadFile = File(..., description="PDF, CSV veya XLSX dosyası"),
    department: str = Form(..., description="Departman etiketi (ör: maintenance, engineering, hr)"),
) -> IngestResponse:
    """Ingest a document into the RAG system.

    - Validates file type (PDF, CSV, XLSX).
    - Computes SHA-256 hash and checks for duplicates in ChromaDB (B4).
    - Returns 409 if duplicate.
    - Runs the full ingestion pipeline and returns the result synchronously.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="Dosya adı belirtilmemiş.")

    # 1. Detect file type
    file_type = _detect_file_type(file.filename, file.content_type)

    department = department.strip().lower()
    if not department:
        raise HTTPException(status_code=400, detail="Departman alanı boş olamaz.")

    # 2. Read file bytes and compute SHA-256 hash (B4)
    try:
        file_bytes = await file.read()
    except Exception as e:
        logger.error("Failed to read upload: %s", e)
        raise HTTPException(status_code=500, detail="Dosya okunamadı.") from e

    file_hash = hash_file_bytes(file_bytes)
    logger.info("File hash: %s (%s)", file_hash[:16], file.filename)

    # 3. Duplicate detection via ChromaDB metadata (B4)
    existing = vector_store_service.find_by_file_hash(file_hash)
    if existing:
        return JSONResponse(
            status_code=409,
            content={
                "error": "Bu belge zaten sisteme yüklenmiş.",
                "file_hash": file_hash,
                "existing_doc_id": existing.get("doc_id", "unknown"),
            },
        )

    # 4. Save file to disk
    file_path = Path(settings.UPLOAD_DIR) / file.filename
    try:
        file_path.write_bytes(file_bytes)
        logger.info("Saved upload: %s (%s, type=%s)", file.filename, department, file_type)
    except Exception as e:
        logger.error("Failed to save upload: %s", e)
        raise HTTPException(status_code=500, detail="Dosya kaydedilemedi.") from e

    # 5. Run ingestion pipeline synchronously and return result
    try:
        if file_type == "pdf":
            result = ingestion_service.ingest_pdf(
                file_path=file_path,
                filename=file.filename,
                department=department,
                file_hash=file_hash,
            )
        else:
            result = ingestion_service.ingest_tabular(
                file_path=file_path,
                filename=file.filename,
                department=department,
                file_hash=file_hash,
            )
        return IngestResponse(**result)

    except ValueError as e:
        logger.warning("Ingestion validation error: %s", e)
        raise HTTPException(status_code=422, detail=str(e)) from e
    except RuntimeError as e:
        logger.error("Ingestion runtime error: %s", e)
        raise HTTPException(status_code=502, detail=str(e)) from e
    except Exception as e:
        logger.error("Unexpected ingestion error: %s", e, exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Doküman işlenirken beklenmeyen bir hata oluştu.",
        ) from e
