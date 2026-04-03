"""Text chunking service.

Splits page text into overlapping chunks of ~CHUNK_SIZE tokens.
Uses a simple whitespace tokenizer (word count ≈ token count for Turkish).
"""

from dataclasses import dataclass

from app.core.config import settings
from app.core.logging import logger


@dataclass
class TextChunk:
    """A chunk of text with its source metadata."""
    text: str
    page_number: int
    chunk_index: int
    token_count: int


def _estimate_tokens(text: str) -> int:
    """Estimate token count using whitespace splitting.

    For Turkish text, word count is a reasonable approximation of token count.
    """
    return len(text.split())


def chunk_pages(
    pages: list,  # list of PDFPage
    chunk_size: int = settings.CHUNK_SIZE,
    chunk_overlap: int = settings.CHUNK_OVERLAP,
    min_chunk_tokens: int = settings.MIN_CHUNK_TOKENS,
) -> list[TextChunk]:
    """Split extracted pages into overlapping text chunks.

    Strategy:
    1. Split each page's text into sentences (by newline and period).
    2. Accumulate sentences until chunk_size is reached.
    3. Overlap the last chunk_overlap tokens into the next chunk.
    4. Skip chunks below min_chunk_tokens.

    Args:
        pages: List of PDFPage objects.
        chunk_size: Target tokens per chunk.
        chunk_overlap: Number of overlapping tokens between chunks.
        min_chunk_tokens: Minimum tokens for a chunk to be kept.

    Returns:
        List of TextChunk objects.
    """
    all_chunks: list[TextChunk] = []
    global_chunk_index = 0

    for page in pages:
        # Split into sentences using common delimiters
        sentences = _split_into_sentences(page.text)
        current_words: list[str] = []

        for sentence in sentences:
            words = sentence.split()
            if not words:
                continue

            current_words.extend(words)

            if len(current_words) >= chunk_size:
                chunk_text = " ".join(current_words)
                token_count = len(current_words)

                if token_count >= min_chunk_tokens:
                    all_chunks.append(
                        TextChunk(
                            text=chunk_text,
                            page_number=page.page_number,
                            chunk_index=global_chunk_index,
                            token_count=token_count,
                        )
                    )
                    global_chunk_index += 1
                else:
                    logger.info(
                        "Skipped short chunk (%d tokens) on page %d",
                        token_count,
                        page.page_number,
                    )

                # Keep overlap words for the next chunk
                current_words = current_words[-chunk_overlap:] if chunk_overlap > 0 else []

        # Flush remaining words for this page
        if current_words:
            token_count = len(current_words)
            if token_count >= min_chunk_tokens:
                chunk_text = " ".join(current_words)
                all_chunks.append(
                    TextChunk(
                        text=chunk_text,
                        page_number=page.page_number,
                        chunk_index=global_chunk_index,
                        token_count=token_count,
                    )
                )
                global_chunk_index += 1
            else:
                logger.info(
                    "Skipped short chunk (%d tokens) on page %d",
                    token_count,
                    page.page_number,
                )

    logger.info("Created %d chunks from %d pages", len(all_chunks), len(pages))
    return all_chunks


def _split_into_sentences(text: str) -> list[str]:
    """Split text into sentence-like segments."""
    # First split by newlines, then by periods
    segments: list[str] = []
    for line in text.split("\n"):
        line = line.strip()
        if not line:
            continue
        # Split by sentence-ending punctuation
        parts = line.replace(". ", ".\n").replace("? ", "?\n").replace("! ", "!\n").split("\n")
        segments.extend(p.strip() for p in parts if p.strip())
    return segments
