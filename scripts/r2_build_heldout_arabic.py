"""Revision 2 (Reviewer A #8, Reviewer B #3): build a held-out Arabic question set for testing the
repaired Arabic citation parser on answers it has never seen.

15 questions from the IslamicEval 2025 QH-QA Subtask 2 test split and 15 from the HalluTruthQA-4K
test split (islamicHallucination subset, questions mentioning a verse, surah or hadith). Items that
appear in any existing benchmark or sample file are excluded. Sampling is seeded (42).

Usage: python scripts/r2_build_heldout_arabic.py
"""
from __future__ import annotations

import csv
import json
import random
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data/benchmarks/r2_heldout_arabic.jsonl"
SEED = 42
N_EACH = 15


def used_ids_and_queries():
    ids, queries = set(), set()
    for p in (ROOT / "data/benchmarks").glob("*.jsonl"):
        if p == OUT:
            continue
        for line in p.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            r = json.loads(line)
            for k in ("item_id", "id"):
                if k in r:
                    ids.add(str(r[k]))
            for k in ("query", "question"):
                if k in r:
                    queries.add(str(r[k]).strip())
    return ids, queries


def main():
    rng = random.Random(SEED)
    used_ids, used_q = used_ids_and_queries()

    qh = []
    with open(ROOT / "data/raw/islamiceval_quran_hadith_qa_2025/data/QH-QA-25_Subtask2_ayatec_v1.3_test.tsv",
              encoding="utf-8") as f:
        for row in csv.reader(f, delimiter="\t"):
            if len(row) < 2:
                continue
            item_id = f"qhqa25_test_{row[0].strip()}"
            q = row[1].strip()
            if item_id in used_ids or q in used_q:
                continue
            qh.append({"item_id": item_id, "language": "ar", "query": q,
                       "source_dataset": "IslamicEval 2025 QH-QA Subtask 2 (test)"})

    cite_cue = re.compile(r"آية|الآية|سورة|حديث|قوله تعالى|قال تعالى|النبي")
    ht = []
    for line in (ROOT / "data/raw/HalluTruthQA-4K/test.jsonl").read_text(encoding="utf-8").splitlines():
        r = json.loads(line)
        if not r["id"].startswith("islamicHallucination_"):
            continue
        item_id = f"hallutruthqa_{r['id']}"
        q = r["question"].strip()
        if item_id in used_ids or q in used_q or not cite_cue.search(q):
            continue
        ht.append({"item_id": item_id, "language": "ar", "query": q,
                   "source_dataset": "HalluTruthQA-4K (test split, islamicHallucination subset)"})

    picked = rng.sample(qh, N_EACH) + rng.sample(ht, N_EACH)
    for p in picked:
        p.update({"stratum": "heldout_arabic_parser_check", "source_category": "heldout_r2", "constructed": False})
    OUT.write_text("".join(json.dumps(p, ensure_ascii=False) + "\n" for p in picked), encoding="utf-8")
    print(f"QH-QA candidates {len(qh)}, HalluTruthQA candidates {len(ht)}; wrote {len(picked)} -> {OUT}")


if __name__ == "__main__":
    main()
