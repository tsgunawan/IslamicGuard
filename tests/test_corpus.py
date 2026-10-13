"""Validation tests for the T07 retrieval corpus (data/corpus/*.jsonl).

Run after `python scripts/build_corpus.py`. Verifies: known reference ayah counts
match public record (canonical text untouched by normalization), Hadith grading
is preserved as multi-scholar data (not collapsed), and every record in every
corpus file carries non-null provenance (paper.md Sec 18: no source-less chunks).
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
CORPUS = REPO_ROOT / "data" / "corpus"


def _read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        pytest.skip(f"{path} not built yet -- run scripts/build_corpus.py first")
    with path.open(encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


@pytest.fixture(scope="module")
def quran_records():
    return _read_jsonl(CORPUS / "quran.jsonl")


@pytest.fixture(scope="module")
def hadith_records():
    return _read_jsonl(CORPUS / "hadith.jsonl")


@pytest.fixture(scope="module")
def fiqh_records():
    return _read_jsonl(CORPUS / "fiqh.jsonl")


# ---------------------------------------------------------------------------
# Qur'an layer
# ---------------------------------------------------------------------------

def test_quran_total_ayah_count(quran_records):
    assert len(quran_records) == 6236


def test_quran_known_surah_ayah_counts(quran_records):
    # Independently well-known, uncontested ayah counts for these surahs.
    counts: dict[int, int] = {}
    for r in quran_records:
        counts[r["surah_id"]] = counts.get(r["surah_id"], 0) + 1
    assert counts[1] == 7    # Al-Fatiha
    assert counts[112] == 4  # Al-Ikhlas
    assert counts[113] == 5  # Al-Falaq
    assert counts[114] == 6  # An-Nas


def test_quran_num_surahs(quran_records):
    assert len({r["surah_id"] for r in quran_records}) == 114


def test_quran_canonical_text_not_normalized_away(quran_records):
    # The canonical field must retain diacritics (a normalized copy is separate).
    bismillah = next(r for r in quran_records if r["surah_id"] == 1 and r["ayah_id"] == 1)
    assert "َ" in bismillah["text_ar"] or "ِ" in bismillah["text_ar"] or \
           "ُ" in bismillah["text_ar"], "canonical text should retain diacritics"
    assert bismillah["text_ar"] != bismillah["text_ar_normalized"]
    assert bismillah["text_ar_normalized"] == "بسم الله الرحمن الرحيم"


def test_quran_every_record_has_provenance(quran_records):
    for r in quran_records:
        assert r.get("provenance", {}).get("source_sha256"), f"missing provenance: {r['id']}"
        assert r["provenance"]["license"]


def test_quran_ids_unique(quran_records):
    ids = [r["id"] for r in quran_records]
    assert len(ids) == len(set(ids))


# ---------------------------------------------------------------------------
# Hadith layer
# ---------------------------------------------------------------------------

def test_hadith_nonzero_and_six_collections(hadith_records):
    assert len(hadith_records) > 30000
    keys = {r["collection_key"] for r in hadith_records}
    assert keys == {"bukhari", "muslim", "abudawud", "tirmidhi", "nasai", "ibnmajah"}


def test_hadith_grading_preserved_multi_scholar_not_collapsed(hadith_records):
    # Ibn Majah hadith #1 is documented (DATASET_CARD.md) to carry 4 scholars' grades.
    h1 = next(r for r in hadith_records
              if r["collection_key"] == "ibnmajah" and r["hadith_number"] == 1)
    assert isinstance(h1["grading"], list)
    assert len(h1["grading"]) == 4
    scholars = {g["scholar"] for g in h1["grading"]}
    assert "Al-Albani" in scholars
    assert all(set(g.keys()) == {"scholar", "grade"} for g in h1["grading"])


def test_hadith_grading_never_silently_collapsed_to_single_label(hadith_records):
    # No record's grading, when a list, should ever be silently reduced to one entry
    # by construction -- spot check a scholar-disagreement case (documented in DATASET_CARD.md).
    h6 = next(r for r in hadith_records
              if r["collection_key"] == "ibnmajah" and r["hadith_number"] == 6)
    grades = {g["grade"] for g in h6["grading"]}
    assert len(grades) > 1, "expected documented scholar disagreement to survive into the corpus"


def test_hadith_bukhari_muslim_marked_collection_authenticated(hadith_records):
    bukhari_sample = [r for r in hadith_records if r["collection_key"] == "bukhari"][:50]
    assert all(
        r["grading"] == "collection-authenticated (no individual grading in source)"
        for r in bukhari_sample
    ), "Bukhari has no individual grading in the source; must not fabricate a grading list"


def test_hadith_translator_attribution_documented_as_unknown(hadith_records):
    sample = hadith_records[0]
    assert sample["translator"] == "unknown"


def test_hadith_canonical_arabic_not_altered(hadith_records):
    h1 = next(r for r in hadith_records
              if r["collection_key"] == "ibnmajah" and r["hadith_number"] == 1)
    assert h1["text_ar"] != h1["text_ar_normalized"]
    assert "َ" in h1["text_ar"] or "ِ" in h1["text_ar"] or "ُ" in h1["text_ar"]


def test_hadith_every_record_has_provenance(hadith_records):
    for r in hadith_records:
        assert r.get("provenance", {}).get("source_sha256"), f"missing provenance: {r['id']}"
        assert r["provenance"]["license"] == "Unlicense"


def test_hadith_ids_unique(hadith_records):
    ids = [r["id"] for r in hadith_records]
    assert len(ids) == len(set(ids))


# ---------------------------------------------------------------------------
# Fiqh layer
# ---------------------------------------------------------------------------

def test_fiqh_record_count(fiqh_records):
    assert len(fiqh_records) == 121


def test_fiqh_bounded_topic_set(fiqh_records):
    categories = {r["category"] for r in fiqh_records}
    assert categories <= {"Prayer", "Purity", "Mariage ", "Fast", "Hajj Omra", "Zakat"}


def test_fiqh_madhhab_field_required_on_every_record(fiqh_records):
    for r in fiqh_records:
        assert r["madhhab_positions"], f"no madhhab positions: {r['id']}"
        madhhabs = {p["madhhab"] for p in r["madhhab_positions"]}
        assert madhhabs <= {"hanafi", "maliki", "shafeii", "hanbali"}


def test_fiqh_content_generation_note_present(fiqh_records):
    # Every record must carry the honesty caveat that madhhab position text is
    # LLM-generated/human-reviewed, not a verbatim primary-source quotation.
    for r in fiqh_records:
        note = r["provenance"]["content_generation_note"]
        assert "GPT-4o-generated" in note


def test_fiqh_every_record_has_provenance(fiqh_records):
    for r in fiqh_records:
        assert r.get("provenance", {}).get("source_sha256")
        assert r["provenance"]["primary_source"]


def test_fiqh_ids_unique(fiqh_records):
    ids = [r["id"] for r in fiqh_records]
    assert len(ids) == len(set(ids))
