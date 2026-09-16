from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.database import get_db
from app.models.user import User
from app.schemas.document import AdvisorRequest, AdvisorResponse
from app.services.advisor import get_recommendation

router = APIRouter(prefix="/api/v1/advisor", tags=["advisor"])


@router.post("/ask", response_model=AdvisorResponse)
def ask_advisor(
    payload: AdvisorRequest,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
):
    result = get_recommendation(db, payload.insurance_type_code, payload.query, payload.budget_inr)
    return AdvisorResponse(**result)
