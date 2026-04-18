"""
Document management routes.

Provides endpoints for uploading, listing, retrieving, and deleting
documents with pagination, file size validation, and ownership checks.
"""
import math
import os
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, status, Request
from sqlalchemy import func as sa_func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.config import settings
from app.core.database import get_db
from app.core.logging import get_logger
from app.core.limiter import limiter
from app.models.document import Document
from app.models.user import User
from app.schemas.document import (
    DocumentResponse,
    DocumentDetailResponse,
    PaginatedDocumentsResponse,
    DocumentStatsResponse,
)
from app.api.auth import get_current_user
from app.worker.tasks import process_document_task

router = APIRouter()
logger = get_logger(__name__)

UPLOAD_DIR = Path("uploads").resolve()
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# Magic-byte signatures for accepted formats. Never trust the client-supplied
# Content-Type header alone — it is user controlled.
_PDF_MAGIC = b"%PDF-"


def _sniff_content_type(head: bytes, declared: str) -> str | None:
    """Return the real content type from magic bytes, or None if unsupported."""
    if head.startswith(_PDF_MAGIC):
        return "application/pdf"
    # Plain text: require the payload to be valid UTF-8 (or latin-1 fallback).
    if declared == "text/plain":
        try:
            head.decode("utf-8")
            return "text/plain"
        except UnicodeDecodeError:
            return None
    return None


@router.post(
    "/upload",
    response_model=DocumentResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Upload a document for AI analysis",
)
@limiter.limit(settings.RATE_LIMIT_UPLOAD)
async def upload_document(
    request: Request,
    file: UploadFile = File(..., description="PDF or plain text file"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Upload a document to be processed by AI in the background.

    **Supported formats**: PDF (.pdf), Plain Text (.txt)
    **Max file size**: Configurable (default 20MB)

    The document will be queued for processing. Use the GET endpoint
    to check its status and retrieve the AI-generated summary.
    """
    # ── Reject by declared content-type early (cheap check) ───────
    if file.content_type not in settings.ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Only PDF or Plain Text files are allowed. Got: {file.content_type}",
        )

    # ── Reject oversized uploads by Content-Length (avoid DoS) ────
    max_size = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    declared_size = request.headers.get("content-length")
    if declared_size and declared_size.isdigit() and int(declared_size) > max_size:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large. Maximum size is {settings.MAX_UPLOAD_SIZE_MB}MB.",
        )

    # ── Stream to disk under a random UUID name (blocks path traversal) ──
    ext = ".pdf" if file.content_type == "application/pdf" else ".txt"
    stored_name = f"{uuid.uuid4().hex}{ext}"
    file_location = UPLOAD_DIR / stored_name
    # Defense in depth: ensure the resolved path is still inside UPLOAD_DIR.
    if not str(file_location.resolve()).startswith(str(UPLOAD_DIR)):
        raise HTTPException(status_code=400, detail="Invalid file path")

    file_size = 0
    sniffed_type: str | None = None
    head_buffer = bytearray()
    try:
        with open(file_location, "wb") as out:
            while chunk := await file.read(1024 * 1024):  # 1 MiB chunks
                file_size += len(chunk)
                if file_size > max_size:
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail=f"File too large. Maximum size is {settings.MAX_UPLOAD_SIZE_MB}MB.",
                    )
                if len(head_buffer) < 512:
                    head_buffer.extend(chunk[: 512 - len(head_buffer)])
                out.write(chunk)

        if file_size == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot upload an empty file.",
            )

        # ── Sniff real type from magic bytes ──────────────────────
        sniffed_type = _sniff_content_type(bytes(head_buffer), file.content_type)
        if sniffed_type is None or sniffed_type != file.content_type:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File content does not match its declared type.",
            )
    except HTTPException:
        if file_location.exists():
            file_location.unlink(missing_ok=True)
        raise

    # ── Create database record ────────────────────────────────────
    db_doc = Document(
        filename=file.filename,
        content_type=sniffed_type,
        file_path=str(file_location),
        file_size_bytes=file_size,
        owner_id=current_user.id,
    )
    db.add(db_doc)
    await db.commit()
    await db.refresh(db_doc)

    # ── Dispatch background task ──────────────────────────────────
    process_document_task.delay(db_doc.id, str(file_location), sniffed_type)

    logger.info(
        "Document uploaded: id=%d, file=%s, size=%d bytes, user=%s",
        db_doc.id, file.filename, file_size, current_user.email,
    )
    return db_doc


@router.get(
    "/",
    response_model=PaginatedDocumentsResponse,
    summary="List your documents (paginated)",
)
async def list_documents(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(None, ge=1, le=100, description="Items per page"),
    status_filter: str | None = Query(None, alias="status", description="Filter by status"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    List all documents belonging to the authenticated user.

    Supports pagination and optional status filtering
    (uploaded, processing, completed, failed).
    """
    if page_size is None:
        page_size = settings.DEFAULT_PAGE_SIZE

    # Base query
    query = select(Document).where(Document.owner_id == current_user.id)
    count_query = select(sa_func.count(Document.id)).where(Document.owner_id == current_user.id)

    # Apply status filter
    if status_filter:
        query = query.where(Document.status == status_filter)
        count_query = count_query.where(Document.status == status_filter)

    # Get total count
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Apply pagination
    offset = (page - 1) * page_size
    query = query.order_by(Document.created_at.desc()).offset(offset).limit(page_size)

    result = await db.execute(query)
    documents = result.scalars().all()

    return PaginatedDocumentsResponse(
        items=documents,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=math.ceil(total / page_size) if total > 0 else 0,
    )


@router.get(
    "/stats",
    response_model=DocumentStatsResponse,
    summary="Get document processing statistics",
)
async def get_document_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Returns aggregate statistics about the user's documents."""
    base = select(sa_func.count(Document.id)).where(Document.owner_id == current_user.id)

    total = (await db.execute(base)).scalar() or 0
    completed = (await db.execute(base.where(Document.status == "completed"))).scalar() or 0
    processing = (await db.execute(base.where(Document.status == "processing"))).scalar() or 0
    failed = (await db.execute(base.where(Document.status == "failed"))).scalar() or 0

    words_result = await db.execute(
        select(sa_func.coalesce(sa_func.sum(Document.word_count), 0))
        .where(Document.owner_id == current_user.id)
    )
    total_words = words_result.scalar() or 0

    return DocumentStatsResponse(
        total_documents=total,
        completed=completed,
        processing=processing,
        failed=failed,
        total_words_analyzed=total_words,
    )


@router.get(
    "/{document_id}",
    response_model=DocumentDetailResponse,
    summary="Get document details and AI summary",
)
async def get_document(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Retrieve full document details including extracted text and AI summary.

    Only the document owner can access their documents.
    """
    result = await db.execute(
        select(Document).where(
            Document.id == document_id,
            Document.owner_id == current_user.id,
        )
    )
    doc = result.scalars().first()
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found or you don't have permission to access it.",
        )
    return doc


@router.delete(
    "/{document_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a document",
)
async def delete_document(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Permanently delete a document and its associated file.

    Only the document owner can delete their documents.
    """
    result = await db.execute(
        select(Document).where(
            Document.id == document_id,
            Document.owner_id == current_user.id,
        )
    )
    doc = result.scalars().first()
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found or you don't have permission to delete it.",
        )

    # Delete file from disk
    if doc.file_path and os.path.exists(doc.file_path):
        os.remove(doc.file_path)

    await db.delete(doc)
    await db.commit()
    logger.info("Document deleted: id=%d by user=%s", document_id, current_user.email)
