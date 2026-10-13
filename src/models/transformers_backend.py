"""Transformers-backed generator (DECISIONS.md DG-2: debugging/validation path).

Non-thinking mode note (DG-3): Qwen3's own `chat_template.jinja` (verified directly against
the cached tokenizer_config.json for Qwen/Qwen3-8B in this environment) contains:

    {%- if add_generation_prompt %}
        {{- '<|im_start|>assistant\\n' }}
        {%- if enable_thinking is defined and enable_thinking is false %}
            {{- '<think>\\n\\n</think>\\n\\n' }}
        {%- endif %}
    {%- endif %}

So passing `enable_thinking=False` to `apply_chat_template(...)` injects an empty, already-closed
think block into the PROMPT (not the generated output), which signals the model to skip its own
reasoning trace. This module still verifies (does not assume) that no `<think>` tag leaks into
the newly generated tokens for every single response, per `base.contains_think_tag`.
"""

from __future__ import annotations

import time

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

from src.models.base import (
    GenerationConfig,
    GenerationRequest,
    GenerationResult,
    contains_think_tag,
)


class TransformersGenerator:
    def __init__(self, model_id: str) -> None:
        if not torch.cuda.is_available():
            raise RuntimeError("CUDA is not available; refusing to run on CPU.")
        self.model_id = model_id
        load_start = time.time()
        self.tokenizer = AutoTokenizer.from_pretrained(model_id, trust_remote_code=False)
        self.model = AutoModelForCausalLM.from_pretrained(
            model_id,
            torch_dtype="auto",
            device_map="cuda",
            trust_remote_code=False,
        )
        self.model.eval()
        self.load_seconds = time.time() - load_start
        self.model_revision = getattr(self.model.config, "_commit_hash", None)

    def generate(self, request: GenerationRequest, config: GenerationConfig) -> GenerationResult:
        torch.manual_seed(config.seed)

        messages = []
        if request.system_prompt:
            messages.append({"role": "system", "content": request.system_prompt})
        messages.append({"role": "user", "content": request.query})

        encoded = self.tokenizer.apply_chat_template(
            messages,
            add_generation_prompt=True,
            return_tensors="pt",
            return_dict=True,
            enable_thinking=config.enable_thinking,
        )
        input_ids = encoded["input_ids"].to(self.model.device)
        prompt_tokens = input_ids.shape[-1]

        gen_start = time.time()
        with torch.no_grad():
            output_ids = self.model.generate(
                input_ids,
                max_new_tokens=config.max_new_tokens,
                do_sample=config.do_sample,
            )
        torch.cuda.synchronize()
        latency_ms = (time.time() - gen_start) * 1000

        new_tokens = output_ids[0, prompt_tokens:]
        response_text = self.tokenizer.decode(new_tokens, skip_special_tokens=True)
        completion_tokens = new_tokens.shape[-1]

        leaked_think = contains_think_tag(response_text)

        return GenerationResult(
            request=request,
            response_text=response_text,
            model_id=self.model_id,
            model_revision=self.model_revision,
            backend="transformers",
            generation_config=config,
            thinking_mode_verified_disabled=(not config.enable_thinking) and (not leaked_think),
            load_seconds=self.load_seconds,
            latency_ms=round(latency_ms, 1),
            prompt_tokens=int(prompt_tokens),
            completion_tokens=int(completion_tokens),
            raw_output_contains_think_tag=leaked_think,
        )
