import json
import math

import pandas as pd
from sqlalchemy.orm import Session

from app.models.dataset import Dataset, DatasetRecord, DatasetStatus
from app.services.data_quality import analyze_quality, clean_dataframe
from app.services.field_mapping import map_columns


def read_dataset_file(path: str) -> pd.DataFrame:
    if path.endswith(".csv"):
        return pd.read_csv(path, low_memory=False)
    if path.endswith((".xlsx", ".xls")):
        return pd.read_excel(path)
    if path.endswith(".json"):
        return pd.read_json(path)
    raise ValueError(f"Unsupported dataset file type: {path}")


def build_preview(dataset: Dataset) -> dict:
    """Read-only inspection used right after upload, before anything is imported."""
    df = read_dataset_file(dataset.stored_path)
    mapping = map_columns(list(df.columns))
    quality = analyze_quality(df)
    sample_rows = json.loads(df.head(5).to_json(orient="records"))
    return {
        "columns": list(df.columns),
        "column_mapping": mapping,
        "quality_report": quality,
        "sample_rows": sample_rows,
    }


def _json_safe(value):
    """NaN/NaT don't round-trip through JSONB; normalize them to None."""
    if value is None:
        return None
    if isinstance(value, float) and math.isnan(value):
        return None
    return value


def process_dataset(db: Session, dataset: Dataset) -> Dataset:
    """
    Validate -> clean -> normalize -> import. Mirrors the pipeline in
    the product spec. Never raises past this function without setting
    status=error and error_message, so the admin panel always has a
    clear status to show rather than a silent failure.
    """
    dataset.status = DatasetStatus.validating
    db.commit()

    try:
        df = read_dataset_file(dataset.stored_path)
        mapping = map_columns(list(df.columns))
        quality = analyze_quality(df)
        cleaned = clean_dataframe(df)

        dataset.column_mapping = mapping
        dataset.quality_report = quality
        dataset.status = DatasetStatus.processing
        db.commit()

        # Clear any previous import of this dataset (re-processing a new version).
        db.query(DatasetRecord).filter(DatasetRecord.dataset_id == dataset.id).delete()

        records = cleaned.to_dict(orient="records")
        for i, row in enumerate(records):
            safe_row = {k: _json_safe(v) for k, v in row.items()}
            db.add(DatasetRecord(dataset_id=dataset.id, row_index=i, data=safe_row))

        dataset.record_count = len(records)
        dataset.status = DatasetStatus.processed
        from datetime import datetime

        dataset.processed_at = datetime.utcnow()
        db.commit()

    except Exception as exc:  # noqa: BLE001 - report to admin panel, don't hide it
        db.rollback()
        dataset.status = DatasetStatus.error
        dataset.error_message = str(exc)
        db.commit()

    return dataset
