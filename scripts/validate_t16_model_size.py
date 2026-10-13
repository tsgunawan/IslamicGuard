"""Validate T16's B0/B2/B5 model-size experiment artifacts.

Unlike the T14 validator, this covers three model sizes on the 41-item T15 benchmark and
checks that each derived B2 view explicitly points to the corresponding completed B5 source.
It only reads run artifacts and exits nonzero on integrity problems.
"""

from __future__ import annotations

import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
RUNS = REPO_ROOT / "runs"
REQUIRED = (
    "config.yaml", "environment.txt", "git_commit.txt", "model_info.json", "prompts.jsonl",
    "responses.jsonl", "retrieval.jsonl", "guardrail_traces.jsonl", "metrics.json",
    "timing.json", "run.log",
)

# The later 32B B5 rerun is canonical because it is the completed run with automated raw GPU
# samples.  The earlier independently completed run remains preserved under runs/.
RUN_IDS = {
    "Qwen3-8B": {
        "B0": "20260920-0426_Qwen__Qwen3-8B_B0_t15_benchmark_s42",
        "B2": "20260920-0800_Qwen__Qwen3-8B_B2_t15benchmark_s42",
        "B5": "20260920-0732_Qwen__Qwen3-8B_B5_t15benchmark_s42",
    },
    "Qwen3-14B-AWQ": {
        "B0": "20260920-0804_Qwen__Qwen3-14B-AWQ_B0_t15_benchmark_s42",
        "B2": "20260920-0840_Qwen__Qwen3-14B-AWQ_B2_t15benchmark_s42",
        "B5": "20260920-0825_Qwen__Qwen3-14B-AWQ_B5_t15benchmark_s42",
    },
    "Qwen3-32B-AWQ": {
        "B0": "20260920-0840_Qwen__Qwen3-32B-AWQ_B0_t15_benchmark_s42",
        "B2": "20260920-2345_Qwen__Qwen3-32B-AWQ_B2_t15benchmark_s42",
        "B5": "20260920-1220_Qwen__Qwen3-32B-AWQ_B5_t15benchmark_s42",
    },
}


def parse_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def validate_run(label: str, condition: str, run_id: str) -> list[str]:
    errors: list[str] = []
    run_dir = RUNS / run_id
    if not run_dir.is_dir():
        return [f"{label}/{condition}: missing directory {run_id}"]
    missing = [name for name in REQUIRED if not (run_dir / name).is_file()]
    if missing:
        errors.append(f"{label}/{condition}: missing files {missing}")
        return errors
    try:
        responses = parse_jsonl(run_dir / "responses.jsonl")
        prompts = parse_jsonl(run_dir / "prompts.jsonl")
        retrieval = parse_jsonl(run_dir / "retrieval.jsonl")
        traces = parse_jsonl(run_dir / "guardrail_traces.jsonl")
        metrics = json.loads((run_dir / "metrics.json").read_text(encoding="utf-8"))
        json.loads((run_dir / "model_info.json").read_text(encoding="utf-8"))
        json.loads((run_dir / "timing.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [f"{label}/{condition}: parse error {exc}"]
    for name, records in (("responses", responses), ("prompts", prompts), ("traces", traces)):
        if len(records) != 41:
            errors.append(f"{label}/{condition}: expected 41 {name}, found {len(records)}")
    if condition in {"B2", "B5"} and len(retrieval) != 41:
        errors.append(f"{label}/{condition}: expected 41 retrieval records, found {len(retrieval)}")
    if metrics.get("n_items") != 41:
        errors.append(f"{label}/{condition}: metrics n_items is {metrics.get('n_items')!r}, not 41")
    if condition == "B2":
        source = metrics.get("derived_from_source_run")
        if not source or not (RUNS / source / "responses.jsonl").is_file():
            errors.append(f"{label}/B2: missing usable B5 derivation source {source!r}")
    if condition == "B5" and not all(trace.get("action") for trace in traces):
        errors.append(f"{label}/B5: one or more guardrail actions are absent")
    return errors


def main() -> int:
    errors: list[str] = []
    for label, conditions in RUN_IDS.items():
        for condition, run_id in conditions.items():
            run_errors = validate_run(label, condition, run_id)
            if run_errors:
                errors.extend(run_errors)
            else:
                print(f"OK {label}/{condition}: {run_id}")
    if errors:
        print("T16 validation failed:")
        print("\n".join(f"- {error}" for error in errors))
        return 1
    print("ALL OK — nine T16 model×condition artifacts are complete and parseable.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
