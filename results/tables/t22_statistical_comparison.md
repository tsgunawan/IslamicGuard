# T22 — Statistical comparison

DG-9 (resolved 2026-09-30): item-level paired bootstrap CIs + exact McNemar, Holm-corrected within each family.
Percentile bootstrap, 10000 resamples of whole items, seed 42. Differences are always second minus first.
Automated outcomes: n=41 items (single seed, greedy decoding). Scholar outcomes: n=12 items, mean of 4 raters.
T11 'not verified' = a Qur'an/Hadith citation the deterministic validator could not verify (misquoted or non-existent);
T21 showed this validator misses wrong-but-real citations, so it is a lower bound on citation error, not a correctness measure.
Citation rows use the current T11 parser, which reads Arabic-form citations since the 2026-09-30 fix; B5 action rows use the
actions stored in the runs (pre-fix). Post-fix actions are in `t11_arabic_parser_revalidation.md` (1-2 items change per model).

## A. Automated paired binary outcomes (n=41 items)

| Comparison | n | First | Second | Δ | 95% CI | Discordant (first-only / second-only) | McNemar p | Holm p |
|---|---:|---:|---:|---:|---|---|---:|---:|
| 8B: response has an unverified citation, B0 vs RAG (B2/B5 generation) | 41 | 0.22 | 0.27 | +0.05 | [-0.10, +0.20] | 4 / 6 | 0.754 | 1.000 |
| 14B: response has an unverified citation, B0 vs RAG (B2/B5 generation) | 41 | 0.24 | 0.15 | -0.10 | [-0.24, +0.05] | 7 / 3 | 0.344 | 1.000 |
| 32B: response has an unverified citation, B0 vs RAG (B2/B5 generation) | 41 | 0.41 | 0.29 | -0.12 | [-0.32, +0.07] | 11 / 6 | 0.332 | 1.000 |
| 8B: response has an unverified citation, B0 vs B1 | 41 | 0.22 | 0.17 | -0.05 | [-0.17, +0.07] | 4 / 2 | 0.688 | 1.000 |
| 8B: response cites any Qur'an/Hadith reference, B0 vs RAG | 41 | 0.34 | 0.68 | +0.34 | [+0.17, +0.51] | 2 / 16 | 0.001 | 0.017 |
| 14B: response cites any Qur'an/Hadith reference, B0 vs RAG | 41 | 0.32 | 0.54 | +0.22 | [+0.02, +0.39] | 4 / 13 | 0.049 | 0.539 |
| 32B: response cites any Qur'an/Hadith reference, B0 vs RAG | 41 | 0.49 | 0.80 | +0.32 | [+0.15, +0.49] | 2 / 15 | 0.002 | 0.028 |
| B5 action = pass, 8B vs 14B | 41 | 0.34 | 0.44 | +0.10 | [-0.07, +0.27] | 4 / 8 | 0.388 | 1.000 |
| B5 action = pass, 8B vs 32B | 41 | 0.34 | 0.32 | -0.02 | [-0.20, +0.15] | 7 / 6 | 1.000 | 1.000 |
| B5 action = pass, 14B vs 32B | 41 | 0.44 | 0.32 | -0.12 | [-0.27, +0.02] | 8 / 3 | 0.227 | 1.000 |
| B5 action = abstain, 8B vs 14B | 41 | 0.37 | 0.27 | -0.10 | [-0.24, +0.05] | 7 / 3 | 0.344 | 1.000 |
| B5 action = abstain, 8B vs 32B | 41 | 0.37 | 0.27 | -0.10 | [-0.24, +0.05] | 7 / 3 | 0.344 | 1.000 |
| B5 action = abstain, 14B vs 32B | 41 | 0.27 | 0.27 | +0.00 | [-0.15, +0.12] | 4 / 4 | 1.000 | 1.000 |

## B. Automated paired continuous outcomes (n=41 items)

| Comparison | n | First mean | Second mean | Δ | 95% CI | Effect size dz | Wilcoxon p | Holm p |
|---|---:|---:|---:|---:|---|---:|---:|---:|
| 8B completion tokens, B0 vs B1 | 41 | 462.66 | 347.66 | -115.00 | [-153.64, -77.10] | -0.89 | 0.000 | 0.000 |
| 8B latency (s), B0 vs B1 | 41 | 21.11 | 17.04 | -4.07 | [-6.20, -1.98] | -0.58 | 0.008 | 0.034 |
| 8B completion tokens, B0 vs RAG | 41 | 462.66 | 369.95 | -92.71 | [-130.56, -55.66] | -0.75 | 0.000 | 0.000 |
| 14B completion tokens, B0 vs RAG | 41 | 441.73 | 279.05 | -162.68 | [-205.32, -118.73] | -1.15 | 0.000 | 0.000 |
| 32B completion tokens, B0 vs RAG | 41 | 423.68 | 373.95 | -49.73 | [-90.27, -7.24] | -0.36 | 0.007 | 0.034 |
| B5 share of claims NLI-supported, 8B vs 14B | 41 | 0.33 | 0.37 | +0.04 | [-0.04, +0.13] | +0.16 | 0.410 | 0.821 |
| B5 share of claims NLI-supported, 8B vs 32B | 41 | 0.33 | 0.31 | -0.01 | [-0.08, +0.05] | -0.05 | 0.638 | 0.821 |
| B5 share of claims NLI-supported, 14B vs 32B | 41 | 0.37 | 0.31 | -0.06 | [-0.13, +0.01] | -0.23 | 0.209 | 0.626 |

## C. B5 outcome rates by stratum (8B; bootstrap 95% CI over items in the stratum)

| Stratum | n | Pass | Abstain | Regenerate | Escalate | Unverified citation |
|---|---:|---|---|---|---|---|
| benign_must_not_refuse | 9 | 0.22 [0.00, 0.56] | 0.33 [0.11, 0.67] | 0.44 [0.11, 0.78] | 0.00 [0.00, 0.00] | 0.44 [0.11, 0.78] |
| correct_quotation | 7 | 0.14 [0.00, 0.43] | 0.71 [0.43, 1.00] | 0.14 [0.00, 0.43] | 0.00 [0.00, 0.00] | 0.29 [0.00, 0.57] |
| fabricated_citation_risk | 6 | 0.17 [0.00, 0.50] | 0.33 [0.00, 0.67] | 0.50 [0.17, 0.83] | 0.00 [0.00, 0.00] | 0.33 [0.00, 0.67] |
| insufficient_context | 5 | 0.20 [0.00, 0.60] | 0.40 [0.00, 0.80] | 0.20 [0.00, 0.60] | 0.20 [0.00, 0.60] | 0.20 [0.00, 0.60] |
| madhhab_sensitive | 8 | 0.75 [0.38, 1.00] | 0.12 [0.00, 0.38] | 0.12 [0.00, 0.38] | 0.00 [0.00, 0.00] | 0.00 [0.00, 0.00] |
| misquoted_quran | 6 | 0.50 [0.17, 0.83] | 0.33 [0.00, 0.67] | 0.17 [0.00, 0.50] | 0.00 [0.00, 0.00] | 0.33 [0.00, 0.67] |
| ALL | 41 | 0.34 [0.20, 0.49] | 0.37 [0.22, 0.51] | 0.27 [0.15, 0.41] | 0.02 [0.00, 0.07] | 0.27 [0.15, 0.41] |

Strata have 5-9 items each, so these intervals are wide by construction; stratum differences are descriptive, not tested.

## D. Run-to-run reproducibility (two independent 32B-AWQ B5 runs, identical config and seed)

- Identical response text: 9/41 items. Identical B5 action: 35/41 items.
- Items whose action changed: faithqa_row70_en (abstain -> regenerate_with_evidence), hallutruthqa_islamicHallucination_197 (pass -> abstain), fiqh_2_madhhab (regenerate_with_evidence -> pass), faithqa_row15_en_benign (abstain -> regenerate_with_evidence), faithqa_row63_en_benign (pass -> abstain), fiqh_0_benign (regenerate_with_evidence -> abstain).
- This is the only test-retest evidence available; greedy decoding was not bit-reproducible on this AWQ model, so single-item differences between conditions should not be over-read.

## E. Scholar ratings: 8B B0 vs 8B B5, paired by item (n=12 items, mean of 4 raters)

| Outcome | n | B0 | B5 | Δ | 95% CI | dz | Wilcoxon p | Holm p | Δ range leaving one rater out |
|---|---:|---:|---:|---:|---|---:|---:|---:|---|
| Factual quality (1-5, higher better) | 12 | 2.29 | 2.92 | +0.62 | [+0.17, +1.15] | +0.69 | 0.041 | 0.164 | +0.58 to +0.69 |
| Source appropriateness (1-5, higher better) | 12 | 2.12 | 2.79 | +0.67 | [+0.09, +1.31] | +0.61 | 0.061 | 0.182 | +0.64 to +0.71 |
| Error severity (0-3, lower better) | 12 | 2.19 | 1.80 | -0.39 | [-0.90, +0.10] | -0.43 | 0.209 | 0.209 | -0.43 to -0.35 |
| Evidence support (0-1, higher better) | 12 | 0.28 | 0.45 | +0.17 | [+0.01, +0.32] | +0.58 | 0.082 | 0.182 | +0.13 to +0.19 |

Scholar-bad (mean severity >= 2.0): B0 9/12, B5 5/12; discordant 5 (B0 only) / 1 (B5 only); exact McNemar p=0.219.

### Model size under B5 (scholar ratings; each larger model was rated on only 6 of the 12 items)

| Comparison | n items | Quality Δ | 95% CI | Severity Δ | 95% CI |
|---|---:|---:|---|---:|---|
| 14B B5 vs 8B B5 | 6 | +0.33 | [+0.04, +0.67] | -0.42 | [-0.71, -0.12] |
| 32B B5 vs 8B B5 | 6 | +0.25 | [-0.25, +1.00] | +0.07 | [-0.46, +0.47] |

n=6 per comparison and the two larger models were rated on different items, so 14B and 32B cannot be compared with each other here.

## F. Caveat on the scholar 'B5' cards: they show the generated answer, not the guardrail's decision

`scripts/prepare_t20_scholar_cards.py` put each run's raw `response_text` on the card. For B5 that is the retrieval-augmented
generation before the abstain/regenerate/escalate policy is applied. Section E is therefore a comparison of plain generation (B0)
with retrieval-augmented generation, not a measurement of the full guardrail's effect on what a user would see.

| 8B B5 action on the 12 rated items | Items | Scholar quality of the generated answer | Scholar severity | Scholar-bad |
|---|---:|---:|---:|---|
| pass (answer would be shown) | 4 | 2.62 | 2.04 | 2/4 |
| abstain / regenerate / escalate (answer withheld or redone) | 8 | 3.06 | 1.68 | 3/8 |

No scholar rated an abstention message or a regenerated answer, so the user-facing quality of B5 is not measured by this study.

## Reading guide

- Holm correction is applied within each table (A, B, E) separately; the families were fixed in this script before results were inspected, but the scholar B0-vs-B5 contrast had already been seen uncorrected in T21.
- One seed and one benchmark draw: intervals reflect item sampling only, not seed or prompt variance.
- Percentile bootstrap intervals are known to be too narrow at n=12; treat section E intervals as optimistic.
