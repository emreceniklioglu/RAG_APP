"""Lightweight hybrid re-ranking service (B2).

Cross-encoder modelleri (örn. cross-encoder/ms-marco-MiniLM) daha yüksek doğruluk sağlar
ancak CPU'da yavaş çalıştığından lightweight hybrid skorlama tercih edildi.

Score = (vector_similarity × 0.7) + (keyword_overlap_ratio × 0.3)
"""

import re
import string

from app.core.logging import logger


def _tokenize(text: str) -> set[str]:
    """Lowercase and strip punctuation, return word set."""
    text = text.lower()
    text = re.sub(f"[{re.escape(string.punctuation)}]", " ", text)
    return set(text.split())


def _keyword_overlap_ratio(question_words: set[str], chunk_words: set[str]) -> float:
    """Fraction of question words found in the chunk."""
    if not question_words:
        return 0.0
    overlap = question_words & chunk_words
    return len(overlap) / len(question_words)


def rerank(
    question: str,
    chunks: list[dict],
    vector_weight: float = 0.7,
    keyword_weight: float = 0.3,
) -> list[dict]:
    """Re-rank retrieved chunks using hybrid scoring.

    Args:
        question: The user's question text.
        chunks: List of dicts, each with at least 'text' and 'score' keys.
        vector_weight: Weight for the vector similarity component.
        keyword_weight: Weight for the keyword overlap component.

    Returns:
        The same list, sorted by rerank_score descending, with 'rerank_score'
        and 'keyword_overlap' fields added.
    """
    question_words = _tokenize(question)

    for chunk in chunks:
        chunk_words = _tokenize(chunk["text"])
        kw_ratio = _keyword_overlap_ratio(question_words, chunk_words)

        vector_sim = chunk.get("score", 0.0)
        rerank_score = round(
            (vector_sim * vector_weight) + (kw_ratio * keyword_weight), 4
        )

        chunk["keyword_overlap"] = round(kw_ratio, 4)
        chunk["rerank_score"] = rerank_score

    chunks.sort(key=lambda c: c["rerank_score"], reverse=True)

    logger.info(
        "Re-ranked %d chunks (top rerank_score=%.4f)",
        len(chunks),
        chunks[0]["rerank_score"] if chunks else 0.0,
    )
    return chunks
