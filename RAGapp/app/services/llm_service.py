"""LLM service using Google Gemini API.

Provides a simple abstraction over the Gemini generative model.
The system prompt enforces Turkish-only answers grounded in context.
"""

import google.generativeai as genai

from app.core.config import settings
from app.core.logging import logger
from app.utils.timers import log_timer

_configured = False


def _ensure_configured() -> None:
    """Configure the Gemini SDK once."""
    global _configured
    if not _configured:
        if not settings.GEMINI_API_KEY:
            raise RuntimeError(
                "GEMINI_API_KEY ortam değişkeni ayarlanmamış. "
                ".env dosyasını kontrol edin."
            )
        genai.configure(api_key=settings.GEMINI_API_KEY)
        _configured = True
        logger.info("Gemini API configured (model=%s)", settings.GEMINI_MODEL)


SYSTEM_PROMPT = """Sen bir teknik dokümantasyon asistanısın. Görevin, sana verilen bağlam bilgilerini kullanarak kullanıcıların sorularını Türkçe olarak yanıtlamaktır.

Kurallar:
1. SADECE sana verilen bağlam bilgilerini kullanarak yanıt ver.
2. Yanıtını her zaman Türkçe olarak ver.
3. Eğer bağlam bilgilerinde sorunun cevabı yoksa, açıkça "Bu bilgi mevcut dokümanlarda bulunamadı." de.
4. Asla bağlamda olmayan bilgileri uydurma.
5. Mümkün olduğunca yanıtında kaynak sayfa numaralarına atıfta bulun (örn: "Sayfa X'e göre...").
6. Yanıtını açık, net ve anlaşılır bir şekilde ver.
"""


def generate_answer(question: str, context_chunks: list[dict]) -> str:
    """Generate an answer using the Gemini LLM.

    Args:
        question: The user's question in Turkish.
        context_chunks: List of dicts with 'text', 'filename', 'page_number' keys.

    Returns:
        The generated answer string.
    """
    _ensure_configured()

    # Build context block
    context_parts: list[str] = []
    for i, chunk in enumerate(context_chunks, 1):
        context_parts.append(
            f"[Kaynak {i} - {chunk['filename']}, Sayfa {chunk['page_number']}]\n"
            f"{chunk['text']}"
        )
    context_text = "\n\n".join(context_parts)

    user_prompt = f"""Bağlam Bilgileri:
{context_text}

Soru: {question}

Lütfen yukarıdaki bağlam bilgilerini kullanarak soruyu Türkçe olarak yanıtla."""

    with log_timer("LLM generation"):
        model = genai.GenerativeModel(
            model_name=settings.GEMINI_MODEL,
            system_instruction=SYSTEM_PROMPT,
        )
        response = model.generate_content(user_prompt)
        answer = response.text

    logger.info("LLM generated answer (%d chars)", len(answer))
    return answer
