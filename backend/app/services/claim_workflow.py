"""
Orchestrates one claim through: coverage check -> fraud/risk scoring
-> STP-vs-human-review routing -> (STP path) assessment -> settlement
-> payment -> email, logging a ClaimEvent at every step so the
customer's claim-tracking timeline is a real audit trail, not a
progress bar.

STP routing triggers, straight from the product spec:
high fraud risk, high claim amount, missing documents, low AI
confidence, coverage uncertainty/policy ambiguity, no claimed amount.
Any one of these sends the claim to human review instead of STP.
"""

from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.models.claim import Claim, ClaimEvent, ClaimStatus, Payment, PaymentStatus
from app.models.claim_config import ClaimConfig
from app.services.coverage_check import verify_coverage
from app.services.email import send_email
from app.services.fraud_risk import score_claim

FRAUD_SCORE_THRESHOLD = 50
CLAIM_TO_SUM_INSURED_THRESHOLD = 0.7
AI_CONFIDENCE_THRESHOLD = 60


def _log_event(db: Session, claim: Claim, event_type: str, status: str, detail: dict | None = None):
    db.add(ClaimEvent(claim_id=claim.id, event_type=event_type, status=status, detail=detail or {}))


def _decide_routing(
    coverage: dict,
    fraud: dict,
    missing_documents: list[str],
    ai_confidence: int | None,
    claimed_amount_inr: int | None,
    sum_insured_inr: int | None,
) -> tuple[str, list[str]]:
    reasons = []

    if claimed_amount_inr is None:
        reasons.append("No claimed amount was provided.")
    if fraud["score"] >= FRAUD_SCORE_THRESHOLD:
        reasons.append(f"High fraud/risk score ({fraud['score']}/100).")
    if sum_insured_inr and claimed_amount_inr and claimed_amount_inr / sum_insured_inr >= CLAIM_TO_SUM_INSURED_THRESHOLD:
        reasons.append("Claimed amount is high relative to the sum insured.")
    if missing_documents:
        reasons.append(f"Missing required document(s): {', '.join(missing_documents)}.")
    if coverage["verified"] != "yes":
        reasons.append(f"Coverage uncertainty: {coverage['notes']}")
    if ai_confidence is not None and ai_confidence < AI_CONFIDENCE_THRESHOLD:
        reasons.append(f"Low AI confidence in damage analysis ({ai_confidence}/100).")

    return ("human_review", reasons) if reasons else ("stp", [])


def _calculate_settlement(claim: Claim, policy) -> int:
    approved = claim.claimed_amount_inr or 0
    if policy.sum_insured_inr:
        approved = min(approved, policy.sum_insured_inr)
    return approved


def run_triage(db: Session, claim: Claim) -> Claim:
    policy = claim.policy
    config = db.query(ClaimConfig).filter(ClaimConfig.insurance_type_id == claim.insurance_type_id).first()

    coverage = verify_coverage(policy, claim.insurance_type_id, claim.incident_date)
    claim.coverage_verified = coverage["verified"]
    claim.coverage_notes = coverage["notes"]
    _log_event(db, claim, "coverage_check", coverage["verified"], coverage)

    required_docs = set(config.required_documents) if config else set()
    uploaded_doc_types = {d.doc_type for d in claim.documents}
    missing_documents = sorted(required_docs - uploaded_doc_types)

    ninety_days_ago = datetime.utcnow() - timedelta(days=90)
    recent_claim_count = (
        db.query(Claim)
        .filter(
            Claim.customer_id == claim.customer_id,
            Claim.id != claim.id,
            Claim.status != ClaimStatus.rejected,
            Claim.created_at >= ninety_days_ago,
        )
        .count()
    )

    fraud = score_claim(
        claimed_amount_inr=claim.claimed_amount_inr,
        sum_insured_inr=policy.sum_insured_inr,
        incident_date=claim.incident_date,
        policy_start_date=policy.start_date,
        missing_document_count=len(missing_documents),
        recent_claim_count=recent_claim_count,
    )
    claim.fraud_risk_score = fraud["score"]
    claim.fraud_risk_reasons = fraud["reasons"]
    _log_event(db, claim, "fraud_check", str(fraud["score"]), fraud)

    confidences = [
        d.ai_damage_analysis.get("confidence")
        for d in claim.documents
        if d.ai_damage_analysis and isinstance(d.ai_damage_analysis.get("confidence"), (int, float))
    ]
    ai_confidence = int(sum(confidences) / len(confidences)) if confidences else None
    claim.ai_confidence = ai_confidence

    routed_to, review_reasons = _decide_routing(
        coverage, fraud, missing_documents, ai_confidence, claim.claimed_amount_inr, policy.sum_insured_inr
    )
    _log_event(db, claim, "triage_decision", routed_to, {"reasons": review_reasons, "missing_documents": missing_documents})

    if routed_to == "stp":
        approved = _calculate_settlement(claim, policy)
        claim.approved_amount_inr = approved
        claim.status = ClaimStatus.settled
        claim.settled_at = datetime.utcnow()
        _log_event(db, claim, "assessment", "approved", {"approved_amount_inr": approved})
        _log_event(db, claim, "settlement", "settled", {"approved_amount_inr": approved})

        payment = Payment(
            claim_id=claim.id,
            amount_inr=approved,
            status=PaymentStatus.paid,
            reference=f"PAY-{claim.claim_number}",
            paid_at=datetime.utcnow(),
        )
        db.add(payment)
        _log_event(db, claim, "payment", "paid", {"amount_inr": approved})

        email_result = send_email(
            claim.customer.email,
            f"Your claim {claim.claim_number} has been settled",
            f"Good news \u2014 your claim {claim.claim_number} was auto-approved and settled for "
            f"\u20b9{approved:,}. Funds have been recorded against your account.",
        )
        _log_event(db, claim, "email_sent", "sent" if email_result["sent"] else "demo_mode", email_result)
    else:
        claim.status = ClaimStatus.human_review
        claim.human_review_reasons = review_reasons
        _log_event(db, claim, "human_review", "pending", {"reasons": review_reasons})

        email_result = send_email(
            claim.customer.email,
            f"Your claim {claim.claim_number} is under review",
            f"Your claim {claim.claim_number} needs a closer look from our team before it can be "
            "settled. We'll update you as soon as a decision is made.",
        )
        _log_event(db, claim, "email_sent", "sent" if email_result["sent"] else "demo_mode", email_result)

    db.commit()
    db.refresh(claim)
    return claim


def resolve_human_review(db: Session, claim: Claim, approve: bool, approved_amount_inr: int | None, note: str) -> Claim:
    """Admin/employee decision on a claim routed to human review."""
    if approve:
        approved = approved_amount_inr if approved_amount_inr is not None else _calculate_settlement(claim, claim.policy)
        claim.approved_amount_inr = approved
        claim.status = ClaimStatus.settled
        claim.settled_at = datetime.utcnow()
        _log_event(db, claim, "assessment", "approved", {"approved_amount_inr": approved, "note": note})
        _log_event(db, claim, "settlement", "settled", {"approved_amount_inr": approved})

        payment = Payment(
            claim_id=claim.id, amount_inr=approved, status=PaymentStatus.paid,
            reference=f"PAY-{claim.claim_number}", paid_at=datetime.utcnow(),
        )
        db.add(payment)
        _log_event(db, claim, "payment", "paid", {"amount_inr": approved})

        email_result = send_email(
            claim.customer.email,
            f"Your claim {claim.claim_number} has been approved",
            f"Your claim {claim.claim_number} was reviewed and approved for \u20b9{approved:,}. {note}".strip(),
        )
    else:
        claim.status = ClaimStatus.rejected
        _log_event(db, claim, "rejected", "rejected", {"note": note})
        email_result = send_email(
            claim.customer.email,
            f"Update on your claim {claim.claim_number}",
            f"After review, your claim {claim.claim_number} was not approved. Reason: {note}",
        )

    _log_event(db, claim, "email_sent", "sent" if email_result["sent"] else "demo_mode", email_result)
    db.commit()
    db.refresh(claim)
    return claim
