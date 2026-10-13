"""T10 — B2 (standard RAG) generation pipeline.

Retrieval (qwen3-embedding-4b, DECISIONS.md DG-4-revised) + generation, no post-hoc
validation (paper.md §10). Same sample/models/seed as T09's B0/B1 for direct comparability.
Writes a full runs/<run_id>/ directory per paper.md §14, including a real (non-empty)
retrieval.jsonl this time.

Usage:
    python scripts/run_rag_baseline.py --model Qwen/Qwen3-8B
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
from src.rag.generate import RagRetriever, format_context_block, passages_to_log  # noqa: E402

SAMPLE_PATH = REPO_ROOT / "data" / "benchmarks" / "t09_pipeline_sample.jsonl"
PROMPT_TEMPLATE_PATH = REPO_ROOT / "prompts" / "b2_rag.md"
SEED = 42
EMBEDDING_MODEL_SLUG = "qwen3-embedding-4b"  # DECISIONS.md DG-4 (revised, provisional)


def load_b2_template() -> str:
    text = PROMPT_TEMPLATE_PATH.read_text(encoding="utf-8")
    marker = "-->"
    idx = text.find(marker)
    return text[idx + len(marker):].strip()


def sanitize(name: str) -> str:
    return name.replace("/", "__")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True)
    parser.add_argument("--max-new-tokens", type=int, default=512)
    parser.add_argument("--k-per-layer", type=int, default=3)
    args = parser.parse_args()

    random.seed(SEED)
    np.random.seed(SEED)
    torch.manual_seed(SEED)

    items = [json.loads(line) for line in SAMPLE_PATH.read_text(encoding="utf-8").splitlines()]
    template = load_b2_template()

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M")
    run_id = f"{timestamp}_{sanitize(args.model)}_B2_t09sample_s{SEED}"
    run_dir = REPO_ROOT / "runs" / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    print(f"[{run_id}] loading retriever ({EMBEDDING_MODEL_SLUG}) ...")
    retriever = RagRetriever(EMBEDDING_MODEL_SLUG)

    print(f"[{run_id}] loading generator {args.model} ...")
    generator = TransformersGenerator(args.model)
    config = GenerationConfig(max_new_tokens=args.max_new_tokens, enable_thinking=False, seed=SEED)

    prompts_log = []
    responses_log = []
    retrieval_log = []
    guardrail_traces_log = []  # empty at B2 -- no post-hoc validation yet (paper.md §10)
    latencies = []
    completion_token_counts = []
    retrieval_scores = []
    thinking_leaks = 0

    for item in items:
        passages = retriever.retrieve(item["query"], k_per_layer=args.k_per_layer)
        context_block = format_context_block(passages)
        user_content = template.format(context=context_block, query=item["query"])

        request = GenerationRequest(
            query=user_content,
            language=item["language"],
            condition="B2",
            system_prompt=None,  # B2 isolates retrieval's effect relative to B0 (no system prompt)
            item_id=item["item_id"],
            metadata={"source_dataset": item["source_dataset"], "source_category": item["source_category"]},
        )
        result = generator.generate(request, config)

        prompts_log.append(
            {
                "item_id": item["item_id"],
                "language": item["language"],
                "query_raw": item["query"],
                "user_content_sent": user_content,
                "system_prompt": None,
            }
        )
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
        passages_logged = passages_to_log(passages)
        retrieval_log.append(
            {
                "item_id": item["item_id"],
                "query": item["query"],
                "embedding_model": EMBEDDING_MODEL_SLUG,
                "k_per_layer": args.k_per_layer,
                "n_retrieved": len(passages_logged),
                "passages": passages_logged,
            }
        )
        guardrail_traces_log.append(
            {
                "item_id": item["item_id"],
                "action": "pass_through",
                "guardrail_flags": [],
                "note": "no guardrails at B2 -- retrieval + generation only (paper.md §10)",
            }
        )

        latencies.append(result.latency_ms)
        completion_token_counts.append(result.completion_tokens)
        retrieval_scores.extend(p.score for p in passages)
        if result.raw_output_contains_think_tag:
            thinking_leaks += 1

        print(
            f"  [{item['item_id']}] retrieved={len(passages)} "
            f"top_score={max((p.score for p in passages), default=0.0):.3f} "
            f"{result.latency_ms:.0f}ms, {result.completion_tokens} tok, "
            f"think_leak={result.raw_output_contains_think_tag}"
        )

    (run_dir / "prompts.jsonl").write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in prompts_log) + "\n", encoding="utf-8"
    )
    (run_dir / "responses.jsonl").write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in responses_log) + "\n", encoding="utf-8"
    )
    (run_dir / "retrieval.jsonl").write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in retrieval_log) + "\n", encoding="utf-8"
    )
    (run_dir / "guardrail_traces.jsonl").write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in guardrail_traces_log) + "\n", encoding="utf-8"
    )

    config_yaml = f"""run_id: {run_id}
model: {args.model}
condition: B2
backend: transformers
embedding_model: {EMBEDDING_MODEL_SLUG}
k_per_layer: {args.k_per_layer}
dataset: data/benchmarks/t09_pipeline_sample.jsonl
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
        "embedding_model": EMBEDDING_MODEL_SLUG,
        "embedding_hf_repo": retriever.spec.hf_repo,
    }
    (run_dir / "model_info.json").write_text(json.dumps(model_info, indent=2), encoding="utf-8")

    metrics = {
        "n_items": len(items),
        "mean_latency_ms": round(sum(latencies) / len(latencies), 1),
        "min_latency_ms": min(latencies),
        "max_latency_ms": max(latencies),
        "mean_completion_tokens": round(sum(completion_token_counts) / len(completion_token_counts), 1),
        "max_completion_tokens": max(completion_token_counts),
        "mean_retrieved_per_item": round(len(retrieval_scores) / len(items), 2),
        "mean_retrieval_score": round(sum(retrieval_scores) / len(retrieval_scores), 4) if retrieval_scores else None,
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
        commit = subprocess.run(
            ["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True, cwd=REPO_ROOT
        ).stdout.strip()
    except Exception:
        commit = "unknown"
    (run_dir / "git_commit.txt").write_text(commit + "\n", encoding="utf-8")

    (run_dir / "run.log").write_text(
        f"run_id={run_id}\nmodel={args.model}\ncondition=B2\n"
        f"embedding_model={EMBEDDING_MODEL_SLUG}\nn_items={len(items)}\n"
        f"thinking_leaks={thinking_leaks}\nmean_latency_ms={metrics['mean_latency_ms']}\n"
        f"mean_retrieval_score={metrics['mean_retrieval_score']}\n",
        encoding="utf-8",
    )

    print(
        f"[{run_id}] done. mean_latency_ms={metrics['mean_latency_ms']} "
        f"mean_completion_tokens={metrics['mean_completion_tokens']} "
        f"mean_retrieval_score={metrics['mean_retrieval_score']} "
        f"thinking_leaks={thinking_leaks}/{len(items)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
