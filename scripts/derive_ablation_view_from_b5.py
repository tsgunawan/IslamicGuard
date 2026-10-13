"""T14 pilot helper -- derive B2/B3/B4 ablation "views" from an already-completed B5 run.

Why this is legitimate, not a shortcut that fakes results: B5's own generation step
(src/guardrails/islamicguard_pipeline.py via scripts/run_islamicguard_b5.py) is IDENTICAL to
B2's (same retriever, same prompt template prompts/b2_rag.md, same seed, greedy/do_sample=False
decoding) -- paper.md's ablation design deliberately isolates the guardrail layer's effect on
top of the SAME underlying generation, not a different generation strategy per condition. B5's
guardrail_traces.jsonl already contains the full per-item guard_result (quotation_checks from
T11, claims from T12, madhhab_context + action from T13) computed once. This script re-slices
that single computation into the B2 (nothing), B3 (T11 only), and B4 (T11+T12) subsets that
paper.md Sec 10's ablation table defines, instead of re-running retrieval+generation+validation
three more times for a pilot whose purpose (paper.md Sec 15 T14) is schema/metric/OOM
validation, not producing final comparative numbers.

Caveat this script states explicitly in every derived run's config.yaml: `generation_latency_ms`
is copied from the B5 run and reflects B5-Phase-A generation only (not re-measured), and no
separate wall-clock cost for "running only T11" (much cheaper than T11+T12's NLI pass) vs
"running T11+T12" is measured here -- a full-scale T15+ run that wants per-condition latency
breakdown should time each validation stage separately, which this pilot-only shortcut does not
attempt to fake.

`action` is left as `null` for B2/B3/B4 (not `"pass"`) because those conditions have no
abstention/escalation POLICY at all (paper.md Sec 10's ablation table only adds that at B5) --
`null` an honest "not applicable at this ablation level", not a real decision.

Usage:
    python scripts/derive_ablation_view_from_b5.py --source-run <b5_run_id> --condition B2
    python scripts/derive_ablation_view_from_b5.py --source-run <b5_run_id> --condition B3
    python scripts/derive_ablation_view_from_b5.py --source-run <b5_run_id> --condition B4
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

T11_FLAGS = {"fabricated_citation_detected", "misquotation_detected"}
T12_FLAG_PREFIXES = (
    "high_contradiction_rate",
    "insufficient_evidence_coverage",
    "no_checkable_substantive_evidence",
    "meta_evidence_claims_excluded_from_contradiction_check",
)


def sanitize(name: str) -> str:
    return name.replace("/", "__")


def filter_flags(flags: list[str], condition: str) -> list[str]:
    if condition == "B2":
        return []
    if condition == "B3":
        return [f for f in flags if f in T11_FLAGS]
    if condition == "B4":
        return [f for f in flags if f in T11_FLAGS or f.startswith(T12_FLAG_PREFIXES)]
    raise ValueError(condition)


def derive_trace(b5_trace: dict, condition: str) -> dict:
    if condition == "B2":
        return {
            "item_id": b5_trace["item_id"],
            "action": "pass_through",
            "guardrail_flags": [],
            "note": "no guardrails at B2 -- retrieval + generation only (paper.md §10)",
        }
    if condition == "B3":
        return {
            "item_id": b5_trace["item_id"],
            "answer": b5_trace["answer"],
            "quotation_checks": b5_trace["quotation_checks"],
            "claims": [],
            "madhhab_context": None,
            "evidence_sufficient": None,
            "action": None,
            "guardrail_flags": filter_flags(b5_trace["guardrail_flags"], "B3"),
            "note": "B3 = RAG + provenance validation only (paper.md §10); claims/madhhab/"
                    "action deliberately not computed at this ablation level.",
            "generation_latency_ms": b5_trace["generation_latency_ms"],
        }
    if condition == "B4":
        return {
            "item_id": b5_trace["item_id"],
            "answer": b5_trace["answer"],
            "quotation_checks": b5_trace["quotation_checks"],
            "claims": b5_trace["claims"],
            "madhhab_context": None,
            "evidence_sufficient": b5_trace["evidence_sufficient"],
            "action": None,
            "guardrail_flags": filter_flags(b5_trace["guardrail_flags"], "B4"),
            "note": "B4 = RAG + provenance + evidence validation (paper.md §10); madhhab/"
                    "abstention policy deliberately not applied at this ablation level.",
            "generation_latency_ms": b5_trace["generation_latency_ms"],
            "validation_latency_ms": b5_trace["validation_latency_ms"],
        }
    raise ValueError(condition)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-run", required=True, help="B5 run_id under runs/")
    parser.add_argument("--condition", required=True, choices=["B2", "B3", "B4"])
    args = parser.parse_args()

    src_dir = REPO_ROOT / "runs" / args.source_run
    if not src_dir.is_dir():
        print(f"source run not found: {src_dir}", file=sys.stderr)
        return 1

    responses = [json.loads(line) for line in (src_dir / "responses.jsonl").read_text(encoding="utf-8").splitlines()]
    retrieval = [json.loads(line) for line in (src_dir / "retrieval.jsonl").read_text(encoding="utf-8").splitlines()]
    traces_b5 = [json.loads(line) for line in (src_dir / "guardrail_traces.jsonl").read_text(encoding="utf-8").splitlines()]
    src_config = (src_dir / "config.yaml").read_text(encoding="utf-8")
    model_info = json.loads((src_dir / "model_info.json").read_text(encoding="utf-8"))

    model_id = model_info["model_id"]
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M")
    # Derive the sample tag from the source B5 run_id itself (format:
    # {ts}_{model}_B5_{sample_tag}_s{seed}) rather than hardcoding "t14pilot", so this script
    # stays correct for any B5 source run (T14's pilot, T15's benchmark, or later ones).
    tag_match = re.search(r"_B5_(.+)_s\d+$", args.source_run)
    sample_tag = tag_match.group(1) if tag_match else "derived"
    run_id = f"{timestamp}_{sanitize(model_id)}_{args.condition}_{sample_tag}_s42"
    run_dir = REPO_ROOT / "runs" / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    derived_traces = [derive_trace(t, args.condition) for t in traces_b5]

    (run_dir / "responses.jsonl").write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in responses) + "\n", encoding="utf-8"
    )
    (run_dir / "retrieval.jsonl").write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in retrieval) + "\n", encoding="utf-8"
    )
    (run_dir / "guardrail_traces.jsonl").write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in derived_traces) + "\n", encoding="utf-8"
    )
    prompts_src = src_dir / "prompts.jsonl"
    if prompts_src.exists():
        shutil.copyfile(prompts_src, run_dir / "prompts.jsonl")

    action_dist = None
    risk_dist = None
    if args.condition in ("B3", "B4"):
        n_flagged = sum(1 for t in derived_traces if t["guardrail_flags"])
    else:
        n_flagged = 0

    metrics = {
        "n_items": len(responses),
        "derived_from_source_run": args.source_run,
        "condition": args.condition,
        "n_items_with_guardrail_flags": n_flagged,
        "note": "This condition's generation was NOT re-run; it reuses the source B5 run's "
                "identical retrieval+generation step (same retriever/template/seed) per "
                "paper.md §10's ablation design. See scripts/derive_ablation_view_from_b5.py "
                "docstring for the full rationale and stated caveats (esp. latency numbers).",
    }
    (run_dir / "metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")

    config_yaml = (
        f"run_id: {run_id}\n"
        f"model: {model_id}\n"
        f"condition: {args.condition}\n"
        f"backend: transformers\n"
        f"derived_from_source_run: {args.source_run}\n"
        f"derivation_method: reslice_of_b5_guardrail_traces (see script docstring)\n"
        f"n_items: {len(responses)}\n"
        f"seed: 42\n"
    )
    (run_dir / "config.yaml").write_text(config_yaml, encoding="utf-8")
    (run_dir / "model_info.json").write_text(json.dumps(model_info, indent=2), encoding="utf-8")
    shutil.copyfile(src_dir / "environment.txt", run_dir / "environment.txt")
    shutil.copyfile(src_dir / "git_commit.txt", run_dir / "git_commit.txt")
    (run_dir / "timing.json").write_text(
        json.dumps({"note": "no separate timing measured; derived from source run", "source_run": args.source_run}, indent=2),
        encoding="utf-8",
    )
    (run_dir / "run.log").write_text(
        f"run_id={run_id}\nmodel={model_id}\ncondition={args.condition}\n"
        f"derived_from_source_run={args.source_run}\nn_items={len(responses)}\n"
        f"n_items_with_guardrail_flags={n_flagged}\n",
        encoding="utf-8",
    )

    print(f"[{run_id}] done (derived from {args.source_run}). n_items_with_guardrail_flags={n_flagged}/{len(responses)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
