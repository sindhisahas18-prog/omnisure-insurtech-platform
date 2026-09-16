import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.core.deps import require_role
from app.database import get_db
from app.models.document import PolicyDocument
from app.models.insurance_type import InsuranceType
from app.models.user import User, UserRole
from app.schemas.document import DocumentOut
from app.services.document_indexing import index_document

router = APIRouter(prefix="/api/v1/admin/documents", tags=["admin-documents"])

UPLOAD_DIR = Path(__file__).resolve().parents[3] / "data" / "documents"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_EXTENSIONS = {".pdf", ".txt"}


@router.post("/upload", response_model=DocumentOut, status_code=status.HTTP_201_CREATED)
def upload_document(
    insurance_type_code: str = Form(...),
    title: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    _admin: User = Depends(require_role(UserRole.admin)),
):
    insurance_type = db.query(InsuranceType).filter(InsuranceType.code == insurance_type_code).first()
    if not insurance_type:
        raise HTTPException(status_code=404, detail=f"Unknown insurance type: {insurance_type_code}")

    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"Unsupported file type '{ext}'. Allowed: {sorted(ALLOWED_EXTENSIONS)}")

    doc_id = uuid.uuid4()
    stored_path = UPLOAD_DIR / f"{doc_id}{ext}"
    with stored_path.open("wb") as out:
        import shutil

        shutil.copyfileobj(file.file, out)

    document = PolicyDocument(
        id=doc_id,
        insurance_type_id=insurance_type.id,
        title=title,
        original_filename=file.filename,
        stored_path=str(stored_path),
    )
    db.add(document)
    db.commit()
    db.refresh(document)

    return index_document(db, document)


@router.get("", response_model=list[DocumentOut])
def list_documents(
    db: Session = Depends(get_db),
    _admin: User = Depends(require_role(UserRole.admin)),
):
    return db.query(PolicyDocument).order_by(PolicyDocument.uploaded_at.desc()).all()


@router.post("/{document_id}/reindex", response_model=DocumentOut)
def reindex_document(
    document_id: uuid.UUID,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_role(UserRole.admin)),
):
    document = db.query(PolicyDocument).get(document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    return index_document(db, document)


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(
    document_id: uuid.UUID,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_role(UserRole.admin)),
):
    document = db.query(PolicyDocument).get(document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    stored_path = Path(document.stored_path)
    db.delete(document)
    db.commit()
    if stored_path.exists():
        stored_path.unlink()
    # Note: this does not remove the document's vectors from the FAISS index
    # (FAISS flat indexes don't support cheap deletion) — a stale vector may
    # still be returned by search until the insurance type's index is rebuilt.
