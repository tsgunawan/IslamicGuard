"""Inference adapters for the IslamicGuard baseline generation pipeline (T09).

Per DECISIONS.md DG-2 (hybrid inference engine) and DG-3 (non-thinking mode primary):
  - `transformers_backend.TransformersGenerator` is the debugging/validation path.
  - `vllm_backend.VLLMGenerator` is the high-throughput path (T15-T17).

Both force Qwen3 non-thinking mode via `enable_thinking=False` in the chat template
(verified against the actual Qwen3 chat_template.jinja logic, which injects an empty
`<think>\n\n</think>\n\n` block immediately after the assistant generation prompt when
this flag is False — see `docs note` in `transformers_backend.py`), and both report
which mode was used in every response's generation-config metadata (paper.md §14).
"""

from src.models.base import GenerationConfig, GenerationRequest, GenerationResult

__all__ = ["GenerationConfig", "GenerationRequest", "GenerationResult"]
