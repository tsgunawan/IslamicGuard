#!/usr/bin/env python
"""Build a held-out retrieval query->gold-record evaluation set (T08) from
already-acquired benchmark data (T06). Per paper.md §18: no silent dropping --
every candidate item that could NOT be given an unambiguous gold link is
counted and reported, not silently discarded.

Sources actually used, and why:
  - Qur'an gold pairs: IslamicEval dev_SubtaskC "WrongAyah" rows. The
    `Correction` column gives the real canonical ayah text that should have
    been cited; matched against data/corpus/quran.jsonl by normalized-text
    containment (same normalize_arabic() used to build the corpus). The
    query is the question's own <Text> field (real user question, extracted
    from dev_SubtaskC.xml).
  - Fiqh gold pairs: data/corpus/fiqh.jsonl's OWN question_en/question_ar
    fields -- each fiqh record already carries the natural-language question
    it answers (that's how FiqhQA was constructed), so the query->gold link
    is exact and direct, not inferred.
  - Hadith gold pairs: INVESTIGATED, not included. IslamicFaithQA's
    gold_answer text sometimes cites "Sahih al-Bukhari (N)" / "Sahih Muslim
    (N)"-style numbers, but spot-checking 4 such citations against
    data/corpus/hadith.jsonl (built from fawazahmed0/hadith-api,
    per DG-5) by both `hadith_number` and `arabic_number` found the cited
    hadith did NOT topically match the corpus record at that number (0/4
    matched) -- the citation-numbering convention IslamicFaithQA's authors
    used is not the same as fawazahmed0's internal numbering. Forcing this
    match would violate paper.md's "do not guess a fuzzy match and call it
    gold" instruction, so no Hadith gold pairs are included in this pass.
    This is a real, reported limitation of T08's evaluation, not an
    oversight -- see the script's printed summary and t08_retrieval_eval.md.
"""

from __future__ import annotations

import csv
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_corpus import normalize_arabic  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[1]
ISLAMICEVAL_C = REPO_ROOT / "data" / "raw" / "islamiceval_subtask1" / "dev_SubtaskC"
CORPUS_DIR = REPO_ROOT / "data" / "corpus"
OUT_PATH = REPO_ROOT / "data" / "benchmarks" / "retrieval_eval_queries.jsonl"

VERSE_NUM_MARKER = re.compile(r"\s*\(\d+\)\s*")


def load_quran_index() -> list[dict]:
    records = []
    with (CORPUS_DIR / "quran.jsonl").open(encoding="utf-8") as f:
        for line in f:
            records.append(json.loads(line))
    return records


def load_subtaskC_questions() -> dict[str, str]:
    """Question_ID -> query text, extracted tolerantly (the XML is not
    well-formed as a whole document -- individual <ID>/<Text> pairs are
    extracted by regex rather than a strict XML parse)."""
    raw = (ISLAMICEVAL_C / "dev_SubtaskC.xml").read_text(encoding="utf-8")
    pairs = re.findall(r"<ID>(.*?)</ID>.*?<Text>(.*?)</Text>", raw, re.DOTALL)
    return {qid.strip(): text.strip() for qid, text in pairs}


def build_quran_pairs() -> tuple[list[dict], int]:
    quran = load_quran_index()
    # index by normalized text substring lookup: build a list and do
    # substring containment search (corpus is small enough, 6236 records).
    questions = load_subtaskC_questions()

    with (ISLAMICEVAL_C / "dev_SubtaskC.tsv").open(encoding="utf-8") as f:
        rows = list(csv.DictReader(f, delimiter="\t"))
    wrong_ayah_rows = [r for r in rows if r["Label"] == "WrongAyah"]

    pairs = []
    dropped = 0
    for row in wrong_ayah_rows:
        qid = row["Question_ID"]
        query = questions.get(qid)
        if not query:
            dropped += 1
            continue
        correction = row["Correction"]
        # Correction may concatenate multiple ayat with trailing "(N)" markers;
        # split into candidate chunks and match each independently.
        chunks = [c.strip() for c in VERSE_NUM_MARKER.split(correction) if c.strip()]
        if not chunks:
            chunks = [correction]
        matched_any = False
        for chunk in chunks:
            norm_chunk = normalize_arabic(chunk)
            if len(norm_chunk) < 8:  # too short to be a reliable unique match
                continue
            gold = None
            for rec in quran:
                if norm_chunk in rec["text_ar_normalized"] or rec["text_ar_normalized"] in norm_chunk:
                    gold = rec
                    break
            if gold is not None:
                pairs.append(
                    {
                        "query": query,
                        "query_lang": "ar",
                        "gold_layer": "quran",
                        "gold_id": gold["id"],
                        "source": "islamiceval_subtaskC",
                        "source_question_id": qid,
                    }
                )
                matched_any = True
        if not matched_any:
            dropped += 1
    return pairs, dropped


def build_fiqh_pairs() -> tuple[list[dict], dict[str, int]]:
    pairs = []
    missing_en = 0
    missing_ar = 0
    total_records = 0
    with (CORPUS_DIR / "fiqh.jsonl").open(encoding="utf-8") as f:
        for line in f:
            total_records += 1
            rec = json.loads(line)
            q_en = rec.get("question_en")
            q_ar = rec.get("question_ar")
            if q_en:
                pairs.append(
                    {
                        "query": q_en,
                        "query_lang": "en",
                        "gold_layer": "fiqh",
                        "gold_id": rec["id"],
                        "source": "fiqhqa_question_en",
                        "source_question_id": rec["id"],
                    }
                )
            else:
                missing_en += 1
            if q_ar:
                pairs.append(
                    {
                        "query": q_ar,
                        "query_lang": "ar",
                        "gold_layer": "fiqh",
                        "gold_id": rec["id"],
                        "source": "fiqhqa_question_ar",
                        "source_question_id": rec["id"],
                    }
                )
            else:
                missing_ar += 1
    return pairs, {
        "total_records": total_records,
        "missing_question_en": missing_en,
        "missing_question_ar": missing_ar,
    }


def main() -> None:
    quran_pairs, quran_dropped = build_quran_pairs()
    fiqh_pairs, fiqh_stats = build_fiqh_pairs()

    all_pairs = quran_pairs + fiqh_pairs
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUT_PATH.open("w", encoding="utf-8") as f:
        for p in all_pairs:
            f.write(json.dumps(p, ensure_ascii=False) + "\n")

    print(f"Qur'an gold pairs: {len(quran_pairs)} written, {quran_dropped} "
          f"dev_SubtaskC WrongAyah rows dropped (no query text or no confident "
          f"normalized-text match found in data/corpus/quran.jsonl)")
    print(f"Fiqh gold pairs: {len(fiqh_pairs)} written from "
          f"{fiqh_stats['total_records']} fiqh.jsonl records "
          f"({fiqh_stats['missing_question_en']} missing question_en, "
          f"{fiqh_stats['missing_question_ar']} missing question_ar -- "
          f"those language-specific pairs are skipped per-record, not the whole record)")
    print(f"Hadith gold pairs: 0 -- investigated and excluded, see this "
          f"script's module docstring for why (numbering-scheme mismatch, "
          f"verified by spot-check, not assumed)")
    print(f"Total: {len(all_pairs)} query->gold pairs written to {OUT_PATH}")


if __name__ == "__main__":
    main()
