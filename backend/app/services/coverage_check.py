"""
Coverage verification. Deliberately simple, explicit rules — this is
exactly the kind of decision the spec says must be a rules engine,
not an LLM guess. Every check is traceable to a real field on the
policy/claim.
"""

from datetime import date


def verify_coverage(policy, claim_insurance_type_id, incident_date: date | None) -> dict:
    """
    Returns {"verified": "yes"|"no"|"uncertain", "notes": str, "confidence": int 0-100}.
    """
    if policy is None:
        return {"verified": "no", "notes": "No matching policy found for this customer.", "confidence": 100}

    if str(policy.insurance_type_id) != str(claim_insurance_type_id):
        return {
            "verified": "no",
            "notes": "The claim's insurance type does not match the selected policy's insurance type.",
            "confidence": 100,
        }

    from app.models.policy import PolicyStatus

    if policy.status != PolicyStatus.active:
        return {
            "verified": "no",
            "notes": f"Policy status is '{policy.status.value}', not active.",
            "confidence": 100,
        }

    if incident_date is None:
        return {
            "verified": "uncertain",
            "notes": "No incident date provided — cannot confirm the incident falls within the policy period.",
            "confidence": 40,
        }

    if not (policy.start_date <= incident_date <= policy.end_date):
        return {
            "verified": "no",
            "notes": f"Incident date {incident_date} falls outside the policy period "
            f"({policy.start_date} to {policy.end_date}).",
            "confidence": 100,
        }

    days_to_expiry = (policy.end_date - incident_date).days
    if days_to_expiry <= 3:
        return {
            "verified": "yes",
            "notes": "Incident is within the policy period, but very close to expiry — flagged for review.",
            "confidence": 65,
        }

    return {"verified": "yes", "notes": "Incident date falls within an active policy period.", "confidence": 95}
