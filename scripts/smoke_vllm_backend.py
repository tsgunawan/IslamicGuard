"""Prove the vLLM backend (src/models/vllm_backend.py) actually works (DECISIONS.md DG-2).

Not a throughput benchmark (that's T15-T17) -- just confirms the interface loads a model,
generates via LLM.chat, and correctly forces/verifies non-thinking mode through the same
enable_thinking=False chat_template_kwargs mechanism as the Transformers backend.

Usage:
    python scripts/smoke_vllm_backend.py --model Qwen/Qwen3-8B
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from src.models.base import GenerationConfig, GenerationRequest  # noqa: E402
from src.models.vllm_backend import VLLMGenerator  # noqa: E402

PROMPTS = [
    ("en", "In one or two sentences, what is the significance of seeking knowledge in Islam?"),
    ("ar", "في جملة أو جملتين، ما أهمية طلب العلم في الإسلام؟"),
]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True)
    parser.add_argument("--max-model-len", type=int, default=4096)
    args = parser.parse_args()

    print(f"loading {args.model} via vLLM (enforce_eager=True for faster smoke-test startup)...")
    generator = VLLMGenerator(args.model, max_model_len=args.max_model_len, enforce_eager=True)
    config = GenerationConfig(max_new_tokens=256, enable_thinking=False, seed=42)

    results = []
    for lang, query in PROMPTS:
        request = GenerationRequest(query=query, language=lang, condition="smoke", item_id=f"vllm_smoke_{lang}")
        result = generator.generate(request, config)
        results.append(
            {
                "language": lang,
                "latency_ms": result.latency_ms,
                "completion_tokens": result.completion_tokens,
                "thinking_mode_verified_disabled": result.thinking_mode_verified_disabled,
                "raw_output_contains_think_tag": result.raw_output_contains_think_tag,
                "response_text": result.response_text,
            }
        )
        print(f"[{lang}] {result.latency_ms:.0f}ms, {result.completion_tokens} tok, "
              f"think_leak={result.raw_output_contains_think_tag}")
        print(f"  {result.response_text[:200]}")

    out_path = REPO_ROOT / "runs" / "smoke" / f"vllm_backend_smoke_{args.model.replace('/', '__')}.json"
    out_path.write_text(json.dumps({"model": args.model, "load_seconds": generator.load_seconds, "results": results}, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"saved {out_path}")
    all_ok = all(r["thinking_mode_verified_disabled"] for r in results)
    print(f"vLLM backend smoke test: {'PASS' if all_ok else 'FAIL'}")
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
