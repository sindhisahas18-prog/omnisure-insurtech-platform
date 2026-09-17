import uuid

from sqlalchemy import Column, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.database import Base


class ClaimConfig(Base):
    """
    The reusable-insurance-engine piece for claims: one row per
    insurance type, holding everything the claim wizard needs to
    behave differently per type WITHOUT any per-type code. Adding a
    13th insurance category's claim flow is a new seed row here, not
    a new branch of if/else somewhere in the claims API.
    """

    __tablename__ = "claim_configs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    insurance_type_id = Column(UUID(as_uuid=True), ForeignKey("insurance_types.id"), unique=True, nullable=False)

    incident_types = Column(JSONB, nullable=False, default=list)  # e.g. ["Accident", "Theft", "Fire"]
    damaged_components = Column(JSONB, nullable=False, default=list)  # e.g. ["Bumper", "Headlight", ...]
    required_documents = Column(JSONB, nullable=False, default=list)  # e.g. ["Identity Proof", "RC Copy", ...]

    # Each item: {key, label, type, options?, applies_to: [component,...] or [] for "always shown"}
    dynamic_questions = Column(JSONB, nullable=False, default=list)

    insurance_type = relationship("InsuranceType")
