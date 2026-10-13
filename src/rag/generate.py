"""B2 (standard RAG) retrieval+generation, per paper.md §10.

B2 = retrieval + generation, nothing else: no provenance validator, no claim-evidence
check, no madhhab policy, no abstention logic (those are B3-B5, later tasks T11-T13).
Every response is saved alongside its retrieved passages and source metadata
(paper.md §10's explicit B2 acceptance criterion).

Retrieval uses the DG-4-revised primary embedding model (qwen3-embedding-4b,
DECISIONS.md) against the three corpus-layer indexes built in T08.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from src.rag.embed import MODELS, Embedder
from src.rag.index import LayerIndex, load_index

REPO_ROOT = Path(__file__).resolve().parents[2]
CORPUS_DIR = REPO_ROOT / "data" / "corpus"
LAYERS = ["quran", "hadith", "fiqh"]

# Retrieved passages per layer. Chosen so the combined context (up to 9 short
# atomic records: 1 ayah / 1 hadith / 1 fiqh ruling each) stays well within any
# of the three models' context windows while still giving the generator real
# candidate evidence from every layer relevant to a mixed Qur'an/Hadith/fiqh
# question set (T09's sample mixes IslamicFaithQA and FiqhQA items spanning all
# three domains) -- documented here rather than silently assumed correct.
TOP_K_PER_LAYER = 3


def _load_raw_records(layer: str) -> dict[str, dict[str, Any]]:
    records: dict[str, dict[str, Any]] = {}
    with (CORPUS_DIR / f"{layer}.jsonl").open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            records[rec["id"]] = rec
    return records


@dataclass
class RetrievedPassage:
    layer: str
    record_id: str
    score: float
    citation: str
    text_for_context: str
    raw_provenance: dict[str, Any]


def _citation_and_text(layer: str, rec: dict[str, Any]) -> tuple[str, str]:
    """Human-readable citation label + the text block shown to the generator."""
    if layer == "quran":
        citation = f"Qur'an {rec['surah_id']}:{rec['ayah_id']} ({rec['surah_name']})"
        text = rec["text_ar"]
    elif layer == "hadith":
        citation = f"{rec['collection']} #{rec['hadith_number']}"
        text = rec["text_en"] or rec.get("text_ar") or ""
    elif layer == "fiqh":
        madhhabs = ", ".join(p["madhhab"] for p in rec.get("madhhab_positions", []))
        citation = f"FiqhQA #{rec['id'].split(':')[-1]} ({rec['category']}; madhhabs: {madhhabs})"
        text = rec.get("statement_en") or rec.get("question_en") or ""
    else:  # pragma: no cover - LAYERS is fixed
        raise ValueError(layer)
    return citation, text


class RagRetriever:
    """Loads all three layer indexes + the corpus records + the embedder once."""

    def __init__(self, embedding_model_slug: str = "qwen3-embedding-4b") -> None:
        self.spec = MODELS[embedding_model_slug]
        self.embedder = Embedder(self.spec)
        self.layer_indexes: dict[str, LayerIndex] = {
            layer: load_index(embedding_model_slug, layer) for layer in LAYERS
        }
        self.layer_records: dict[str, dict[str, dict[str, Any]]] = {
            layer: _load_raw_records(layer) for layer in LAYERS
        }

    def retrieve(self, query: str, k_per_layer: int = TOP_K_PER_LAYER) -> list[RetrievedPassage]:
        query_vec = self.embedder.encode_queries([query])
        passages: list[RetrievedPassage] = []
        for layer in LAYERS:
            hits = self.layer_indexes[layer].search(query_vec, k_per_layer)[0]
            for record_id, score in hits:
                rec = self.layer_records[layer][record_id]
                citation, text = _citation_and_text(layer, rec)
                passages.append(
                    RetrievedPassage(
                        layer=layer,
                        record_id=record_id,
                        score=score,
                        citation=citation,
                        text_for_context=text,
                        raw_provenance=rec.get("provenance", {}),
                    )
                )
        return passages


def format_context_block(passages: list[RetrievedPassage]) -> str:
    lines = ["Retrieved passages (may or may not be relevant -- use your judgment):", ""]
    for p in passages:
        lines.append(f"[{p.layer.upper()}] {p.citation} (similarity={p.score:.3f})")
        lines.append(p.text_for_context)
        lines.append("")
    return "\n".join(lines)


def passages_to_log(passages: list[RetrievedPassage]) -> list[dict[str, Any]]:
    return [
        {
            "layer": p.layer,
            "record_id": p.record_id,
            "score": round(p.score, 4),
            "citation": p.citation,
            "provenance": p.raw_provenance,
        }
        for p in passages
    ]
