import uuid
from datetime import date, datetime

from pydantic import BaseModel

from app.models.claim import ClaimStatus, DocumentOCRStatus, PaymentStatus


class ClaimConfigOut(BaseModel):
    incident_types: list[str]
    damaged_components: list[str]
    required_documents: list[str]
    dynamic_questions: list[dict]


class ClaimCreateRequest(BaseModel):
    policy_id: uuid.UUID
    incident_type: str | None = None
    damaged_component: str | None = None
    incident_date: date | None = None
    description: str | None = None
    answers: dict = {}
    claimed_amount_inr: int | None = None


class ClaimUpdateRequest(BaseModel):
    incident_type: str | None = None
    damaged_component: str | None = None
    incident_date: date | None = None
    description: str | None = None
    answers: dict | None = None
    claimed_amount_inr: int | None = None


class ClaimDocumentOut(BaseModel):
    id: uuid.UUID
    doc_type: str
    original_filename: str
    ocr_status: DocumentOCRStatus
    ocr_text: str | None
    ai_damage_analysis: dict | None
    uploaded_at: datetime

    class Config:
        from_attributes = True


class ClaimEventOut(BaseModel):
    id: uuid.UUID
    event_type: str
    status: str
    detail: dict | None
    created_at: datetime

    class Config:
        from_attributes = True


class PaymentOut(BaseModel):
    amount_inr: int
    status: PaymentStatus
    reference: str | None
    paid_at: datetime | None

    class Config:
        from_attributes = True


class ClaimOut(BaseModel):
    id: uuid.UUID
    claim_number: str
    policy_id: uuid.UUID
    insurance_type_id: uuid.UUID
    incident_type: str | None
    damaged_component: str | None
    incident_date: date | None
    description: str | None
    answers: dict
    claimed_amount_inr: int | None
    approved_amount_inr: int | None
    status: ClaimStatus
    coverage_verified: str | None
    coverage_notes: str | None
    fraud_risk_score: int | None
    fraud_risk_reasons: list | None
    ai_confidence: int | None
    human_review_reasons: list | None
    created_at: datetime
    submitted_at: datetime | None
    settled_at: datetime | None

    class Config:
        from_attributes = True


class ClaimDetailOut(ClaimOut):
    documents: list[ClaimDocumentOut]
    events: list[ClaimEventOut]
    payment: PaymentOut | None


class HumanReviewDecisionRequest(BaseModel):
    approve: bool
    approved_amount_inr: int | None = None
    note: str = ""
