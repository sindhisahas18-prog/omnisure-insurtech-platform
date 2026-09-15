from pydantic import BaseModel
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import require_role
from app.database import get_db
from app.models.policy import Policy, PolicyStatus
from app.models.user import User, UserRole

router = APIRouter(prefix="/api/v1/admin", tags=["admin"])


class AdminKPIs(BaseModel):
    total_customers: int
    total_employees: int
    active_policies: int
    total_claims: int  # 0 until Phase 3 claims tables exist
    settled_claims: int
    pending_claims: int


@router.get("/kpis", response_model=AdminKPIs)
def admin_kpis(
    db: Session = Depends(get_db),
    _admin: User = Depends(require_role(UserRole.admin)),
):
    total_customers = db.query(User).filter(User.role == UserRole.customer).count()
    total_employees = db.query(User).filter(User.role == UserRole.employee).count()
    active_policies = db.query(Policy).filter(Policy.status == PolicyStatus.active).count()

    return AdminKPIs(
        total_customers=total_customers,
        total_employees=total_employees,
        active_policies=active_policies,
        total_claims=0,
        settled_claims=0,
        pending_claims=0,
    )
