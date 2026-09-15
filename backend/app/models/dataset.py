import enum
import uuid
from datetime import datetime

from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Enum, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.database import Base


class DatasetStatus(str, enum.Enum):
    uploaded = "uploaded"
    validating = "validating"
    validated = "validated"
    processing = "processing"
    processed = "processed"
    error = "error"


class Dataset(Base):
    """
    One uploaded file for one insurance type. Raw rows land in
    DatasetRecord once processed; this row tracks status, the
    column-mapping report, and the data-quality report so the admin
    panel can show exactly what happened without re-scanning the file.
    """

    __tablename__ = "datasets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    insurance_type_id = Column(UUID(as_uuid=True), ForeignKey("insurance_types.id"), nullable=False)

    name = Column(String, nullable=False)
    original_filename = Column(String, nullable=False)
    stored_path = Column(String, nullable=False)
    version = Column(Integer, default=1, nullable=False)

    status = Column(Enum(DatasetStatus), default=DatasetStatus.uploaded, nullable=False)
    record_count = Column(Integer, default=0, nullable=False)

    column_mapping = Column(JSONB, nullable=True)  # {raw_column: canonical_field_or_null}
    quality_report = Column(JSONB, nullable=True)

    uploaded_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    processed_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)

    insurance_type = relationship("InsuranceType")
    records = relationship("DatasetRecord", back_populates="dataset", cascade="all, delete-orphan")


class DatasetRecord(Base):
    """
    One cleaned row from a processed dataset, kept under its original
    column names in `data` (JSONB) — see Dataset.column_mapping for
    how those column names map to canonical concepts. Storing raw
    column names (rather than forcing everything into a fixed schema)
    is what lets very different insurance-type datasets share one
    table without losing information.
    """

    __tablename__ = "dataset_records"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    dataset_id = Column(UUID(as_uuid=True), ForeignKey("datasets.id"), nullable=False)
    row_index = Column(Integer, nullable=False)
    data = Column(JSONB, nullable=False)

    dataset = relationship("Dataset", back_populates="records")
