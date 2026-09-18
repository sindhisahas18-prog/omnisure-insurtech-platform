from pydantic import BaseModel
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import require_role
from app.database import get_db
from app.models.user import User, UserRole
from app.services.analytics import get_charts, get_kpis

router = APIRouter(prefix="/api/v1/admin", tags=["admin"])


class AdminKPIs(BaseModel):
    total_customers: int
    total_employees: int
    active_policies: int
    total_claims: int
    settled_claims: int
    pending_claims: int  # submitted + in_triage + human_review
    stp_rate: float  # percent of triaged claims that went straight-through
    manual_review_rate: float  # percent of triaged claims sent to human review
    average_claim_amount_inr: int
    fraud_risk_claims: int  # claims with fraud/risk score >= 50


class ChartSeries(BaseModel):
    label: str
    value: int | float


class AdminCharts(BaseModel):
    claims_by_insurance_type: list[ChartSeries]
    claims_by_status: list[ChartSeries]
    settlement_amount_by_month: list[ChartSeries]
    stp_vs_manual: list[ChartSeries]
    fraud_risk_distribution: list[ChartSeries]
    monthly_claims: list[ChartSeries]
    premium_revenue_by_type: list[ChartSeries]


@router.get("/kpis", response_model=AdminKPIs)
def admin_kpis(
    db: Session = Depends(get_db),
    _admin: User = Depends(require_role(UserRole.admin)),
):
    return get_kpis(db)


@router.get("/analytics/charts", response_model=AdminCharts)
def admin_analytics_charts(
    db: Session = Depends(get_db),
    _admin: User = Depends(require_role(UserRole.admin)),
):
    return get_charts(db)
