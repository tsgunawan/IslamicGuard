"""T13 — B5 (full IslamicGuard) pipeline run.

Retrieval + generation (identical to B2's pipeline -- same retriever, same prompt template,
prompts/b2_rag.md, so the ablation isolates the guardrail layer's effect, not a different
generation strategy) followed by the full T11 (provenance) + T13 (madhhab/abstention) guardrail
stack from src/guardrails/islamicguard_pipeline.py. Writes a real (non-empty)
guardrail_traces.jsonl this time, unlike B0-B2's empty/pass-through logs.

Staged GPU usage: retrieval (Qwen3-Embedding-4B) + generation (Qwen3-8B) run together first
(same combination already proven to fit in T10's B2 run, ~24GB used), then both are freed
before loading the claim-evidence faithfulness NLI model (T12's mDeBERTa-v3-base-mnli-xnli) --
avoids ever holding all three models in VRAM simultaneously on this 24GB card.

Usage:
    python scripts/run_islamicguard_b5.py --model Qwen/Qwen3-8B
"""

from __future__ import annotations

import argparse
import gc
import json
import random
import subprocess
import sys
from collections import Counter
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import torch

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from src.guardrails.islamicguard_pipeline import run_guardrails  # noqa: E402
from src.models.base import GenerationConfig, GenerationRequest  # noqa: E402
from src.models.transformers_backend import TransformersGenerator  # noqa: E402
from src.rag.generate import RagRetriever, format_context_block, passages_to_log  # noqa: E402

DEFAULT_SAMPLE_PATH = REPO_ROOT / "data" / "benchmarks" / "t13_pipeline_sample.jsonl"
PROMPT_TEMPLATE_PATH = REPO_ROOT / "prompts" / "b2_rag.md"  # B5 reuses B2's generation step as-is
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
    parser.add_argument("--sample", type=Path, default=DEFAULT_SAMPLE_PATH,
                         help="Override the item sample (default: t13_pipeline_sample.jsonl, "
                              "kept as default so re-running with no flags stays reproducible "
                              "with the already-committed T13 run).")
    args = parser.parse_args()
    sample_path: Path = args.sample.resolve()
    sample_tag = sample_path.stem.replace("_pipeline_sample", "sample").replace("_benchmark", "benchmark")

    random.seed(SEED)
    np.random.seed(SEED)
    torch.manual_seed(SEED)

    items = [json.loads(line) for line in sample_path.read_text(encoding="utf-8").splitlines()]
    template = load_b2_template()

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M")
    run_id = f"{timestamp}_{sanitize(args.model)}_B5_{sample_tag}_s{SEED}"
    run_dir = REPO_ROOT / "runs" / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    # --- Phase A: retrieval + generation (same combination T10 already proved fits) ---
    print(f"[{run_id}] Phase A: loading retriever ({EMBEDDING_MODEL_SLUG}) + generator {args.model} ...")
    retriever = RagRetriever(EMBEDDING_MODEL_SLUG)
    generator = TransformersGenerator(args.model)
    config = GenerationConfig(max_new_tokens=args.max_new_tokens, enable_thinking=False, seed=SEED)

    generation_records = []  # one dict per item: item, passages (RetrievedPassage list), result
    for item in items:
        passages = retriever.retrieve(item["query"], k_per_layer=args.k_per_layer)
        context_block = format_context_block(passages)
        user_content = template.format(context=context_block, query=item["query"])
        request = GenerationRequest(
            query=user_content,
            language=item["language"],
            condition="B5",
            system_prompt=None,
            item_id=item["item_id"],
            metadata={"source_dataset": item["source_dataset"], "source_category": item["source_category"]},
        )
        result = generator.generate(request, config)
        generation_records.append({"item": item, "passages": passages, "result": result})
        print(
            f"  [{item['item_id']}] retrieved={len(passages)} "
            f"{result.latency_ms:.0f}ms, {result.completion_tokens} tok, "
            f"think_leak={result.raw_output_contains_think_tag}"
        )

    load_seconds = generator.load_seconds
    embedding_hf_repo = retriever.spec.hf_repo

    # --- Free retrieval + generation models before loading the NLI model (VRAM headroom) ---
    print(f"[{run_id}] Phase A done. Freeing retriever+generator GPU memory before Phase B ...")
    del generator.model, generator.tokenizer, generator
    del retriever.embedder.model, retriever.embedder, retriever
    gc.collect()
    torch.cuda.empty_cache()

    # --- Phase B: T11 provenance + T12 faithfulness + T13 madhhab/abstention guardrails ---
    print(f"[{run_id}] Phase B: running guardrail stack (loads NLI model on first claim check) ...")
    prompts_log, responses_log, retrieval_log, guardrail_traces_log = [], [], [], []
    latencies_gen, completion_token_counts, retrieval_scores = [], [], []
    thinking_leaks = 0
    action_counts: Counter[str] = Counter()
    risk_counts: Counter[str] = Counter()

    for rec in generation_records:
        item, passages, result = rec["item"], rec["passages"], rec["result"]
        guard_result = run_guardrails(query=item["query"], response_text=result.response_text, passages=passages)

        prompts_log.append({"item_id": item["item_id"], "language": item["language"], "query_raw": item["query"]})
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
                **guard_result.to_dict(),
                "generation_latency_ms": result.latency_ms,
                "validation_latency_ms": guard_result.latency_ms,
            }
        )

        latencies_gen.append(result.latency_ms)
        completion_token_counts.append(result.completion_tokens)
        retrieval_scores.extend(p.score for p in passages)
        if result.raw_output_contains_think_tag:
            thinking_leaks += 1
        action_counts[guard_result.action] += 1
        risk_counts[guard_result.risk_level] += 1

        print(
            f"  [{item['item_id']}] action={guard_result.action} risk={guard_result.risk_level} "
            f"flags={guard_result.guardrail_flags} n_claims={len(guard_result.claims)}"
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
condition: B5
backend: transformers
embedding_model: {EMBEDDING_MODEL_SLUG}
k_per_layer: {args.k_per_layer}
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
        "load_seconds": load_seconds,
        "embedding_model": EMBEDDING_MODEL_SLUG,
        "embedding_hf_repo": embedding_hf_repo,
    }
    (run_dir / "model_info.json").write_text(json.dumps(model_info, indent=2), encoding="utf-8")

    metrics = {
        "n_items": len(items),
        "mean_generation_latency_ms": round(sum(latencies_gen) / len(latencies_gen), 1),
        "mean_completion_tokens": round(sum(completion_token_counts) / len(completion_token_counts), 1),
        "mean_retrieved_per_item": round(len(retrieval_scores) / len(items), 2),
        "mean_retrieval_score": round(sum(retrieval_scores) / len(retrieval_scores), 4) if retrieval_scores else None,
        "thinking_leaks": thinking_leaks,
        "action_distribution": dict(action_counts),
        "risk_level_distribution": dict(risk_counts),
    }
    (run_dir / "metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    (run_dir / "timing.json").write_text(
        json.dumps({"load_seconds": load_seconds, "generation_latencies_ms": latencies_gen}, indent=2),
        encoding="utf-8",
    )

    try:
        env_txt = subprocess.run([sys.executable, "-m", "pip", "freeze"], capture_output=True, text=True, check=True).stdout
    except Exception as exc:  # pragma: no cover - best-effort
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
        f"run_id={run_id}\nmodel={args.model}\ncondition=B5\n"
        f"action_distribution={dict(action_counts)}\n"
        f"risk_level_distribution={dict(risk_counts)}\n"
        f"thinking_leaks={thinking_leaks}\n",
        encoding="utf-8",
    )

    print(f"[{run_id}] done. action_distribution={dict(action_counts)} risk_distribution={dict(risk_counts)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
