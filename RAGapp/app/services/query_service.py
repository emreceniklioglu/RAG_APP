"""Query orchestration service.

Handles: RBAC check -> embed question -> vector search -> re-rank (B2) -> LLM generation.
"""

from app.core.logging import logger
from app.core.rbac import get_allowed_departments
from app.services import embedding_service, llm_service, reranking_service, vector_store_service
from app.utils.timers import log_timer

CAPABILITY_RESPONSE = (
    "Doküman bazlı sorularınızı yanıtlayabilir, yüklenen PDF/Excel dosyalarından "
    "ilgili bilgileri bulup kaynak sayfa veya satır referanslarıyla açıklayabilirim."
)


def _is_capability_question(question: str) -> bool:
    """Return True when the user asks about assistant capabilities."""
    normalized_question = " ".join(question.casefold().split())
    return "neler yapabilirsin" in normalized_question


def query_documents(question: str, user_role: str) -> dict:
    """Execute a RAG query against ingested documents.

    Args:
        question: User's question in Turkish.
        user_role: Role of the user (determines accessible departments).

    Returns:
        Dict with 'answer' and 'sources' list.

    Raises:
        ValueError: If user_role is invalid.
    """
    with log_timer(f"RAG query: {question[:50]}..."):
        # 1. RBAC: determine allowed departments
        departments = get_allowed_departments(user_role)
        logger.info("User role '%s' -> departments: %s", user_role, departments)

        if _is_capability_question(question):
            logger.info("Capability question detected")
            return {
                "answer": CAPABILITY_RESPONSE,
                "sources": [],
            }

        # 2. Embed the question
        query_embedding = embedding_service.get_single_embedding(question)

        # 3. Search vector store with department filter
        results = vector_store_service.query_chunks(
            query_embedding=query_embedding,
            departments=departments,
        )

        # 4. Check if any results were found
        if not results["ids"] or not results["ids"][0]:
            logger.info("No relevant chunks found for query")
            return {
                "answer": (
                    "Erişiminiz dahilindeki dokümanlarda bu soruyla ilgili "
                    "bilgi bulunamadı."
                ),
                "sources": [],
            }

        # 5. Build intermediate chunk list with scores
        raw_chunks: list[dict] = []
        for i in range(len(results["ids"][0])):
            doc_text = results["documents"][0][i]
            metadata = results["metadatas"][0][i]
            distance = results["distances"][0][i]
            score = round(1.0 - distance, 4)

            raw_chunks.append({
                "text": doc_text,
                "filename": metadata["filename"],
                "page_number": metadata.get("page_number") or metadata.get("row_index", 0),
                "score": score,
            })

        # 6. Apply hybrid re-ranking (B2)
        ranked_chunks = reranking_service.rerank(question, raw_chunks)

        # 7. Build context and sources from re-ranked results
        context_chunks: list[dict] = []
        sources: list[dict] = []

        for chunk in ranked_chunks:
            context_chunks.append({
                "text": chunk["text"],
                "filename": chunk["filename"],
                "page_number": chunk.get("page_number", 0),
            })

            excerpt = chunk["text"][:200] + "..." if len(chunk["text"]) > 200 else chunk["text"]

            sources.append({
                "filename": chunk["filename"],
                "page_number": chunk["page_number"],
                "chunk_excerpt": excerpt,
                "score": chunk["score"],
                "rerank_score": chunk["rerank_score"],
            })

        # 8. Generate answer with LLM
        answer = llm_service.generate_answer(question, context_chunks)

        logger.info("Query completed with %d sources", len(sources))
        return {
            "answer": answer,
            "sources": sources,
        }
