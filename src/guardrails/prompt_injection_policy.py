"""Conservative pre-retrieval prompt-injection screen for T17.

This is an intentionally narrow pattern policy, not a general jailbreak detector.  Its role is
to keep instructions that attempt to override evidence/provenance controls from reaching the
retrieval-and-generation path.  Unmatched attacks remain a documented false-negative risk.
"""
from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class InjectionScreen:
    detected: bool
    categories: list[str]


_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("instruction_override", re.compile(r"\b(ignore|disregard|override|forget)\b.{0,60}\b(previous|above|system|instructions?|rules?|context)\b", re.I)),
    ("role_impersonation", re.compile(r"\b(you are now|act as|system message|developer message)\b", re.I)),
    ("context_exfiltration", re.compile(r"\b(reveal|print|repeat|dump)\b.{0,80}\b(retrieved|context|system prompt|instructions?)\b", re.I)),
    ("delimiter_smuggling", re.compile(r"<\s*/?(system|developer|tool|instruction)\s*>", re.I)),
    ("fabrication_coercion", re.compile(r"\b(invent|fabricate|make up)\b.{0,80}\b(verse|hadith|citation|source)\b", re.I)),
    ("arabic_override", re.compile(r"(تجاهل|تخطى).{0,50}(التعليمات|القواعد|السابق|النظام)|اكشف.{0,50}(السياق|التعليمات)", re.I)),
)


def screen_prompt_injection(query: str) -> InjectionScreen:
    """Return all matched attack categories; normal religious questions must return clear."""
    categories = [category for category, pattern in _PATTERNS if pattern.search(query)]
    return InjectionScreen(detected=bool(categories), categories=categories)
