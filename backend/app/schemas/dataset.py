import uuid
from datetime import datetime

from pydantic import BaseModel

from app.models.dataset import DatasetStatus


class DatasetOut(BaseModel):
    id: uuid.UUID
    insurance_type_id: uuid.UUID
    name: str
    original_filename: str
    version: int
    status: DatasetStatus
    record_count: int
    column_mapping: dict | None
    quality_report: dict | None
    uploaded_at: datetime
    processed_at: datetime | None
    error_message: str | None

    class Config:
        from_attributes = True


class DatasetPreview(BaseModel):
    columns: list[str]
    column_mapping: dict
    quality_report: dict
    sample_rows: list[dict]


class DatasetRecordOut(BaseModel):
    id: uuid.UUID
    row_index: int
    data: dict

    class Config:
        from_attributes = True
