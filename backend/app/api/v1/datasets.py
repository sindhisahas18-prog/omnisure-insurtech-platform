import shutil
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.orm import Session

from app.core.deps import require_role
from app.database import get_db
from app.models.dataset import Dataset, DatasetRecord
from app.models.insurance_type import InsuranceType
from app.models.user import User, UserRole
from app.schemas.dataset import DatasetOut, DatasetPreview, DatasetRecordOut
from app.services.ingestion import build_preview, process_dataset

router = APIRouter(prefix="/api/v1/admin/datasets", tags=["admin-datasets"])

UPLOAD_DIR = Path(__file__).resolve().parents[3] / "data" / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_EXTENSIONS = {".csv", ".xlsx", ".xls", ".json"}


@router.post("/upload", response_model=DatasetPreview, status_code=status.HTTP_201_CREATED)
def upload_dataset(
    insurance_type_code: str = Form(...),
    name: str = Form(...),
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

    existing_count = db.query(Dataset).filter(
        Dataset.insurance_type_id == insurance_type.id, Dataset.name == name
    ).count()

    dataset_id = uuid.uuid4()
    stored_path = UPLOAD_DIR / f"{dataset_id}{ext}"
    with stored_path.open("wb") as out:
        shutil.copyfileobj(file.file, out)

    dataset = Dataset(
        id=dataset_id,
        insurance_type_id=insurance_type.id,
        name=name,
        original_filename=file.filename,
        stored_path=str(stored_path),
        version=existing_count + 1,
    )
    db.add(dataset)
    db.commit()
    db.refresh(dataset)

    try:
        preview = build_preview(dataset)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=400, detail=f"Could not read uploaded file: {exc}")

    return DatasetPreview(**preview)


@router.get("", response_model=list[DatasetOut])
def list_datasets(
    db: Session = Depends(get_db),
    _admin: User = Depends(require_role(UserRole.admin)),
):
    return db.query(Dataset).order_by(Dataset.uploaded_at.desc()).all()


@router.get("/{dataset_id}", response_model=DatasetOut)
def get_dataset(
    dataset_id: uuid.UUID,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_role(UserRole.admin)),
):
    dataset = db.query(Dataset).get(dataset_id)
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    return dataset


@router.post("/{dataset_id}/process", response_model=DatasetOut)
def process_dataset_route(
    dataset_id: uuid.UUID,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_role(UserRole.admin)),
):
    dataset = db.query(Dataset).get(dataset_id)
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    return process_dataset(db, dataset)


@router.get("/{dataset_id}/records", response_model=list[DatasetRecordOut])
def get_dataset_records(
    dataset_id: uuid.UUID,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_role(UserRole.admin)),
):
    return (
        db.query(DatasetRecord)
        .filter(DatasetRecord.dataset_id == dataset_id)
        .order_by(DatasetRecord.row_index)
        .offset(offset)
        .limit(min(limit, 500))
        .all()
    )


@router.delete("/{dataset_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_dataset(
    dataset_id: uuid.UUID,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_role(UserRole.admin)),
):
    dataset = db.query(Dataset).get(dataset_id)
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    stored_path = Path(dataset.stored_path)
    db.delete(dataset)
    db.commit()
    if stored_path.exists():
        stored_path.unlink()
