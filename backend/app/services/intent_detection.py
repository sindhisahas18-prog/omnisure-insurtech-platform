"""
AI intent detection for the voice/text assistant. The product spec's
own example is code-mixed Hindi-English ("Merki car ka accident ho
gaya hai aur mujhe claim file karna hai"), so the DEMO_MODE fallback
is a genuine keyword-based classifier over English *and* common
Hinglish claim vocabulary — not a toy that only understands English.
When OPENAI_API_KEY is configured, a real LLM call replaces it for
much broader language/phrasing coverage.
"""

import json

from app.config import settings

INTENTS = ["file_claim", "track_claims", "get_recommendation", "explain_policy", "general_help"]

# Order matters: on a tied score, _rule_based_detect keeps the first
# max() hit, so more specific intents (status/recommendation/explain
# checks) are listed before the catch-all file_claim — otherwise a
# generic word like "claim" in "what's the status of my claim" would
# always win against the more specific "status" signal.
INTENT_KEYWORDS: dict[str, list[str]] = {
    "track_claims": [
        "status", "track", "update on my claim", "claim status", "kaha hai", "kab tak",
        "when will my claim", "my claims", "progress on my claim",
    ],
    "get_recommendation": [
        "recommend", "suggest", "best policy", "which policy", "compare", "advice",
        "insurance chahiye", "policy chahiye", "new policy", "buy a policy", "naya policy",
    ],
    "explain_policy": [
        "explain", "what does my policy cover", "policy details", "samjhao",
        "what is covered", "kya cover hai", "coverage details",
    ],
    "file_claim": [
        "file a claim", "file claim", "make a claim", "claim karna", "claim file", "new claim",
        "raise a claim", "claim", "accident", "damage", "damaged", "broke", "broken", "crashed",
        "crash", "stolen", "theft", "chori", "nuksan", "dava", "ho gaya", "toot gaya", "chori ho gayi",
    ],
}

INSURANCE_TYPE_KEYWORDS: dict[str, list[str]] = {
    "car": ["car", "gaadi", "gadi", "vehicle"],
    "bike": ["bike", "motorcycle", "scooter", "scooty"],
    "health": ["health", "medical", "hospital", "ilaj", "bimari"],
    "mobile": ["mobile", "phone", "fon", "smartphone"],
    "laptop": ["laptop", "computer", "notebook"],
    "electronics": ["electronics", "tv", "gadget", "appliance"],
    "home": ["home", "house", "ghar", "property"],
    "travel": ["travel", "flight", "trip", "baggage", "vacation"],
    "crop": ["crop", "fasal", "farm", "kheti"],
    "business": ["business", "shop", "dukaan", "office"],
    "life": ["life insurance", "life policy"],
    "livestock": ["cattle", "animal", "cow", "pashu", "livestock", "buffalo"],
}


def _keyword_score(text: str, keywords: list[str]) -> int:
    text_lower = text.lower()
    return sum(1 for kw in keywords if kw in text_lower)


def _rule_based_detect(text: str) -> dict:
    intent_scores = {intent: _keyword_score(text, kws) for intent, kws in INTENT_KEYWORDS.items()}
    best_intent = max(intent_scores, key=intent_scores.get)
    if intent_scores[best_intent] == 0:
        best_intent = "general_help"

    type_scores = {t: _keyword_score(text, kws) for t, kws in INSURANCE_TYPE_KEYWORDS.items()}
    best_type = max(type_scores, key=type_scores.get)
    insurance_type_code = best_type if type_scores[best_type] > 0 else None

    return {
        "intent": best_intent,
        "insurance_type_code": insurance_type_code,
        "damaged_component": None,
        "demo_mode": True,
    }


def _llm_detect(text: str) -> dict | None:
    try:
        from openai import OpenAI

        client = OpenAI(api_key=settings.OPENAI_API_KEY)
        system_prompt = (
            "Classify the user's insurance-assistant request. The user may write in English, "
            "Hindi, or a Hindi-English mix (Hinglish). Respond with strict JSON only: "
            '{"intent": one of ' + json.dumps(INTENTS) + ', '
            '"insurance_type_code": one of ' + json.dumps(list(INSURANCE_TYPE_KEYWORDS.keys()) + [None]) + ' or null, '
            '"damaged_component": a short string naming what was damaged/affected, or null}'
        )
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": text}],
            temperature=0,
            response_format={"type": "json_object"},
        )
        result = json.loads(response.choices[0].message.content)
        result["demo_mode"] = False
        return result
    except Exception:  # noqa: BLE001
        return None


def detect_intent(text: str) -> dict:
    if settings.OPENAI_API_KEY and not settings.DEMO_MODE:
        result = _llm_detect(text)
        if result is not None:
            return result
    return _rule_based_detect(text)
