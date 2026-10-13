"""Arabic-form citation parsing for the T11 provenance validators.

Added after T23 found that the original parsers matched English-form references only, so
Arabic answers reached the abstention policy with no provenance signal at all (33 of 34 Arabic
B5 answers had zero citations checked). Supported forms, all taken from real model output in
the T15/T16 runs (documented, not exhaustive):

  Qur'an:  "سورة مريم (19:4)", "سورة الروم، الآيات 1-5", "(سورة لقمان، الآية 13)",
           "الآية 3 من سورة النساء", "(لقمان: 17)", "[الأعراف: 81]"
  Hadith:  "سنن ابن ماجه #2568", "حديث البخاري (5885)", "صحيح مسلم رقم 334", "الترمذي 3194"

Arabic-Indic digits are accepted. A bare surah name followed by a number is NOT treated as a
citation unless it has the "سورة" prefix or the bracketed "(name: n)" form, because many surah
names are ordinary words or personal names (النساء, مريم, محمد, يوسف). "مسلم" alone is likewise
not matched; "صحيح مسلم" is required, mirroring the English rule.
"""

from __future__ import annotations

import json
import re
import unicodedata
from functools import lru_cache
from pathlib import Path

from src.utils.text_normalize import ARABIC_DIACRITICS

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
QURAN_JSONL = REPO_ROOT / "data" / "corpus" / "quran.jsonl"

_DIGITS = str.maketrans("٠١٢٣٤٥٦٧٨٩۰۱۲۳۴۵۶۷۸۹", "01234567890123456789")
_DIAC = r"[ً-ْٰـ]*"  # optional diacritics/tatweel between letters
_ALEF = "اأإآٱ"
_NON_LETTER = re.compile(r"[^ء-ي\s]")


def ascii_digits(text: str) -> str:
    """Length-preserving conversion of Arabic-Indic digits, so regex spans stay valid."""
    return text.translate(_DIGITS)


def normalize_arabic_loose(text: str) -> str:
    """Matching-only form: no diacritics, unified alef/ya forms, letters and spaces only."""
    if not text:
        return ""
    t = unicodedata.normalize("NFC", text)
    t = ARABIC_DIACRITICS.sub("", t).replace("ـ", "")
    t = re.sub(f"[{_ALEF}]", "ا", t).replace("ى", "ي")
    t = _NON_LETTER.sub(" ", t)
    return re.sub(r"\s+", " ", t).strip()


def _letter_pattern(name: str) -> str:
    out = []
    for ch in name:
        if ch in _ALEF:
            out.append(f"[{_ALEF}]")
        elif ch == " ":
            out.append(r"\s+")
            continue
        elif ch in "يى":
            out.append("[يى]")
        elif ch in "هة":
            out.append("[هة]")
        else:
            out.append(re.escape(ch))
        out.append(_DIAC)
    return "".join(out)


@lru_cache(maxsize=1)
def _surah_names() -> dict[str, int]:
    names: dict[str, int] = {}
    with QURAN_JSONL.open(encoding="utf-8") as f:
        for line in f:
            rec = json.loads(line)
            names.setdefault(normalize_arabic_loose(rec["surah_name"]), rec["surah_id"])
    return names


@lru_cache(maxsize=1)
def _quran_res() -> list[tuple[str, re.Pattern]]:
    names = sorted(_surah_names(), key=len, reverse=True)
    name = "(?:ال)?(?P<name>" + "|".join(_letter_pattern(n) for n in names) + ")"  # tolerate a doubled article ("اللّقمان")
    ayah_word = rf"(?:ال)?[{_ALEF}]ي(?:ة|ات)"
    rng = r"(?:(?P<s>\d{1,3})\s*:\s*)?(?P<a>\d{1,3})(?!\d)(?:\s*[-–]\s*(?P<b>\d{1,3}))?"  # optional "2:" surah prefix
    return [
        # سورة مريم (19:4) / سورة الواقعة (56:27-40)
        ("pair", re.compile(rf"سورة\s+{name}\s*[\(\[]\s*(?P<x>\d{{1,3}})\s*:\s*(?P<y>\d{{1,3}})(?:\s*[-–]\s*(?P<b>\d{{1,3}}))?")),
        # سورة لقمان، الآية 13 / سورة الروم، الآيات 1-5 / سورة البقرة آية رقم 255
        ("single", re.compile(rf"سورة\s+{name}\s*[،,:]?\s*{ayah_word}\s*(?:رقم\s*)?{rng}")),
        # الآية 3 من سورة النساء
        ("single", re.compile(rf"{ayah_word}\s*(?:رقم\s*)?{rng}\s*من\s+سورة\s+{name}")),
        # (لقمان: 17) / [الأعراف: 81] -- brackets required when the سورة prefix is absent
        ("single", re.compile(rf"[\(\[]\s*(?:سورة\s+)?{name}\s*[:،]\s*{rng}\s*[\)\]]")),
    ]


def find_quran_citations(text: str) -> list[dict]:
    """Arabic-form Qur'an citations: {citation_raw, surah_id, surah_name_raw, ayah_id, ayah_end, span}."""
    t = ascii_digits(text)
    found: list[dict] = []
    spans: list[tuple[int, int]] = []
    for kind, regex in _quran_res():
        for m in regex.finditer(t):
            span = m.span()
            if any(s[0] < span[1] and span[0] < s[1] for s in spans):
                continue
            surah_id = _surah_names()[normalize_arabic_loose(m.group("name"))]
            if kind == "pair":
                x, y = int(m.group("x")), int(m.group("y"))
                if x != surah_id:
                    continue  # surah name and number disagree -- do not guess which is meant
                ayah = y
            else:
                if m.group("s") and int(m.group("s")) != surah_id:
                    continue
                ayah = int(m.group("a"))
            end = int(m.group("b")) if m.group("b") else None
            spans.append(span)
            found.append({"citation_raw": text[span[0]:span[1]], "surah_id": surah_id,
                          "surah_name_raw": m.group("name"), "ayah_id": ayah,
                          "ayah_end": end if end and end > ayah else None, "span": span})
    return found


_HADITH_PATTERNS: list[tuple[str, str]] = [
    ("bukhari", "البخاري"),
    ("muslim", "صحيح مسلم"),  # bare "مسلم" deliberately not matched
    ("abudawud", "أبي داود|أبو داود|ابي داود|ابو داود|أبي داوود|أبو داوود"),
    ("tirmidhi", "الترمذي"),
    ("nasai", "النسائي"),
    ("ibnmajah", "ابن ماجه|ابن ماجة"),
]
_HADITH_RES = [
    (key, re.compile("(?:" + "|".join(_letter_pattern(a) for a in alts.split("|")) + r")[^\d\n]{0,12}?(\d{1,5})(?!\d)"))
    for key, alts in _HADITH_PATTERNS
]


def find_hadith_citations(text: str) -> list[dict]:
    """Arabic-form hadith citations: {citation_raw, collection_key, hadith_number, span}."""
    t = ascii_digits(text)
    found: list[dict] = []
    spans: list[tuple[int, int]] = []
    for key, regex in _HADITH_RES:
        for m in regex.finditer(t):
            span = m.span()
            if any(s[0] < span[1] and span[0] < s[1] for s in spans):
                continue
            spans.append(span)
            found.append({"citation_raw": text[span[0]:span[1]], "collection_key": key,
                          "hadith_number": int(m.group(1)), "span": span})
    return found


_AR_QUOTE_RE = re.compile(r"[\"“]([^\"”\n]{4,600})[\"”]|«([^»\n]{4,600})»|﴿([^﴾\n]{4,600})﴾|\{([^}\n]{4,600})\}")


@lru_cache(maxsize=64)
def _all_citation_spans(text: str) -> tuple[tuple[int, int], ...]:
    return tuple(c["span"] for c in find_quran_citations(text) + find_hadith_citations(text))


def extract_nearby_arabic_quote(text: str, span: tuple[int, int], window: int = 300) -> str | None:
    """The Arabic-script quotation that belongs to a citation, or None if that is unclear.

    Recognises "...", «...», ﴿...﴾ and {...}. Stricter than text_normalize.extract_nearby_quote,
    because real T15/T16 Arabic answers are mostly citation-headed lists, where plain
    nearest-by-distance pairing attached each quote to the NEXT list item's citation and
    produced false MISQUOTED flags on correct verses:
      * a citation followed by a colon ("سورة الدخان (44:43):") takes the first quote after it;
      * a citation that directly follows a closing quote mark takes that preceding quote;
      * otherwise the nearest quote is used, unless a blank line separates it from the citation;
      * in every case the quote is rejected if another citation lies between the two, if it has
        fewer than 8 Arabic letters, or if the citation is the last thing in the answer (its
        number may be truncated by the token limit). No quote means an existence-only check.
    """
    if span[1] == len(text):
        return None  # reference number runs into the end of the answer and may be cut short
    quotes = []
    for m in _AR_QUOTE_RE.finditer(text):
        q = next(g for g in m.groups() if g is not None).strip()
        if len(re.findall(r"[\u0621-\u064A]", q)) >= 8:
            quotes.append((m.span(), q))
    after = [(qs[0] - span[1], qs, q) for qs, q in quotes if qs[0] >= span[1]]
    before = [(span[0] - qs[1], qs, q) for qs, q in quotes if qs[1] <= span[0]]
    nearest_fallback = False
    if re.match(r"[\)\]\*\s]*[:：]", text[span[1]:span[1] + 8]):
        candidates = sorted(after)[:1]
    elif re.search(r"[\"”»﴾}][\*\s]*[\(\[]?\s*$", text[max(0, span[0] - 8):span[0]]):
        candidates = sorted(before)[:1]
    else:
        candidates = sorted(after + before)[:1]
        nearest_fallback = True
    if not candidates or candidates[0][0] > window:
        return None
    _, qs, quote = candidates[0]
    lo, hi = (span[1], qs[0]) if qs[0] >= span[1] else (qs[1], span[0])
    if nearest_fallback and "\n\n" in text[lo:hi]:
        return None  # a paragraph break separates them -- the quote belongs to other prose
    if any(lo <= o[0] and o[1] <= hi for o in _all_citation_spans(text) if o != span):
        return None
    return quote
