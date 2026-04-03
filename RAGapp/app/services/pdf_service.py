"""PDF text extraction service using PyMuPDF."""

from pathlib import Path

import fitz  # PyMuPDF

from app.core.logging import logger
from app.utils.timers import log_timer


class PDFPage:
    """Represents extracted text from a single PDF page."""

    def __init__(self, page_number: int, text: str):
        self.page_number = page_number
        self.text = text


def extract_pages(file_path: Path) -> list[PDFPage]:
    """Extract text from each page of a PDF file.

    Args:
        file_path: Path to the PDF file.

    Returns:
        List of PDFPage objects with page numbers (1-indexed) and text.

    Raises:
        ValueError: If no text could be extracted from the PDF.
    """
    pages: list[PDFPage] = []

    with log_timer(f"PDF extraction: {file_path.name}"):
        doc = fitz.open(str(file_path))
        total_pages = len(doc)
        try:
            for i in range(total_pages):
                page = doc[i]
                text = page.get_text("text").strip()
                if text:
                    pages.append(PDFPage(page_number=i + 1, text=text))
                else:
                    logger.warning(
                        "Page %d of %s has no extractable text", i + 1, file_path.name
                    )
        finally:
            doc.close()

    if not pages:
        raise ValueError(
            f"PDF dosyasından metin çıkarılamadı: {file_path.name}. "
            "Dosya görsel tabanlı veya boş olabilir."
        )

    logger.info(
        "Extracted %d pages with text from %s (total pages: %d)",
        len(pages),
        file_path.name,
        total_pages,
    )
    return pages
