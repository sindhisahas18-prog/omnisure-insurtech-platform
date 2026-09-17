"""
Rule-based fraud/risk scoring (per the spec: "Structured Database +
RAG + AI + Rules Engine", not a black-box model guess). Every point
added to the score comes with a plain-language reason so the human
reviewer (or the customer, indirectly) can see exactly why a claim
was flagged.
"""

from datetime import date


def score_claim(
    claimed_amount_inr: int | None,
    sum_insured_inr: int | None,
    incident_date: date | None,
    policy_start_date: date | None,
    missing_document_count: int,
    recent_claim_count: int,
) -> dict:
    """Returns {"score": int 0-100, "reasons": list[str]}."""
    score = 0
    reasons = []

    if claimed_amount_inr is not None and sum_insured_inr:
        ratio = claimed_amount_inr / sum_insured_inr
        if ratio >= 0.9:
            score += 25
            reasons.append(f"Claimed amount is {ratio:.0%} of the sum insured — near the policy limit.")
        elif ratio >= 0.7:
            score += 10
            reasons.append(f"Claimed amount is {ratio:.0%} of the sum insured.")

    if incident_date and policy_start_date:
        days_since_start = (incident_date - policy_start_date).days
        if 0 <= days_since_start <= 15:
            score += 25
            reasons.append(f"Incident occurred only {days_since_start} day(s) after the policy started.")

    if missing_document_count > 0:
        points = min(15 * missing_document_count, 30)
        score += points
        reasons.append(f"{missing_document_count} required document(s) missing.")

    if recent_claim_count >= 2:
        score += 20
        reasons.append(f"{recent_claim_count} other claim(s) filed by this customer in the last 90 days.")

    return {"score": min(score, 100), "reasons": reasons}
