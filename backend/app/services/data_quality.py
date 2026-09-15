"""
Data-quality checks run on every dataset before import. Nothing here
silently drops or corrupts data — every issue is reported so the
admin can see it before the data is imported.
"""

import pandas as pd


def analyze_quality(df: pd.DataFrame) -> dict:
    total_rows = len(df)

    missing_by_column = {
        col: int(df[col].isna().sum()) for col in df.columns if df[col].isna().sum() > 0
    }

    duplicate_rows = int(df.duplicated().sum())

    # Columns that look numeric-ish by name/content but contain non-numeric junk
    invalid_numeric: dict[str, int] = {}
    for col in df.columns:
        if df[col].dtype == object:
            sample = df[col].dropna().astype(str).head(200)
            looks_numeric = sample.str.match(r"^-?\d+(\.\d+)?$").mean() if len(sample) else 0
            if looks_numeric > 0.7:
                coerced = pd.to_numeric(df[col], errors="coerce")
                bad = int((coerced.isna() & df[col].notna()).sum())
                if bad > 0:
                    invalid_numeric[col] = bad

    return {
        "total_rows": total_rows,
        "total_columns": len(df.columns),
        "missing_values_by_column": missing_by_column,
        "duplicate_rows": duplicate_rows,
        "invalid_numeric_by_column": invalid_numeric,
    }


def clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Conservative cleaning only: drop exact duplicate rows and strip
    whitespace from string columns. Does NOT impute, drop columns, or
    guess at missing values — that's a business decision the admin
    should make explicitly, not something the pipeline does silently.
    """
    cleaned = df.drop_duplicates().copy()
    for col in cleaned.columns:
        if cleaned[col].dtype == object:
            cleaned[col] = cleaned[col].astype(str).str.strip().replace({"nan": None, "": None})
    return cleaned
