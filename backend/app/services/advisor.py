"""
The AI Insurance Advisor. Per the product spec's "AI ANSWER GROUNDING"
rule: every number in a response must trace back to an actual
DatasetRecord or DocumentChunk retrieved this call. If nothing
relevant is found, the advisor says so explicitly rather than
inventing premiums, coverage, or policy terms.

Structured Dataset + RAG + Rules  ->  Recommendation
"""

from sqlalchemy.orm import Session

from app.config import settings
from app.models.dataset import Dataset, DatasetRecord, DatasetStatus
from app.models.document import DocumentChunk, DocumentStatus
from app.models.insurance_type import InsuranceType
from app.services.embeddings import embed_texts
from app.services.vector_store import VectorStore

NOT_ENOUGH_DATA_MESSAGE = (
    "I couldn't find enough information in the available insurance data to answer this accurately."
)

CANONICAL_FIELDS_OF_INTEREST = ["insurer_name", "policy_number", "policy_name", "premium", "sum_insured", "deductible"]


def _extract_canonical(record_data: dict, column_mapping: dict) -> dict:
    """Pull canonical fields (premium, sum_insured, ...) out of one raw record using its dataset's mapping."""
    canonical: dict = {}
    for raw_col, value in record_data.items():
        field = column_mapping.get(raw_col)
        if field in CANONICAL_FIELDS_OF_INTEREST and value is not None and field not in canonical:
            canonical[field] = value
    return canonical


def _find_structured_candidates(db: Session, insurance_type: InsuranceType, budget_inr: float | None, limit: int = 200) -> list[dict]:
    datasets = (
        db.query(Dataset)
        .filter(Dataset.insurance_type_id == insurance_type.id, Dataset.status == DatasetStatus.processed)
        .all()
    )
    candidates = []
    for dataset in datasets:
        mapping = dataset.column_mapping or {}
        records = (
            db.query(DatasetRecord)
            .filter(DatasetRecord.dataset_id == dataset.id)
            .limit(limit)
            .all()
        )
        for record in records:
            canonical = _extract_canonical(record.data, mapping)
            premium = canonical.get("premium")
            if premium is None:
                continue
            try:
                premium_value = float(premium)
            except (TypeError, ValueError):
                continue
            if budget_inr is not None and premium_value > budget_inr:
                continue
            canonical["premium"] = premium_value
            canonical["_dataset_name"] = dataset.name
            candidates.append(canonical)
    return candidates


def _rank_candidates(candidates: list[dict], top_n: int = 3) -> list[dict]:
    def sort_key(c):
        sum_insured = c.get("sum_insured")
        try:
            sum_insured = float(sum_insured) if sum_insured is not None else 0.0
        except (TypeError, ValueError):
            sum_insured = 0.0
        return (-sum_insured, c["premium"])

    return sorted(candidates, key=sort_key)[:top_n]


def _retrieve_chunks(db: Session, insurance_type: InsuranceType, query: str, top_k: int = 5) -> list[dict]:
    store = VectorStore(insurance_type.code)
    if store._index.ntotal == 0:
        return []
    query_vector = embed_texts([query])[0]
    hits = store.search(query_vector, top_k=top_k)
    results = []
    for chunk_id, score in hits:
        chunk = db.query(DocumentChunk).get(chunk_id)
        if chunk and chunk.document.status == DocumentStatus.indexed:
            results.append({"text": chunk.text, "score": score, "document_title": chunk.document.title})
    return results


def _compose_demo_answer(query: str, candidates: list[dict], chunks: list[dict]) -> str:
    """DEMO_MODE fallback: template the retrieved data into prose, no LLM call, no invented numbers."""
    lines = []
    if candidates:
        lines.append("Based on the policies in your uploaded datasets, here are the closest matches:")
        for i, c in enumerate(candidates, start=1):
            parts = [f"₹{c['premium']:,.0f} premium"]
            if c.get("sum_insured"):
                parts.append(f"₹{float(c['sum_insured']):,.0f} sum insured")
            if c.get("insurer_name"):
                parts.append(f"from {c['insurer_name']}")
            if c.get("policy_name"):
                parts.append(f"({c['policy_name']})")
            lines.append(f"{i}. " + ", ".join(parts) + f" — source: {c['_dataset_name']}")
    if chunks:
        lines.append("\nRelevant policy document excerpts:")
        for c in chunks:
            excerpt = c["text"][:280] + ("..." if len(c["text"]) > 280 else "")
            lines.append(f"- From \"{c['document_title']}\": {excerpt}")
    return "\n".join(lines)


def _compose_llm_answer(query: str, candidates: list[dict], chunks: list[dict]) -> str:
    from openai import OpenAI

    client = OpenAI(api_key=settings.OPENAI_API_KEY)
    context_parts = []
    if candidates:
        context_parts.append("Structured policy records:\n" + "\n".join(str(c) for c in candidates))
    if chunks:
        context_parts.append(
            "Policy document excerpts:\n" + "\n".join(f'[{c["document_title"]}] {c["text"]}' for c in chunks)
        )
    context = "\n\n".join(context_parts)

    system_prompt = (
        "You are OmniSure's insurance advisor. Answer ONLY using the provided context. "
        "Never invent premiums, coverage amounts, waiting periods, or exclusions that aren't "
        f'in the context. If the context is insufficient, reply exactly: "{NOT_ENOUGH_DATA_MESSAGE}"'
    )
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Context:\n{context}\n\nCustomer question: {query}"},
        ],
        temperature=0.2,
    )
    return response.choices[0].message.content


def get_recommendation(db: Session, insurance_type_code: str, query: str, budget_inr: float | None = None) -> dict:
    insurance_type = db.query(InsuranceType).filter(InsuranceType.code == insurance_type_code).first()
    if not insurance_type:
        return {"answer": NOT_ENOUGH_DATA_MESSAGE, "candidates": [], "sources": [], "demo_mode": True}

    raw_candidates = _find_structured_candidates(db, insurance_type, budget_inr)
    ranked = _rank_candidates(raw_candidates)
    chunks = _retrieve_chunks(db, insurance_type, query)

    if not ranked and not chunks:
        return {"answer": NOT_ENOUGH_DATA_MESSAGE, "candidates": [], "sources": [], "demo_mode": not settings.OPENAI_API_KEY}

    if settings.OPENAI_API_KEY:
        answer = _compose_llm_answer(query, ranked, chunks)
    else:
        answer = _compose_demo_answer(query, ranked, chunks)

    return {
        "answer": answer,
        "candidates": [{k: v for k, v in c.items() if k != "_dataset_name"} for c in ranked],
        "sources": [c["document_title"] for c in chunks],
        "demo_mode": not settings.OPENAI_API_KEY,
    }
