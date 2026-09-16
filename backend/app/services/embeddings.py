"""
Embedding provider abstraction.

If OPENAI_API_KEY is configured, real semantic embeddings come from
OpenAI's embedding API. If it isn't (DEMO_MODE), we fall back to a
deterministic hash-based pseudo-embedding so the ingestion → FAISS →
retrieval pipeline still runs end-to-end without crashing or
requiring a paid key — but this fallback is clearly labeled and does
NOT produce meaningful semantic similarity, only exact/near-exact
token overlap. Swap in a real key to get real retrieval quality.
"""

import hashlib

import numpy as np

from app.config import settings

EMBEDDING_DIM = 384


def _demo_embed_one(text: str) -> np.ndarray:
    """
    Deterministic, dependency-free pseudo-embedding: hash overlapping
    word shingles into buckets of a fixed-size vector. Same text
    always yields the same vector; texts sharing more words end up
    closer together. This is NOT a real semantic embedding.
    """
    vec = np.zeros(EMBEDDING_DIM, dtype="float32")
    words = text.lower().split()
    if not words:
        return vec
    for word in words:
        digest = hashlib.sha256(word.encode("utf-8")).digest()
        bucket = int.from_bytes(digest[:4], "big") % EMBEDDING_DIM
        sign = 1.0 if digest[4] % 2 == 0 else -1.0
        vec[bucket] += sign
    norm = np.linalg.norm(vec)
    return vec / norm if norm > 0 else vec


def is_demo_mode() -> bool:
    return not settings.OPENAI_API_KEY


def embed_texts(texts: list[str]) -> np.ndarray:
    """Returns an (n, EMBEDDING_DIM) float32 array, one row per input text."""
    if not texts:
        return np.zeros((0, EMBEDDING_DIM), dtype="float32")

    if settings.OPENAI_API_KEY:
        from openai import OpenAI

        client = OpenAI(api_key=settings.OPENAI_API_KEY)
        response = client.embeddings.create(model="text-embedding-3-small", input=texts)
        # text-embedding-3-small is 1536-dim; truncate/pad isn't needed since
        # we use a separate FAISS index dimension per mode (see vector_store.py).
        vectors = np.array([d.embedding for d in response.data], dtype="float32")
        # normalize for cosine similarity via inner product
        norms = np.linalg.norm(vectors, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        return vectors / norms

    return np.vstack([_demo_embed_one(t) for t in texts])


def embedding_dimension() -> int:
    return 1536 if settings.OPENAI_API_KEY else EMBEDDING_DIM
