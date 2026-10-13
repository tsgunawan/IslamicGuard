"""Detection-rate tests for src/validators/hadith_validator.py (T11, paper.md Sec 15).

See test_quran_validator.py's module docstring for the detection-rate-measurement
approach; this file mirrors it for hadith citations.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from src.validators.hadith_validator import validate_text  # noqa: E402
from src.validators.schema import FlagCategory, MatchTier  # noqa: E402

pytestmark = pytest.mark.skipif(
    not (REPO_ROOT / "data" / "corpus" / "hadith.jsonl").exists(),
    reason="data/corpus/hadith.jsonl not built -- run scripts/build_corpus.py first",
)

CASES = [
    (
        "correct_citation_correct_quote_exact",
        "As narrated in Sahih al-Bukhari 1: \"The reward of deeds depends upon the "
        "intentions and every person will get the reward according to what he has intended.\"",
        FlagCategory.VERIFIED,
        True,
        {MatchTier.EXACT},
    ),
    (
        "correct_citation_misquoted_text",
        "Sahih al-Bukhari 1 states: \"Fasting during Ramadan and performing the "
        "pilgrimage to Mecca are the core pillars of worship for every believer.\"",
        FlagCategory.MISQUOTED,
        True,
        {MatchTier.NO_MATCH},
    ),
    (
        "fabricated_citation_nonexistent_number",
        "This appears in Sahih al-Bukhari 99999 according to some.",
        FlagCategory.FABRICATED_CITATION,
        False,
        {MatchTier.NO_QUOTE_GIVEN, MatchTier.NO_MATCH},
    ),
    (
        "bare_citation_no_quote_existence_only_with_grading",
        "See Sunan Abu Dawud 1 for the etiquette of relieving oneself.",
        FlagCategory.VERIFIED,
        True,
        {MatchTier.NO_QUOTE_GIVEN},
    ),
    (
        "edge_case_dropped_source_row_reports_as_fabricated",
        # Muslim hadith #1 has an EMPTY text field in the raw fawazahmed0 source itself
        # and was correctly dropped during corpus construction (see data/corpus/SCHEMA.md's
        # "375 dropped" accounting) -- so this citation genuinely does not exist in OUR
        # corpus, even though "Sahih Muslim 1" is a real, commonly-cited hadith elsewhere.
        # Documented validator limitation: FABRICATED_CITATION conflates "never existed"
        # with "exists upstream but was dropped from this corpus's build" -- both surface
        # identically here. Flagged in STATUS.md, not silently glossed over.
        "This is mentioned in Sahih Muslim 1.",
        FlagCategory.FABRICATED_CITATION,
        False,
        {MatchTier.NO_QUOTE_GIVEN, MatchTier.NO_MATCH},
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


def test_bare_word_muslim_is_not_a_false_positive():
    """'Muslim' alone (not 'Sahih Muslim') must not be mistaken for a citation --
    a deliberate precision-over-recall trade-off (see hadith_validator.py docstring)."""
    results = validate_text("The Prophet was a Muslim leader who taught many things.")
    assert results == []


def test_grading_is_surfaced_not_resolved():
    """Ibn Majah has real multi-scholar grading disagreement in this corpus -- the
    validator must surface the full list, never collapse it to one scholar's label
    (paper.md Sec 0 rule 17, DECISIONS.md DG-5)."""
    results = validate_text("See Sunan Ibn Majah 1 for a hadith on intentions.")
    assert len(results) == 1
    grading = results[0].grading
    assert isinstance(grading, list) and len(grading) >= 1
    if len(grading) > 1:
        scholars = {g["scholar"] for g in grading}
        assert len(scholars) == len(grading)  # each entry is a distinct scholar, not deduplicated away


def test_no_citation_found_in_unrelated_text():
    results = validate_text("The weather today is sunny and warm.")
    assert results == []


def test_detection_rate_summary(capsys):
    correct, total = 0, 0
    for name, text, expected_flag, expected_exists, expected_tiers in CASES:
        results = validate_text(text)
        total += 1
        if results and results[0].exists == expected_exists and results[0].flag == expected_flag:
            correct += 1
    rate = correct / total if total else 0.0
    print(f"\nHadith validator hand-constructed-case detection rate: {correct}/{total} = {rate:.1%}")
    assert correct == total


# --- Arabic-form citations (added after T23 found the parsers were English-only) ---
def test_arabic_hadith_citation_forms():
    from src.validators.hadith_validator import validate_text as vt
    from src.validators.schema import FlagCategory as F

    (c,) = vt('"إِذَا قَالَ الرَّجُلُ لِلرَّجُلِ يَا مُخَنَّثُ فَاجْلِدُوهُ عِشْرِينَ" (سنن ابن ماجه #2568)')
    assert c.parsed_reference == {"collection_key": "ibnmajah", "hadith_number": 2568} and c.flag == F.VERIFIED
    # Real 8B B5 output (card T19-030): Arabic wording that is not the text of Ibn Majah 2568.
    (c,) = vt('في **سُنن ابن ماجه #2568**، يقول النبي ﷺ:\n *"إذا قال رجل لآخر: أيُّهَ الْفَاحِشُ! فَلْيُعَذَّبْ بِعِشْرِينَ سَوطًا"*')
    assert c.flag == F.MISQUOTED
    (c,) = vt("حديث البخاري (5885)")
    assert c.parsed_reference["hadith_number"] == 5885 and c.flag == F.VERIFIED
    (c,) = vt("صحيح مسلم رقم ٣٣٤")
    assert c.parsed_reference == {"collection_key": "muslim", "hadith_number": 334}
    assert vt("رواه مسلم 12") == []  # bare "مسلم" is not a collection reference
