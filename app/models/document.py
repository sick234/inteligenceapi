"""
SQLAlchemy ORM model for the Document entity.

Stores document metadata, file path, processing status,
extracted text, AI summary, and analytics (word count, page count).
"""
from sqlalchemy import Column, Integer, String, Text, Float, ForeignKey, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.core.database import Base


class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(500), index=True, nullable=False)
    content_type = Column(String(100), nullable=False)
    file_path = Column(String(1000), nullable=False)
    file_size_bytes = Column(Integer, nullable=True)

    # Processing status: uploaded → processing → completed | failed
    status = Column(String(20), default="uploaded", index=True)

    # Extracted content
    extracted_text = Column(Text, nullable=True)
    summary = Column(Text, nullable=True)

    # Analytics
    word_count = Column(Integer, nullable=True)
    page_count = Column(Integer, nullable=True)
    processing_time_seconds = Column(Float, nullable=True)

    # Ownership
    owner_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    owner = relationship("User", back_populates="documents")

    def __repr__(self) -> str:
        return f"<Document(id={self.id}, filename='{self.filename}', status='{self.status}')>"
