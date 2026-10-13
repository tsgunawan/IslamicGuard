"""Load IslamicGuard corpus layers (data/corpus/*.jsonl) and produce the text
that gets embedded for retrieval, per record.

Per paper.md §18, canonical text fields (text_ar, statement_ar) are read-only
here -- this module never mutates them. The "embed text" returned for each
record concatenates whatever fields are useful for matching a natural-language
query (e.g. English translation + normalized Arabic), not the canonical field
alone, since queries may be in either language.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterator, Literal

CorpusLayer = Literal["quran", "hadith", "fiqh"]

REPO_ROOT = Path(__file__).resolve().parents[2]
CORPUS_DIR = REPO_ROOT / "data" / "corpus"


@dataclass(frozen=True)
class CorpusRecord:
    id: str
    layer: CorpusLayer
    embed_text: str
    raw: dict[str, Any]


def _quran_embed_text(rec: dict[str, Any]) -> str:
    return rec["text_ar"]


def _hadith_embed_text(rec: dict[str, Any]) -> str:
    parts = [rec.get("text_ar") or "", rec.get("text_en") or ""]
    return "\n".join(p for p in parts if p)


def _fiqh_embed_text(rec: dict[str, Any]) -> str:
    parts = [
        rec.get("statement_ar") or "",
        rec.get("statement_en") or "",
        rec.get("question_en") or "",
    ]
    return "\n".join(p for p in parts if p)


_EMBED_TEXT_FN = {
    "quran": _quran_embed_text,
    "hadith": _hadith_embed_text,
    "fiqh": _fiqh_embed_text,
}


def corpus_path(layer: CorpusLayer) -> Path:
    return CORPUS_DIR / f"{layer}.jsonl"


def iter_corpus(layer: CorpusLayer) -> Iterator[CorpusRecord]:
    path = corpus_path(layer)
    if not path.exists():
        raise FileNotFoundError(
            f"{path} not found -- run `python scripts/build_corpus.py` first (T07)."
        )
    embed_fn = _EMBED_TEXT_FN[layer]
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            yield CorpusRecord(
                id=rec["id"], layer=layer, embed_text=embed_fn(rec), raw=rec
            )


def load_corpus(layer: CorpusLayer) -> list[CorpusRecord]:
    return list(iter_corpus(layer))
