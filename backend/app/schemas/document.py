import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.models.document import DocumentStatus


class DocumentOut(BaseModel):
    id: uuid.UUID
    insurance_type_id: uuid.UUID
    title: str
    original_filename: str
    status: DocumentStatus
    chunk_count: int
    error_message: str | None
    uploaded_at: datetime
    indexed_at: datetime | None

    class Config:
        from_attributes = True


class AdvisorRequest(BaseModel):
    insurance_type_code: str
    query: str = Field(min_length=3)
    budget_inr: float | None = None


class AdvisorResponse(BaseModel):
    answer: str
    candidates: list[dict]
    sources: list[str]
    demo_mode: bool
