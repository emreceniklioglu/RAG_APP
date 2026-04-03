"""Embedding service using Jina v3 API.

Calls the Jina Embeddings API to generate dense vector representations.
Uses a module-level session for connection reuse.
"""

import requests

from app.core.config import settings
from app.core.logging import logger
from app.utils.timers import log_timer

JINA_API_URL = "https://api.jina.ai/v1/embeddings"

# Reusable session for connection pooling
_session = requests.Session()


def get_embeddings(texts: list[str]) -> list[list[float]]:
    """Generate embeddings for a list of texts using Jina v3 API.

    Args:
        texts: List of text strings to embed.

    Returns:
        List of embedding vectors (each a list of floats).

    Raises:
        RuntimeError: If the API call fails.
    """
    if not texts:
        return []

    if not settings.JINA_API_KEY:
        raise RuntimeError(
            "JINA_API_KEY ortam değişkeni ayarlanmamış. "
            ".env dosyasını kontrol edin."
        )

    with log_timer(f"Jina embedding ({len(texts)} texts)"):
        headers = {
            "Authorization": f"Bearer {settings.JINA_API_KEY}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": settings.JINA_MODEL,
            "input": texts,
        }

        response = _session.post(JINA_API_URL, json=payload, headers=headers, timeout=60)

        if response.status_code != 200:
            logger.error("Jina API error: %s %s", response.status_code, response.text[:500])
            raise RuntimeError(
                f"Embedding API hatası: {response.status_code}"
            )

        data = response.json()
        embeddings = [item["embedding"] for item in data["data"]]

    logger.info("Generated %d embeddings (dim=%d)", len(embeddings), len(embeddings[0]))
    return embeddings


def get_single_embedding(text: str) -> list[float]:
    """Generate an embedding for a single text."""
    results = get_embeddings([text])
    return results[0]
