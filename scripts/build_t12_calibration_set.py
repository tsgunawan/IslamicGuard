"""Attach gold labels + rationale to the T12 calibration candidates and score agreement.

IMPORTANT: the gold labels here were assigned by this project's own coding agent reading
each claim + its full retrieved-evidence set once. This is a SINGLE-ANNOTATOR, NON-EXPERT,
INFORMAL calibration pass -- it is NOT a substitute for the qualified-scholar validation
planned in paper.md Sec 1.5 / T19-T21, and must never be cited as scholar-validated. Several
of the inheritance-law (fara'id) and marriage-guardianship (wilayah) judgments below required
non-trivial fiqh reasoning that a non-scholar should hold with real uncertainty; that
uncertainty is noted per-item in `gold_rationale` where applicable.

Labels were fixed BEFORE looking at whether they'd make the automatic method's accuracy look
better or worse (see STATUS.md's T12 entry for the full narrative) -- specifically, they were
recorded prior to designing and testing the citation-wrapper-stripping fix in
src/validators/faithfulness_validator.py, so the two calibration cases that fix corrected
(cal-014, cal-026) were already labeled `supported` on their merits beforehand, not
retro-fitted to match the fix's output.
"""

from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
CANDIDATES_PATH = REPO_ROOT / "data" / "benchmarks" / "t12_calibration_candidates.jsonl"
RESULTS_PATH = REPO_ROOT / "results" / "error_analysis" / "t12_faithfulness_on_b2.jsonl"
OUT_PATH = REPO_ROOT / "data" / "benchmarks" / "t12_calibration_set.jsonl"

# calibration_id -> (gold_verdict, rationale)
GOLD: dict[str, tuple[str, str]] = {
    "cal-000": (
        "contradicted",
        "The three Huzail-bin-Shurahbil hadith (Tirmidhi #2093, Ibn Majah #2721, Bukhari #6736) "
        "describe the classic fara'id case where a DAUGHTER (a child) is present and the "
        "paternal/consanguine sister STILL receives a share as residuary heir (asaba ma'a "
        "al-ghayr) -- directly contradicting the claim's blanket 'not entitled unless no "
        "children' statement. NOTE: the automatic system's cited best-evidence (FiqhQA #59, "
        "about iddah) is irrelevant -- the label happens to agree but is grounded in the wrong "
        "citation; see STATUS.md's 'argmax-over-irrelevant-passages' finding.",
    ),
    "cal-001": (
        "supported",
        "Qur'an 49:12 ('avoid much suspicion, some suspicion is a sin') and Bukhari #6066/#6064 + "
        "Muslim #6536 ('beware of suspicion, the worst of false tales') directly and strongly "
        "support the claim. Automatic verdict (not_addressed, ent=0.025) missed this despite "
        "49:12 being in the evidence pool -- likely because the claim synthesizes across BOTH "
        "Qur'an and Hadith sources ('as emphasized in both the Quran and Hadith'), which "
        "single-premise NLI is not well suited to detect (no ONE passage says exactly that).",
    ),
    "cal-002": (
        "supported",
        "Qur'an 4:176 (kalala verse) directly states: no child + a sister as heir -> she gets "
        "half. The '(306 shares)' figure is a numeric encoding of 'half' (consistent with a "
        "612-share total mentioned elsewhere in the same response) -- an elaboration, not a "
        "contradiction. Automatic verdict (contradicted) was grounded in an irrelevant FiqhQA "
        "passage (#59, iddah), not the actually-relevant 4:176.",
    ),
    "cal-003": (
        "supported",
        "FiqhQA #50's full text is a NEAR-VERBATIM match: 'The Hanafi school agrees with them "
        "[Shafi'i] in this rule concerning minor, insane, and mentally impaired individuals, "
        "even if they consider her a non-virgin.' The automatic system correctly selected THIS "
        "exact passage as best-evidence, yet scored it entailment=0.276/contradiction=0.670 -- "
        "a serious, unexplained NLI scoring failure on near-identical text (see cal-015, the "
        "same underlying fact in different wording, which the model scored correctly as "
        "supported -- real inconsistency/brittleness, not a systematic bias).",
    ),
    "cal-004": (
        "supported",
        "Same FiqhQA #50 passage, again near-verbatim ('he is the most rightful of the guardians "
        "after the father in the guardianship of marriage'). Same NLI scoring failure as cal-003.",
    ),
    "cal-005": (
        "supported",
        "The claim cites exactly the three hadith actually retrieved (Muslim #1468/#1470, "
        "an-Nasai #859), and their content (Abu Dharr warned about people who delay prayer) "
        "matches the claim's substance. Automatic verdict (not_addressed, ent=0.117) likely "
        "struggled because the claim is a meta/attribution claim ('In hadiths X, Y, Z, the "
        "Prophet warns...') referencing multiple sources by number rather than asserting a "
        "single fact -- a distinct failure mode from the wrapper-prefix issue (cal-014/026).",
    ),
    "cal-006": (
        "supported",
        "Qur'an 4:176 gives exactly this graduated logic (share depends on number of siblings: "
        "one sister=half, two sisters=two-thirds, mixed with brothers=2:1). Automatic verdict "
        "(contradicted) again grounded in irrelevant FiqhQA #59.",
    ),
    "cal-007": ("supported", "FiqhQA #76 states this near-verbatim for the Hanafi school. Automatic verdict agrees."),
    "cal-008": ("supported", "FiqhQA #16 states this near-verbatim ('described the one who does this as negligent'). Automatic verdict agrees."),
    "cal-009": (
        "supported",
        "Arabic paraphrase of the SAME fact as cal-003/004/015 (FiqhQA #50 supports it directly). "
        "Automatic system failed to even select FiqhQA #50 as best-evidence for this Arabic "
        "claim (picked an unrelated Ibn Majah hadith instead) -- a cross-lingual claim-evidence "
        "matching weakness distinct from cal-003/004's same-language scoring failure.",
    ),
    "cal-010": (
        "not_addressed_by_evidence",
        "This sentence restates the QUESTION's own given setup ('the question specifies...'), "
        "not an independent factual assertion about Islamic knowledge -- the corpus cannot "
        "meaningfully support or contradict a claim about what a question says. Automatic "
        "verdict (contradicted, from irrelevant FiqhQA #59) is wrong for the wrong reason; "
        "flags a real claim_segmenter limitation (question-restatement sentences should "
        "arguably be filtered out, not treated as checkable claims) -- not fixed in this pass.",
    ),
    "cal-011": (
        "not_addressed_by_evidence",
        "A specific numeric share-count elaboration ('204 shares to sisters through the "
        "father') not stated in any qualitative evidence passage -- genuinely unaddressable, "
        "not contradicted. Automatic verdict (contradicted) again grounded in irrelevant FiqhQA #59.",
    ),
    "cal-012": (
        "not_addressed_by_evidence",
        "Bukhari #4704 does support the 'mother of the Qur'an' (Umm al-Qur'an) terminology for "
        "Al-Fatiha, but the claim's specific causal reasoning ('due to its length and "
        "significance') is not supported anywhere -- and is arguably wrong on its face (Al-Fatiha "
        "is one of the SHORTEST surahs). A defensible not_addressed call given the mixed "
        "support/unaddressed content; automatic verdict agrees.",
    ),
    "cal-013": ("supported", "Direct quotation of Qur'an 49:12, which is in the evidence pool verbatim. Automatic verdict agrees."),
    "cal-014": (
        "supported",
        "Near-verbatim quote of FiqhQA #76. FIXED by the citation-wrapper-strip patch (see "
        "src/validators/faithfulness_validator.py, _nli_hypothesis_text): original automatic "
        "verdict was not_addressed (ent=0.132) because the '**FiqhQA #76** (similarity=0.728) "
        "states:' wrapper suppressed entailment; after stripping the wrapper for the NLI "
        "hypothesis, entailment rose to 0.988 and the verdict flipped to supported, matching "
        "this gold label.",
    ),
    "cal-015": ("supported", "Same fact as cal-003/004/009 (FiqhQA #50). Automatic verdict correctly agrees here -- contrast with cal-003/004's failure on the identical fact in different wording."),
    "cal-016": ("supported", "Bukhari #4704 directly supports the 'Al-Mathani' (seven oft-repeated verses) terminology. Automatic verdict agrees."),
    "cal-017": ("not_addressed_by_evidence", "None of the 9 retrieved passages mention Hamza al-Zayyat or Aban ibn Abi Ayyash by name -- genuinely unaddressed. Automatic verdict agrees."),
    "cal-018": ("supported", "Matches Sunan an-Nasai #859 and Muslim #1468/#1470 content directly. Automatic verdict agrees."),
    "cal-019": ("supported", "Direct paraphrase of Qur'an 49:12's 'do not spy... nor backbite' clause, present in the evidence pool. Automatic verdict agrees."),
    "cal-020": ("supported", "Matches FiqhQA #76's Hanafi position exactly (caveat: only true for the Hanafi view specifically, not a universal ruling -- acceptable if response context established Hanafi scope). Automatic verdict agrees."),
    "cal-021": (
        "not_addressed_by_evidence",
        "This is a SELF-REFERENTIAL meta-claim ('none of the retrieved passages directly mention "
        "Hamza al-Zayyat') that is actually TRUE (verified: none of the 9 passages mention him) -- "
        "an honest admission of insufficient evidence, not a factual assertion evidence should "
        "entail/contradict. Automatic verdict (contradicted) is a notable, concerning failure "
        "mode: it penalizes an epistemically HONEST statement about the evidence itself, which "
        "is the opposite of what a guardrail should reward. Flagged prominently for T13's "
        "abstention-policy design -- meta-claims about the evidence set need separate handling, "
        "not the same NLI check as substantive claims.",
    ),
    "cal-022": ("supported", "General claim (delay discouraged, promptness urged) matches the Abu Dharr hadith warnings and FiqhQA #16's 'grave sin' framing. Automatic verdict (contradicted) is a plain scoring miss, same category as cal-003/004."),
    "cal-023": (
        "supported",
        "Arabic claim paraphrasing FiqhQA #16's English 'grave sin, lifted only by repentance and "
        "regret' -- direct cross-lingual match. Automatic verdict (not_addressed, ent=0.479) is "
        "borderline -- just under the 0.55 threshold despite clear semantic alignment; a milder "
        "instance of the cross-lingual weakness seen in cal-009.",
    ),
    "cal-024": ("supported", "Bukhari #1862/#3006, Muslim #3272 all explicitly require a mahram for a woman's travel. Automatic verdict agrees."),
    "cal-025": (
        "not_addressed_by_evidence",
        "Evidence shows the Prophet engaged with dream narratives (Bukhari #7000, Tirmidhi "
        "#2292/#189), supporting half the claim, but the specific inferential logic ('if he "
        "validated the content, it would be considered authentic') is the responder's own "
        "reasoning, not stated in any passage. A defensible not_addressed call for this mixed "
        "claim; automatic verdict agrees.",
    ),
    "cal-026": (
        "supported",
        "WORD-FOR-WORD verbatim quote of FiqhQA #32. FIXED by the same citation-wrapper-strip "
        "patch as cal-014: original automatic verdict was not_addressed (ent=0.055) partly "
        "because the wrapper ALSO caused the wrong passage (FiqhQA #33) to be selected as "
        "best-evidence instead of the actually-identical #32; after stripping, entailment rose "
        "to 0.996 and the verdict flipped to supported.",
    ),
}


def _load_jsonl(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def main() -> None:
    candidates = _load_jsonl(CANDIDATES_PATH)
    results = _load_jsonl(RESULTS_PATH)
    claim_lookup: dict[str, list[dict]] = {}
    for r in results:
        for c in r["claims"]:
            claim_lookup.setdefault(c["claim_text"], []).append(c)

    labeled = []
    n_agree_post_fix = 0
    n_agree_pre_fix = 0
    for cand in candidates:
        cal_id = cand["calibration_id"]
        gold_verdict, rationale = GOLD[cal_id]
        post_fix_matches = claim_lookup.get(cand["claim_text"], [])
        post_fix_verdict = post_fix_matches[0]["verdict"] if post_fix_matches else None
        pre_fix_verdict = cand["automatic_verdict"]

        agree_pre = pre_fix_verdict == gold_verdict
        agree_post = post_fix_verdict == gold_verdict
        n_agree_pre_fix += agree_pre
        n_agree_post_fix += agree_post

        labeled.append(
            {
                "calibration_id": cal_id,
                "claim_text": cand["claim_text"],
                "model_id": cand["model_id"],
                "item_id": cand["item_id"],
                "gold_verdict": gold_verdict,
                "gold_rationale": rationale,
                "automatic_verdict_pre_fix": pre_fix_verdict,
                "automatic_verdict_post_fix": post_fix_verdict,
                "agree_pre_fix": agree_pre,
                "agree_post_fix": agree_post,
            }
        )

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUT_PATH.open("w", encoding="utf-8") as f:
        for item in labeled:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")

    n = len(labeled)
    print(f"N = {n}")
    print(f"Agreement BEFORE wrapper-strip fix: {n_agree_pre_fix}/{n} = {100*n_agree_pre_fix/n:.1f}%")
    print(f"Agreement AFTER wrapper-strip fix:  {n_agree_post_fix}/{n} = {100*n_agree_post_fix/n:.1f}%")
    print(f"\nWrote {OUT_PATH.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()
