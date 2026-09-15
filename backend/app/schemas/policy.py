import uuid
from datetime import date, datetime

from pydantic import BaseModel

from app.models.policy import PolicyStatus
from app.schemas.catalog import InsuranceTypeOut


class PolicyOut(BaseModel):
    id: uuid.UUID
    policy_number: str
    provider_name: str
    premium_inr: int
    sum_insured_inr: int | None
    start_date: date
    end_date: date
    status: PolicyStatus
    created_at: datetime
    insurance_type: InsuranceTypeOut

    class Config:
        from_attributes = True


class DashboardSummary(BaseModel):
    active_policies: int
    total_coverage_inr: int
    open_claims: int
    upcoming_renewals: int
    policies: list[PolicyOut]
