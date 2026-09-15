import uuid
from datetime import datetime

from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Boolean
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship

from app.database import Base


class ServicePlan(Base):
    """
    Premium service plans. Prices are stored as integer paise-free
    rupees (whole ₹) since the product spec prices them in round
    numbers — never hardcode these in the frontend, always read
    from here.
    """

    __tablename__ = "service_plans"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code = Column(String, unique=True, index=True, nullable=False)  # "essential" | "pro" | "max"
    name = Column(String, nullable=False)
    price_inr = Column(Integer, nullable=False)  # e.g. 800, 1000, 1500
    is_most_popular = Column(Boolean, default=False, nullable=False)
    features = Column(ARRAY(String), nullable=False, default=list)

    subscriptions = relationship("ServicePlanSubscription", back_populates="plan")


class ServicePlanSubscription(Base):
    __tablename__ = "service_plan_subscriptions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), unique=True, nullable=False)
    plan_id = Column(UUID(as_uuid=True), ForeignKey("service_plans.id"), nullable=False)
    started_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="service_plan_subscription")
    plan = relationship("ServicePlan", back_populates="subscriptions")


# Seed data — ₹ pricing from the product spec, never dollars.
SERVICE_PLAN_SEED = [
    {
        "code": "essential",
        "name": "Essential",
        "price_inr": 800,
        "is_most_popular": False,
        "features": ["Basic policy management", "Email support", "Claim tracking"],
    },
    {
        "code": "pro",
        "name": "Professional",
        "price_inr": 1000,
        "is_most_popular": True,
        "features": ["Everything in Essential", "AI Advisor priority access", "Faster claim review"],
    },
    {
        "code": "max",
        "name": "Premium",
        "price_inr": 1500,
        "is_most_popular": False,
        "features": ["Everything in Pro", "Dedicated support", "STP priority queue"],
    },
]
