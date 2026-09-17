"""
OCR for claim documents. Uses real Tesseract (via pytesseract) for
image files — no API key required, nothing invented. PDFs are text-
extracted directly (reusing the same extractor as policy documents)
since most uploaded claim PDFs (invoices, estimates) are digitally
generated, not scans.
"""

from pathlib import Path

import pytesseract
from PIL import Image

from app.services.document_processing import extract_text as extract_pdf_text

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".webp"}


def run_ocr(path: str) -> dict:
    """Returns {"text": str, "status": "processed"|"error", "error": str|None}."""
    p = Path(path)
    ext = p.suffix.lower()
    try:
        if ext == ".pdf":
            text = extract_pdf_text(path)
        elif ext in IMAGE_EXTENSIONS:
            text = pytesseract.image_to_string(Image.open(path))
        else:
            return {"text": "", "status": "error", "error": f"Unsupported document type for OCR: {ext}"}
        return {"text": text.strip(), "status": "processed", "error": None}
    except Exception as exc:  # noqa: BLE001
        return {"text": "", "status": "error", "error": str(exc)}
