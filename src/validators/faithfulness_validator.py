"""Claim-evidence faithfulness validator (T12, condition B4, paper.md Sec 9.1).

Separate from T11's quran_validator.py/hadith_validator.py (which check "does the cited
source exist and does the quote match it"): this module checks "does the retrieved
evidence actually support the claim", per Sec 9.1's explicit "separate source existence
from source supports claim."

Method chosen: a dedicated multilingual NLI model (MoritzLaurer/mDeBERTa-v3-base-mnli-xnli,
verified to exist and load -- see STATUS.md T12 entry), used as premise=retrieved-evidence-
text, hypothesis=claim, rather than an LLM-as-judge. This is the "Preferred if feasible"
option in paper.md Sec 9.1: it is model-family-independent (no risk of the same generator
being its own judge, which Sec 9.1 explicitly warns against), multilingual (the corpus and
generated responses are Arabic/English), and its 3-way entailment/neutral/contradiction
output maps directly onto this module's supported/not_addressed/contradicted verdicts.

IMPORTANT LIMITATION, stated plainly per paper.md's "state uncertainty" principle: this NLI
model's own training data (MNLI/XNLI/ANLI/etc.) is general-domain, not Islamic-text-specific,
and its calibration here is a single-annotator (this project's own, non-expert) informal
pass -- see data/benchmarks/t12_calibration_set.jsonl and STATUS.md's T12 entry for the
honestly-reported accuracy against that set. This is NOT a substitute for the qualified-
scholar validation planned in T19-T21(paper.md Sec 1.5), and no manuscript claim should cite
this validator's verdicts as scholar-verified.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from enum import Enum
from functools import lru_cache
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent.parent

NLI_MODEL_NAME = "MoritzLaurer/mDeBERTa-v3-base-mnli-xnli"

# Thresholds chosen conservatively (favoring not_addressed_by_evidence over a confident
# supported/contradicted call in ambiguous cases) prior to calibration; revisited against
# the informal calibration set in STATUS.md's T12 entry -- see that entry for whether these
# held up or needed adjustment, exactly as T11's fuzzy-match threshold was recalibrated
# against real evidence rather than left as an untested guess.
ENTAILMENT_THRESHOLD = 0.55
CONTRADICTION_THRESHOLD = 0.55

LAYERS = ["quran", "hadith", "fiqh"]

# Real finding from T12's informal calibration pass (see STATUS.md / data/benchmarks/
# t12_calibration_set.jsonl): claims that WRAP a citation before stating it -- e.g.
# "**FiqhQA #76** (similarity=0.728) states:\n- The Hanafi school allows..." or
# "According to FiqhQA #32, which is relevant to this question: > \"...\"" -- measurably
# suppressed entailment scores even when the wrapped content was a NEAR-VERBATIM match to
# its cited evidence. Verified directly on two calibration cases: stripping the wrapper
# before building the NLI hypothesis moved entailment from 0.364->0.988 and 0.055->0.996
# on otherwise-identical premise/claim pairs. This is a documented, evidence-driven fix
# (same methodology as T11's real-bug-fix pattern), not a guess -- see STATUS.md's T12
# entry for the before/after numbers and which calibration cases it affects.
_WRAPPER_STATES_RE = re.compile(r"^.{0,90}?\b(?:states|indicates|says)\s*:\s*", re.IGNORECASE | re.DOTALL)
_WRAPPER_ACCORDING_RE = re.compile(r"^according to\b.{0,90}?:\s*", re.IGNORECASE | re.DOTALL)


def _nli_hypothesis_text(claim_text: str) -> str:
    """Strip a leading citation-attribution wrapper for the NLI hypothesis only.

    Returns the wrapped content on a match (falls back to the original claim_text if
    stripping would leave under 10 chars, or if no wrapper pattern matches at all).
    The caller's ClaimCheck.claim_text always keeps the ORIGINAL, unstripped text --
    this function only changes what's fed to the NLI model, never what's reported as
    "the claim" in output.
    """
    for pattern in (_WRAPPER_ACCORDING_RE, _WRAPPER_STATES_RE):
        m = pattern.match(claim_text)
        if not m:
            continue
        rest = claim_text[m.end() :].strip()
        rest = rest.lstrip("*->\n\t ").strip("\"“”*")
        rest = rest.split("\n\n")[0].strip().rstrip("\"“”*")
        if len(rest) >= 10:
            return rest
    return claim_text


class ClaimVerdict(str, Enum):
    SUPPORTED = "supported"
    CONTRADICTED = "contradicted"
    NOT_ADDRESSED_BY_EVIDENCE = "not_addressed_by_evidence"
    UNPARSEABLE_CLAIM = "unparseable_claim"


@dataclass
class ClaimCheck:
    claim_text: str
    verdict: ClaimVerdict
    best_evidence_record_id: str | None = None
    best_evidence_citation: str | None = None
    entailment_prob: float | None = None
    contradiction_prob: float | None = None
    neutral_prob: float | None = None
    n_evidence_considered: int = 0
    hypothesis_text_used: str | None = None  # differs from claim_text when a citation
    # wrapper was stripped before the NLI check (see _nli_hypothesis_text) -- kept for
    # auditability so a reviewer can see exactly what was compared, not just the verdict.
    notes: str = ""

    def to_dict(self) -> dict:
        return dict(
            claim_text=self.claim_text,
            verdict=self.verdict.value,
            best_evidence_record_id=self.best_evidence_record_id,
            best_evidence_citation=self.best_evidence_citation,
            entailment_prob=self.entailment_prob,
            contradiction_prob=self.contradiction_prob,
            neutral_prob=self.neutral_prob,
            n_evidence_considered=self.n_evidence_considered,
            hypothesis_text_used=self.hypothesis_text_used,
            notes=self.notes,
        )


@lru_cache(maxsize=1)
def _load_raw_records(layer: str) -> dict[str, dict[str, Any]]:
    records: dict[str, dict[str, Any]] = {}
    with (REPO_ROOT / "data" / "corpus" / f"{layer}.jsonl").open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            records[rec["id"]] = rec
    return records


def _citation_and_text(layer: str, rec: dict[str, Any]) -> tuple[str, str]:
    """Mirrors src/rag/generate.py's _citation_and_text exactly -- the same text shown to
    the generator is what we check the claim against, not some other rendering of the record.
    """
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


def evidence_texts_from_retrieval_entry(retrieval_entry: dict[str, Any]) -> list[dict[str, Any]]:
    """Build {record_id, citation, text} for every passage retrieval logged for one item,
    using the exact text the generator was actually shown (per _citation_and_text above).
    """
    out: list[dict[str, Any]] = []
    for p in retrieval_entry.get("passages", []):
        layer = p["layer"]
        rec = _load_raw_records(layer).get(p["record_id"])
        if rec is None:
            continue  # shouldn't happen (retrieval logged an id that vanished from the corpus)
        citation, text = _citation_and_text(layer, rec)
        if not text:
            continue
        out.append({"record_id": p["record_id"], "citation": citation, "text": text, "layer": layer})
    return out


_tokenizer = None
_model = None
_device = "cpu"


def _load_model():
    global _tokenizer, _model, _device
    if _model is not None:
        return _tokenizer, _model
    import torch
    from transformers import AutoModelForSequenceClassification, AutoTokenizer

    _tokenizer = AutoTokenizer.from_pretrained(NLI_MODEL_NAME)
    _model = AutoModelForSequenceClassification.from_pretrained(NLI_MODEL_NAME)
    _model.eval()
    if torch.cuda.is_available():
        _device = "cuda"
        _model.to(_device)
    return _tokenizer, _model


def _nli_probs(premise: str, hypothesis: str) -> dict[str, float]:
    import torch

    tokenizer, model = _load_model()
    inputs = tokenizer(premise, hypothesis, return_tensors="pt", truncation=True, max_length=512)
    if _device == "cuda":
        inputs = {k: v.to(_device) for k, v in inputs.items()}
    with torch.no_grad():
        logits = model(**inputs).logits
    probs = torch.softmax(logits, dim=-1)[0].tolist()
    id2label = model.config.id2label
    return {id2label[i].lower(): probs[i] for i in range(len(probs))}


def check_claim(claim_text: str, evidence_passages: list[dict[str, Any]]) -> ClaimCheck:
    """Check one claim against the set of passages actually retrieved for its response.

    Picks the single evidence passage with the highest entailment probability as the
    "best evidence" and bases the verdict on it -- a claim only needs ONE supporting
    passage to be `supported`; it is `contradicted` only if the best-entailing passage's
    own contradiction score doesn't dominate (i.e. we don't average across passages,
    since one irrelevant passage among nine shouldn't drag down a genuinely supported claim).
    """
    if not claim_text or not claim_text.strip():
        return ClaimCheck(claim_text=claim_text, verdict=ClaimVerdict.UNPARSEABLE_CLAIM, notes="empty claim text")
    if not evidence_passages:
        return ClaimCheck(
            claim_text=claim_text,
            verdict=ClaimVerdict.NOT_ADDRESSED_BY_EVIDENCE,
            n_evidence_considered=0,
            notes="no retrieved passages available for this item",
        )

    hypothesis = _nli_hypothesis_text(claim_text)

    best_probs = None
    best_passage = None
    for passage in evidence_passages:
        probs = _nli_probs(premise=passage["text"], hypothesis=hypothesis)
        if best_probs is None or probs.get("entailment", 0.0) > best_probs.get("entailment", 0.0):
            best_probs, best_passage = probs, passage

    ent = best_probs.get("entailment", 0.0)
    contra = best_probs.get("contradiction", 0.0)
    neutral = best_probs.get("neutral", 0.0)

    if ent >= ENTAILMENT_THRESHOLD and ent > contra:
        verdict = ClaimVerdict.SUPPORTED
    elif contra >= CONTRADICTION_THRESHOLD and contra > ent:
        verdict = ClaimVerdict.CONTRADICTED
    else:
        verdict = ClaimVerdict.NOT_ADDRESSED_BY_EVIDENCE

    return ClaimCheck(
        claim_text=claim_text,
        verdict=verdict,
        best_evidence_record_id=best_passage["record_id"],
        best_evidence_citation=best_passage["citation"],
        entailment_prob=round(ent, 4),
        contradiction_prob=round(contra, 4),
        neutral_prob=round(neutral, 4),
        n_evidence_considered=len(evidence_passages),
        hypothesis_text_used=hypothesis if hypothesis != claim_text else None,
    )
