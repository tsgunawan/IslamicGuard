"""FAISS index build/load/query for one corpus layer + embedding model."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import faiss
import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[2]
INDEX_DIR = REPO_ROOT / "data" / "corpus" / "index"


@dataclass
class LayerIndex:
    index: "faiss.Index"
    ids: list[str]

    def search(self, query_vecs: np.ndarray, k: int) -> list[list[tuple[str, float]]]:
        scores, idxs = self.index.search(query_vecs.astype("float32"), k)
        results = []
        for row_scores, row_idxs in zip(scores, idxs):
            results.append(
                [
                    (self.ids[i], float(s))
                    for s, i in zip(row_scores, row_idxs)
                    if i != -1
                ]
            )
        return results


def index_paths(model_slug: str, layer: str) -> tuple[Path, Path]:
    d = INDEX_DIR / model_slug
    d.mkdir(parents=True, exist_ok=True)
    return d / f"{layer}.faiss", d / f"{layer}.ids.json"


def build_index(embeddings: np.ndarray, ids: list[str], model_slug: str, layer: str) -> LayerIndex:
    dim = embeddings.shape[1]
    index = faiss.IndexFlatIP(dim)  # embeddings are pre-normalized -> IP == cosine
    index.add(embeddings.astype("float32"))
    idx_path, ids_path = index_paths(model_slug, layer)
    faiss.write_index(index, str(idx_path))
    ids_path.write_text(json.dumps(ids), encoding="utf-8")
    return LayerIndex(index=index, ids=ids)


def load_index(model_slug: str, layer: str) -> LayerIndex:
    idx_path, ids_path = index_paths(model_slug, layer)
    if not idx_path.exists() or not ids_path.exists():
        raise FileNotFoundError(
            f"No saved index for model={model_slug} layer={layer} -- run scripts/build_index.py first."
        )
    index = faiss.read_index(str(idx_path))
    ids = json.loads(ids_path.read_text(encoding="utf-8"))
    return LayerIndex(index=index, ids=ids)
