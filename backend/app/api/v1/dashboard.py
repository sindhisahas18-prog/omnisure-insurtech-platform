from datetime import date, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session, joinedload

from app.core.deps import get_current_user
from app.database import get_db
from app.models.claim import Claim, ClaimStatus
from app.models.policy import Policy, PolicyStatus
from app.models.user import User
from app.schemas.policy import DashboardSummary, PolicyOut

router = APIRouter(prefix="/api/v1/dashboard", tags=["dashboard"])

OPEN_CLAIM_STATUSES = [ClaimStatus.submitted, ClaimStatus.in_triage, ClaimStatus.human_review]


@router.get("/summary", response_model=DashboardSummary)
def dashboard_summary(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Everything here is computed from the database — no hardcoded stats."""
    policies = (
        db.query(Policy)
        .options(joinedload(Policy.insurance_type))
        .filter(Policy.customer_id == current_user.id)
        .order_by(Policy.end_date)
        .all()
    )

    active_policies = [p for p in policies if p.status == PolicyStatus.active]
    total_coverage = sum(p.sum_insured_inr or 0 for p in active_policies)

    renewal_window = date.today() + timedelta(days=30)
    upcoming_renewals = sum(1 for p in active_policies if p.end_date <= renewal_window)

    open_claims = (
        db.query(Claim)
        .filter(Claim.customer_id == current_user.id, Claim.status.in_(OPEN_CLAIM_STATUSES))
        .count()
    )

    return DashboardSummary(
        active_policies=len(active_policies),
        total_coverage_inr=total_coverage,
        open_claims=open_claims,
        upcoming_renewals=upcoming_renewals,
        policies=[PolicyOut.model_validate(p) for p in policies],
    )
