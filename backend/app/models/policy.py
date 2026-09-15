import enum
import uuid
from datetime import datetime

from sqlalchemy import Column, String, Integer, Date, DateTime, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class PolicyStatus(str, enum.Enum):
    active = "active"
    expired = "expired"
    cancelled = "cancelled"
    pending_renewal = "pending_renewal"


class Policy(Base):
    """
    A customer's purchased policy. Phase 1 stores the record only —
    the AI recommendation/comparison engine that fills this in from
    the RAG knowledge base + datasets is Phase 2.
    """

    __tablename__ = "policies"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    insurance_type_id = Column(UUID(as_uuid=True), ForeignKey("insurance_types.id"), nullable=False)

    policy_number = Column(String, unique=True, index=True, nullable=False)
    provider_name = Column(String, nullable=False)
    premium_inr = Column(Integer, nullable=False)
    sum_insured_inr = Column(Integer, nullable=True)

    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    status = Column(Enum(PolicyStatus), default=PolicyStatus.active, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    customer = relationship("User", back_populates="policies")
    insurance_type = relationship("InsuranceType", back_populates="policies")
