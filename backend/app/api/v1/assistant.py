from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.database import get_db
from app.models.user import User
from app.services.assistant import interpret_request

router = APIRouter(prefix="/api/v1/assistant", tags=["assistant"])


class InterpretRequest(BaseModel):
    text: str = Field(min_length=1)


class InterpretResponse(BaseModel):
    intent: str
    action: str
    policy_id: str | None
    insurance_type_code: str | None
    spoken_response: str
    demo_mode: bool


@router.post("/interpret", response_model=InterpretResponse)
def interpret(
    payload: InterpretRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Takes free text — from the browser's speech-to-text or typed
    directly — and resolves it into a concrete action against the
    customer's own data. The frontend executes the action (navigate
    to the claim wizard, open the advisor, ...) and speaks
    `spoken_response` back via text-to-speech.
    """
    return interpret_request(db, current_user.id, payload.text)
