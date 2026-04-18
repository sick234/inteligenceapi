"""
Celery background tasks for document processing.

Handles the complete document analysis pipeline:
1. Update status to "processing"
2. Extract text from PDF (PyMuPDF) or plain text files
3. Compute analytics (word count, page count)
4. Generate AI summary via Groq (Llama 3)
5. Update status to "completed" with all results

Each task creates its own async database session to avoid
conflicts with the main FastAPI event loop.
"""
import asyncio
import time

import fitz  # PyMuPDF
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.worker.celery_app import celery_app
from app.services.ai_service import generate_summary
from app.models.document import Document
from app.models.user import User  # Required for SQLAlchemy mapper
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

# One engine per worker process. Created lazily inside the async loop so the
# asyncpg connection pool binds to the loop that will actually use it.
_engine = None
_SessionLocal = None


def _get_session_factory():
    global _engine, _SessionLocal
    if _SessionLocal is None:
        _engine = create_async_engine(
            settings.DATABASE_URL,
            echo=False,
            pool_size=5,
            max_overflow=5,
            pool_pre_ping=True,
        )
        _SessionLocal = async_sessionmaker(
            _engine, class_=AsyncSession, expire_on_commit=False
        )
    return _SessionLocal


def extract_text_from_pdf(file_path: str) -> tuple[str, int]:
    """
    Extract text from a PDF file using PyMuPDF.

    Returns:
        A tuple of (extracted_text, page_count).
    """
    try:
        doc = fitz.open(file_path)
        page_count = len(doc)
        text_parts = []
        for page in doc:
            text_parts.append(page.get_text())
        doc.close()
        return "\n".join(text_parts), page_count
    except Exception as e:
        logger.error("PDF extraction failed for %s: %s", file_path, str(e))
        return f"Error reading PDF: {str(e)}", 0


def count_words(text: str) -> int:
    """Count the number of words in a text string."""
    if not text or text.startswith("Error"):
        return 0
    return len(text.split())


async def _process_document_async(document_id: int, file_path: str, content_type: str):
    """Async implementation of the document processing pipeline."""
    SessionLocal = _get_session_factory()
    start_time = time.perf_counter()

    async def update_document(**kwargs):
        """Update document fields in the database."""
        async with SessionLocal() as session:
            doc = await session.get(Document, document_id)
            if doc:
                for key, value in kwargs.items():
                    setattr(doc, key, value)
                await session.commit()

    try:
        logger.info("🔄 Processing document id=%d (type=%s)", document_id, content_type)
        await update_document(status="processing")

        # ── Step 1: Extract text ──────────────────────────────────
        extracted_text = ""
        page_count = None

        if content_type == "application/pdf":
            extracted_text, page_count = extract_text_from_pdf(file_path)
        elif content_type == "text/plain":
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                extracted_text = f.read()
        else:
            extracted_text = "Unsupported format for text extraction."

        word_count = count_words(extracted_text)
        logger.info(
            "📄 Text extracted: %d words, %s pages",
            word_count, page_count or "N/A",
        )

        # ── Step 2: Generate AI summary ───────────────────────────
        summary = ""
        if extracted_text and not extracted_text.startswith("Error") and word_count > 0:
            summary = generate_summary(extracted_text)
        elif word_count == 0:
            summary = "⚠️ No text content found in the document."

        # ── Step 3: Save results ──────────────────────────────────
        processing_time = round(time.perf_counter() - start_time, 2)

        await update_document(
            status="completed",
            extracted_text=extracted_text,
            summary=summary,
            word_count=word_count,
            page_count=page_count,
            processing_time_seconds=processing_time,
        )
        logger.info(
            "✅ Document id=%d completed in %.2fs (%d words)",
            document_id, processing_time, word_count,
        )

    except Exception as e:
        processing_time = round(time.perf_counter() - start_time, 2)
        logger.exception("❌ Document id=%d failed: %s", document_id, str(e))
        await update_document(
            status="failed",
            summary=f"Processing error: {str(e)}",
            processing_time_seconds=processing_time,
        )


@celery_app.task(
    name="process_document_task",
    bind=True,
    max_retries=2,
    default_retry_delay=10,
)
def process_document_task(self, document_id: int, file_path: str, content_type: str):
    """
    Celery task entry point for document processing.

    Wraps the async pipeline in asyncio.run() since Celery
    workers run in synchronous mode.
    """
    logger.info("📥 Task received: document_id=%d", document_id)
    try:
        asyncio.run(_process_document_async(document_id, file_path, content_type))
    except Exception as exc:
        logger.error("Task failed for document_id=%d: %s", document_id, str(exc))
        raise self.retry(exc=exc)
