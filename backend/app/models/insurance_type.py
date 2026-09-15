import uuid

from sqlalchemy import Column, String, Text, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class InsuranceType(Base):
    """
    One row per insurance category (Car, Bike, Health, ...).

    This is the anchor of the reusable insurance engine: every
    category-specific config (dynamic claim questions, required
    documents, damaged-component lists, coverage/claim/settlement
    rules) hangs off this row instead of being hardcoded per type,
    so Phase 2/3 can add new categories via data, not new code.
    """

    __tablename__ = "insurance_types"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code = Column(String, unique=True, index=True, nullable=False)  # e.g. "car", "health"
    name = Column(String, nullable=False)  # e.g. "Car Insurance"
    description = Column(Text, nullable=True)
    icon = Column(String, nullable=True)  # icon identifier used by the frontend
    is_active = Column(Boolean, default=True, nullable=False)

    policies = relationship("Policy", back_populates="insurance_type")


# Seed data for Phase 1 — the 12 categories from the product spec.
INSURANCE_TYPE_SEED = [
    {"code": "car", "name": "Car Insurance", "icon": "car"},
    {"code": "bike", "name": "Bike Insurance", "icon": "bike"},
    {"code": "health", "name": "Health Insurance", "icon": "heart-pulse"},
    {"code": "mobile", "name": "Mobile Insurance", "icon": "smartphone"},
    {"code": "laptop", "name": "Laptop Insurance", "icon": "laptop"},
    {"code": "electronics", "name": "Electronics Insurance", "icon": "tv"},
    {"code": "home", "name": "Home / Property Insurance", "icon": "home"},
    {"code": "travel", "name": "Travel Insurance", "icon": "plane"},
    {"code": "crop", "name": "Crop / Agriculture Insurance", "icon": "wheat"},
    {"code": "business", "name": "Business Insurance", "icon": "briefcase"},
    {"code": "life", "name": "Life / Term Insurance", "icon": "shield-heart"},
    {"code": "livestock", "name": "Livestock Insurance", "icon": "cow"},
]
