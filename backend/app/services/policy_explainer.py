"""
AI policy explanation. Grounded the same way the advisor is: the
policy's own database fields plus whatever's actually retrievable
from that insurance type's indexed policy documents — never
invented coverage/exclusion details.
"""

from sqlalchemy.orm import Session

from app.config import settings
from app.models.policy import Policy
from app.services.advisor import _compose_demo_answer, _compose_llm_answer, _retrieve_chunks


def explain_policy(db: Session, policy: Policy) -> dict:
    query = f"Explain the coverage, exclusions, and key terms of this {policy.insurance_type.name} policy."
    chunks = _retrieve_chunks(db, policy.insurance_type, query, top_k=5)

    policy_facts = [
        {
            "policy_number": policy.policy_number,
            "insurer_name": policy.provider_name,
            "premium": policy.premium_inr,
            "sum_insured": policy.sum_insured_inr,
            "_dataset_name": "your policy record",
        }
    ]

    if not chunks:
        base = (
            f"Your policy {policy.policy_number} with {policy.provider_name} has a premium of "
            f"₹{policy.premium_inr:,} and sum insured of ₹{policy.sum_insured_inr:,}"
            if policy.sum_insured_inr
            else f"Your policy {policy.policy_number} with {policy.provider_name} has a premium of ₹{policy.premium_inr:,}"
        )
        return {
            "answer": base
            + ". No policy wording document has been indexed for this insurance type yet, so I can't "
            "detail specific coverage, exclusions, or waiting periods — ask your admin to upload the "
            "policy document for a fuller explanation.",
            "sources": [],
            "demo_mode": True,
        }

    if settings.OPENAI_API_KEY:
        answer = _compose_llm_answer(query, policy_facts, chunks)
    else:
        answer = _compose_demo_answer(query, policy_facts, chunks)

    return {
        "answer": answer,
        "sources": [c["document_title"] for c in chunks],
        "demo_mode": not settings.OPENAI_API_KEY,
    }
