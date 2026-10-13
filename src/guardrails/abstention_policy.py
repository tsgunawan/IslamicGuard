"""Abstention / escalation decision policy (T13, paper.md Sec 9 flow, Sec 4 'human scholarly
authority' + 'epistemic caution' constructs).

Combines T11's deterministic provenance flags, T12's claim-evidence faithfulness verdicts, and
this task's madhhab-context assessment into one of four actions per paper.md Sec 9's flow:
PASS / REGENERATE WITH EVIDENCE / ABSTAIN / ESCALATE TO QUALIFIED SCHOLAR.

REGENERATE WITH EVIDENCE is implemented here as a POLICY DECISION ONLY -- this module decides
that a regeneration attempt would be warranted and says why (via guardrail_flags), but does not
itself implement a regeneration loop (re-prompting the generator with corrective instructions).
That loop is real follow-up engineering work, not built in this task; every REGENERATE_WITH_
EVIDENCE decision from this module should be read as "flagged for regeneration," not "already
regenerated."

Critical design constraint from T12 (results/error_analysis/t12_faithfulness_on_b2.jsonl and
STATUS.md's T12 entry, failure mode 4): T12's NLI-based faithfulness checker can score an
honest model admission of insufficient evidence (e.g. "none of the retrieved passages mention
X") as `contradicted` -- which is backwards for a guardrail that should REWARD appropriate
epistemic caution, not penalize it. This module's `is_meta_evidence_claim` heuristic excludes
such self-referential/hedging claims from the substantive contradiction-rate calculation before
making a PASS/REGENERATE/ABSTAIN decision, precisely to avoid inheriting that miscalibration.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from src.guardrails.madhhab_policy import MadhhabContext, response_surfaces_plurality
from src.validators.faithfulness_validator import ClaimCheck, ClaimVerdict
from src.validators.schema import FlagCategory, QuotationCheck

# Threshold on the NOT-addressed-by-evidence share of *substantive* (non-meta) claims above
# which the response is treated as having genuinely insufficient evidence, warranting
# abstention rather than a pass/regenerate decision. Not independently calibrated against a
# labelled set (same caveat as FIQH_RELEVANCE_MIN_SCORE in madhhab_policy.py) -- a documented,
# reasonable-but-unvalidated engineering default, to be revisited once T14+ has enough scale
# to calibrate it properly.
NOT_ADDRESSED_ABSTAIN_THRESHOLD = 0.8

# Threshold on the contradicted share of substantive claims above which a regeneration
# attempt is warranted (evidence exists, the model just disagreed with it on enough claims
# that regenerating with more explicit grounding is worth trying).
CONTRADICTION_REGENERATE_THRESHOLD = 0.3


class Action(str, Enum):
    PASS = "pass"
    REGENERATE_WITH_EVIDENCE = "regenerate_with_evidence"
    ABSTAIN = "abstain"
    ESCALATE = "escalate"


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass
class AbstentionDecision:
    action: Action
    risk_level: RiskLevel
    evidence_sufficient: bool | None  # None only when ESCALATE short-circuits before assessment
    guardrail_flags: list[str] = field(default_factory=list)
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return dict(
            action=self.action.value,
            risk_level=self.risk_level.value,
            evidence_sufficient=self.evidence_sufficient,
            guardrail_flags=self.guardrail_flags,
            notes=self.notes,
        )


# --- Personal-fatwa / high-risk-ruling heuristic (paper.md Sec 4 "human scholarly authority") ---
#
# Documented, deliberately conservative heuristic: first-person situational phrasing combined
# with a request for a personal ruling. This is NOT a semantic classifier and will miss
# indirectly-phrased personal questions and may over-trigger on hypothetical "what if someone..."
# questions that are not truly personal -- flagged as a known limitation, not claimed to be
# comprehensive. A real classifier (e.g. a small fine-tuned model) is a reasonable follow-up,
# out of scope here.
_PERSONAL_PRONOUN_RE = re.compile(r"\b(i|my|me|myself|i'm|i've|i'd)\b", re.IGNORECASE)
_RULING_REQUEST_RE = re.compile(
    r"\b(should i|can i|am i (allowed|permitted|obligated|required)|"
    r"is it (permissible|halal|haram|forbidden|obligatory|sinful) for me|"
    r"what (should|must) i do|do i (have to|need to)|is my .* (valid|permissible|sinful))\b",
    re.IGNORECASE,
)


def classify_risk(query: str) -> RiskLevel:
    """HIGH if the query reads as a request for a personalized ruling on the asker's own
    specific situation (an autonomous-fatwa request, per paper.md Sec 4's "human scholarly
    authority" construct: the model is not an autonomous mufti). LOW/MEDIUM otherwise -- this
    module does not currently distinguish LOW from MEDIUM (a documented simplification; the
    ablation's headline distinction is HIGH-risk-escalate vs. not).
    """
    if _RULING_REQUEST_RE.search(query) and _PERSONAL_PRONOUN_RE.search(query):
        return RiskLevel.HIGH
    return RiskLevel.LOW


# --- Meta/self-referential evidence-sufficiency claims (T12 failure mode 4) ---
#
# Phrases a model uses to honestly acknowledge that the retrieved evidence doesn't address the
# question, or that it is uncertain -- these must not be scored as ordinary substantive claims
# for contradiction-rate purposes. Documented, non-exhaustive keyword heuristic (the same kind
# of "good enough, not perfect, honestly limited" heuristic used elsewhere in this module).
_META_EVIDENCE_PATTERNS = [
    re.compile(p, re.IGNORECASE)
    for p in [
        r"none of the retrieved passages",
        r"no relevant (passage|evidence|source)",
        r"not (directly )?(addressed|mentioned|covered) (by|in) the retrieved",
        r"i am unsure",
        r"i'm unsure",
        r"cannot (determine|find|confirm)",
        r"not (clear|possible to determine) from the (retrieved|available) (passages|evidence)",
        r"do(es)? not (appear|seem) to (be )?(a commonly recognized|address)",
    ]
]


def is_meta_evidence_claim(claim_text: str) -> bool:
    return any(pat.search(claim_text) for pat in _META_EVIDENCE_PATTERNS)


def decide_action(
    query: str,
    response_text: str,
    quotation_checks: list[QuotationCheck],
    claim_checks: list[ClaimCheck],
    madhhab_context: MadhhabContext,
    n_retrieved: int,
) -> AbstentionDecision:
    """The core B5 decision. See module docstring for the T12-derived design constraint this
    implements (excluding meta-evidence claims from the contradiction-rate calculation).
    """
    risk = classify_risk(query)
    if risk == RiskLevel.HIGH:
        return AbstentionDecision(
            action=Action.ESCALATE,
            risk_level=risk,
            evidence_sufficient=None,
            guardrail_flags=["high_risk_personal_ruling_request"],
            notes="Query reads as a request for a personalized ruling on the asker's own "
            "situation; escalated to a qualified human scholar per paper.md Sec 4's "
            "'human scholarly authority' construct, without assessing evidence sufficiency "
            "(the authority-boundary concern applies regardless of evidence quality).",
        )

    flags: list[str] = []
    substantive = [c for c in claim_checks if not is_meta_evidence_claim(c.claim_text)]
    meta = [c for c in claim_checks if is_meta_evidence_claim(c.claim_text)]
    if meta:
        flags.append(f"meta_evidence_claims_excluded_from_contradiction_check:{len(meta)}")

    n_sub = len(substantive)
    if n_retrieved == 0 or n_sub == 0:
        action = Action.ABSTAIN
        evidence_sufficient = False
        flags.append("no_checkable_substantive_evidence")
        notes = (
            f"n_retrieved={n_retrieved}, substantive_claims={n_sub} (meta claims excluded "
            f"separately) -- nothing to assess claim-evidence support against."
        )
    else:
        n_not_addr = sum(1 for c in substantive if c.verdict == ClaimVerdict.NOT_ADDRESSED_BY_EVIDENCE)
        n_contra = sum(1 for c in substantive if c.verdict == ClaimVerdict.CONTRADICTED)
        not_addr_ratio = n_not_addr / n_sub
        contra_ratio = n_contra / n_sub
        fabricated = any(q.flag == FlagCategory.FABRICATED_CITATION for q in quotation_checks)
        misquoted = any(q.flag == FlagCategory.MISQUOTED for q in quotation_checks)

        if not_addr_ratio >= NOT_ADDRESSED_ABSTAIN_THRESHOLD:
            action = Action.ABSTAIN
            evidence_sufficient = False
            flags.append("insufficient_evidence_coverage")
            notes = f"{n_not_addr}/{n_sub} substantive claims not addressed by any retrieved evidence."
        elif fabricated:
            action = Action.REGENERATE_WITH_EVIDENCE
            evidence_sufficient = True
            flags.append("fabricated_citation_detected")
            notes = "T11 found a citation to a source that does not exist in the corpus."
        elif contra_ratio >= CONTRADICTION_REGENERATE_THRESHOLD:
            action = Action.REGENERATE_WITH_EVIDENCE
            evidence_sufficient = True
            flags.append("high_contradiction_rate")
            notes = f"{n_contra}/{n_sub} substantive claims contradicted their own best-matching retrieved evidence."
        elif misquoted:
            action = Action.REGENERATE_WITH_EVIDENCE
            evidence_sufficient = True
            flags.append("misquotation_detected")
            notes = "T11 found a citation whose quoted text does not match the corpus's canonical text."
        else:
            action = Action.PASS
            evidence_sufficient = True
            notes = f"{n_sub - n_not_addr - n_contra}/{n_sub} substantive claims supported; no provenance flags."

    # Madhhab plurality check can escalate an otherwise-PASS decision to REGENERATE.
    if action == Action.PASS and not response_surfaces_plurality(response_text, madhhab_context):
        action = Action.REGENERATE_WITH_EVIDENCE
        flags.append("madhhab_plurality_not_surfaced")
        notes += (
            f" However, fiqh record {madhhab_context.fiqh_record_id} has agreement="
            f"'Disagreement' and the response does not mention >=2 madhhab schools by name."
        )

    return AbstentionDecision(
        action=action, risk_level=risk, evidence_sufficient=evidence_sufficient,
        guardrail_flags=flags, notes=notes.strip(),
    )
