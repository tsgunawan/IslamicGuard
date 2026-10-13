"""Shared text-normalization helpers for fuzzy matching against the corpus.

Mirrors scripts/build_corpus.py's normalize_arabic exactly (kept here so validators
and the corpus builder use one definition). Per paper.md Sec 18: normalized forms
are for matching only and never replace canonical text fields.
"""

from __future__ import annotations

import re
import unicodedata

ARABIC_DIACRITICS = re.compile("[ً-ْٓ-ٰٟۖ-ۭࣔ-ࣣ࣡-ࣿ]")

_PUNCT_RE = re.compile(r"[^\w\s]", flags=re.UNICODE)
_WS_RE = re.compile(r"\s+")


def normalize_arabic(text: str) -> str:
    """Diacritics-stripped, whitespace-normalized Arabic form for fuzzy matching only."""
    if not text:
        return ""
    t = unicodedata.normalize("NFC", text)
    t = ARABIC_DIACRITICS.sub("", t)
    t = t.replace("ـ", "")  # tatweel/kashida
    t = re.sub(r"\s+", " ", t).strip()
    return t


def normalize_english(text: str) -> str:
    """Lowercase, punctuation-stripped, whitespace-collapsed English form for fuzzy matching."""
    if not text:
        return ""
    t = text.lower()
    t = _PUNCT_RE.sub(" ", t)
    t = _WS_RE.sub(" ", t).strip()
    return t


_QUOTE_RE = re.compile(r"[\"“]([^\"”]{4,400})[\"”]")


def extract_nearby_quote(text: str, span: tuple[int, int], window: int = 300) -> str | None:
    """Find the CLOSEST quoted string to a citation span, within `window` chars either side.

    Real bug found and fixed during T11 (see STATUS.md): a naive single `.search()` over a
    text *slice* around the citation breaks whenever more than one complete quote-pair falls
    in that slice -- e.g. "...ridicule.\"\n\nThis reinforces... Bukhari #6066 states:\n  \"Beware
    of suspicion...\"" has TWO quote-pairs near the citation. A plain ASCII `"` doesn't
    distinguish open from close, so `.search()` on the slice pairs the *closing* quote of the
    first passage with the *opening* quote of the second, extracting the prose IN BETWEEN them
    (neither actual quotation) instead of the real, closer quote. Fixed by finding all
    complete quote-pairs in the full text via `finditer`, then picking whichever pair's span is
    numerically closest to the citation span -- not just whatever `.search()` finds first in an
    arbitrary slice boundary.
    """
    all_spans = [(m.span(), m.group(1)) for m in _QUOTE_RE.finditer(text)]
    if not all_spans:
        return None

    def distance(qspan: tuple[int, int]) -> int:
        if qspan[1] <= span[0]:
            return span[0] - qspan[1]
        if qspan[0] >= span[1]:
            return qspan[0] - span[1]
        return 0  # overlapping (shouldn't normally happen for a citation vs. a quote)

    qspan, quote = min(all_spans, key=lambda item: distance(item[0]))
    if distance(qspan) > window:
        return None
    return quote.strip()


def normalize_name_key(text: str) -> str:
    """Aggressive key for matching surah/collection name spelling variants:
    lowercase, strip hyphens/apostrophes/spaces entirely (e.g. "Al-Fatihah" -> "alfatihah").
    """
    if not text:
        return ""
    t = text.lower()
    t = re.sub(r"[-'’ ]", "", t)
    return t
