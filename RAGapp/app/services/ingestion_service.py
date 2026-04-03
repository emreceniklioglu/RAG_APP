"""Ingestion orchestration service.

Coordinates the full pipeline:
  - PDF:       parse pages -> chunk -> embed -> store
  - CSV/XLSX:  parse rows  -> row-as-chunk -> embed -> store
"""

from datetime import datetime, timezone
from pathlib import Path

from app.core.logging import logger
from app.repositories import document_repository
from app.services import (
    chunking_service,
    embedding_service,
    pdf_service,
    tabular_service,
    vector_store_service,
)
from app.utils.hashing import generate_chunk_id, generate_doc_id, hash_content
from app.utils.timers import log_timer


def ingest_pdf(file_path: Path, filename: str, department: str, file_hash: str) -> dict:
    """Run the full ingestion pipeline for a PDF file.

    Args:
        file_path: Path to the saved PDF file.
        filename: Original filename from upload.
        department: Department tag for RBAC filtering.
        file_hash: Pre-computed SHA-256 hash of the raw file bytes.

    Returns:
        Dict with doc_id, filename, page_count, chunk_count, status.
    """
    with log_timer(f"Full ingestion: {filename}"):
        # 1. Extract text from PDF pages
        pages = pdf_service.extract_pages(file_path)
        page_count = len(pages)

        # 2. Generate document ID from content
        all_text = "".join(p.text for p in pages)
        content_hash = hash_content(all_text)
        doc_id = generate_doc_id(filename, content_hash)

        # Check for duplicate via metadata repo
        if document_repository.document_exists(doc_id):
            logger.info("Document already ingested: %s (doc_id=%s)", filename, doc_id)
            existing = document_repository.get_document(doc_id)
            return {
                "doc_id": doc_id,
                "filename": filename,
                "page_count": existing["page_count"],
                "chunk_count": existing["chunk_count"],
                "status": "already_exists",
            }

        # 3. Chunk the pages
        chunks = chunking_service.chunk_pages(pages)
        if not chunks:
            raise ValueError(
                f"Dokümandan yeterli uzunlukta metin parçası oluşturulamadı: {filename}"
            )

        # 4. Generate embeddings
        chunk_texts = [c.text for c in chunks]
        embeddings = embedding_service.get_embeddings(chunk_texts)

        # 5. Prepare metadata and store in vector DB
        ingested_at = datetime.now(timezone.utc).isoformat()
        ids: list[str] = []
        metadatas: list[dict] = []

        for i, chunk in enumerate(chunks):
            chunk_id = generate_chunk_id(doc_id, chunk.page_number, i)
            ids.append(chunk_id)
            metadatas.append({
                "doc_id": doc_id,
                "chunk_id": chunk_id,
                "filename": filename,
                "page_number": chunk.page_number,
                "department": department,
                "ingested_at": ingested_at,
                "token_count": chunk.token_count,
                "file_hash": file_hash,
            })

        vector_store_service.add_chunks(
            ids=ids,
            embeddings=embeddings,
            documents=chunk_texts,
            metadatas=metadatas,
        )

        # 6. Save document metadata
        document_repository.save_document({
            "doc_id": doc_id,
            "filename": filename,
            "department": department,
            "page_count": page_count,
            "chunk_count": len(chunks),
            "ingested_at": ingested_at,
            "file_hash": file_hash,
        })

        logger.info(
            "Ingestion complete: %s -> %d pages, %d chunks",
            filename, page_count, len(chunks),
        )

        return {
            "doc_id": doc_id,
            "filename": filename,
            "page_count": page_count,
            "chunk_count": len(chunks),
            "status": "success",
        }


def ingest_tabular(file_path: Path, filename: str, department: str, file_hash: str) -> dict:
    """Run the ingestion pipeline for a CSV or Excel file.

    Each row is treated as a single chunk (no further splitting).

    Args:
        file_path: Path to the saved CSV/XLSX file.
        filename: Original filename from upload.
        department: Department tag for RBAC filtering.
        file_hash: Pre-computed SHA-256 hash of the raw file bytes.

    Returns:
        Dict with doc_id, filename, row_count, chunk_count, status.
    """
    with log_timer(f"Tabular ingestion: {filename}"):
        # 1. Parse rows
        row_strings = tabular_service.parse_tabular(file_path, filename)
        row_count = len(row_strings)

        # 2. Generate document ID
        all_text = "\n".join(row_strings)
        content_hash = hash_content(all_text)
        doc_id = generate_doc_id(filename, content_hash)

        if document_repository.document_exists(doc_id):
            logger.info("Document already ingested: %s (doc_id=%s)", filename, doc_id)
            existing = document_repository.get_document(doc_id)
            return {
                "doc_id": doc_id,
                "filename": filename,
                "row_count": existing.get("row_count", existing.get("page_count", 0)),
                "chunk_count": existing["chunk_count"],
                "status": "already_exists",
            }

        # 3. Generate embeddings (each row is a chunk)
        embeddings = embedding_service.get_embeddings(row_strings)

        # 4. Store in vector DB
        ingested_at = datetime.now(timezone.utc).isoformat()
        ids: list[str] = []
        metadatas: list[dict] = []

        for i, row_text in enumerate(row_strings):
            chunk_id = generate_chunk_id(doc_id, 0, i)
            ids.append(chunk_id)
            metadatas.append({
                "doc_id": doc_id,
                "chunk_id": chunk_id,
                "filename": filename,
                "page_number": 0,  # CSV/XLSX have no pages
                "row_index": i,
                "department": department,
                "ingested_at": ingested_at,
                "token_count": len(row_text.split()),
                "file_hash": file_hash,
            })

        vector_store_service.add_chunks(
            ids=ids,
            embeddings=embeddings,
            documents=row_strings,
            metadatas=metadatas,
        )

        # 5. Save document metadata
        document_repository.save_document({
            "doc_id": doc_id,
            "filename": filename,
            "department": department,
            "page_count": 0,
            "row_count": row_count,
            "chunk_count": len(row_strings),
            "ingested_at": ingested_at,
            "file_hash": file_hash,
        })

        logger.info(
            "Tabular ingestion complete: %s -> %d rows, %d chunks",
            filename, row_count, len(row_strings),
        )

        return {
            "doc_id": doc_id,
            "filename": filename,
            "row_count": row_count,
            "chunk_count": len(row_strings),
            "status": "success",
        }
