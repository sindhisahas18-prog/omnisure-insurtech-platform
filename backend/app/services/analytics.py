"""
Admin analytics: every number and chart series here is a live query
against the database. Grouping/aggregation is done in Python rather
than with Postgres-only SQL (e.g. to_char) so this stays portable and
testable against SQLite in development, at the scale an admin
dashboard actually needs.
"""

from collections import Counter, defaultdict

from sqlalchemy.orm import Session

from app.models.claim import Claim, ClaimEvent, ClaimStatus
from app.models.insurance_type import InsuranceType
from app.models.policy import Policy, PolicyStatus
from app.models.user import User, UserRole


def get_kpis(db: Session) -> dict:
    total_customers = db.query(User).filter(User.role == UserRole.customer).count()
    total_employees = db.query(User).filter(User.role == UserRole.employee).count()
    active_policies = db.query(Policy).filter(Policy.status == PolicyStatus.active).count()

    claims = db.query(Claim).all()
    total_claims = len(claims)
    settled_claims = sum(1 for c in claims if c.status == ClaimStatus.settled)
    pending_claims = sum(
        1 for c in claims if c.status in (ClaimStatus.submitted, ClaimStatus.in_triage, ClaimStatus.human_review)
    )

    triage_events = db.query(ClaimEvent).filter(ClaimEvent.event_type == "triage_decision").all()
    stp_count = sum(1 for e in triage_events if e.status == "stp")
    manual_count = sum(1 for e in triage_events if e.status == "human_review")
    triaged_total = stp_count + manual_count
    stp_rate = round(100 * stp_count / triaged_total, 1) if triaged_total else 0.0
    manual_review_rate = round(100 * manual_count / triaged_total, 1) if triaged_total else 0.0

    settled_amounts = [c.approved_amount_inr for c in claims if c.approved_amount_inr is not None]
    average_claim_amount = round(sum(settled_amounts) / len(settled_amounts)) if settled_amounts else 0

    fraud_risk_claims = sum(1 for c in claims if c.fraud_risk_score is not None and c.fraud_risk_score >= 50)

    return {
        "total_customers": total_customers,
        "total_employees": total_employees,
        "active_policies": active_policies,
        "total_claims": total_claims,
        "settled_claims": settled_claims,
        "pending_claims": pending_claims,
        "stp_rate": stp_rate,
        "manual_review_rate": manual_review_rate,
        "average_claim_amount_inr": average_claim_amount,
        "fraud_risk_claims": fraud_risk_claims,
    }


def get_charts(db: Session) -> dict:
    claims = db.query(Claim).all()
    insurance_types = {t.id: t.name for t in db.query(InsuranceType).all()}

    # Claims by insurance type
    by_type = Counter(insurance_types.get(c.insurance_type_id, "Unknown") for c in claims)
    claims_by_insurance_type = [{"label": k, "value": v} for k, v in sorted(by_type.items(), key=lambda x: -x[1])]

    # Claims by status
    by_status = Counter(c.status.value for c in claims)
    claims_by_status = [{"label": k, "value": v} for k, v in by_status.items()]

    # Settlement amount by month (settled claims only)
    settlement_by_month: dict[str, int] = defaultdict(int)
    for c in claims:
        if c.status == ClaimStatus.settled and c.settled_at and c.approved_amount_inr:
            key = c.settled_at.strftime("%Y-%m")
            settlement_by_month[key] += c.approved_amount_inr
    settlement_amount_by_month = [{"label": k, "value": v} for k, v in sorted(settlement_by_month.items())]

    # STP vs manual review (from triage_decision events, not just current status,
    # since a human-reviewed claim can also end up "settled")
    triage_events = db.query(ClaimEvent).filter(ClaimEvent.event_type == "triage_decision").all()
    stp_vs_manual = [
        {"label": "STP", "value": sum(1 for e in triage_events if e.status == "stp")},
        {"label": "Manual Review", "value": sum(1 for e in triage_events if e.status == "human_review")},
    ]

    # Fraud/risk score distribution
    buckets = {"Low (0-29)": 0, "Medium (30-59)": 0, "High (60-100)": 0}
    for c in claims:
        if c.fraud_risk_score is None:
            continue
        if c.fraud_risk_score < 30:
            buckets["Low (0-29)"] += 1
        elif c.fraud_risk_score < 60:
            buckets["Medium (30-59)"] += 1
        else:
            buckets["High (60-100)"] += 1
    fraud_risk_distribution = [{"label": k, "value": v} for k, v in buckets.items()]

    # Monthly claim volume
    monthly: dict[str, int] = defaultdict(int)
    for c in claims:
        monthly[c.created_at.strftime("%Y-%m")] += 1
    monthly_claims = [{"label": k, "value": v} for k, v in sorted(monthly.items())]

    # Premium revenue by insurance type (active policies)
    active_policies = db.query(Policy).filter(Policy.status == PolicyStatus.active).all()
    revenue_by_type: dict[str, int] = defaultdict(int)
    for p in active_policies:
        revenue_by_type[insurance_types.get(p.insurance_type_id, "Unknown")] += p.premium_inr
    premium_revenue_by_type = [
        {"label": k, "value": v} for k, v in sorted(revenue_by_type.items(), key=lambda x: -x[1])
    ]

    return {
        "claims_by_insurance_type": claims_by_insurance_type,
        "claims_by_status": claims_by_status,
        "settlement_amount_by_month": settlement_amount_by_month,
        "stp_vs_manual": stp_vs_manual,
        "fraud_risk_distribution": fraud_risk_distribution,
        "monthly_claims": monthly_claims,
        "premium_revenue_by_type": premium_revenue_by_type,
    }
