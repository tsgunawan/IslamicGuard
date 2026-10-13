"""vLLM-backed generator (DECISIONS.md DG-2: high-throughput path, T15-T17).

Non-thinking mode (DG-3) is forced via `chat_template_kwargs={"enable_thinking": False}` on
`LLM.chat(...)`, which vLLM forwards to the tokenizer's `apply_chat_template` exactly like the
Transformers path (see `transformers_backend.py`'s docstring for what that flag actually does
in Qwen3's chat template). Verified against the installed vllm==0.29.0 `LLM.chat` signature,
which accepts `chat_template_kwargs`.

WSL2-SPECIFIC REQUIREMENT (discovered running scripts/smoke_vllm_backend.py in T09, not
theoretical): vllm==0.29.0's V1 GPU worker raises `RuntimeError: UVA is not available` on a
plain WSL2 launch. Root cause (traced to
`vllm.platforms.cuda.NvmlCudaPlatform.is_pin_memory_available`): vLLM detects WSL2 and disables
pinned host memory BY DEFAULT even on a kernel new enough to support it (this environment's
kernel, 5.15.153.1-microsoft-standard-WSL2, is well above the 4.19.121 floor vLLM checks for),
requiring an explicit opt-in. Fix: set `VLLM_WSL2_ENABLE_PIN_MEMORY=1` in the environment before
constructing `VLLMGenerator` / calling any vLLM entrypoint. This is a real platform quirk to
document (e.g. in a launch script or `~/.bashrc` alongside the other T01 env vars), not a bug in
this module -- callers must set it themselves.
"""

from __future__ import annotations

import time

from vllm import LLM, SamplingParams

from src.models.base import (
    GenerationConfig,
    GenerationRequest,
    GenerationResult,
    contains_think_tag,
)


class VLLMGenerator:
    def __init__(self, model_id: str, max_model_len: int | None = None, **llm_kwargs) -> None:
        self.model_id = model_id
        load_start = time.time()
        self.llm = LLM(model=model_id, max_model_len=max_model_len, **llm_kwargs)
        self.load_seconds = time.time() - load_start

    def generate(self, request: GenerationRequest, config: GenerationConfig) -> GenerationResult:
        messages = []
        if request.system_prompt:
            messages.append({"role": "system", "content": request.system_prompt})
        messages.append({"role": "user", "content": request.query})

        sampling_params = SamplingParams(
            max_tokens=config.max_new_tokens,
            temperature=0.0 if not config.do_sample else (config.temperature or 1.0),
            top_p=config.top_p if config.top_p is not None else 1.0,
            seed=config.seed,
        )

        gen_start = time.time()
        outputs = self.llm.chat(
            messages=[messages],
            sampling_params=sampling_params,
            chat_template_kwargs={"enable_thinking": config.enable_thinking},
            use_tqdm=False,
        )
        latency_ms = (time.time() - gen_start) * 1000

        output = outputs[0]
        response_text = output.outputs[0].text
        prompt_tokens = len(output.prompt_token_ids)
        completion_tokens = len(output.outputs[0].token_ids)
        leaked_think = contains_think_tag(response_text)

        return GenerationResult(
            request=request,
            response_text=response_text,
            model_id=self.model_id,
            model_revision=None,
            backend="vllm",
            generation_config=config,
            thinking_mode_verified_disabled=(not config.enable_thinking) and (not leaked_think),
            load_seconds=self.load_seconds,
            latency_ms=round(latency_ms, 1),
            prompt_tokens=int(prompt_tokens),
            completion_tokens=int(completion_tokens),
            raw_output_contains_think_tag=leaked_think,
        )
