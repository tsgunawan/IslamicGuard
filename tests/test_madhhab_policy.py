"""Tests for src.guardrails.madhhab_policy (T13).

Uses two real records from data/corpus/fiqh.jsonl (verified by direct inspection):
  - fiqh:0 -- agreement="Agreement" (silent "Amin" during prayer -- all 4 schools agree).
  - fiqh:1 -- agreement="Disagreement" (qabd/hand position in prayer -- Malikis differ from
    the other three schools). Confirmed present in the corpus before writing these tests.
"""

from __future__ import annotations

from src.guardrails.madhhab_policy import assess_madhhab_context, response_surfaces_plurality


def _passage(layer: str, record_id: str, score: float) -> dict:
    return {"layer": layer, "record_id": record_id, "score": score}


class TestAssessMadhhabContext:
    def test_no_fiqh_passages_not_relevant(self):
        ctx = assess_madhhab_context([_passage("quran", "quran:1:1", 0.9)])
        assert ctx.is_fiqh_relevant is False

    def test_low_score_fiqh_passage_not_relevant(self):
        # Below FIQH_RELEVANCE_MIN_SCORE -- retrieved but not treated as genuinely on-topic.
        ctx = assess_madhhab_context([_passage("fiqh", "fiqh:1", 0.1)])
        assert ctx.is_fiqh_relevant is False

    def test_agreement_record_surfaces_no_disclosure(self):
        ctx = assess_madhhab_context([_passage("fiqh", "fiqh:0", 0.9)])
        assert ctx.is_fiqh_relevant is True
        assert ctx.agreement == "Agreement"
        assert ctx.disclosure_note == ""
        assert len(ctx.madhhab_positions) == 4

    def test_disagreement_record_produces_disclosure_naming_all_schools(self):
        ctx = assess_madhhab_context([_passage("fiqh", "fiqh:1", 0.9)])
        assert ctx.is_fiqh_relevant is True
        assert ctx.agreement == "Disagreement"
        assert ctx.disclosure_note != ""
        assert "fiqh:1" == ctx.fiqh_record_id
        for school in ("hanafi", "maliki", "shafeii", "hanbali"):
            assert any(p["madhhab"] == school for p in ctx.madhhab_positions)

    def test_picks_highest_scoring_fiqh_passage_among_several(self):
        ctx = assess_madhhab_context(
            [_passage("fiqh", "fiqh:0", 0.55), _passage("fiqh", "fiqh:1", 0.91)]
        )
        assert ctx.fiqh_record_id == "fiqh:1"


class TestResponseSurfacesPlurality:
    def test_not_applicable_when_not_fiqh_relevant(self):
        ctx = assess_madhhab_context([])
        assert response_surfaces_plurality("any text at all", ctx) is True

    def test_not_applicable_when_agreement(self):
        ctx = assess_madhhab_context([_passage("fiqh", "fiqh:0", 0.9)])
        assert response_surfaces_plurality("just one sentence, no school names", ctx) is True

    def test_disagreement_with_only_one_school_named_fails(self):
        ctx = assess_madhhab_context([_passage("fiqh", "fiqh:1", 0.9)])
        text = "According to the Hanafi school, qabd is a sunnah act in prayer."
        assert response_surfaces_plurality(text, ctx) is False

    def test_disagreement_with_two_schools_named_passes(self):
        ctx = assess_madhhab_context([_passage("fiqh", "fiqh:1", 0.9)])
        text = (
            "The Hanafi, Shafi'i, and Hanbali schools hold that qabd is sunnah, while the "
            "Maliki school considers it disliked (makruh) in obligatory prayer."
        )
        assert response_surfaces_plurality(text, ctx) is True

    def test_disagreement_with_zero_schools_named_fails(self):
        ctx = assess_madhhab_context([_passage("fiqh", "fiqh:1", 0.9)])
        assert response_surfaces_plurality("Scholars differ on this matter.", ctx) is False
