"""
Canonical field aliases for the flexible dataset ingestion layer.

The product spec is explicit: never assume a dataset's column names.
"company", "insurer", "insurance_company" must all be recognized as
the same concept. This module is the single place that mapping lives,
so adding a new alias later doesn't touch ingestion logic anywhere.

Matching is case-insensitive and ignores separators (_, -, space), so
"Annual_Premium", "annual premium", and "AnnualPremium" all match the
same alias entry without listing every variant.
"""

import re

# canonical_field -> list of known aliases (aliases are normalized at match time)
FIELD_ALIASES: dict[str, list[str]] = {
    "insurer_name": [
        "company", "insurer", "insurance_company", "underwriter", "provider",
        "provider_name", "carrier",
    ],
    "policy_number": [
        "policy_number", "policy_no", "policy_id", "product_id", "policy_ref",
    ],
    "policy_name": [
        "policy_name", "product_name", "plan_name",
    ],
    "premium": [
        "premium", "annual_premium", "price", "premium_amount",
        "last_ann_prem_gross", "mta_fap",
    ],
    "sum_insured": [
        "sum_insured", "coverage_amount", "coverage", "sum_assured",
        "sum_insured_buildings", "sum_insured_contents", "spec_sum_insured",
    ],
    "deductible": [
        "deductible", "excess", "co_pay", "copay",
    ],
    "waiting_period": [
        "waiting_period", "waiting_period_days", "cooling_period",
    ],
    "policy_start_date": [
        "policy_start_date", "start_date", "cover_start", "quote_date",
    ],
    "policy_end_date": [
        "policy_end_date", "end_date", "expiry_date", "maturity_date",
    ],
    "customer_age": [
        "age", "customer_age", "p1_dob", "insured_age",
    ],
    "customer_gender": [
        "gender", "sex", "p1_sex",
    ],
    "region": [
        "region", "region_code", "state", "location", "risk_rated_area_b",
        "risk_rated_area_c",
    ],
    "vehicle_age": [
        "vehicle_age", "car_age",
    ],
    "vehicle_damage": [
        "vehicle_damage", "prior_damage",
    ],
    "prior_claims_flag": [
        "claim3years", "prior_claims", "had_previous_claim",
    ],
    "policy_status": [
        "status", "pol_status", "policy_status",
    ],
}


def _normalize(name: str) -> str:
    return re.sub(r"[^a-z0-9]", "", name.lower())


# Build a reverse lookup: normalized alias -> canonical field, once at import time.
_ALIAS_LOOKUP: dict[str, str] = {}
for canonical, aliases in FIELD_ALIASES.items():
    _ALIAS_LOOKUP[_normalize(canonical)] = canonical
    for alias in aliases:
        _ALIAS_LOOKUP[_normalize(alias)] = canonical


def map_columns(columns: list[str]) -> dict[str, str | None]:
    """
    Map each raw dataset column name to a canonical field name, or
    None if it doesn't match any known concept (it's still imported,
    just kept under its original name rather than merged).
    """
    return {col: _ALIAS_LOOKUP.get(_normalize(col)) for col in columns}
