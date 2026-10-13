"""Sample real claim-evidence pairs from T12's B2 run for manual calibration labeling.

Stratified sample (seeded) across the three automatic-verdict categories found by
scripts/run_t12_faithfulness.py, so the calibration set can check accuracy within each
category rather than just the majority one. For each sampled claim, includes ALL evidence
passages retrieved for that item (not just the validator's chosen "best" one) so the human
labeler judges independently rather than being anchored to the automatic pick.

Output: data/benchmarks/t12_calibration_candidates.jsonl (UNLABELED -- gold_verdict/
gold_rationale are filled in by hand afterward to produce t12_calibration_set.jsonl).
"""

from __future__ import annotations

import json
import random
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from src.validators.faithfulness_validator import evidence_texts_from_retrieval_entry  # noqa: E402

SEED = 42
N_PER_CATEGORY = 9  # 3 categories * 9 = 27, within the 25-40 range paper.md T12 asks for

IN_PATH = REPO_ROOT / "results" / "error_analysis" / "t12_faithfulness_on_b2.jsonl"
RUNS_DIR = REPO_ROOT / "runs"
OUT_PATH = REPO_ROOT / "data" / "benchmarks" / "t12_calibration_candidates.jsonl"


def _load_jsonl(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def main() -> None:
    records = _load_jsonl(IN_PATH)

    # Rebuild retrieval lookups per run_dir so we can attach ALL evidence passages
    # (not just the automatic validator's chosen best_evidence_record_id) to each candidate.
    retrieval_by_run: dict[str, list[dict]] = {}
    for run_dir_name in {r["run_dir"] for r in records}:
        retrieval_by_run[run_dir_name] = _load_jsonl(RUNS_DIR / run_dir_name / "retrieval.jsonl")

    by_category: dict[str, list[dict]] = {"supported": [], "contradicted": [], "not_addressed_by_evidence": []}
    for rec in records:
        run_dir = rec["run_dir"]
        retrievals = retrieval_by_run[run_dir]
        # run_t12_faithfulness.py wrote one output row per response IN THE SAME ORDER
        # responses.jsonl/retrieval.jsonl were iterated (positionally paired there
        # specifically to handle the known duplicate item_id safely -- see that script's
        # comment) -- so find this record's position among all t12 output rows sharing
        # this run_dir and index into retrievals the same way.
        sibling_rows = [r for r in records if r["run_dir"] == run_dir]
        pos = sibling_rows.index(rec)
        retrieval_entry = retrievals[pos]
        all_evidence = evidence_texts_from_retrieval_entry(retrieval_entry)

        for claim in rec["claims"]:
            if claim["verdict"] not in by_category:
                continue
            by_category[claim["verdict"]].append(
                {
                    "run_dir": run_dir,
                    "model_id": rec["model_id"],
                    "item_id": rec["item_id"],
                    "claim_text": claim["claim_text"],
                    "automatic_verdict": claim["verdict"],
                    "automatic_entailment_prob": claim["entailment_prob"],
                    "automatic_contradiction_prob": claim["contradiction_prob"],
                    "automatic_best_evidence_citation": claim["best_evidence_citation"],
                    "all_evidence_passages": [
                        {"citation": e["citation"], "text": e["text"]} for e in all_evidence
                    ],
                }
            )

    rng = random.Random(SEED)
    sampled: list[dict] = []
    for category, items in by_category.items():
        k = min(N_PER_CATEGORY, len(items))
        sampled.extend(rng.sample(items, k))
        print(f"{category}: sampled {k} of {len(items)} available")

    rng.shuffle(sampled)  # so labeling order doesn't reveal the automatic verdict pattern
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUT_PATH.open("w", encoding="utf-8") as f:
        for i, item in enumerate(sampled):
            item["calibration_id"] = f"cal-{i:03d}"
            f.write(json.dumps(item, ensure_ascii=False) + "\n")

    print(f"\nWrote {len(sampled)} candidates to {OUT_PATH.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()
