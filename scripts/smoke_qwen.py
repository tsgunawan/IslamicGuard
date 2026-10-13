"""Smoke-test a Qwen3 model with Transformers (paper.md section 8.4).

Loads the tokenizer/model onto the GPU, runs one benign English and one benign
Arabic prompt, and saves the raw generation plus VRAM/timing/config metadata to
runs/smoke/<run_id>.json.

Usage:
    conda activate islamicguard
    python scripts/smoke_qwen.py --model Qwen/Qwen3-8B
    python scripts/smoke_qwen.py --model Qwen/Qwen3-14B-AWQ
    python scripts/smoke_qwen.py --model Qwen/Qwen3-32B-AWQ --max-model-len 4096
"""

from __future__ import annotations

import argparse
import json
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

REPO_ROOT = Path(__file__).resolve().parents[1]
SMOKE_DIR = REPO_ROOT / "runs" / "smoke"

PROMPTS = {
    "en": "In one or two sentences, what is the significance of seeking knowledge in Islam?",
    "ar": "في جملة أو جملتين، ما أهمية طلب العلم في الإسلام؟",
}


@dataclass
class GenerationConfig:
    max_new_tokens: int
    do_sample: bool
    temperature: float | None
    top_p: float | None


def sanitize_model_name(model_id: str) -> str:
    return model_id.replace("/", "__")


def run_smoke_test(model_id: str, max_new_tokens: int, max_model_len: int | None) -> dict:
    if not torch.cuda.is_available():
        raise RuntimeError("CUDA is not available; refusing to run smoke test on CPU.")

    torch.cuda.reset_peak_memory_stats()
    load_start = time.time()

    tokenizer = AutoTokenizer.from_pretrained(model_id, trust_remote_code=False)
    model = AutoModelForCausalLM.from_pretrained(
        model_id,
        torch_dtype="auto",
        device_map="cuda",
        trust_remote_code=False,
    )
    load_seconds = time.time() - load_start

    gen_config = GenerationConfig(
        max_new_tokens=max_new_tokens,
        do_sample=False,
        temperature=None,
        top_p=None,
    )

    responses = {}
    latencies_ms = {}
    for lang, prompt in PROMPTS.items():
        messages = [{"role": "user", "content": prompt}]
        encoded = tokenizer.apply_chat_template(
            messages,
            add_generation_prompt=True,
            return_tensors="pt",
            return_dict=True,
        )
        input_ids = encoded["input_ids"]
        if max_model_len is not None and input_ids.shape[-1] > max_model_len:
            raise ValueError(f"Prompt exceeds max_model_len={max_model_len}")
        input_ids = input_ids.to(model.device)

        gen_start = time.time()
        with torch.no_grad():
            output_ids = model.generate(
                input_ids,
                max_new_tokens=gen_config.max_new_tokens,
                do_sample=gen_config.do_sample,
            )
        torch.cuda.synchronize()
        latencies_ms[lang] = round((time.time() - gen_start) * 1000, 1)

        new_tokens = output_ids[0, input_ids.shape[-1]:]
        responses[lang] = tokenizer.decode(new_tokens, skip_special_tokens=True)

    allocated_mb = round(torch.cuda.memory_allocated() / (1024**2), 2)
    reserved_mb = round(torch.cuda.memory_reserved() / (1024**2), 2)
    peak_allocated_mb = round(torch.cuda.max_memory_allocated() / (1024**2), 2)

    revision = getattr(model.config, "_commit_hash", None)

    result = {
        "model_id": model_id,
        "revision": revision,
        "run_timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "load_seconds": round(load_seconds, 2),
        "generation_config": asdict(gen_config),
        "max_model_len_requested": max_model_len,
        "prompts": PROMPTS,
        "responses": responses,
        "latency_ms": latencies_ms,
        "vram_allocated_mb": allocated_mb,
        "vram_reserved_mb": reserved_mb,
        "vram_peak_allocated_mb": peak_allocated_mb,
        "torch_dtype": str(next(model.parameters()).dtype),
    }
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True, help="HF repo id, e.g. Qwen/Qwen3-8B")
    parser.add_argument("--max-new-tokens", type=int, default=128)
    parser.add_argument("--max-model-len", type=int, default=None)
    args = parser.parse_args()

    SMOKE_DIR.mkdir(parents=True, exist_ok=True)
    run_id = f"{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}_{sanitize_model_name(args.model)}"
    out_path = SMOKE_DIR / f"{run_id}.json"

    try:
        result = run_smoke_test(args.model, args.max_new_tokens, args.max_model_len)
        result["status"] = "pass"
    except torch.cuda.OutOfMemoryError as exc:  # noqa: PERF203 - explicit is fine here
        result = {
            "model_id": args.model,
            "status": "fail_oom",
            "error": str(exc),
            "max_model_len_requested": args.max_model_len,
            "run_timestamp_utc": datetime.now(timezone.utc).isoformat(),
        }

    out_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"status={result['status']} saved={out_path}")
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
