"""
Turns an uploaded policy document (PDF or plain text) into overlapping
text chunks ready for embedding. Chunking is by word count, not
sentence-aware NLP, to keep this dependency-light — good enough for
retrieval, not meant to be a perfect semantic splitter.
"""

from pathlib import Path

from pypdf import PdfReader


def extract_text(path: str) -> str:
    p = Path(path)
    if p.suffix.lower() == ".pdf":
        reader = PdfReader(str(p))
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    return p.read_text(encoding="utf-8", errors="ignore")


def chunk_text(text: str, chunk_size: int = 220, overlap: int = 40) -> list[str]:
    """
    Word-based sliding window chunks. chunk_size/overlap are in words,
    tuned to keep each chunk small enough to be a focused, retrievable
    unit (roughly a paragraph or two of a policy document).
    """
    words = text.split()
    if not words:
        return []

    chunks = []
    start = 0
    while start < len(words):
        end = min(start + chunk_size, len(words))
        chunk = " ".join(words[start:end])
        if chunk.strip():
            chunks.append(chunk.strip())
        if end == len(words):
            break
        start = end - overlap
    return chunks
