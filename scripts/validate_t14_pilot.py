"""T14 pilot -- validate schema/logging integrity and metric calculability across B0-B5.

Actually re-parses every JSON/JSONL file in each run directory (not just checks existence) and
computes whatever paper.md §12 metrics are currently implementable given what's built through
T13, confirming none error out or produce NaN/undefined on this pilot sample. Prints a report;
does not modify any run directory.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
RUNS_DIR = REPO_ROOT / "runs"

REQUIRED_FILES = [
    "config.yaml", "environment.txt", "model_info.json", "git_commit.txt",
    "prompts.jsonl", "retrieval.jsonl", "responses.jsonl", "guardrail_traces.jsonl",
    "metrics.json", "timing.json", "run.log",
]

RUN_DIRS = {
    "B0": "20260920-0400_Qwen__Qwen3-8B_B0_t13sample_s42",
    "B1": "20260920-0407_Qwen__Qwen3-8B_B1_t13sample_s42",
    "B2": "20260920-0411_Qwen__Qwen3-8B_B2_t14pilot_s42",
    "B3": "20260920-0411_Qwen__Qwen3-8B_B3_t14pilot_s42",
    "B4": "20260920-0411_Qwen__Qwen3-8B_B4_t14pilot_s42",
    "B5": "20260920-0331_Qwen__Qwen3-8B_B5_t13sample_s42",
}


def parse_jsonl(path: Path) -> list[dict]:
    text = path.read_text(encoding="utf-8")
    if not text.strip():
        return []
    return [json.loads(line) for line in text.splitlines() if line.strip()]


def main() -> int:
    overall_ok = True
    report_lines = []

    for cond, run_id in RUN_DIRS.items():
        run_dir = RUNS_DIR / run_id
        line = [f"\n=== {cond}: {run_id} ==="]
        if not run_dir.is_dir():
            line.append(f"  MISSING RUN DIR")
            overall_ok = False
            report_lines.extend(line)
            continue

        missing = [f for f in REQUIRED_FILES if not (run_dir / f).exists()]
        if missing:
            line.append(f"  MISSING FILES: {missing}")
            overall_ok = False
        else:
            line.append(f"  all {len(REQUIRED_FILES)} required files present")

        # Actually parse every JSON/JSONL file back.
        try:
            responses = parse_jsonl(run_dir / "responses.jsonl")
            retrieval = parse_jsonl(run_dir / "retrieval.jsonl")
            traces = parse_jsonl(run_dir / "guardrail_traces.jsonl")
            prompts = parse_jsonl(run_dir / "prompts.jsonl")
            metrics = json.loads((run_dir / "metrics.json").read_text(encoding="utf-8"))
            model_info = json.loads((run_dir / "model_info.json").read_text(encoding="utf-8"))
            line.append(
                f"  parsed OK: {len(responses)} responses, {len(retrieval)} retrieval entries, "
                f"{len(prompts)} prompts, {len(traces)} guardrail traces"
            )
        except Exception as exc:
            line.append(f"  PARSE ERROR: {exc!r}")
            overall_ok = False
            report_lines.extend(line)
            continue

        if len(responses) != 15:
            line.append(f"  WARNING: expected 15 items, got {len(responses)}")

        # Metric calculability per condition (whatever's implementable given T09-T13's build state).
        try:
            if cond in ("B0", "B1"):
                lat = [r["latency_ms"] for r in responses]
                tok = [r["completion_tokens"] for r in responses]
                truncated = sum(1 for t in tok if t >= 512)
                line.append(
                    f"  metrics OK: mean_latency={sum(lat)/len(lat):.1f}ms "
                    f"mean_tokens={sum(tok)/len(tok):.1f} truncated_at_cap={truncated}/{len(tok)}"
                )
            elif cond == "B2":
                n_retrieved = [len(r["passages"]) for r in retrieval]
                scores = [p["score"] for r in retrieval for p in r["passages"]]
                line.append(
                    f"  metrics OK: mean_retrieved={sum(n_retrieved)/len(n_retrieved):.2f} "
                    f"mean_score={sum(scores)/len(scores):.4f} (n_scores={len(scores)})"
                )
            elif cond in ("B3", "B4"):
                n_quotation_checks = sum(len(t.get("quotation_checks") or []) for t in traces)
                flagged = sum(1 for t in traces if t.get("guardrail_flags"))
                verdicts = None
                if cond == "B4":
                    all_claims = [c for t in traces for c in (t.get("claims") or [])]
                    verdict_counts: dict[str, int] = {}
                    for c in all_claims:
                        v = c.get("verdict", "MISSING_VERDICT_KEY")
                        verdict_counts[v] = verdict_counts.get(v, 0) + 1
                    verdicts = verdict_counts
                line.append(
                    f"  metrics OK: n_quotation_checks={n_quotation_checks} items_flagged={flagged}/{len(traces)}"
                    + (f" claim_verdicts={verdicts}" if verdicts is not None else "")
                )
            elif cond == "B5":
                actions: dict[str, int] = {}
                risks: dict[str, int] = {}
                for t in traces:
                    actions[t["action"]] = actions.get(t["action"], 0) + 1
                    risks[t["risk_level"]] = risks.get(t["risk_level"], 0) + 1
                line.append(f"  metrics OK: action_distribution={actions} risk_distribution={risks}")
        except Exception as exc:
            line.append(f"  METRIC CALCULATION ERROR: {exc!r}")
            overall_ok = False

        report_lines.extend(line)

    print("\n".join(report_lines))
    print(f"\n=== overall: {'ALL OK' if overall_ok else 'ISSUES FOUND'} ===")
    return 0 if overall_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
