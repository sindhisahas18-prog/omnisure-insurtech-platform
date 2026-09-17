import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.deps import require_role
from app.database import get_db
from app.models.claim import Claim, ClaimStatus
from app.models.user import User, UserRole
from app.schemas.claim import ClaimDetailOut, ClaimOut, HumanReviewDecisionRequest
from app.services.claim_workflow import resolve_human_review

router = APIRouter(prefix="/api/v1/admin/claims", tags=["admin-claims"])


@router.get("", response_model=list[ClaimOut])
def list_claims(
    status_filter: ClaimStatus | None = None,
    db: Session = Depends(get_db),
    _reviewer: User = Depends(require_role(UserRole.admin, UserRole.employee)),
):
    query = db.query(Claim)
    if status_filter:
        query = query.filter(Claim.status == status_filter)
    return query.order_by(Claim.created_at.desc()).all()


@router.get("/{claim_id}", response_model=ClaimDetailOut)
def get_claim(
    claim_id: uuid.UUID,
    db: Session = Depends(get_db),
    _reviewer: User = Depends(require_role(UserRole.admin, UserRole.employee)),
):
    claim = db.query(Claim).get(claim_id)
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")
    return claim


@router.post("/{claim_id}/decision", response_model=ClaimDetailOut)
def decide_claim(
    claim_id: uuid.UUID,
    payload: HumanReviewDecisionRequest,
    db: Session = Depends(get_db),
    _reviewer: User = Depends(require_role(UserRole.admin, UserRole.employee)),
):
    claim = db.query(Claim).get(claim_id)
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")
    if claim.status != ClaimStatus.human_review:
        raise HTTPException(status_code=400, detail="Only claims in human_review can be decided here")

    return resolve_human_review(db, claim, payload.approve, payload.approved_amount_inr, payload.note)
