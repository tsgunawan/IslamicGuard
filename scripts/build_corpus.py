"""Build the IslamicGuard verified retrieval corpus (paper.md T07).

Reads acquired raw datasets under data/raw/ and DG-1/DG-5-resolved source choices
(see DECISIONS.md) and writes three normalized, provenance-tagged JSONL corpora
under data/corpus/: quran.jsonl, hadith.jsonl, fiqh.jsonl.

Canonical source text is never altered for matching purposes — every record keeps
the untouched original alongside a separately-derived normalized field (paper.md
Sec 18).

Usage:
    python scripts/build_corpus.py
"""

from __future__ import annotations

import csv
import hashlib
import json
import re
import unicodedata
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
RAW = REPO_ROOT / "data" / "raw"
CORPUS = REPO_ROOT / "data" / "corpus"

HADITH_API_BASE = "https://cdn.jsdelivr.net/gh/fawazahmed0/hadith-api@1/editions"
HADITH_API_DIR = RAW / "hadith-api-fawazahmed0"
HADITH_BOOKS = ["bukhari", "muslim", "abudawud", "tirmidhi", "nasai", "ibnmajah"]

ARABIC_DIACRITICS = re.compile(
    "[ً-ْٓ-ٰٟۖ-ۭࣔ-ࣣ࣡-ࣿ]"
)


def normalize_arabic(text: str) -> str:
    """Diacritics-stripped, whitespace-normalized form for fuzzy matching only.

    Never used to replace the canonical field -- paper.md Sec 18 requires the
    canonical sacred text to remain immutable.
    """
    if not text:
        return ""
    t = unicodedata.normalize("NFC", text)
    t = ARABIC_DIACRITICS.sub("", t)
    t = t.replace("ـ", "")  # tatweel/kashida
    t = re.sub(r"\s+", " ", t).strip()
    return t


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def ensure_hadith_api_files() -> None:
    """Fetch the fawazahmed0/hadith-api six-book corpus if not already present."""
    import urllib.request

    HADITH_API_DIR.mkdir(parents=True, exist_ok=True)
    targets = [f"{lang}-{book}" for lang in ("eng", "ara") for book in HADITH_BOOKS]
    targets.append("editions")
    for name in targets:
        dest = HADITH_API_DIR / f"{name}.json"
        if dest.exists() and dest.stat().st_size > 0:
            continue
        url = f"{HADITH_API_BASE}/{name}.json" if name != "editions" else (
            "https://cdn.jsdelivr.net/gh/fawazahmed0/hadith-api@1/editions.json"
        )
        print(f"fetching {url} -> {dest}")
        with urllib.request.urlopen(url, timeout=60) as resp:
            dest.write_bytes(resp.read())


# ---------------------------------------------------------------------------
# Qur'an layer
# ---------------------------------------------------------------------------

def build_quran() -> dict[str, Any]:
    src = RAW / "islamiceval_subtask1" / "Quran" / "quranic_verses.json"
    ayat = json.loads(src.read_text(encoding="utf-8"))
    source_sha = sha256_of(src)

    dropped = 0
    out_path = CORPUS / "quran.jsonl"
    with out_path.open("w", encoding="utf-8") as f:
        for a in ayat:
            surah_id = a.get("surah_id")
            ayah_id = a.get("ayah_id")
            text = a.get("ayah_text")
            if surah_id is None or ayah_id is None or not text:
                dropped += 1
                continue
            record = {
                "id": f"quran:{surah_id}:{ayah_id}",
                "surah_id": surah_id,
                "surah_name": a.get("surah_name"),
                "ayah_id": ayah_id,
                "text_ar": text,
                "text_ar_normalized": normalize_arabic(text),
                "provenance": {
                    "dataset": "islamiceval_subtask1 (Mubarak et al. 2025, IslamicEval 2025 "
                                "Subtask 1 companion repo)",
                    "source_file": "Quran/quranic_verses.json",
                    "source_git_commit": "256e2d2d007ca5cde0f2dea6b89a45a77ee59476",
                    "source_sha256": source_sha,
                    "license": "Apache-2.0",
                },
            }
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    return {"total": len(ayat), "written": len(ayat) - dropped, "dropped": dropped,
            "expected_total": 6236, "path": str(out_path)}


# ---------------------------------------------------------------------------
# Hadith layer (DG-5 = Option B: fawazahmed0/hadith-api, six-book canon,
# multi-scholar grading preserved)
# ---------------------------------------------------------------------------

def _load_hadith_json(name: str) -> dict:
    return json.loads((HADITH_API_DIR / f"{name}.json").read_text(encoding="utf-8"))


def build_hadith() -> dict[str, Any]:
    ensure_hadith_api_files()

    islamiceval_src = RAW / "islamiceval_subtask1" / "Hadith" / "six_hadith_books.json"
    islamiceval_counts_by_id: dict[int, int] = {}
    if islamiceval_src.exists():
        ie = json.loads(islamiceval_src.read_text(encoding="utf-8"))
        for row in ie:
            book_id = int(row.get("BookID"))
            islamiceval_counts_by_id[book_id] = islamiceval_counts_by_id.get(book_id, 0) + 1
    # BookID convention confirmed in data/raw/islamiceval_subtask1/DATASET_CARD.md
    islamiceval_book_id = {"bukhari": 1, "muslim": 2, "abudawud": 3, "tirmidhi": 4,
                            "nasai": 5, "ibnmajah": 6}

    out_path = CORPUS / "hadith.jsonl"
    total_written = 0
    total_dropped = 0
    per_book_counts: dict[str, int] = {}
    cross_check: dict[str, Any] = {}

    with out_path.open("w", encoding="utf-8") as f:
        for book in HADITH_BOOKS:
            eng = _load_hadith_json(f"eng-{book}")
            ara = _load_hadith_json(f"ara-{book}")
            eng_sha = sha256_of(HADITH_API_DIR / f"eng-{book}.json")
            ara_sha = sha256_of(HADITH_API_DIR / f"ara-{book}.json")

            book_name = eng["metadata"]["name"]
            sections = eng["metadata"].get("sections", {})

            ara_by_num = {h["hadithnumber"]: h for h in ara["hadiths"]}

            book_written = 0
            for h in eng["hadiths"]:
                num = h.get("hadithnumber")
                text_en = h.get("text")
                if num is None or not text_en:
                    total_dropped += 1
                    continue
                ara_h = ara_by_num.get(num)
                text_ar = ara_h.get("text") if ara_h else None

                grades = h.get("grades") or []
                if grades:
                    grading = [{"scholar": g.get("name"), "grade": g.get("grade")} for g in grades]
                else:
                    grading = "collection-authenticated (no individual grading in source)"

                section_id = str(h.get("reference", {}).get("book"))
                record = {
                    "id": f"hadith:{book}:{num}",
                    "collection": book_name,
                    "collection_key": book,
                    "book_section": sections.get(section_id, section_id),
                    "hadith_number": num,
                    "arabic_number": h.get("arabicnumber"),
                    "text_ar": text_ar,
                    "text_ar_normalized": normalize_arabic(text_ar) if text_ar else None,
                    "text_en": text_en,
                    "translator": "unknown",
                    "grading": grading,
                    "provenance": {
                        "dataset": "fawazahmed0/hadith-api",
                        "source_files": [f"eng-{book}.json", f"ara-{book}.json"],
                        "source_sha256": {f"eng-{book}.json": eng_sha, f"ara-{book}.json": ara_sha},
                        "license": "Unlicense",
                    },
                }
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
                book_written += 1
                total_written += 1

            per_book_counts[book] = book_written
            cross_check[book] = {
                "fawazahmed0_eng_count": len(eng["hadiths"]),
                "fawazahmed0_ara_count": len(ara["hadiths"]),
                "written": book_written,
                "islamiceval_bundle_count": islamiceval_counts_by_id.get(
                    islamiceval_book_id[book]
                ),
            }

    return {
        "total_written": total_written,
        "dropped": total_dropped,
        "per_book": per_book_counts,
        "cross_check_vs_islamiceval_bundle": cross_check,
        "path": str(out_path),
    }


# ---------------------------------------------------------------------------
# Fiqh / madhhab layer (DG-1 = Option B: narrow 4-madhhab layer, bounded topic
# set). Source: FiqhQA (Atif et al. 2025) -- rulings manually extracted from the
# Kuwaiti Fiqh Encyclopedia, QA pairs GPT-4o-generated + native-speaker reviewed.
# See data/corpus/FIQH_LAYER_NOTES.md for the honesty caveat on provenance depth.
# ---------------------------------------------------------------------------

MADHHABS = ["hanafi", "maliki", "shafeii", "hanbali"]


def build_fiqh() -> dict[str, Any]:
    en_path = RAW / "FiqhQA" / "FiqhQA - English.csv"
    ar_path = RAW / "FiqhQA" / "FiqhQA - Arabic.csv"
    en_sha = sha256_of(en_path)
    ar_sha = sha256_of(ar_path) if ar_path.exists() else None

    with en_path.open(newline="", encoding="utf-8") as f:
        en_rows = list(csv.DictReader(f))

    ar_rows_by_title: dict[str, dict] = {}
    if ar_path.exists():
        with ar_path.open(newline="", encoding="utf-8") as f:
            for r in csv.DictReader(f):
                ar_rows_by_title[r.get("Title_original", "")] = r

    out_path = CORPUS / "fiqh.jsonl"
    written = 0
    dropped = 0
    categories: set[str] = set()

    with out_path.open("w", encoding="utf-8") as f:
        for i, row in enumerate(en_rows):
            title = row.get("Title_original")
            statement = row.get("statement_original")
            if not title or not statement:
                dropped += 1
                continue
            categories.add(row.get("Category", ""))
            ar_row = ar_rows_by_title.get(title, {})

            positions = []
            for m in MADHHABS:
                ans = row.get(f"{m}_ans")
                if ans:
                    positions.append({
                        "madhhab": m,
                        "position_en": ans,
                        "position_ar": ar_row.get(f"{m}_ans") if ar_row else None,
                    })

            record = {
                "id": f"fiqh:{i}",
                "category": row.get("Category"),
                "title_ar": title,
                "statement_ar": statement,
                "statement_ar_normalized": normalize_arabic(statement),
                "title_en": row.get("title_en"),
                "statement_en": row.get("statement_en"),
                "agreement": row.get("Agreement"),
                "question_en": row.get("question_en"),
                "question_ar": ar_row.get("question_ar") if ar_row else None,
                "madhhab_positions": positions,
                "provenance": {
                    "dataset": "FiqhQA (Atif et al., 2025)",
                    "primary_source": "Kuwaiti Fiqh Encyclopedia (الموسوعة "
                                       "الفقهية الكويتية), "
                                       "per the origin paper's Dataset Construction section",
                    "content_generation_note": "statement_original/Title_original are "
                                                "manually extracted from the encyclopedia; "
                                                "per-madhhab answer text is GPT-4o-generated "
                                                "from the extracted ruling, native-speaker "
                                                "reviewed -- NOT a verbatim primary-source "
                                                "quotation. See FIQH_LAYER_NOTES.md.",
                    "source_files": ["FiqhQA - English.csv", "FiqhQA - Arabic.csv"],
                    "source_sha256": {"FiqhQA - English.csv": en_sha,
                                       "FiqhQA - Arabic.csv": ar_sha},
                    "license": "MIT",
                },
            }
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
            written += 1

    return {"written": written, "dropped": dropped, "categories": sorted(categories),
            "path": str(out_path)}


def main() -> None:
    CORPUS.mkdir(parents=True, exist_ok=True)
    print("=== Qur'an layer ===")
    q = build_quran()
    print(json.dumps(q, indent=2))

    print("=== Hadith layer ===")
    h = build_hadith()
    print(json.dumps(h, indent=2))

    print("=== Fiqh layer ===")
    fq = build_fiqh()
    print(json.dumps(fq, indent=2))


if __name__ == "__main__":
    main()
