"""
AI visual damage analysis for uploaded claim photos.

Per the "never pretend a demo result is real" rule: without a
configured vision-capable LLM key, this does NOT guess a severity or
description from the image — it honestly reports that no automated
assessment was performed, with a low confidence score that pushes
the claim toward human review (see fraud_risk / triage_decision).
"""

import base64
from pathlib import Path

from app.config import settings

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}


def _demo_result() -> dict:
    return {
        "severity": "not_assessed",
        "confidence": 35,
        "description": (
            "Automated visual damage analysis requires OPENAI_API_KEY to be configured. "
            "This document was received and stored but not automatically assessed — "
            "flagged for human review."
        ),
        "demo_mode": True,
    }


def _openai_vision_result(image_path: str, insurance_type_name: str, damaged_component: str | None) -> dict | None:
    try:
        from openai import OpenAI

        client = OpenAI(api_key=settings.OPENAI_API_KEY)
        image_b64 = base64.b64encode(Path(image_path).read_bytes()).decode("utf-8")
        ext = Path(image_path).suffix.lstrip(".").lower()

        component_note = f" The customer reported damage to the {damaged_component}." if damaged_component else ""
        prompt = (
            f"You are assessing a {insurance_type_name} insurance claim photo.{component_note} "
            "Look ONLY at what is visible in the image. Respond with strict JSON: "
            '{"severity": "minor"|"moderate"|"severe"|"unclear", "confidence": 0-100, '
            '"description": "1-2 factual sentences describing what is visible, no invented details"}'
        )

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": f"data:image/{ext};base64,{image_b64}"}},
                    ],
                }
            ],
            temperature=0.1,
            response_format={"type": "json_object"},
        )
        import json

        result = json.loads(response.choices[0].message.content)
        result["demo_mode"] = False
        return result
    except Exception:  # noqa: BLE001
        return None


def analyze_damage(image_path: str, insurance_type_name: str, damaged_component: str | None = None) -> dict:
    ext = Path(image_path).suffix.lower()
    if ext not in IMAGE_EXTENSIONS:
        return {
            "severity": "not_applicable",
            "confidence": None,
            "description": "This document is not an image, so no visual damage analysis applies.",
            "demo_mode": None,
        }

    if settings.OPENAI_API_KEY and not settings.DEMO_MODE:
        result = _openai_vision_result(image_path, insurance_type_name, damaged_component)
        if result is not None:
            return result

    return _demo_result()
