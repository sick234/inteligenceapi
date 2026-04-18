"""
AI Service — Groq (Llama 3) integration for document analysis.

Provides text summarization with:
- Configurable model parameters via environment variables
- Automatic retry with exponential backoff
- Input text truncation to fit model context window
- Error handling and graceful degradation
"""
import time
from groq import Groq
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

# Initialize client lazily to avoid errors if key is not set
_client: Groq | None = None


def _get_client() -> Groq | None:
    """Get or create the Groq client singleton."""
    global _client
    if _client is None and settings.GROQ_API_KEY:
        _client = Groq(api_key=settings.GROQ_API_KEY)
    return _client


def generate_summary(text: str, max_retries: int = 3) -> str:
    """
    Generate an AI-powered summary of the provided text using Groq.

    Args:
        text: The extracted document text to summarize.
        max_retries: Number of retry attempts on transient failures.

    Returns:
        The AI-generated summary string, or an error message.
    """
    client = _get_client()
    if not client:
        logger.warning("GROQ_API_KEY not configured. Skipping AI summary.")
        return "⚠️ AI summary unavailable: GROQ_API_KEY not configured."

    # Truncate to fit model context window (~6000 tokens ≈ 24000 chars)
    max_chars = 20000
    truncated = len(text) > max_chars
    input_text = text[:max_chars]

    if truncated:
        logger.info("Text truncated from %d to %d chars for AI processing", len(text), max_chars)

    system_prompt = (
        "You are an expert document analyst. Your task is to:\n"
        "1. Extract the key information and main points from the document.\n"
        "2. Generate a well-structured, concise summary.\n"
        "3. Highlight any important dates, numbers, names, or action items.\n"
        "4. Use bullet points for clarity when appropriate.\n"
        "5. If the document is in Spanish, respond in Spanish. "
        "If in English, respond in English."
    )

    user_prompt = (
        f"Please analyze and summarize the following document"
        f"{' (truncated)' if truncated else ''}:\n\n{input_text}"
    )

    for attempt in range(1, max_retries + 1):
        try:
            start = time.perf_counter()
            chat_completion = client.chat.completions.create(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                model=settings.GROQ_MODEL,
                temperature=settings.GROQ_TEMPERATURE,
                max_tokens=settings.GROQ_MAX_TOKENS,
            )
            elapsed = time.perf_counter() - start
            summary = chat_completion.choices[0].message.content

            logger.info(
                "AI summary generated in %.2fs (model=%s, attempt=%d/%d)",
                elapsed, settings.GROQ_MODEL, attempt, max_retries,
            )
            return summary

        except Exception as e:
            logger.warning(
                "AI summary attempt %d/%d failed: %s",
                attempt, max_retries, str(e),
            )
            if attempt < max_retries:
                # Exponential backoff: 1s, 2s, 4s
                backoff = 2 ** (attempt - 1)
                logger.info("Retrying in %ds...", backoff)
                time.sleep(backoff)

    return "❌ AI summary failed after all retry attempts."
