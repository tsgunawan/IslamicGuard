"""Shared request/response/config types for both inference backends (T09)."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class GenerationConfig:
    """Fixed generation protocol per DECISIONS.md DG-3 (non-thinking primary).

    `enable_thinking=False` is the DG-3-mandated default. `max_new_tokens` is deliberately
    much smaller than T02's thinking-mode smoke tests needed (those needed >128 tokens just
    to start emitting a final answer) -- non-thinking responses are expected to be far
    shorter; T09 empirically verifies this rather than assuming it.
    """

    max_new_tokens: int = 512
    do_sample: bool = False
    temperature: float | None = None
    top_p: float | None = None
    enable_thinking: bool = False
    seed: int = 42


@dataclass(frozen=True)
class GenerationRequest:
    """One generation call: a user query, optional system prompt, and condition label."""

    query: str
    language: str  # "en" | "ar"
    condition: str  # "B0" | "B1" | ...
    system_prompt: str | None = None
    item_id: str | None = None
    metadata: dict = field(default_factory=dict)


@dataclass(frozen=True)
class GenerationResult:
    """One generation response with full reproducibility metadata (paper.md §14)."""

    request: GenerationRequest
    response_text: str
    model_id: str
    model_revision: str | None
    backend: str  # "transformers" | "vllm"
    generation_config: GenerationConfig
    thinking_mode_verified_disabled: bool
    load_seconds: float | None
    latency_ms: float
    prompt_tokens: int
    completion_tokens: int
    raw_output_contains_think_tag: bool


def contains_think_tag(text: str) -> bool:
    """Detect a leaked `<think>` reasoning trace in generated text.

    Used to empirically verify non-thinking mode actually suppressed the reasoning trace,
    rather than trusting the `enable_thinking=False` flag was honored (paper.md §0 rule 2:
    do not write claims the corresponding check hasn't actually run).
    """
    return "<think>" in text or "</think>" in text
