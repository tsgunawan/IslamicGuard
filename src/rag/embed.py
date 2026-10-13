"""Embedding-model wrapper for the retrieval pipeline.

Supports the DG-4 primary (multilingual-e5-large-instruct) and the DG-4-mandated
comparison candidate (Qwen3-Embedding), both instruction-tuned models that use
an "Instruct: ...\\nQuery: {query}" prefix for QUERIES only -- passages/corpus
text are embedded with no prefix. See:
  - intfloat/multilingual-e5-large-instruct model card
  - Qwen/Qwen3-Embedding-* model card
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from sentence_transformers import SentenceTransformer

RETRIEVAL_INSTRUCTION = (
    "Given a question about Islamic religious knowledge (Qur'an, Hadith, or fiqh), "
    "retrieve the passage that best answers or supports it."
)


@dataclass(frozen=True)
class EmbeddingModelSpec:
    slug: str
    hf_repo: str
    trust_remote_code: bool = False
    # Cap actual encoding sequence length regardless of the model's advertised
    # max context (e.g. Qwen3-Embedding-4B advertises 32768 tokens, but full
    # attention over long batches at that model size OOMs a 24GB GPU well
    # before that limit -- see t08_retrieval_eval.md for the real OOM hit and
    # fix during this evaluation). Corpus records here are short (single
    # ayah/hadith/ruling), so this cap does not truncate real content in
    # practice -- verified per-layer, not assumed.
    max_seq_length: int = 2048

    def query_text(self, query: str) -> str:
        return f"Instruct: {RETRIEVAL_INSTRUCTION}\nQuery: {query}"

    def passage_text(self, passage: str) -> str:
        return passage


MODELS: dict[str, EmbeddingModelSpec] = {
    "me5-large-instruct": EmbeddingModelSpec(
        slug="me5-large-instruct",
        hf_repo="intfloat/multilingual-e5-large-instruct",
    ),
    "qwen3-embedding-4b": EmbeddingModelSpec(
        slug="qwen3-embedding-4b",
        hf_repo="Qwen/Qwen3-Embedding-4B",
        max_seq_length=1024,  # see max_seq_length docstring above -- 4B model OOMs at 24GB
                               # with longer caps combined with batch>=8 on the hadith layer
    ),
    "qwen3-embedding-0.6b": EmbeddingModelSpec(
        slug="qwen3-embedding-0.6b",
        hf_repo="Qwen/Qwen3-Embedding-0.6B",
    ),
}


class Embedder:
    def __init__(self, spec: EmbeddingModelSpec, device: str = "cuda") -> None:
        self.spec = spec
        self.model = SentenceTransformer(
            spec.hf_repo, device=device, trust_remote_code=spec.trust_remote_code
        )
        self.model.max_seq_length = spec.max_seq_length

    def encode_passages(self, texts: list[str], batch_size: int = 32) -> np.ndarray:
        formatted = [self.spec.passage_text(t) for t in texts]
        return self.model.encode(
            formatted,
            batch_size=batch_size,
            normalize_embeddings=True,
            show_progress_bar=True,
            convert_to_numpy=True,
        )

    def encode_queries(self, texts: list[str], batch_size: int = 32) -> np.ndarray:
        formatted = [self.spec.query_text(t) for t in texts]
        return self.model.encode(
            formatted,
            batch_size=batch_size,
            normalize_embeddings=True,
            show_progress_bar=True,
            convert_to_numpy=True,
        )
