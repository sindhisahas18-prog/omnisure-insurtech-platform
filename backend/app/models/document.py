import enum
import uuid
from datetime import datetime

from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Enum, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class DocumentStatus(str, enum.Enum):
    uploaded = "uploaded"
    processing = "processing"
    indexed = "indexed"
    error = "error"


class PolicyDocument(Base):
    """
    An unstructured policy document (PDF or text) for one insurance
    type. Gets chunked + embedded + added to that insurance type's
    FAISS index; DocumentChunk rows hold the retrievable text.
    """

    __tablename__ = "policy_documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    insurance_type_id = Column(UUID(as_uuid=True), ForeignKey("insurance_types.id"), nullable=False)

    title = Column(String, nullable=False)
    original_filename = Column(String, nullable=False)
    stored_path = Column(String, nullable=False)

    status = Column(Enum(DocumentStatus), default=DocumentStatus.uploaded, nullable=False)
    chunk_count = Column(Integer, default=0, nullable=False)
    error_message = Column(Text, nullable=True)

    uploaded_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    indexed_at = Column(DateTime, nullable=True)

    insurance_type = relationship("InsuranceType")
    chunks = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan")


class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey("policy_documents.id"), nullable=False)
    chunk_index = Column(Integer, nullable=False)
    text = Column(Text, nullable=False)

    document = relationship("PolicyDocument", back_populates="chunks")
