"""
AI action execution: takes the intent detected from free text and
resolves it against the customer's *actual* policies in the database
— never guesses a policy that doesn't exist, always asks for
clarification when the request is ambiguous (multiple matching
policies) or unresolvable (no matching policy at all).
"""

from sqlalchemy.orm import Session

from app.models.policy import Policy, PolicyStatus
from app.services.intent_detection import detect_intent


def _matching_policies(db: Session, customer_id, insurance_type_code: str | None) -> list[Policy]:
    query = db.query(Policy).filter(Policy.customer_id == customer_id, Policy.status == PolicyStatus.active)
    if insurance_type_code:
        from app.models.insurance_type import InsuranceType

        insurance_type = db.query(InsuranceType).filter(InsuranceType.code == insurance_type_code).first()
        if not insurance_type:
            # Detected a type code that doesn't exist in the catalog — there can be
            # no matching policy, so return nothing rather than silently skipping
            # the filter and matching every policy the customer owns.
            return []
        query = query.filter(Policy.insurance_type_id == insurance_type.id)
    return query.all()


def interpret_request(db: Session, customer_id, text: str) -> dict:
    detection = detect_intent(text)
    intent = detection["intent"]
    insurance_type_code = detection.get("insurance_type_code")

    if intent in ("file_claim", "explain_policy"):
        policies = _matching_policies(db, customer_id, insurance_type_code)

        if len(policies) == 1:
            policy = policies[0]
            action = "start_claim" if intent == "file_claim" else "explain_policy"
            verb = "Starting a claim for" if intent == "file_claim" else "Here's an explanation of"
            return {
                "intent": intent,
                "action": action,
                "policy_id": str(policy.id),
                "insurance_type_code": policy.insurance_type.code,
                "spoken_response": f"{verb} your {policy.insurance_type.name} policy, {policy.policy_number}.",
                "demo_mode": detection["demo_mode"],
            }

        if len(policies) > 1:
            options = ", ".join(p.policy_number for p in policies)
            return {
                "intent": intent,
                "action": "clarify",
                "policy_id": None,
                "insurance_type_code": insurance_type_code,
                "spoken_response": f"You have more than one matching policy: {options}. Please open one from your dashboard.",
                "demo_mode": detection["demo_mode"],
            }

        if insurance_type_code:
            return {
                "intent": intent,
                "action": "clarify",
                "policy_id": None,
                "insurance_type_code": insurance_type_code,
                "spoken_response": f"I couldn't find an active {insurance_type_code} policy on your account. "
                "Would you like a recommendation instead?",
                "demo_mode": detection["demo_mode"],
            }

        return {
            "intent": intent,
            "action": "clarify",
            "policy_id": None,
            "insurance_type_code": None,
            "spoken_response": "Which policy is this about?",
            "demo_mode": detection["demo_mode"],
        }

    if intent == "track_claims":
        return {
            "intent": intent,
            "action": "view_claims",
            "policy_id": None,
            "insurance_type_code": None,
            "spoken_response": "Here are your claims.",
            "demo_mode": detection["demo_mode"],
        }

    if intent == "get_recommendation":
        return {
            "intent": intent,
            "action": "open_advisor",
            "policy_id": None,
            "insurance_type_code": insurance_type_code,
            "spoken_response": "Opening the AI advisor" + (f" for {insurance_type_code} insurance." if insurance_type_code else "."),
            "demo_mode": detection["demo_mode"],
        }

    return {
        "intent": "general_help",
        "action": "none",
        "policy_id": None,
        "insurance_type_code": None,
        "spoken_response": (
            "I can help you file a claim, track an existing claim, get a policy recommendation, "
            "or explain a policy you already have. What would you like to do?"
        ),
        "demo_mode": detection["demo_mode"],
    }
