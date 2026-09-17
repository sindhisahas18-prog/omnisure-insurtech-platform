import enum
import uuid
from datetime import datetime

from sqlalchemy import Column, String, Integer, Date, DateTime, ForeignKey, Enum, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.database import Base


class ClaimStatus(str, enum.Enum):
    draft = "draft"  # FNOL started, not yet submitted
    submitted = "submitted"
    in_triage = "in_triage"
    stp_approved = "stp_approved"
    human_review = "human_review"
    settled = "settled"
    rejected = "rejected"


class DocumentOCRStatus(str, enum.Enum):
    pending = "pending"
    processed = "processed"
    error = "error"


class PaymentStatus(str, enum.Enum):
    pending = "pending"
    paid = "paid"
    failed = "failed"


class Claim(Base):
    """
    One filed claim. `answers` holds the dynamic-question responses
    (see ClaimConfig.dynamic_questions) as {question_key: value} —
    kept as JSONB rather than a fixed set of columns because the
    question set itself varies by insurance type + damaged component.
    """

    __tablename__ = "claims"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    claim_number = Column(String, unique=True, index=True, nullable=False)

    policy_id = Column(UUID(as_uuid=True), ForeignKey("policies.id"), nullable=False)
    customer_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    insurance_type_id = Column(UUID(as_uuid=True), ForeignKey("insurance_types.id"), nullable=False)

    incident_type = Column(String, nullable=True)
    damaged_component = Column(String, nullable=True)
    incident_date = Column(Date, nullable=True)
    description = Column(Text, nullable=True)
    answers = Column(JSONB, nullable=False, default=dict)

    claimed_amount_inr = Column(Integer, nullable=True)
    approved_amount_inr = Column(Integer, nullable=True)

    status = Column(Enum(ClaimStatus), default=ClaimStatus.draft, nullable=False)

    coverage_verified = Column(String, nullable=True)  # "yes" | "no" | "uncertain" — kept as string for the notes it carries
    coverage_notes = Column(Text, nullable=True)

    fraud_risk_score = Column(Integer, nullable=True)  # 0-100
    fraud_risk_reasons = Column(JSONB, nullable=True)

    ai_confidence = Column(Integer, nullable=True)  # 0-100, from damage analysis / OCR quality
    human_review_reasons = Column(JSONB, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    submitted_at = Column(DateTime, nullable=True)
    settled_at = Column(DateTime, nullable=True)

    policy = relationship("Policy")
    customer = relationship("User")
    insurance_type = relationship("InsuranceType")
    documents = relationship("ClaimDocument", back_populates="claim", cascade="all, delete-orphan")
    events = relationship("ClaimEvent", back_populates="claim", cascade="all, delete-orphan", order_by="ClaimEvent.created_at")
    payment = relationship("Payment", back_populates="claim", uselist=False, cascade="all, delete-orphan")


class ClaimDocument(Base):
    __tablename__ = "claim_documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    claim_id = Column(UUID(as_uuid=True), ForeignKey("claims.id"), nullable=False)

    doc_type = Column(String, nullable=False)  # e.g. "Identity Proof", "Incident Photo", "Repair Estimate"
    original_filename = Column(String, nullable=False)
    stored_path = Column(String, nullable=False)

    ocr_status = Column(Enum(DocumentOCRStatus), default=DocumentOCRStatus.pending, nullable=False)
    ocr_text = Column(Text, nullable=True)

    ai_damage_analysis = Column(JSONB, nullable=True)  # {severity, confidence, description, demo_mode}

    uploaded_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    claim = relationship("Claim", back_populates="documents")


class ClaimEvent(Base):
    """
    Append-only timeline: one row per step the claim goes through.
    This is what powers claim tracking / claim history — never
    overwritten, only added to.
    """

    __tablename__ = "claim_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    claim_id = Column(UUID(as_uuid=True), ForeignKey("claims.id"), nullable=False)

    event_type = Column(String, nullable=False)  # "submitted" | "coverage_check" | "fraud_check" | "triage_decision" | "assessment" | "settlement" | "payment" | "email_sent" | "human_review" | "rejected"
    status = Column(String, nullable=False)
    detail = Column(JSONB, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    claim = relationship("Claim", back_populates="events")


class Payment(Base):
    __tablename__ = "payments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    claim_id = Column(UUID(as_uuid=True), ForeignKey("claims.id"), unique=True, nullable=False)

    amount_inr = Column(Integer, nullable=False)
    status = Column(Enum(PaymentStatus), default=PaymentStatus.pending, nullable=False)
    reference = Column(String, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    paid_at = Column(DateTime, nullable=True)

    claim = relationship("Claim", back_populates="payment")
