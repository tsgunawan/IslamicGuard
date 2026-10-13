"""B5 = full IslamicGuard pipeline (T13, paper.md Sec 9 architecture diagram + Sec 9.2 schema).

Wires together every component built in T08 (retrieval), T10-style generation, T11
(deterministic Qur'an/Hadith provenance validators), and this task's madhhab policy +
abstention/escalation policy, into one function producing the exact structured output fields
paper.md Sec 9.2 specifies: answer, risk_level, retrieved_sources, claims, quotation_checks,
madhhab_context, evidence_sufficient, action, guardrail_flags, latency_ms.

Deliberately reuses B2's generation step as-is (same retrieval, same prompt template,
prompts/b2_rag.md) -- B2 through B5 in paper.md Sec 10's ablation table are meant to isolate
each guardrail component's marginal contribution on top of the SAME underlying generation, not
to compare different generation strategies. Only the post-hoc validation/policy layer differs.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any

from src.guardrails.abstention_policy import AbstentionDecision, decide_action
from src.guardrails.madhhab_policy import MadhhabContext, assess_madhhab_context
from src.rag.generate import RetrievedPassage, passages_to_log
from src.validators import hadith_validator, quran_validator
from src.validators.claim_segmenter import segment_claims
from src.validators.faithfulness_validator import ClaimCheck, check_claim, evidence_texts_from_retrieval_entry
from src.validators.schema import QuotationCheck


@dataclass
class IslamicGuardResult:
    """Mirrors paper.md Sec 9.2's per-response output schema exactly."""

    answer: str
    risk_level: str
    retrieved_sources: list[dict[str, Any]]
    claims: list[dict[str, Any]]
    quotation_checks: list[dict[str, Any]]
    madhhab_context: dict[str, Any]
    evidence_sufficient: bool | None
    action: str
    guardrail_flags: list[str]
    latency_ms: float

    def to_dict(self) -> dict[str, Any]:
        return dict(
            answer=self.answer,
            risk_level=self.risk_level,
            retrieved_sources=self.retrieved_sources,
            claims=self.claims,
            quotation_checks=self.quotation_checks,
            madhhab_context=self.madhhab_context,
            evidence_sufficient=self.evidence_sufficient,
            action=self.action,
            guardrail_flags=self.guardrail_flags,
            latency_ms=self.latency_ms,
        )


def run_guardrails(
    query: str,
    response_text: str,
    passages: list[RetrievedPassage],
    validation_latency_start: float | None = None,
) -> IslamicGuardResult:
    """Run every post-generation guardrail stage (T11 provenance + T13 madhhab/abstention) on
    an already-generated `response_text` (from B2-style retrieval+generation) and assemble the
    Sec 9.2 output schema. Does NOT itself call the generator or retriever -- callers (e.g.
    scripts/run_islamicguard_b5.py) are responsible for retrieval+generation, matching B2's
    pipeline, and pass the results in here for validation/policy.

    `validation_latency_start`: if given (a `time.perf_counter()` value taken right before
    generation started), `latency_ms` in the returned result measures end-to-end
    retrieval+generation+validation time; if omitted, only validation time is measured
    (documented either way via which the caller chose, not silently ambiguous).
    """
    t0 = validation_latency_start if validation_latency_start is not None else time.perf_counter()

    quotation_checks: list[QuotationCheck] = (
        quran_validator.validate_text(response_text) + hadith_validator.validate_text(response_text)
    )

    claims = segment_claims(response_text)
    passages_logged = passages_to_log(passages)
    evidence_passages = evidence_texts_from_retrieval_entry({"passages": passages_logged})
    claim_checks: list[ClaimCheck] = [check_claim(c.text, evidence_passages) for c in claims]

    madhhab_context: MadhhabContext = assess_madhhab_context(passages)

    decision: AbstentionDecision = decide_action(
        query=query,
        response_text=response_text,
        quotation_checks=quotation_checks,
        claim_checks=claim_checks,
        madhhab_context=madhhab_context,
        n_retrieved=len(passages),
    )

    latency_ms = (time.perf_counter() - t0) * 1000.0

    return IslamicGuardResult(
        answer=response_text,
        risk_level=decision.risk_level.value,
        retrieved_sources=passages_logged,
        claims=[c.to_dict() for c in claim_checks],
        quotation_checks=[q.to_dict() for q in quotation_checks],
        madhhab_context=madhhab_context.to_dict(),
        evidence_sufficient=decision.evidence_sufficient,
        action=decision.action.value,
        guardrail_flags=decision.guardrail_flags,
        latency_ms=round(latency_ms, 2),
    )
