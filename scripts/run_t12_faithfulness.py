"""Run claim segmentation + faithfulness checking (T12) against T10's real B2 responses.

Usage:
    python scripts/run_t12_faithfulness.py

Reads every runs/*_B2_*/{responses.jsonl,retrieval.jsonl} pair, segments each response into
claims (src/validators/claim_segmenter.py), checks each claim against that item's actually-
retrieved evidence (src/validators/faithfulness_validator.py, mDeBERTa-v3-base-mnli-xnli),
and writes one JSON line per response to results/error_analysis/t12_faithfulness_on_b2.jsonl.
Prints summary statistics (verdict counts, overall and per model) -- real numbers from this
run, not estimates.
"""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from src.validators.claim_segmenter import segment_claims  # noqa: E402
from src.validators.faithfulness_validator import (  # noqa: E402
    check_claim,
    evidence_texts_from_retrieval_entry,
)

RUNS_DIR = REPO_ROOT / "runs"
OUT_PATH = REPO_ROOT / "results" / "error_analysis" / "t12_faithfulness_on_b2.jsonl"


def _load_jsonl(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def main() -> None:
    b2_dirs = sorted(d for d in RUNS_DIR.iterdir() if d.is_dir() and "_B2_" in d.name)
    if not b2_dirs:
        raise SystemExit(f"No B2 run directories found under {RUNS_DIR}")

    overall_counts: Counter[str] = Counter()
    per_model_counts: dict[str, Counter[str]] = {}
    n_responses = 0
    n_claims_total = 0
    n_responses_with_zero_claims = 0

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUT_PATH.open("w", encoding="utf-8") as out_f:
        for run_dir in b2_dirs:
            responses = _load_jsonl(run_dir / "responses.jsonl")
            retrievals = _load_jsonl(run_dir / "retrieval.jsonl")
            model_id = responses[0]["model_id"] if responses else run_dir.name

            # NOTE: pair by POSITIONAL INDEX, not by item_id dict lookup. T11's real-data
            # sanity check found data/benchmarks/t09_pipeline_sample.jsonl has a duplicate
            # item_id (14 unique ids across 15 rows) -- both responses.jsonl and
            # retrieval.jsonl were written in the same iteration order over that same
            # sample (verified: the two files' item_id sequences are identical), so a
            # dict keyed by item_id would silently collapse the duplicate and mismatch
            # one of the two same-id responses against the wrong retrieval entry.
            if len(responses) != len(retrievals):
                raise ValueError(
                    f"{run_dir.name}: responses.jsonl has {len(responses)} rows but "
                    f"retrieval.jsonl has {len(retrievals)} -- cannot pair positionally."
                )
            for resp, retrieval_entry in zip(responses, retrievals):
                n_responses += 1
                item_id = resp["item_id"]
                if retrieval_entry["item_id"] != item_id:
                    raise ValueError(
                        f"{run_dir.name}: positional mismatch at response item_id={item_id!r} "
                        f"vs retrieval item_id={retrieval_entry['item_id']!r} -- files are not "
                        "in the same order; positional pairing is unsafe here."
                    )
                evidence = evidence_texts_from_retrieval_entry(retrieval_entry) if retrieval_entry else []

                claims = segment_claims(resp["response_text"])
                n_claims_total += len(claims)
                if not claims:
                    n_responses_with_zero_claims += 1

                claim_checks = [check_claim(c.text, evidence) for c in claims]

                per_model_counts.setdefault(model_id, Counter())
                for cc in claim_checks:
                    overall_counts[cc.verdict.value] += 1
                    per_model_counts[model_id][cc.verdict.value] += 1

                out_f.write(
                    json.dumps(
                        {
                            "run_dir": run_dir.name,
                            "model_id": model_id,
                            "item_id": item_id,
                            "n_claims": len(claims),
                            "n_evidence_passages": len(evidence),
                            "claims": [cc.to_dict() for cc in claim_checks],
                        },
                        ensure_ascii=False,
                    )
                    + "\n"
                )

    print(f"Responses processed: {n_responses}")
    print(f"Responses with zero extracted claims: {n_responses_with_zero_claims}")
    print(f"Total claims checked: {n_claims_total}")
    print("\nOverall verdict distribution:")
    for verdict, count in overall_counts.most_common():
        pct = 100.0 * count / n_claims_total if n_claims_total else 0.0
        print(f"  {verdict}: {count} ({pct:.1f}%)")

    print("\nPer-model verdict distribution:")
    for model_id, counts in per_model_counts.items():
        total = sum(counts.values())
        print(f"  {model_id} (n={total} claims):")
        for verdict, count in counts.most_common():
            pct = 100.0 * count / total if total else 0.0
            print(f"    {verdict}: {count} ({pct:.1f}%)")

    print(f"\nWrote {OUT_PATH.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()
