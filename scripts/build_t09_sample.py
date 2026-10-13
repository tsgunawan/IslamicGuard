"""Build a small, deterministic, stratified sample for T09 pipeline validation.

NOT the pilot experiment (that's T14) and NOT the final benchmark. This exists only to prove
the B0/B1 generation pipeline works end-to-end across all three models, in both English and
Arabic, over a couple of question types. Every item traces back to an already-acquired T06
dataset -- nothing here is synthesized.

Usage:
    python scripts/build_t09_sample.py
Writes: data/benchmarks/t09_pipeline_sample.jsonl
"""

from __future__ import annotations

import argparse
import csv
import json
import random
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
RAW = REPO_ROOT / "data" / "raw"
DEFAULT_OUT = REPO_ROOT / "data" / "benchmarks" / "t09_pipeline_sample.jsonl"

SEED = 42


def load_faithqa(lang: str) -> list[dict]:
    path = RAW / "IslamicFaithQA" / lang / "dataset_with_difficulty_clean_updated.jsonl"
    items = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            items.append(json.loads(line))
    return items


def load_fiqhqa(lang: str) -> list[dict]:
    label = "English" if lang == "english" else "Arabic"
    path = RAW / "FiqhQA" / f"FiqhQA - {label}.csv"
    with path.open(encoding="utf-8") as f:
        return list(csv.DictReader(f))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--out", type=Path, default=DEFAULT_OUT,
        help="Output path. Defaults to the original T09 sample path -- pass a different path "
             "(e.g. for T13) rather than overwriting it, since already-committed runs "
             "(T09/T10/T11/T12) reference the original file's exact content.",
    )
    args = parser.parse_args()
    out_path = args.out
    rng = random.Random(SEED)

    faithqa_en = load_faithqa("english")
    faithqa_ar = load_faithqa("arabic")
    # A handful of rows in the raw Arabic file are missing `id`/`question`/`gold_answer`
    # entirely (a pre-existing data-quality issue in the source, not introduced here) --
    # skip those defensively for this sample-pulling convenience script (not the corpus
    # builder; T07's stricter no-silent-dropping accounting doesn't apply to this file).
    malformed_ar_rows = sum(1 for r in faithqa_ar if "id" not in r)
    if malformed_ar_rows:
        print(f"note: {malformed_ar_rows}/{len(faithqa_ar)} raw IslamicFaithQA Arabic rows "
              f"lack an 'id' field and are skipped for id-lookup purposes")
    faithqa_ar_by_id = {r["id"]: r for r in faithqa_ar if "id" in r}

    fiqhqa_en = load_fiqhqa("english")
    fiqhqa_ar = load_fiqhqa("arabic")

    sample = []

    # 5 IslamicFaithQA English items, one per distinct category where possible.
    #
    # BUG FIX (found during T13, paper.md HIGH-reasoning validators task): the source
    # dataset's own `id` field (e.g. "MIZAN-002") is NOT a unique key -- it is reused across
    # dozens of unrelated questions in different categories throughout the ~3,808-row file
    # (verified directly: "MIZAN-002" alone labels 17+ distinct questions spanning categories
    # from "Qur'anic Stories" to "Islamic Jurisprudence"). The original code used `item['id']`
    # directly as the item_id suffix, so two picks that happened to share a source `id` (easy,
    # since dedup here is by *category*, not by `id`) collided into one item_id -- this is what
    # produced `t09_pipeline_sample.jsonl`'s known duplicate (`faithqa_MIZAN-002_en`, flagged in
    # T11/T12). Fixed by keying on the row's own index instead (mirroring the FiqhQA half of
    # this script below, which already did this correctly) -- an index into a fixed list is
    # always unique, unlike this dataset's `id` field.
    seen_categories: set[str] = set()
    en_faith_candidates = list(enumerate(faithqa_en))
    rng.shuffle(en_faith_candidates)
    picked_faith_en = []
    for idx, item in en_faith_candidates:
        if item["category"] not in seen_categories:
            picked_faith_en.append((idx, item))
            seen_categories.add(item["category"])
        if len(picked_faith_en) == 5:
            break
    for idx, item in picked_faith_en:
        sample.append(
            {
                "item_id": f"faithqa_row{idx}_en",
                "language": "en",
                "query": item["question"],
                "source_dataset": "IslamicFaithQA",
                "source_category": item["category"],
                "gold_answer_reference": item["gold_answer"],
            }
        )

    # 2 of those same items in Arabic (row-aligned by `id`), for a same-question EN/AR pair.
    for idx, item in picked_faith_en[:2]:
        ar_item = faithqa_ar_by_id.get(item["id"])
        if ar_item is None:
            continue
        sample.append(
            {
                "item_id": f"faithqa_row{idx}_ar",
                "language": "ar",
                "query": ar_item["question"],
                "source_dataset": "IslamicFaithQA",
                "source_category": ar_item["category"],
                "gold_answer_reference": ar_item["gold_answer"],
            }
        )

    # 5 FiqhQA English items, spread across distinct categories.
    seen_fiqh_categories: set[str] = set()
    fiqh_en_candidates = list(enumerate(fiqhqa_en))
    rng.shuffle(fiqh_en_candidates)
    picked_fiqh_en = []
    for idx, row in fiqh_en_candidates:
        if row["Category"] not in seen_fiqh_categories:
            picked_fiqh_en.append((idx, row))
            seen_fiqh_categories.add(row["Category"])
        if len(picked_fiqh_en) == 5:
            break
    for idx, row in picked_fiqh_en:
        sample.append(
            {
                "item_id": f"fiqhqa_row{idx}_en",
                "language": "en",
                "query": row["question_en"],
                "source_dataset": "FiqhQA",
                "source_category": row["Category"],
                "gold_answer_reference": {
                    "maliki": row["maliki_ans"],
                    "hanafi": row["hanafi_ans"],
                    "shafeii": row["shafeii_ans"],
                    "hanbali": row["hanbali_ans"],
                },
            }
        )

    # 3 of those same rows in Arabic (row-aligned by CSV row index).
    for idx, row in picked_fiqh_en[:3]:
        ar_row = fiqhqa_ar[idx]
        sample.append(
            {
                "item_id": f"fiqhqa_row{idx}_ar",
                "language": "ar",
                "query": ar_row["question_ar"],
                "source_dataset": "FiqhQA",
                "source_category": ar_row["Category"],
                "gold_answer_reference": {
                    "maliki": ar_row["maliki_ans"],
                    "hanafi": ar_row["hanafi_ans"],
                    "shafeii": ar_row["shafeii_ans"],
                    "hanbali": ar_row["hanbali_ans"],
                },
            }
        )

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        for item in sample:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")

    print(f"wrote {len(sample)} items to {out_path}")
    print(f"  en={sum(1 for i in sample if i['language']=='en')} "
          f"ar={sum(1 for i in sample if i['language']=='ar')} "
          f"faithqa={sum(1 for i in sample if i['source_dataset']=='IslamicFaithQA')} "
          f"fiqhqa={sum(1 for i in sample if i['source_dataset']=='FiqhQA')}")


if __name__ == "__main__":
    main()
