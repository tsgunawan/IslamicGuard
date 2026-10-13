# T19 follow-up — automated validators vs scholar ratings (exploratory)

- 36 cards (12 items x 3 responses). Automated signals recomputed from response text; evidence = B5 retrieval for the query (same for all models).
- Scholar reference = mean over 4 raters. 'Scholar-bad' = mean error severity >= 2.0 (moderate); threshold set before looking at detection rates.
- Cards from the same item are not independent; treat p-values as descriptive.

Consistency with stored B5 traces (24 cards): misquote count identical on 22/24; supported-claim share identical (±0.01) on 24/24.

## 1. Rank correlation with scholar means (Spearman, n=36)

| Automated signal | vs quality | vs source | vs severity |
|---|---|---|---|
| Share of claims 'supported' (T12) | +0.06 (p=0.728) | +0.20 (p=0.238) | -0.01 (p=0.972) |
| Mean entailment prob (T12) | +0.14 (p=0.422) | +0.27 (p=0.108) | -0.08 (p=0.626) |
| Share of claims 'contradicted' (T12) | -0.02 (p=0.923) | -0.12 (p=0.488) | +0.04 (p=0.812) |
| Misquoted-citation count (T11) | -0.45 (p=0.006) | -0.40 (p=0.016) | +0.47 (p=0.004) |

### 1b. Same, with the automated signals as computed before the Arabic-parser fix (commit 474429b)

| Automated signal | vs quality | vs source | vs severity |
|---|---|---|---|
| Share of claims 'supported' (T12) | +0.06 (p=0.728) | +0.20 (p=0.238) | -0.01 (p=0.972) |
| Mean entailment prob (T12) | +0.14 (p=0.422) | +0.27 (p=0.108) | -0.08 (p=0.626) |
| Share of claims 'contradicted' (T12) | -0.02 (p=0.923) | -0.12 (p=0.488) | +0.04 (p=0.812) |
| Misquoted-citation count (T11, pre-fix) | -0.06 (p=0.718) | +0.00 (p=0.986) | +0.08 (p=0.630) |

## 2. Detecting scholar-bad responses (severity >= 2.0)

Base rate: 18/36 cards scholar-bad.

| Automated rule | Flagged | TP | FP | FN | TN | Sensitivity | Precision | Specificity |
|---|---|---|---|---|---|---|---|---|
| T11: any misquoted citation | 8 | 7 | 1 | 11 | 17 | 0.39 | 0.88 | 0.94 |
| T12: <50% claims supported | 32 | 17 | 15 | 1 | 3 | 0.94 | 0.53 | 0.17 |
| T11 or T12 (either) | 33 | 17 | 16 | 1 | 2 | 0.94 | 0.52 | 0.11 |
| B5 action != pass (B5 cards only, n=24) | 14 | 6 | 8 | 3 | 7 | 0.67 | 0.43 | 0.47 |

## 3. Scholar ratings by B5 action (B5 cards only)

| B5 action | Cards | Mean quality | Mean severity | Scholar-bad |
|---|---|---|---|---|
| abstain | 6 | 3.04 | 1.65 | 2/6 |
| escalate | 2 | 2.62 | 2.12 | 1/2 |
| pass | 10 | 3.05 | 1.74 | 3/10 |
| regenerate_with_evidence | 6 | 3.25 | 1.58 | 3/6 |

## 4. Scholar ratings by T11 misquote flag (all cards)

| Misquote flag | Cards | Mean quality | Mean severity | Mean source |
|---|---|---|---|---|
| not flagged | 28 | 3.00 | 1.72 | 2.81 |
| flagged | 8 | 2.12 | 2.40 | 2.05 |

Mann-Whitney on quality (flagged vs not): p=0.015.

## 5. Cards scholars judged bad but no automated rule flagged (T11 or T12)

T19-028 (8B_B5, q=2.0, sev=2.5)
