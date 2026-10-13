# T11 Arabic-parser fix — re-validation of saved B5 responses

Provenance checks re-run with the Arabic-form citation parser; claim checks and madhhab context reused from the stored traces;
B5 action recomputed with the unchanged policy. No text was regenerated.

## 1. Effect on the 41-item benchmark

| Model | Policy replay reproduces stored action | Arabic answers with >=1 citation checked (before -> after) | Citations checked, all items (before -> after) | Items whose action changed | Action counts before | Action counts after |
|---|---:|---|---|---:|---|---|
| 8B | 41/41 | 1/11 -> 9/11 | 51 -> 72 | 2 | abstain 15, escalate 1, pass 14, regenerate 11 | abstain 15, escalate 1, pass 12, regenerate 13 |
| 14B | 41/41 | 0/11 -> 7/11 | 34 -> 47 | 1 | abstain 11, escalate 1, pass 18, regenerate 11 | abstain 11, escalate 1, pass 17, regenerate 12 |
| 32B | 41/41 | 0/12 -> 12/12 | 56 -> 81 | 1 | abstain 11, escalate 1, pass 13, regenerate 16 | abstain 11, escalate 1, pass 12, regenerate 17 |

## 2. Items whose B5 action changed

| Model | Item | Stratum | Before | After | New flags | New non-verified citations |
|---|---|---|---|---|---|---|
| 8B | islamiceval_subtaskC_C-Q02 | misquoted_quran | pass | regenerate_with_evidence | misquotation_detected | ابن ماجه #2568 (misquoted); ابن ماجه #2550 (misquoted); ابن ماجه #2568 (misquoted) |
| 8B | islamiceval_subtaskC_C-Q08 | misquoted_quran | pass | regenerate_with_evidence | misquotation_detected | الترمذي #3660 (misquoted); النسائي #3830 (misquoted) |
| 14B | islamiceval_subtaskC_C-Q08 | misquoted_quran | pass | regenerate_with_evidence | misquotation_detected | النسائي #3830 (misquoted) |
| 32B | islamiceval_subtaskC_C-Q02 | misquoted_quran | pass | regenerate_with_evidence | misquotation_detected | ابن ماجه (2568 (misquoted) |

Citations now checked in Arabic answers, by flag: {'misquoted': 10, 'verified': 50}; by match tier: {'no_match': 10, 'no_quote_given': 24, 'exact': 26}.

## 3. Against the scholar ratings (36 cards; scholar-bad = mean severity >= 2.0, 18 cards)

| Rule | Flagged | TP | FP | FN | TN | Sensitivity | Precision | Specificity |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| T11 any non-verified citation, before fix (flags from commit 474429b) | 3 | 2 | 1 | 16 | 17 | 0.11 | 0.67 | 0.94 |
| T11 any non-verified citation, after fix (36 cards) | 9 | 8 | 1 | 10 | 17 | 0.44 | 0.89 | 0.94 |
| B5 action != pass, before fix (24 B5 cards) | 14 | 6 | 8 | 3 | 7 | 0.67 | 0.43 | 0.47 |
| B5 action != pass, after fix (24 B5 cards) | 16 | 8 | 8 | 1 | 7 | 0.89 | 0.50 | 0.47 |

Rated cards whose B5 action changed: T19-018 (32B_B5: pass -> regenerate_with_evidence; scholar-bad=True), T19-030 (8B_B5: pass -> regenerate_with_evidence; scholar-bad=True).
Scholar-bad cards that B5 passed before the fix (3): T19-018 -> regenerate_with_evidence, T19-028 -> pass, T19-030 -> regenerate_with_evidence.

## Limits

- The scholar cards were used to find the blind spot, and two real card excerpts are now unit tests, so section 3 is not an independent test of the fixed parser.
- Still not detected: a real reference cited for the wrong content with no quotation (T21's main finding), and source-type errors such as Qur'an verses described as hadith (T19-028).
- Quote-to-citation pairing is nearest-by-distance, as in the English path, and can misattribute when several citations share a paragraph.
- Hadith numbering follows this corpus only; an Arabic citation using another numbering scheme is reported as not found or misquoted.
