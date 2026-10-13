"""Deterministic Hadith quotation/provenance validator (T11, paper.md Sec 9.1).

Given free text that cites and/or quotes a hadith, determines:
  1. existence -- does the cited collection+number exist in data/corpus/hadith.jsonl?
  2. quotation -- if quoted text is given, does it match the canonical hadith text?
  3. grading   -- surfaces (does not resolve) the corpus's multi-scholar authenticity
                  grading for the matched hadith, per DECISIONS.md DG-5 and paper.md
                  Sec 0 rule 17 (never resolve scholarly disagreement by preference).

Supported citation format: "<collection name/alias> <marker>? <number>", e.g.
"Sahih al-Bukhari 1234", "Bukhari #1234", "Sunan Abu Dawud, Hadith 184". The number is
matched against this corpus's own `hadith_number` field, i.e. fawazahmed0/hadith-api's
internal numbering (see DECISIONS.md DG-5 and data/corpus/SCHEMA.md's documented finding
that this numbering does NOT match every other citation convention in circulation, e.g.
T08 found IslamicFaithQA's inline citations use a different scheme). A citation using an
unsupported/unrecognized collection name, or one whose number doesn't resolve under this
corpus's numbering, is reported as fabricated/not-found rather than silently accepted or
guessed against a different numbering scheme.

"Sahih Muslim" requires the "Sahih" qualifier (bare "Muslim" is not matched) to avoid
false-positive triggers on the common English word/adjective "Muslim" elsewhere in text --
a documented, deliberate precision-over-recall trade-off.

KNOWN LIMITATION (found via real T10 B2 data during T11, not hypothetical): quote-to-citation
pairing uses nearest-quote-by-distance (see extract_nearby_quote in text_normalize.py), which
works well when a response states one citation immediately followed by its one quote. It can
MISATTRIBUTE when a response discusses several citations in one paragraph without a strict
one-quote-per-citation structure (e.g. "In X and Y, the Prophet said: '...'. In Z, he also
said: '...'" -- a quote can end up paired with the citation closest to it by raw character
distance rather than the one a human reader would judge it belongs to). This produced at least
one confirmed false MISQUOTED flag in the real T10 sanity check (see STATUS.md's T11 entry) that
was traced to misattribution, not an actual misquote. Not fixed in T11 -- would need either
stricter same-sentence/no-intervening-citation pairing rules or LLM-assisted attribution
(arguably T12's territory, which already has to reason about claim-evidence structure). Treat
a MISQUOTED flag as "needs closer look," not an infallible verdict, until this is addressed.
"""

from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path

from rapidfuzz import fuzz

from src.utils.text_normalize import extract_nearby_quote, normalize_arabic, normalize_english
from src.validators import arabic_citations
from src.validators.arabic_citations import normalize_arabic_loose
from src.validators.schema import FlagCategory, MatchTier, QuotationCheck

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
HADITH_JSONL = REPO_ROOT / "data" / "corpus" / "hadith.jsonl"

EXACT_CONTAINMENT_MIN_LEN_AR = 8
EXACT_CONTAINMENT_MIN_LEN_EN = 15
# Calibrated against real T10 B2 data, not just the synthetic test cases: a genuine,
# accurate-but-abbreviated Qwen3-8B quote of hadith:bukhari:6066 (omitting one clause,
# "and do not practice Najsh") scored fuzz.ratio=84.8 -- just under an earlier 85.0
# threshold, which would have wrongly flagged it MISQUOTED. The synthetic
# correct_citation_misquoted_text test case (genuinely different content) scores 41,
# leaving a wide, safe margin at 80. See tests/test_hadith_validator.py.
FUZZY_THRESHOLD = 80.0
# Arabic quotes are normally the matn only, while text_ar also carries the isnad, so a
# whole-string ratio cannot succeed. A quote no longer than the record may instead align
# inside it (see quran_validator.py for why this direction is the safe one).
PARTIAL_MIN_LEN_AR = 20
PARTIAL_THRESHOLD_AR = 88.0

# (collection_key, name-alternation regex fragment). Order matters: more specific
# aliases first so e.g. "Sunan Abu Dawud" isn't partially eaten by a looser pattern.
_COLLECTION_PATTERNS: list[tuple[str, str]] = [
    ("bukhari", r"Sahih\s+al[- ]?Bukhari|Sahih\s+Bukhari|Bukhari"),
    ("muslim", r"Sahih\s+Muslim"),  # bare "Muslim" deliberately NOT matched -- see module docstring
    ("abudawud", r"Sunan\s+Abu\s+Dawud|Sunan\s+Abi\s+Dawud|Abu\s+Dawud"),
    ("tirmidhi", r"Jami['’]?\s+at[- ]?Tirmidhi|Sunan\s+al[- ]?Tirmidhi|Tirmidhi"),
    ("nasai", r"Sunan\s+an[- ]?Nasa['’]?i|Sunan\s+al[- ]?Nasa['’]?i|An[- ]?Nasa['’]?i|Nasa['’]?i"),
    ("ibnmajah", r"Sunan\s+Ibn\s+Majah|Ibn\s+Majah"),
]

_CITATION_RES = [
    (key, re.compile(rf"\b(?:{pattern})\b[^\d]{{0,40}}?(\d{{1,5}})", flags=re.IGNORECASE))
    for key, pattern in _COLLECTION_PATTERNS
]


@lru_cache(maxsize=1)
def _load_corpus() -> dict[tuple[str, int], dict]:
    lookup: dict[tuple[str, int], dict] = {}
    with HADITH_JSONL.open(encoding="utf-8") as f:
        for line in f:
            rec = json.loads(line)
            lookup[(rec["collection_key"], rec["hadith_number"])] = rec
    return lookup


def find_citations(text: str) -> list[dict]:
    """Return raw citation matches: {citation_raw, collection_key, hadith_number, quote}."""
    found: list[dict] = []
    seen_spans: set[tuple[int, int]] = set()
    for key, regex in _CITATION_RES:
        for m in regex.finditer(text):
            span = m.span()
            if any(s[0] <= span[0] < s[1] or s[0] < span[1] <= s[1] for s in seen_spans):
                continue
            seen_spans.add(span)
            found.append(
                {
                    "citation_raw": m.group(0),
                    "collection_key": key,
                    "hadith_number": int(m.group(1)),
                    "quote": extract_nearby_quote(text, span),
                }
            )
    # Arabic-form citations ("سنن ابن ماجه #2568", "حديث البخاري (5885)") -- see arabic_citations.py.
    for c in arabic_citations.find_hadith_citations(text):
        span = c.pop("span")
        c["quote"] = arabic_citations.extract_nearby_arabic_quote(text, span)
        found.append(c)
    return found


def _match_tier(quote: str | None, record: dict) -> MatchTier:
    if not quote:
        return MatchTier.NO_QUOTE_GIVEN
    has_arabic = any("؀" <= ch <= "ۿ" for ch in quote)
    if has_arabic:
        if not record["text_ar"]:
            return MatchTier.NO_QUOTE_GIVEN  # this record's Arabic text is null in the source
        q_norm, c_norm = normalize_arabic(quote), normalize_arabic(record["text_ar"])
        min_len = EXACT_CONTAINMENT_MIN_LEN_AR
    else:
        q_norm, c_norm = normalize_english(quote), normalize_english(record["text_en"])
        min_len = EXACT_CONTAINMENT_MIN_LEN_EN

    if len(q_norm) >= min_len and (q_norm in c_norm or c_norm in q_norm):
        return MatchTier.EXACT
    # fuzz.ratio (whole-string), not partial_ratio -- see quran_validator.py's identical
    # comment: partial_ratio was found to over-credit misquotes sharing only an opening phrase.
    score = fuzz.ratio(q_norm, c_norm)
    if score >= FUZZY_THRESHOLD:
        return MatchTier.NORMALIZED_FUZZY
    if has_arabic:
        q_loose, c_loose = normalize_arabic_loose(quote), normalize_arabic_loose(record["text_ar"])
        if len(q_loose) >= min_len and q_loose in c_loose:
            return MatchTier.EXACT
        if PARTIAL_MIN_LEN_AR <= len(q_loose) <= len(c_loose) and fuzz.partial_ratio(q_loose, c_loose) >= PARTIAL_THRESHOLD_AR:
            return MatchTier.NORMALIZED_FUZZY
    return MatchTier.NO_MATCH


def validate_hadith_citation(citation: dict) -> QuotationCheck:
    lookup = _load_corpus()
    key, number = citation["collection_key"], citation["hadith_number"]
    record = lookup.get((key, number))
    parsed_ref = {"collection_key": key, "hadith_number": number}

    if record is None:
        return QuotationCheck(
            citation_raw=citation["citation_raw"],
            citation_type="hadith",
            parsed_reference=parsed_ref,
            exists=False,
            match_tier=MatchTier.NO_MATCH if citation.get("quote") else MatchTier.NO_QUOTE_GIVEN,
            matched_record_id=None,
            flag=FlagCategory.FABRICATED_CITATION,
            notes=(
                f"No hadith numbered {number} in '{key}' under this corpus's numbering "
                "(fawazahmed0/hadith-api, per DECISIONS.md DG-5). Note: other sources use "
                "different internal numbering for the same collections (see "
                "data/corpus/SCHEMA.md's cross-check against the IslamicEval bundle) -- a "
                "'not found' result here does not necessarily mean the hadith doesn't exist "
                "under some other citation convention, only that it doesn't exist under this "
                "corpus's."
            ),
        )

    tier = _match_tier(citation.get("quote"), record)
    flag = (
        FlagCategory.VERIFIED
        if tier in (MatchTier.EXACT, MatchTier.NORMALIZED_FUZZY, MatchTier.NO_QUOTE_GIVEN)
        else FlagCategory.MISQUOTED
    )
    return QuotationCheck(
        citation_raw=citation["citation_raw"],
        citation_type="hadith",
        parsed_reference=parsed_ref,
        exists=True,
        match_tier=tier,
        matched_record_id=record["id"],
        grading=record["grading"],  # surfaced as-is; never collapsed/resolved, per DG-5 + rule 17
        flag=flag,
        notes="",
    )


def validate_text(text: str) -> list[QuotationCheck]:
    """Find and validate every Hadith citation in a piece of text."""
    return [validate_hadith_citation(c) for c in find_citations(text)]
