"""
Thin FAISS wrapper: one flat inner-product index per insurance type,
persisted to disk alongside a sidecar JSON file mapping each vector's
position in the index back to its DocumentChunk id (FAISS itself only
knows about positions, not our UUIDs).

Kept intentionally simple (IndexFlatIP, full rebuild-friendly) since
the dataset sizes here are policy-document chunks, not web-scale — an
IVF/HNSW index would be premature optimization for this stage.
"""

import json
from pathlib import Path

import faiss
import numpy as np

from app.services.embeddings import embedding_dimension

INDEX_DIR = Path(__file__).resolve().parents[3] / "data" / "faiss"
INDEX_DIR.mkdir(parents=True, exist_ok=True)


class VectorStore:
    def __init__(self, insurance_type_code: str):
        self.code = insurance_type_code
        self.index_path = INDEX_DIR / f"{insurance_type_code}.index"
        self.ids_path = INDEX_DIR / f"{insurance_type_code}.ids.json"
        self.dim = embedding_dimension()
        self._index = self._load_index()
        self._chunk_ids: list[str] = self._load_ids()

    def _load_index(self):
        if self.index_path.exists():
            return faiss.read_index(str(self.index_path))
        return faiss.IndexFlatIP(self.dim)

    def _load_ids(self) -> list[str]:
        if self.ids_path.exists():
            return json.loads(self.ids_path.read_text())
        return []

    def _persist(self):
        faiss.write_index(self._index, str(self.index_path))
        self.ids_path.write_text(json.dumps(self._chunk_ids))

    def add(self, chunk_ids: list[str], vectors: np.ndarray):
        if len(chunk_ids) == 0:
            return
        self._index.add(vectors)
        self._chunk_ids.extend(chunk_ids)
        self._persist()

    def search(self, query_vector: np.ndarray, top_k: int = 5) -> list[tuple[str, float]]:
        if self._index.ntotal == 0:
            return []
        scores, positions = self._index.search(query_vector.reshape(1, -1), min(top_k, self._index.ntotal))
        results = []
        for pos, score in zip(positions[0], scores[0]):
            if pos == -1:
                continue
            results.append((self._chunk_ids[pos], float(score)))
        return results
