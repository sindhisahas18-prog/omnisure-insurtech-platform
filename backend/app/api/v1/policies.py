import uuid

from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.database import get_db
from app.models.policy import Policy
from app.models.user import User
from app.services.policy_explainer import explain_policy

router = APIRouter(prefix="/api/v1/policies", tags=["policies"])


class PolicyExplanation(BaseModel):
    answer: str
    sources: list[str]
    demo_mode: bool


@router.get("/{policy_id}/explain", response_model=PolicyExplanation)
def explain(
    policy_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    policy = db.query(Policy).filter(Policy.id == policy_id, Policy.customer_id == current_user.id).first()
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")
    return explain_policy(db, policy)
