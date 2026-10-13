"""Detection-rate tests for src/validators/quran_validator.py (T11, paper.md Sec 15).

Per the T11 acceptance criterion ("known correct/misquoted/fabricated cases are
detected at documented rates"), this file's test functions double as the
detection-rate measurement: each category below is a hand-constructed case with a
known-correct expected flag, run against the real corpus at data/corpus/quran.jsonl
(not a mock), and the actual pass/fail count IS the documented rate -- see the
docstring on `test_detection_rate_summary` for how to read the printed summary.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from src.validators.quran_validator import validate_text  # noqa: E402
from src.validators.schema import FlagCategory, MatchTier  # noqa: E402

pytestmark = pytest.mark.skipif(
    not (REPO_ROOT / "data" / "corpus" / "quran.jsonl").exists(),
    reason="data/corpus/quran.jsonl not built -- run scripts/build_corpus.py first",
)

# (name, text, expected_flag, expected_exists, expected_min_tier_in)
CASES = [
    (
        "correct_citation_correct_quote_exact",
        "The verse states in Qur'an 1:1: \"بسم الله الرحمن الرحيم\" as an opening.",
        FlagCategory.VERIFIED,
        True,
        {MatchTier.EXACT},
    ),
    (
        "correct_citation_correct_quote_via_surah_name",
        "Surah Al-Ikhlas, Ayah 1 says: \"قل هو الله أحد\"",
        FlagCategory.VERIFIED,
        True,
        {MatchTier.EXACT},
    ),
    (
        "correct_citation_misquoted_text",
        # Real ayah 112:1 is "قل هو الله أحد"; this instead quotes 112:2's text
        # ("قل هو الله الصمد") while citing 112:1 -- a realistic misquote pattern
        # (adjacent-ayah confusion), not a garbled string.
        "It is claimed that in Qur'an 112:1 it says: \"قل هو الله الصمد\" which is wrong.",
        FlagCategory.MISQUOTED,
        True,
        {MatchTier.NO_MATCH},
    ),
    (
        "fabricated_citation_nonexistent_surah",
        "This is found in Qur'an 115:1 according to some.",  # only 114 surahs exist
        FlagCategory.FABRICATED_CITATION,
        False,
        {MatchTier.NO_QUOTE_GIVEN, MatchTier.NO_MATCH},
    ),
    (
        "fabricated_citation_nonexistent_ayah",
        "Also Qur'an 2:900 is cited.",  # Al-Baqarah has 286 ayahs, not 900
        FlagCategory.FABRICATED_CITATION,
        False,
        {MatchTier.NO_QUOTE_GIVEN, MatchTier.NO_MATCH},
    ),
    (
        "bare_citation_no_quote_existence_only",
        "See Qur'an 2:255 for the Ayat al-Kursi.",
        FlagCategory.VERIFIED,
        True,
        {MatchTier.NO_QUOTE_GIVEN},
    ),
    (
        "edge_case_english_quote_not_checkable",
        # Corpus has no text_en for Qur'an (see data/corpus/SCHEMA.md) -- an English
        # "quote" cannot be checked against text_ar, so this must NOT be reported as
        # a false NO_MATCH/misquote; it degrades to existence-only.
        "Qur'an 1:1 says \"In the name of Allah\"",
        FlagCategory.VERIFIED,
        True,
        {MatchTier.NO_QUOTE_GIVEN},
    ),
]


@pytest.mark.parametrize("name,text,expected_flag,expected_exists,expected_tiers", CASES, ids=[c[0] for c in CASES])
def test_case(name, text, expected_flag, expected_exists, expected_tiers):
    results = validate_text(text)
    assert len(results) == 1, f"{name}: expected exactly 1 citation found, got {len(results)}: {results}"
    r = results[0]
    assert r.exists == expected_exists, f"{name}: exists={r.exists}, expected {expected_exists}"
    assert r.flag == expected_flag, f"{name}: flag={r.flag}, expected {expected_flag} (full: {r.to_dict()})"
    assert r.match_tier in expected_tiers, f"{name}: tier={r.match_tier}, expected one of {expected_tiers}"


def test_no_citation_found_in_unrelated_text():
    results = validate_text("The weather today is sunny and warm.")
    assert results == []


def test_detection_rate_summary(capsys):
    """Not a pass/fail assertion -- prints the actual per-category detection rate,
    which is what paper.md Sec 15's T11 acceptance criterion asks to be documented.
    """
    correct, total = 0, 0
    for name, text, expected_flag, expected_exists, expected_tiers in CASES:
        results = validate_text(text)
        total += 1
        if results and results[0].exists == expected_exists and results[0].flag == expected_flag:
            correct += 1
    rate = correct / total if total else 0.0
    print(f"\nQur'an validator hand-constructed-case detection rate: {correct}/{total} = {rate:.1%}")
    assert correct == total  # all hand-constructed cases are expected to pass; a regression here is real


# --- Arabic-form citations (added after T23 found the parsers were English-only) ---
AR_CASES = [
    ("ar_surah_ayah_correct_partial_quote",
     'سورة الأنعام، الآية 151:\n> "وَلَا تَقْرَبُوا الْفَوَاحِشَ مَا ظَهَرَ مِنْهَا وَمَا بَطَنَ"', 6, 151, FlagCategory.VERIFIED),
    ("ar_quote_before_citation",
     '"يا بُنَيَّ لَا تُشْرِكْ بِاللَّهِ ۖ إِنَّ الشِّرْكَ لَظُلْمٌ عَظِيمٌ" (سورة لقمان، الآية 13).', 31, 13, FlagCategory.VERIFIED),
    ("ar_ornate_brackets", "﴿قال رب إني وهن العظم مني واشتعل الرأس شيبًا﴾ (سورة مريم، الآية 4).", 19, 4, FlagCategory.VERIFIED),
    ("ar_numeric_pair", "هذا موجود في سورة مريم (19:4)، وهو", 19, 4, FlagCategory.VERIFIED),
    ("ar_ayah_of_surah_indic_digits",
     'الآية ٣ من سورة النساء تقول: "فانكحوا ما طاب لكم من النساء مثنى وثلاث ورباع"', 4, 3, FlagCategory.VERIFIED),
    ("ar_bracketed_name", "كما في قوله تعالى [الأعراف: 81]", 7, 81, FlagCategory.VERIFIED),
    # Real 8B B0 output rated 'major' by all three scholars (card T19-015): invented text.
    ("ar_fabricated_text_real_reference",
     "**سورة التوبة، الآية 120:**\n\n> **{وَإِذْ أَنْذَرْنَاكُمْ فَتَوَلَّى أَكْثَرُكُمْ فَأَتَيْنَاهُمْ بِالْعَذَابِ مُتَتَاعًا}**",
     9, 120, FlagCategory.MISQUOTED),
    ("ar_nonexistent_ayah", "سورة مريم، الآية 400", 19, 400, FlagCategory.FABRICATED_CITATION),
]


@pytest.mark.parametrize("name,text,surah,ayah,flag", AR_CASES, ids=[c[0] for c in AR_CASES])
def test_arabic_citation(name, text, surah, ayah, flag):
    checks = validate_text(text)
    assert len(checks) == 1, f"{name}: expected one citation, got {[c.citation_raw for c in checks]}"
    assert (checks[0].parsed_reference["surah_id"], checks[0].parsed_reference["ayah_id"]) == (surah, ayah)
    assert checks[0].flag == flag


@pytest.mark.parametrize("text", ["تزوج النساء 4 مرات", "قال محمد 3 مرات", "سورة البقرة (1:5)"])
def test_arabic_non_citations_are_not_matched(text):
    """Bare surah-name words and name/number mismatches must not be guessed into citations."""
    assert validate_text(text) == []


def test_arabic_verse_range_matches_quote_inside_range():
    text = 'سورة الروم، الآيات 1-5: "غُلِبَتِ الرُّومُ"'
    (check,) = validate_text(text)
    assert check.parsed_reference["ayah_end"] == 5 and check.flag == FlagCategory.VERIFIED


def test_arabic_citation_headed_list_pairs_each_quote_with_its_own_citation():
    """Real 8B B5 output: three correct verses in a list. Nearest-by-distance pairing shifted
    every quote to the next item's citation and flagged correct verses as misquoted."""
    text = ('- **سورة الدخان (44:43):**  \n  "إِنَّ شَجَرَتَ الزَّقُّومِ"\n\n'
            '- **سورة الواقعة (56:52):**  \n  "لَآكِلُونَ مِنْ شَجَرٍ مِنْ زَقُّومٍ"\n\n'
            '- **سورة الصافات (37:62):**  \n  "أَذَٰلِكَ خَيْرٌ نُزُلًا أَمْ شَجَرَةُ الزَّقُّومِ"\n\nانتهى.')
    checks = validate_text(text)
    assert [c.parsed_reference["surah_id"] for c in checks] == [44, 56, 37]
    assert all(c.flag == FlagCategory.VERIFIED and c.match_tier == MatchTier.EXACT for c in checks)


def test_arabic_surah_prefixed_ayah_number():
    (check,) = validate_text("كما ورد في سورة البقرة، الآية 2:194: \"الشَّهْرُ الْحَرَامُ بِالشَّهْرِ الْحَرَامِ وَالْحُرُمَاتُ قِصَاصٌ\" ثم")
    assert check.parsed_reference["ayah_id"] == 194 and check.flag == FlagCategory.VERIFIED
