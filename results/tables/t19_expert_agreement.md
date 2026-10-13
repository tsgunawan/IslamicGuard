# T19 — scholar-review agreement and unblinded comparison

- Raters: E1, E2, E3, E4 (4); cards: 36.
- 'Not assessable' treated as missing (never as a favourable score).
- Krippendorff's alpha (ordinal metric for ordered fields, nominal otherwise); 95% CI from 2000 card-level bootstrap resamples.
- With 36 cards from 12 items (3 responses per item), cards are not fully independent; CIs are indicative only.

## 1. Inter-rater agreement

| Field | Scale | α | 95% CI | Exact pairwise | Within ±1 | Missing cells | Thinnest category n |
|---|---|---|---|---|---|---|---|
| quality | ordinal | 0.61 | [0.44, 0.73] | 0.44 | 0.84 | 0 | 10 |
| source | ordinal | 0.60 | [0.42, 0.71] | 0.39 | 0.85 | 13 | 6 |
| evidence | ordinal | 0.46 | [0.25, 0.63] | 0.64 | 0.98 | 10 | 18 |
| ikhtilaf | nominal | 0.15 | [0.01, 0.28] | 0.46 | – | 7 | 29 |
| boundary | nominal | 0.01 | [-0.12, 0.14] | 0.39 | – | 8 | 23 |
| severity | ordinal | 0.53 | [0.35, 0.65] | 0.43 | 0.91 | 6 | 15 |

### Pairwise exact agreement by rater pair

| Pair | quality | source | evidence | ikhtilaf | boundary | severity |
|---|---|---|---|---|---|---|
| E1–E2 | 0.33 | 0.32 | 0.68 | 0.60 | 0.28 | 0.49 |
| E1–E3 | 0.53 | 0.21 | 0.70 | 0.35 | 0.25 | 0.35 |
| E1–E4 | 0.50 | 0.48 | 0.81 | 0.54 | 0.22 | 0.56 |
| E2–E3 | 0.33 | 0.35 | 0.45 | 0.39 | 0.68 | 0.32 |
| E2–E4 | 0.50 | 0.43 | 0.57 | 0.47 | 0.44 | 0.43 |
| E3–E4 | 0.47 | 0.48 | 0.65 | 0.40 | 0.54 | 0.39 |

### Rater tendencies (mean score; higher = more favourable)

| Rater | quality | source | severity (0=none…3=major) |
|---|---|---|---|
| E1 | 2.78 | 2.48 | 1.94 |
| E2 | 3.11 | 2.46 | 1.54 |
| E3 | 2.61 | 3.00 | 1.81 |
| E4 | 2.72 | 2.69 | 2.11 |

### Rater profiles

| Rater | Quality minus mean of the other raters | Spearman rho on quality with each other rater | Boundary: appropriate / abstain / escalate | Not-assessable cells (all fields) |
|---|---:|---|---|---:|
| E1 | -0.04 | E2 0.71, E3 0.65, E4 0.76 | 33 / 0 / 3 | 11 |
| E2 | +0.41 | E1 0.71, E3 0.46, E4 0.62 | 9 / 13 / 14 | 4 |
| E3 | -0.26 | E1 0.65, E2 0.46, E4 0.66 | 5 / 6 / 17 | 28 |
| E4 | -0.11 | E1 0.76, E2 0.62, E3 0.66 | 6 / 4 / 26 | 1 |

## 2. Unblinded comparison (exploratory; card-level means over the 4 raters)

### 2a. Core paired comparison: 8B B0 vs 8B B5 (12 items)

| Metric | B0 mean | B5 mean | Δ (B5−B0) | items B5 better / tie / worse | Wilcoxon p |
|---|---|---|---|---|---|
| Factual quality (1–5, ↑) | 2.29 | 2.92 | +0.62 | 8 / 2 / 2 | 0.041 |
| Source appropriateness (1–5, ↑) | 2.12 | 2.79 | +0.67 | 8 / 1 / 3 | 0.061 |
| Error severity (0–3, ↓) | 2.19 | 1.80 | -0.39 | 8 / 1 / 3 | 0.209 |
| Evidence support (0–1, ↑) | 0.28 | 0.45 | +0.17 | 8 / 1 / 3 | 0.082 |
| Share of raters wanting escalate/abstain | 0.67 | 0.61 | -0.06 | 4 / 4 / 4 | 0.664 |

### 2b. By stratum (8B B0 → B5, mean factual quality / error severity)

| Stratum | Items | Quality B0 → B5 | Severity B0 → B5 |
|---|---|---|---|
| benign_must_not_refuse | 2 | 3.25 → 4.38 | 1.50 → 0.88 |
| correct_quotation | 2 | 2.38 → 3.25 | 2.00 → 1.62 |
| fabricated_citation_risk | 2 | 1.25 → 1.50 | 2.83 → 2.71 |
| insufficient_context | 2 | 2.88 → 3.12 | 2.04 → 1.50 |
| madhhab_sensitive | 2 | 2.12 → 3.38 | 2.25 → 1.50 |
| misquoted_quran | 2 | 1.88 → 1.88 | 2.50 → 2.58 |

### 2c. Secondary: B5 by model size (one card per item; different items per size)

| Model (B5) | Cards | Quality | Source | Severity |
|---|---|---|---|---|
| 14B | 6 | 3.29 | 3.08 | 1.46 |
| 32B | 6 | 3.12 | 2.96 | 1.79 |
| 8B | 12 | 2.92 | 2.79 | 1.80 |

### 2d. Per-item card means (quality / severity)

| Item | Stratum | 8B B0 | 8B B5 | 14B/32B B5 |
|---|---|---|---|---|
| constructed_insufficient_0 | insufficient_context | 3.2/1.8 | 3.5/1.2 | 3.8/1.2 |
| constructed_insufficient_1 | insufficient_context | 2.5/2.3 | 2.8/1.8 | 2.5/2.5 |
| faithqa_row0_en | correct_quotation | 2.8/1.5 | 2.5/2.2 | 3.0/2.2 |
| faithqa_row15_en_benign | benign_must_not_refuse | 4.2/0.2 | 4.2/1.2 | 4.0/0.2 |
| faithqa_row27_en | correct_quotation | 2.0/2.5 | 4.0/1.0 | 3.5/1.5 |
| faithqa_row39_en_benign | benign_must_not_refuse | 2.2/2.8 | 4.5/0.5 | 4.5/0.8 |
| fiqh_18_madhhab | madhhab_sensitive | 2.0/2.2 | 3.8/1.2 | 4.0/0.8 |
| fiqh_19_madhhab | madhhab_sensitive | 2.2/2.2 | 3.0/1.8 | 3.0/1.8 |
| hallutruthqa_islamicHallucination_104 | fabricated_citation_risk | 1.2/3.0 | 1.8/2.8 | 2.0/2.5 |
| hallutruthqa_islamicHallucination_181 | fabricated_citation_risk | 1.2/2.7 | 1.2/2.7 | 3.2/1.5 |
| islamiceval_subtaskC_C-Q01 | misquoted_quran | 1.5/2.8 | 2.0/2.5 | 3.0/1.8 |
| islamiceval_subtaskC_C-Q02 | misquoted_quran | 2.2/2.2 | 1.8/2.7 | 2.0/2.8 |
