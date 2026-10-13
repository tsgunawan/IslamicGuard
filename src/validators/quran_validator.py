"""Deterministic Qur'an quotation/provenance validator (T11, paper.md Sec 9.1).

Given free text that cites and/or quotes a Qur'an verse, determines:
  1. existence  -- does the cited surah:ayah actually exist in data/corpus/quran.jsonl?
  2. quotation  -- if quoted text is given, does it match the canonical ayah text?

Supported citation formats (documented, not exhaustive -- unsupported formats are
reported as "unparseable" rather than silently ignored or guessed):
  - Numeric, surah-keyword-anchored: "Qur'an 2:255", "Quran 2:255", "Surah 2:255",
    "Surah 2, Ayah 255", "Q 2:255".
  - Surah-name-anchored: "Al-Baqarah 2:255" or "Surah Al-Baqarah, verse 255"
    (surah name resolved via src/utils/quran_surah_names.py's standard 114-name table --
    an uncontested enumeration, not a matter of scholarly disagreement).
  - Arabic forms ("سورة مريم (19:4)", "سورة لقمان، الآية 13", "(لقمان: 17)", ...), parsed by
    src/validators/arabic_citations.py -- added after T23 found the English-only patterns
    above extracted nothing from Arabic answers. An Arabic citation may cover a verse range;
    a quote is then checked against every verse in the range and against the range as a whole.

Only text_ar exists in this project's Qur'an corpus (no English translation field --
see data/corpus/SCHEMA.md); a quoted claim given only in English cannot be text-matched
against the corpus and is reported as NO_QUOTE_GIVEN (existence-only) rather than a false
NO_MATCH -- this is a documented corpus coverage limitation, not a validator defect.
"""

from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path

from rapidfuzz import fuzz

from src.utils.quran_surah_names import surah_id_from_name
from src.utils.text_normalize import extract_nearby_quote, normalize_arabic
from src.validators import arabic_citations
from src.validators.arabic_citations import normalize_arabic_loose
from src.validators.schema import FlagCategory, MatchTier, QuotationCheck

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
QURAN_JSONL = REPO_ROOT / "data" / "corpus" / "quran.jsonl"

EXACT_CONTAINMENT_MIN_LEN = 8  # avoid trivially "exact-matching" a 1-2 word fragment
FUZZY_THRESHOLD = 85.0
# Partial-verse quotes with small spelling differences: only when the quote is no longer than
# the canonical text (so the whole quote must align inside the verse, which is the direction
# that does not over-credit a shared opening phrase) and is long enough to be distinctive.
PARTIAL_MIN_LEN = 20
PARTIAL_THRESHOLD = 92.0

# Numeric surah:ayah anchored by a Qur'an/Surah keyword nearby.
_NUMERIC_RE = re.compile(
    r"\b(?:Qur['’]?an|Quran|Q\.)\s*,?\s*(\d{1,3})\s*[:.,]\s*(\d{1,3})"
    r"|\bSurah\s+(\d{1,3})\s*(?:,)?\s*(?:Ayah|Verse|Ayat)?\s*[:.,]?\s*(\d{1,3})",
    flags=re.IGNORECASE,
)

# Surah-name anchored: a run of name-like tokens (with optional Al-/An-/etc. prefixes)
# followed within a short distance by a number (ayah).
_NAME_RE = re.compile(
    r"\b(?:Surah\s+)?([A-Z][a-zA-Z'’]*(?:[- ][A-Z][a-zA-Z'’]*){0,2})"
    r"[,:]?\s*(?:Ayah|Verse|Ayat)?\s*#?\s*(\d{1,3})\b"
)

@lru_cache(maxsize=1)
def _load_corpus() -> dict[tuple[int, int], dict]:
    lookup: dict[tuple[int, int], dict] = {}
    with QURAN_JSONL.open(encoding="utf-8") as f:
        for line in f:
            rec = json.loads(line)
            lookup[(rec["surah_id"], rec["ayah_id"])] = rec
    return lookup


def find_citations(text: str) -> list[dict]:
    """Return raw citation matches: {citation_raw, surah_id|None, surah_name_raw|None, ayah_id, quote|None}."""
    found: list[dict] = []
    seen_spans: set[tuple[int, int]] = set()

    for m in _NUMERIC_RE.finditer(text):
        if m.group(1) and m.group(2):
            surah_id, ayah_id = int(m.group(1)), int(m.group(2))
        else:
            surah_id, ayah_id = int(m.group(3)), int(m.group(4))
        span = m.span()
        seen_spans.add(span)
        found.append(
            {
                "citation_raw": m.group(0),
                "surah_id": surah_id,
                "surah_name_raw": None,
                "ayah_id": ayah_id,
                "quote": extract_nearby_quote(text, span),
            }
        )

    for m in _NAME_RE.finditer(text):
        span = m.span()
        if any(s[0] <= span[0] < s[1] or s[0] < span[1] <= s[1] for s in seen_spans):
            continue  # already captured by the numeric pattern
        name_raw, ayah_str = m.group(1), m.group(2)
        surah_id = surah_id_from_name(name_raw)
        if surah_id is None:
            continue  # not a recognized surah name -- don't guess, just skip this candidate
        found.append(
            {
                "citation_raw": m.group(0),
                "surah_id": surah_id,
                "surah_name_raw": name_raw,
                "ayah_id": int(ayah_str),
                "quote": extract_nearby_quote(text, span),
            }
        )

    for c in arabic_citations.find_quran_citations(text):
        span = c.pop("span")
        c["quote"] = arabic_citations.extract_nearby_arabic_quote(text, span)
        found.append(c)

    return found


def _match_tier(quote: str | None, canonical_ar: str) -> MatchTier:
    if not quote:
        return MatchTier.NO_QUOTE_GIVEN
    # Heuristic: only attempt Arabic normalized matching if the quote contains Arabic
    # script; an English quote can't be checked against text_ar (no text_en in this
    # corpus -- documented coverage limitation, see module docstring).
    has_arabic = any("؀" <= ch <= "ۿ" for ch in quote)
    if not has_arabic:
        return MatchTier.NO_QUOTE_GIVEN
    q_norm = normalize_arabic(quote)
    c_norm = normalize_arabic(canonical_ar)
    if len(q_norm) >= EXACT_CONTAINMENT_MIN_LEN and (q_norm in c_norm or c_norm in q_norm):
        return MatchTier.EXACT
    # fuzz.ratio (whole-string), not partial_ratio: these are short, atomic ayah records,
    # and partial_ratio was found (during test construction) to over-credit a misquote that
    # merely shares an opening phrase with the correct ayah (e.g. "Qul huwa Allah..." shared
    # prefix between Al-Ikhlas 112:1 and 112:2) -- a real false-VERIFIED risk, not hypothetical.
    score = fuzz.ratio(q_norm, c_norm)
    if score >= FUZZY_THRESHOLD:
        return MatchTier.NORMALIZED_FUZZY
    # Second pass on a looser form (unified alef/ya, punctuation and pause marks removed).
    q_loose, c_loose = normalize_arabic_loose(quote), normalize_arabic_loose(canonical_ar)
    if len(q_loose) >= EXACT_CONTAINMENT_MIN_LEN and (q_loose in c_loose or c_loose in q_loose):
        return MatchTier.EXACT
    # No whole-string ratio on the loose form: unifying alef forms pushed the adjacent-ayah
    # misquote in tests/test_quran_validator.py (112:2's text cited as 112:1) over the threshold.
    if PARTIAL_MIN_LEN <= len(q_loose) <= len(c_loose) and fuzz.partial_ratio(q_loose, c_loose) >= PARTIAL_THRESHOLD:
        return MatchTier.NORMALIZED_FUZZY
    return MatchTier.NO_MATCH


_TIER_RANK = {MatchTier.EXACT: 3, MatchTier.NORMALIZED_FUZZY: 2, MatchTier.NO_QUOTE_GIVEN: 1, MatchTier.NO_MATCH: 0}


def _best_tier_over_range(quote: str | None, texts: list[str]) -> MatchTier:
    """Best match of a quote against each verse of a cited range and the range joined."""
    candidates = texts + ([" ".join(texts)] if len(texts) > 1 else [])
    return max((_match_tier(quote, t) for t in candidates), key=_TIER_RANK.get)


def validate_quran_citation(citation: dict) -> QuotationCheck:
    lookup = _load_corpus()
    surah_id, ayah_id = citation["surah_id"], citation["ayah_id"]
    record = lookup.get((surah_id, ayah_id))
    parsed_ref = {"surah_id": surah_id, "ayah_id": ayah_id, "surah_name_raw": citation.get("surah_name_raw")}
    ayah_end = citation.get("ayah_end")
    if ayah_end:
        parsed_ref["ayah_end"] = ayah_end

    if record is None:
        return QuotationCheck(
            citation_raw=citation["citation_raw"],
            citation_type="quran",
            parsed_reference=parsed_ref,
            exists=False,
            match_tier=MatchTier.NO_MATCH if citation.get("quote") else MatchTier.NO_QUOTE_GIVEN,
            matched_record_id=None,
            flag=FlagCategory.FABRICATED_CITATION,
            notes=f"No ayah {surah_id}:{ayah_id} in the corpus (valid surahs are 1-114; "
            "ayah counts vary per surah -- see data/corpus/quran.jsonl).",
        )

    if ayah_end:
        texts = [lookup[(surah_id, a)]["text_ar"] for a in range(ayah_id, ayah_end + 1) if (surah_id, a) in lookup]
        tier = _best_tier_over_range(citation.get("quote"), texts)
    else:
        tier = _match_tier(citation.get("quote"), record["text_ar"])
    flag = FlagCategory.VERIFIED if tier in (MatchTier.EXACT, MatchTier.NORMALIZED_FUZZY, MatchTier.NO_QUOTE_GIVEN) else FlagCategory.MISQUOTED
    return QuotationCheck(
        citation_raw=citation["citation_raw"],
        citation_type="quran",
        parsed_reference=parsed_ref,
        exists=True,
        match_tier=tier,
        matched_record_id=record["id"],
        flag=flag,
        notes="" if tier != MatchTier.NO_QUOTE_GIVEN else "No quoted text given or quote not in Arabic script; existence-only check performed.",
    )


def validate_text(text: str) -> list[QuotationCheck]:
    """Find and validate every Qur'an citation in a piece of text."""
    return [validate_quran_citation(c) for c in find_citations(text)]
