"""Tests for src.guardrails.abstention_policy (T13) -- the acceptance-criterion test cases
paper.md Sec 15 T13 requires: insufficient evidence, disagreement, high-risk personal
questions, and (per RQ7's over-refusal concern) a benign well-evidenced question that must
still PASS rather than be over-flagged.
"""

from __future__ import annotations

from src.guardrails.abstention_policy import Action, RiskLevel, classify_risk, decide_action
from src.guardrails.madhhab_policy import assess_madhhab_context
from src.validators.faithfulness_validator import ClaimCheck, ClaimVerdict
from src.validators.schema import FlagCategory, QuotationCheck

NO_MADHHAB = assess_madhhab_context([])  # is_fiqh_relevant=False -- neutral for non-fiqh tests


def _claim(text: str, verdict: ClaimVerdict) -> ClaimCheck:
    return ClaimCheck(claim_text=text, verdict=verdict, n_evidence_considered=1)


class TestClassifyRisk:
    def test_general_knowledge_question_is_low_risk(self):
        assert classify_risk("What is the ruling on saying Amin during silent prayer?") == RiskLevel.LOW

    def test_personal_ruling_request_is_high_risk(self):
        q = "I am traveling for work -- is it permissible for me to combine my prayers?"
        assert classify_risk(q) == RiskLevel.HIGH

    def test_hypothetical_third_person_question_stays_low_risk(self):
        # Documented heuristic limitation: only first-person phrasing is caught.
        q = "Is it permissible for a traveler to combine prayers?"
        assert classify_risk(q) == RiskLevel.LOW


class TestDecideActionInsufficientEvidence:
    def test_no_retrieval_at_all_abstains(self):
        d = decide_action(
            query="What is the ruling on an obscure, unretrieved topic?",
            response_text="I could not find relevant information on this.",
            quotation_checks=[],
            claim_checks=[],
            madhhab_context=NO_MADHHAB,
            n_retrieved=0,
        )
        assert d.action == Action.ABSTAIN
        assert d.evidence_sufficient is False
        assert "no_checkable_substantive_evidence" in d.guardrail_flags

    def test_only_meta_evidence_claims_abstains_not_falsely_flagged_contradicted(self):
        """The exact T12-derived design constraint: an honest 'no evidence found' admission
        must not be treated as a substantive contradiction driving a REGENERATE decision --
        it should route to ABSTAIN via the meta-claim exclusion, per this module's docstring.
        """
        claims = [_claim("None of the retrieved passages mention this topic.", ClaimVerdict.CONTRADICTED)]
        d = decide_action(
            query="Some fairly specific question.",
            response_text="None of the retrieved passages mention this topic. I am unsure.",
            quotation_checks=[],
            claim_checks=claims,
            madhhab_context=NO_MADHHAB,
            n_retrieved=9,
        )
        assert d.action == Action.ABSTAIN
        assert any(f.startswith("meta_evidence_claims_excluded") for f in d.guardrail_flags)
        assert "no_checkable_substantive_evidence" in d.guardrail_flags

    def test_mostly_not_addressed_substantive_claims_abstains(self):
        # 3/3 = 100% not-addressed, well above NOT_ADDRESSED_ABSTAIN_THRESHOLD (0.8) -- a
        # clean case of genuinely insufficient evidence, distinct from the meta-claim test
        # above (these are ordinary substantive claims, not self-referential hedging).
        claims = [
            _claim("Claim one is unrelated to any retrieved passage.", ClaimVerdict.NOT_ADDRESSED_BY_EVIDENCE),
            _claim("Claim two is also unrelated.", ClaimVerdict.NOT_ADDRESSED_BY_EVIDENCE),
            _claim("Claim three is unrelated too.", ClaimVerdict.NOT_ADDRESSED_BY_EVIDENCE),
        ]
        d = decide_action(
            query="A broad question with weak retrieval.",
            response_text="...",
            quotation_checks=[],
            claim_checks=claims,
            madhhab_context=NO_MADHHAB,
            n_retrieved=3,
        )
        assert d.action == Action.ABSTAIN
        assert d.evidence_sufficient is False


class TestDecideActionDisagreement:
    def test_ikhtilaf_not_surfaced_triggers_regenerate(self):
        madhhab_ctx = assess_madhhab_context([{"layer": "fiqh", "record_id": "fiqh:1", "score": 0.9}])
        claims = [_claim("Qabd is a sunnah act in prayer.", ClaimVerdict.SUPPORTED)]
        d = decide_action(
            query="What is the ruling on qabd (hand position) in prayer?",
            response_text="According to the Hanafi school, qabd is a sunnah act in prayer.",
            quotation_checks=[],
            claim_checks=claims,
            madhhab_context=madhhab_ctx,
            n_retrieved=9,
        )
        assert d.action == Action.REGENERATE_WITH_EVIDENCE
        assert "madhhab_plurality_not_surfaced" in d.guardrail_flags

    def test_ikhtilaf_surfaced_passes(self):
        madhhab_ctx = assess_madhhab_context([{"layer": "fiqh", "record_id": "fiqh:1", "score": 0.9}])
        claims = [_claim("Most schools consider qabd sunnah in prayer.", ClaimVerdict.SUPPORTED)]
        d = decide_action(
            query="What is the ruling on qabd (hand position) in prayer?",
            response_text=(
                "The Hanafi, Shafi'i, and Hanbali schools hold qabd is sunnah in prayer, "
                "while the Maliki school considers it disliked in obligatory prayer."
            ),
            quotation_checks=[],
            claim_checks=claims,
            madhhab_context=madhhab_ctx,
            n_retrieved=9,
        )
        assert d.action == Action.PASS


class TestDecideActionHighRisk:
    def test_personal_ruling_question_escalates_regardless_of_evidence(self):
        d = decide_action(
            query="I am traveling for work -- is it permissible for me to combine my prayers?",
            response_text="Some answer text.",
            quotation_checks=[],
            claim_checks=[_claim("Travelers may combine prayers.", ClaimVerdict.SUPPORTED)],
            madhhab_context=NO_MADHHAB,
            n_retrieved=5,
        )
        assert d.action == Action.ESCALATE
        assert d.risk_level == RiskLevel.HIGH
        assert d.evidence_sufficient is None
        assert "high_risk_personal_ruling_request" in d.guardrail_flags


class TestDecideActionProvenanceFlags:
    def test_fabricated_citation_triggers_regenerate(self):
        qc = [QuotationCheck(citation_raw="Sunan Al-Fake 999", citation_type="hadith", flag=FlagCategory.FABRICATED_CITATION)]
        claims = [_claim("A well-supported claim.", ClaimVerdict.SUPPORTED)]
        d = decide_action(
            query="A question citing a nonexistent hadith.",
            response_text="...",
            quotation_checks=qc,
            claim_checks=claims,
            madhhab_context=NO_MADHHAB,
            n_retrieved=5,
        )
        assert d.action == Action.REGENERATE_WITH_EVIDENCE
        assert "fabricated_citation_detected" in d.guardrail_flags

    def test_misquoted_citation_triggers_regenerate(self):
        qc = [QuotationCheck(citation_raw="Qur'an 112:1", citation_type="quran", flag=FlagCategory.MISQUOTED)]
        claims = [_claim("A well-supported claim.", ClaimVerdict.SUPPORTED)]
        d = decide_action(
            query="A question with a misquoted verse.",
            response_text="...",
            quotation_checks=qc,
            claim_checks=claims,
            madhhab_context=NO_MADHHAB,
            n_retrieved=5,
        )
        assert d.action == Action.REGENERATE_WITH_EVIDENCE
        assert "misquotation_detected" in d.guardrail_flags

    def test_high_contradiction_rate_triggers_regenerate(self):
        claims = [
            _claim("Claim one contradicts the evidence.", ClaimVerdict.CONTRADICTED),
            _claim("Claim two also contradicts.", ClaimVerdict.CONTRADICTED),
            _claim("Claim three is fine.", ClaimVerdict.SUPPORTED),
        ]
        d = decide_action(
            query="A question with a mostly-wrong answer.",
            response_text="...",
            quotation_checks=[],
            claim_checks=claims,
            madhhab_context=NO_MADHHAB,
            n_retrieved=5,
        )
        assert d.action == Action.REGENERATE_WITH_EVIDENCE
        assert "high_contradiction_rate" in d.guardrail_flags


class TestDecideActionBenignPass:
    def test_benign_well_evidenced_question_passes_without_over_refusal(self):
        """paper.md RQ7 / Sec 7's over-refusal concern: a benign question with good evidence
        and no provenance/madhhab issues must PASS, not be swept into ABSTAIN/REGENERATE."""
        claims = [
            _claim("Ablution is required before prayer.", ClaimVerdict.SUPPORTED),
            _claim("This is confirmed by multiple hadith.", ClaimVerdict.SUPPORTED),
        ]
        d = decide_action(
            query="Is ablution required before prayer?",
            response_text="Yes, ablution (wudu) is required before performing the prayer.",
            quotation_checks=[],
            claim_checks=claims,
            madhhab_context=NO_MADHHAB,
            n_retrieved=5,
        )
        assert d.action == Action.PASS
        assert d.evidence_sufficient is True
        assert d.guardrail_flags == []
