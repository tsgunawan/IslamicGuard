"""T09 — reproducible B0/B1 baseline generation pipeline.

Runs a condition (B0 = no system prompt, B1 = Islamic policy system prompt) against one model
over `data/benchmarks/t09_pipeline_sample.jsonl` (built by `build_t09_sample.py`), using the
Transformers backend (DECISIONS.md DG-2: debugging/validation path) with non-thinking mode
forced (DECISIONS.md DG-3) and verified per-response (see src/models/base.contains_think_tag).

Writes a full runs/<run_id>/ directory per paper.md §14.

Usage:
    python scripts/run_baseline.py --model Qwen/Qwen3-8B --condition B0
    python scripts/run_baseline.py --model Qwen/Qwen3-8B --condition B1
"""

from __future__ import annotations

import argparse
import json
import random
import subprocess
import sys
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import torch

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from src.models.base import GenerationConfig, GenerationRequest  # noqa: E402
from src.models.transformers_backend import TransformersGenerator  # noqa: E402

DEFAULT_SAMPLE_PATH = REPO_ROOT / "data" / "benchmarks" / "t09_pipeline_sample.jsonl"
PROMPTS_DIR = REPO_ROOT / "prompts"
SEED = 42

CONDITIONS = {
    "B0": None,  # no system prompt
    "B1": (PROMPTS_DIR / "b1_islamic_policy.md"),
}


def load_b1_system_prompt() -> str:
    text = CONDITIONS["B1"].read_text(encoding="utf-8")
    # Strip the leading HTML comment block; everything after it is the exact system text.
    marker = "-->"
    idx = text.find(marker)
    return text[idx + len(marker):].strip()


def sanitize(name: str) -> str:
    return name.replace("/", "__")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True)
    parser.add_argument("--condition", required=True, choices=list(CONDITIONS.keys()))
    parser.add_argument("--max-new-tokens", type=int, default=512)
    parser.add_argument("--sample", type=Path, default=DEFAULT_SAMPLE_PATH,
                         help="Override the item sample (default: t09_pipeline_sample.jsonl, "
                              "the original T09 sample -- kept as the default so re-running this "
                              "script with no flags stays reproducible with the already-committed "
                              "T09 runs).")
    args = parser.parse_args()
    sample_path: Path = args.sample.resolve()
    sample_tag = sample_path.stem.replace("_pipeline_sample", "sample")  # e.g. t09sample, t14_pilotsample

    random.seed(SEED)
    np.random.seed(SEED)
    torch.manual_seed(SEED)

    items = [json.loads(line) for line in sample_path.read_text(encoding="utf-8").splitlines()]

    system_prompt = None
    if args.condition == "B1":
        system_prompt = load_b1_system_prompt()

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M")
    run_id = f"{timestamp}_{sanitize(args.model)}_{args.condition}_{sample_tag}_s{SEED}"
    run_dir = REPO_ROOT / "runs" / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    print(f"[{run_id}] loading {args.model} ...")
    generator = TransformersGenerator(args.model)
    config = GenerationConfig(max_new_tokens=args.max_new_tokens, enable_thinking=False, seed=SEED)

    prompts_log = []
    responses_log = []
    guardrail_traces_log = []  # empty at B0/B1 -- no guardrails exist yet
    latencies = []
    completion_token_counts = []
    thinking_leaks = 0

    for item in items:
        request = GenerationRequest(
            query=item["query"],
            language=item["language"],
            condition=args.condition,
            system_prompt=system_prompt,
            item_id=item["item_id"],
            metadata={"source_dataset": item["source_dataset"], "source_category": item["source_category"]},
        )
        result = generator.generate(request, config)

        prompts_log.append({"item_id": item["item_id"], "language": item["language"], "query": item["query"], "system_prompt": system_prompt})
        responses_log.append(
            {
                "item_id": item["item_id"],
                "response_text": result.response_text,
                "backend": result.backend,
                "model_id": result.model_id,
                "model_revision": result.model_revision,
                "thinking_mode_verified_disabled": result.thinking_mode_verified_disabled,
                "raw_output_contains_think_tag": result.raw_output_contains_think_tag,
                "latency_ms": result.latency_ms,
                "prompt_tokens": result.prompt_tokens,
                "completion_tokens": result.completion_tokens,
                "generation_config": asdict(result.generation_config),
            }
        )
        guardrail_traces_log.append({"item_id": item["item_id"], "action": "pass_through", "guardrail_flags": [], "note": "no guardrails at B0/B1 (paper.md §10)"})

        latencies.append(result.latency_ms)
        completion_token_counts.append(result.completion_tokens)
        if result.raw_output_contains_think_tag:
            thinking_leaks += 1

        print(f"  [{item['item_id']}] {result.latency_ms:.0f}ms, {result.completion_tokens} tok, "
              f"think_leak={result.raw_output_contains_think_tag}")

    (run_dir / "prompts.jsonl").write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in prompts_log) + "\n", encoding="utf-8"
    )
    (run_dir / "responses.jsonl").write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in responses_log) + "\n", encoding="utf-8"
    )
    (run_dir / "retrieval.jsonl").write_text("", encoding="utf-8")  # not applicable at B0/B1
    (run_dir / "guardrail_traces.jsonl").write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in guardrail_traces_log) + "\n", encoding="utf-8"
    )

    config_yaml = f"""run_id: {run_id}
model: {args.model}
condition: {args.condition}
backend: transformers
dataset: {sample_path.relative_to(REPO_ROOT)}
n_items: {len(items)}
seed: {SEED}
generation_config:
  max_new_tokens: {config.max_new_tokens}
  do_sample: {config.do_sample}
  enable_thinking: {config.enable_thinking}
"""
    (run_dir / "config.yaml").write_text(config_yaml, encoding="utf-8")

    model_info = {
        "model_id": args.model,
        "model_revision": generator.model_revision,
        "load_seconds": generator.load_seconds,
    }
    (run_dir / "model_info.json").write_text(json.dumps(model_info, indent=2), encoding="utf-8")

    metrics = {
        "n_items": len(items),
        "mean_latency_ms": round(sum(latencies) / len(latencies), 1),
        "min_latency_ms": min(latencies),
        "max_latency_ms": max(latencies),
        "mean_completion_tokens": round(sum(completion_token_counts) / len(completion_token_counts), 1),
        "max_completion_tokens": max(completion_token_counts),
        "thinking_leaks": thinking_leaks,
        "thinking_leak_rate": round(thinking_leaks / len(items), 4),
    }
    (run_dir / "metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    (run_dir / "timing.json").write_text(
        json.dumps({"load_seconds": generator.load_seconds, "latencies_ms": latencies}, indent=2),
        encoding="utf-8",
    )

    try:
        env_txt = subprocess.run([sys.executable, "-m", "pip", "freeze"], capture_output=True, text=True, check=True).stdout
    except Exception as exc:  # pragma: no cover - environment capture is best-effort
        env_txt = f"pip freeze failed: {exc}"
    (run_dir / "environment.txt").write_text(env_txt, encoding="utf-8")

    try:
        commit = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True, cwd=REPO_ROOT).stdout.strip()
    except Exception:
        commit = "unknown"
    (run_dir / "git_commit.txt").write_text(commit + "\n", encoding="utf-8")

    (run_dir / "run.log").write_text(
        f"run_id={run_id}\nmodel={args.model}\ncondition={args.condition}\n"
        f"n_items={len(items)}\nthinking_leaks={thinking_leaks}\n"
        f"mean_latency_ms={metrics['mean_latency_ms']}\n",
        encoding="utf-8",
    )

    print(f"[{run_id}] done. mean_latency_ms={metrics['mean_latency_ms']} "
          f"mean_completion_tokens={metrics['mean_completion_tokens']} "
          f"thinking_leaks={thinking_leaks}/{len(items)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
