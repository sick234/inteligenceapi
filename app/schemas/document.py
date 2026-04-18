"""
Pydantic schemas for Document request/response validation.

Supports pagination metadata and detailed document analytics
(word count, page count, processing time).
"""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class DocumentResponse(BaseModel):
    """Summary view of a document (used in lists)."""
    id: int
    filename: str
    content_type: str
    file_size_bytes: Optional[int] = None
    status: str = Field(description="uploaded | processing | completed | failed")
    word_count: Optional[int] = None
    page_count: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class DocumentDetailResponse(DocumentResponse):
    """Full document view including extracted text and AI summary."""
    extracted_text: Optional[str] = None
    summary: Optional[str] = None
    processing_time_seconds: Optional[float] = None


class PaginatedDocumentsResponse(BaseModel):
    """Paginated list of documents with metadata."""
    items: list[DocumentResponse]
    total: int = Field(description="Total number of documents")
    page: int = Field(description="Current page number")
    page_size: int = Field(description="Number of items per page")
    total_pages: int = Field(description="Total number of pages")


class DocumentStatsResponse(BaseModel):
    """Aggregate statistics about a user's documents."""
    total_documents: int
    completed: int
    processing: int
    failed: int
    total_words_analyzed: int
