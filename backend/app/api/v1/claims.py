import shutil
import uuid
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.database import get_db
from app.models.claim import Claim, ClaimDocument, ClaimStatus, DocumentOCRStatus
from app.models.claim_config import ClaimConfig
from app.models.policy import Policy
from app.models.user import User
from app.schemas.claim import (
    ClaimConfigOut,
    ClaimCreateRequest,
    ClaimDetailOut,
    ClaimDocumentOut,
    ClaimOut,
    ClaimUpdateRequest,
)
from app.services.claim_workflow import run_triage
from app.services.damage_analysis import analyze_damage
from app.services.ocr import run_ocr

router = APIRouter(prefix="/api/v1/claims", tags=["claims"])

DOCS_DIR = Path(__file__).resolve().parents[3] / "data" / "claim_documents"
DOCS_DIR.mkdir(parents=True, exist_ok=True)


def _owned_policy(db: Session, policy_id: uuid.UUID, user: User) -> Policy:
    policy = db.query(Policy).filter(Policy.id == policy_id, Policy.customer_id == user.id).first()
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found for this customer")
    return policy


def _owned_claim(db: Session, claim_id: uuid.UUID, user: User) -> Claim:
    claim = db.query(Claim).filter(Claim.id == claim_id, Claim.customer_id == user.id).first()
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")
    return claim


def _generate_claim_number(db: Session) -> str:
    year = datetime.utcnow().year
    count = db.query(Claim).count() + 1
    return f"CLM-{year}-{count:06d}"


@router.get("/config/{insurance_type_code}", response_model=ClaimConfigOut)
def get_claim_config(insurance_type_code: str, db: Session = Depends(get_db), _user: User = Depends(get_current_user)):
    """
    The dynamic-question engine's read side: the frontend calls this
    once it knows the insurance type (and, once picked, filters
    dynamic_questions client-side by damaged_component / applies_to).
    """
    from app.models.insurance_type import InsuranceType

    insurance_type = db.query(InsuranceType).filter(InsuranceType.code == insurance_type_code).first()
    if not insurance_type:
        raise HTTPException(status_code=404, detail="Unknown insurance type")

    config = db.query(ClaimConfig).filter(ClaimConfig.insurance_type_id == insurance_type.id).first()
    if not config:
        raise HTTPException(status_code=404, detail="No claim configuration found for this insurance type yet")

    return ClaimConfigOut(
        incident_types=config.incident_types,
        damaged_components=config.damaged_components,
        required_documents=config.required_documents,
        dynamic_questions=config.dynamic_questions,
    )


@router.post("", response_model=ClaimOut, status_code=status.HTTP_201_CREATED)
def start_claim(
    payload: ClaimCreateRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)
):
    """Start FNOL — creates a draft claim the customer fills in over subsequent calls."""
    policy = _owned_policy(db, payload.policy_id, user)

    claim = Claim(
        claim_number=_generate_claim_number(db),
        policy_id=policy.id,
        customer_id=user.id,
        insurance_type_id=policy.insurance_type_id,
        incident_type=payload.incident_type,
        damaged_component=payload.damaged_component,
        incident_date=payload.incident_date,
        description=payload.description,
        answers=payload.answers,
        claimed_amount_inr=payload.claimed_amount_inr,
        status=ClaimStatus.draft,
    )
    db.add(claim)
    db.commit()
    db.refresh(claim)
    return claim


@router.patch("/{claim_id}", response_model=ClaimOut)
def update_claim(
    claim_id: uuid.UUID,
    payload: ClaimUpdateRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    claim = _owned_claim(db, claim_id, user)
    if claim.status != ClaimStatus.draft:
        raise HTTPException(status_code=400, detail="Only draft claims can be edited")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(claim, field, value)
    db.commit()
    db.refresh(claim)
    return claim


@router.post("/{claim_id}/documents", response_model=ClaimDocumentOut, status_code=status.HTTP_201_CREATED)
def upload_claim_document(
    claim_id: uuid.UUID,
    doc_type: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    claim = _owned_claim(db, claim_id, user)
    if claim.status != ClaimStatus.draft:
        raise HTTPException(status_code=400, detail="Documents can only be added to a draft claim")

    ext = Path(file.filename).suffix.lower()
    doc_id = uuid.uuid4()
    stored_path = DOCS_DIR / f"{doc_id}{ext}"
    with stored_path.open("wb") as out:
        shutil.copyfileobj(file.file, out)

    document = ClaimDocument(
        id=doc_id, claim_id=claim.id, doc_type=doc_type,
        original_filename=file.filename, stored_path=str(stored_path),
    )

    ocr_result = run_ocr(str(stored_path))
    document.ocr_text = ocr_result["text"] or None
    document.ocr_status = DocumentOCRStatus.processed if ocr_result["status"] == "processed" else DocumentOCRStatus.error

    document.ai_damage_analysis = analyze_damage(
        str(stored_path), claim.insurance_type.name, claim.damaged_component
    )

    db.add(document)
    db.commit()
    db.refresh(document)
    return document


@router.post("/{claim_id}/submit", response_model=ClaimDetailOut)
def submit_claim(claim_id: uuid.UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    claim = _owned_claim(db, claim_id, user)
    if claim.status != ClaimStatus.draft:
        raise HTTPException(status_code=400, detail="This claim has already been submitted")

    claim.status = ClaimStatus.submitted
    claim.submitted_at = datetime.utcnow()
    db.commit()
    db.refresh(claim)

    return run_triage(db, claim)


@router.get("", response_model=list[ClaimOut])
def list_my_claims(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return db.query(Claim).filter(Claim.customer_id == user.id).order_by(Claim.created_at.desc()).all()


@router.get("/{claim_id}", response_model=ClaimDetailOut)
def get_claim(claim_id: uuid.UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return _owned_claim(db, claim_id, user)
