"""Structured output schema for T11's deterministic provenance validators.

Compatible with paper.md Sec 9.2's per-response output schema (quotation_checks,
guardrail_flags). Kept deliberately separate from claim-evidence verification
(T12: "does the retrieved/cited source actually support the claim") and from
madhhab/abstention policy (T13) -- this module answers only "does the cited
source exist" and "does the quoted text match it", per paper.md Sec 9.1's
"separate source existence from source supports claim."
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class MatchTier(str, Enum):
    EXACT = "exact"
    NORMALIZED_FUZZY = "normalized_fuzzy"
    NO_MATCH = "no_match"
    NO_QUOTE_GIVEN = "no_quote_given"


class FlagCategory(str, Enum):
    VERIFIED = "verified"  # citation exists; quote (if given) matches
    MISQUOTED = "misquoted"  # citation exists; quote given but does not match
    FABRICATED_CITATION = "fabricated_citation"  # citation does not exist in the corpus
    UNPARSEABLE_CITATION = "unparseable_citation"  # text looked like a citation attempt but couldn't be parsed


@dataclass
class QuotationCheck:
    citation_raw: str
    citation_type: str  # "quran" | "hadith"
    parsed_reference: dict = field(default_factory=dict)
    exists: bool = False
    match_tier: MatchTier = MatchTier.NO_QUOTE_GIVEN
    matched_record_id: str | None = None
    grading: object | None = None  # hadith only: list[{scholar, grade}] or the collection-authenticated string
    flag: FlagCategory = FlagCategory.UNPARSEABLE_CITATION
    notes: str = ""

    def to_dict(self) -> dict:
        d = dict(
            citation_raw=self.citation_raw,
            citation_type=self.citation_type,
            parsed_reference=self.parsed_reference,
            exists=self.exists,
            match_tier=self.match_tier.value,
            matched_record_id=self.matched_record_id,
            grading=self.grading,
            flag=self.flag.value,
            notes=self.notes,
        )
        return d
