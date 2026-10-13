# Table 5 — Main results, Qwen3-8B

| Outcome | B0 (no retrieval, no guardrail) | B5 generation (retrieval-augmented) | Difference [95% CI] | n |
|---|---|---|---|---:|
| Scholar factual quality (1-5) | 2.29 [1.88, 2.79] | 2.92 [2.33, 3.50] | +0.62 [+0.17, +1.15] | 12 |
| Scholar source appropriateness (1-5) | 2.12 [1.70, 2.60] | 2.79 [2.31, 3.27] | +0.67 [+0.09, +1.31] | 12 |
| Scholar error severity (0-3, lower is better) | 2.19 [1.74, 2.53] | 1.80 [1.39, 2.20] | -0.39 [-0.90, +0.10] | 12 |
| Scholar evidence support (0-1) | 0.28 [0.15, 0.42] | 0.45 [0.31, 0.59] | +0.17 [+0.01, +0.32] | 12 |
| Answers citing a Qur'an/hadith reference | 0.34 [0.20, 0.49] | 0.68 [0.54, 0.83] | +0.34 [+0.17, +0.51] | 41 |
| Answers with a citation T11 could not verify | 0.22 [0.10, 0.34] | 0.27 [0.15, 0.41] | +0.05 [-0.10, +0.20] | 41 |
| Completion tokens | 462.66 [432.27, 488.90] | 369.95 [326.90, 411.25] | -92.71 [-130.56, -55.66] | 41 |

*Mean [95% item-bootstrap CI]. Scholar rows: 12 items, mean of 4 raters; scholars rated the generated answer, not the guardrail decision.*
*Automated rows: 41 items. Source: results/error_analysis/t19_expert_ratings_long.jsonl, runs/*/responses.jsonl; tests in table t22.*
