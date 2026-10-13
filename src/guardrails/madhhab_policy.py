"""Madhhab-aware policy (T13, paper.md Sec 4 'Adl / Sec 9 madhhab-sensitive routing).

Per paper.md Sec 4: "'Adl (justice/fair representation) -- do not erase legitimate juristic
diversity." Per DG-1 (DECISIONS.md), this project's fiqh layer is scoped to the 4 major Sunni
schools (Hanafi, Maliki, Shafi'i, Hanbali) on a bounded topic set, drawn from FiqhQA
(data/corpus/fiqh.jsonl). Every fiqh.jsonl record already carries a per-record `agreement`
field ("Agreement" | "Disagreement") plus all 4 schools' positions -- this module uses that
field directly rather than re-deriving disagreement from free text.

Per data/corpus/FIQH_LAYER_NOTES.md (T07's honesty finding): fiqh.jsonl's madhhab_positions
are GPT-4o-generated, human-reviewed paraphrases of a Kuwaiti Fiqh Encyclopedia extraction --
NOT verbatim primary-source quotations. This module's disclosure text reflects that lower
provenance tier explicitly; it never presents a position as a direct classical-text citation.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
FIQH_JSONL = REPO_ROOT / "data" / "corpus" / "fiqh.jsonl"

# A fiqh passage must be at least this relevant (retrieval similarity score) before this
# project treats the query as "fiqh-relevant" for madhhab-policy purposes -- otherwise a fiqh
# record retrieved only because nothing better matched would wrongly trigger madhhab framing
# on an unrelated query. Chosen conservatively; not independently validated against a labelled
# relevance set (that would need the same kind of calibration T12 did for faithfulness -- out
# of scope here, documented as a known limitation).
FIQH_RELEVANCE_MIN_SCORE = 0.5

# Name variants actually used in data/corpus/fiqh.jsonl's `madhhab_positions[].madhhab` field
# (see T07's SCHEMA.md) plus common alternate spellings that might appear in generated prose,
# so the plurality-surfaced check does not false-negative on a spelling variant.
_MADHHAB_NAME_PATTERNS: dict[str, re.Pattern] = {
    "hanafi": re.compile(r"\bhanafi\b", re.IGNORECASE),
    "maliki": re.compile(r"\bmaliki\b", re.IGNORECASE),
    "shafeii": re.compile(r"\bshafi[’']?[iy]{1,2}\b", re.IGNORECASE),
    "hanbali": re.compile(r"\bhanbali\b", re.IGNORECASE),
}


@dataclass
class MadhhabContext:
    is_fiqh_relevant: bool
    fiqh_record_id: str | None = None
    category: str | None = None
    agreement: str | None = None  # "Agreement" | "Disagreement" | None (not fiqh-relevant)
    madhhab_positions: list[dict[str, str]] = field(default_factory=list)
    disclosure_note: str = ""

    def to_dict(self) -> dict[str, Any]:
        return dict(
            is_fiqh_relevant=self.is_fiqh_relevant,
            fiqh_record_id=self.fiqh_record_id,
            category=self.category,
            agreement=self.agreement,
            madhhab_positions=self.madhhab_positions,
            disclosure_note=self.disclosure_note,
        )


@lru_cache(maxsize=1)
def _load_fiqh_corpus() -> dict[str, dict[str, Any]]:
    records: dict[str, dict[str, Any]] = {}
    with FIQH_JSONL.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            records[rec["id"]] = rec
    return records


_DISCLOSURE_TEMPLATE = (
    "This question touches a fiqh topic where the four Sunni schools of jurisprudence "
    "({schools}) do not all hold the same position (source: FiqhQA #{num}, category "
    "'{category}'). Per this project's DG-1 scope, these per-madhhab summaries are "
    "GPT-4o-generated, human-reviewed paraphrases of a Kuwaiti Fiqh Encyclopedia extraction "
    "(see data/corpus/FIQH_LAYER_NOTES.md) -- NOT verbatim quotations from a classical fiqh "
    "text. A response on this topic should represent this plurality rather than presenting "
    "one school's view as the single Islamic position."
)


def assess_madhhab_context(
    passages: list[Any], min_score: float = FIQH_RELEVANCE_MIN_SCORE
) -> MadhhabContext:
    """Given retrieved passages (src.rag.generate.RetrievedPassage instances, or any object/
    dict with `.layer`/`.record_id`/`.score` or equivalent keys), find the highest-scoring
    fiqh-layer passage and build the madhhab context from its corpus record.

    Only ever surfaces what fiqh.jsonl's own `agreement` field says -- never infers
    disagreement from free text, and never resolves which school is "correct" (paper.md Sec 0
    rule 17: do not resolve legitimate juristic disagreement by model preference).
    """

    def _get(p: Any, key: str) -> Any:
        return getattr(p, key, None) if not isinstance(p, dict) else p.get(key)

    fiqh_hits = [p for p in passages if _get(p, "layer") == "fiqh"]
    if not fiqh_hits:
        return MadhhabContext(is_fiqh_relevant=False)

    best = max(fiqh_hits, key=lambda p: _get(p, "score") or 0.0)
    if (_get(best, "score") or 0.0) < min_score:
        return MadhhabContext(is_fiqh_relevant=False)

    rec = _load_fiqh_corpus().get(_get(best, "record_id"))
    if rec is None:  # pragma: no cover - would mean retrieval index and corpus drifted apart
        return MadhhabContext(is_fiqh_relevant=False)

    agreement = rec.get("agreement")
    positions = rec.get("madhhab_positions", [])
    disclosure = ""
    if agreement == "Disagreement":
        schools = ", ".join(p["madhhab"] for p in positions)
        disclosure = _DISCLOSURE_TEMPLATE.format(
            schools=schools, num=rec["id"].split(":")[-1], category=rec.get("category", "")
        )

    return MadhhabContext(
        is_fiqh_relevant=True,
        fiqh_record_id=rec["id"],
        category=rec.get("category"),
        agreement=agreement,
        madhhab_positions=positions,
        disclosure_note=disclosure,
    )


def response_surfaces_plurality(response_text: str, context: MadhhabContext) -> bool:
    """Heuristic: does the response text explicitly name >=2 of the 4 madhhab schools?

    This is a coarse, documented heuristic (name-mention counting), not a semantic check of
    whether the response *accurately* represents each school's position -- that stronger claim
    would need T12-style entailment checking against each madhhab_positions entry, which is a
    reasonable follow-up but out of scope for this task. A response could in principle mention
    two school names without genuinely explaining either position and still pass this check;
    documented as a known limitation, not silently assumed away.
    """
    if not context.is_fiqh_relevant or context.agreement != "Disagreement":
        return True  # not applicable -- nothing to surface
    mentioned = sum(1 for pat in _MADHHAB_NAME_PATTERNS.values() if pat.search(response_text))
    return mentioned >= 2
