# Table 7 — Model-size comparison under B5 (41 items)

| Model | B5 pass | B5 regenerate | B5 abstain | B5 escalate | Same, after Arabic-parser fix | NLI-supported claim share | Scholar quality, B5 cards | Scholar severity, B5 cards | Cards |
|---|---:|---:|---:|---:|---|---:|---:|---:|---:|
| Qwen/Qwen3-8B | 14 | 11 | 15 | 1 | 12 / 13 / 15 / 1 | 0.33 | 2.92 | 1.80 | 12 |
| Qwen/Qwen3-14B-AWQ | 18 | 11 | 11 | 1 | 17 / 12 / 11 / 1 | 0.37 | 3.29 | 1.46 | 6 |
| Qwen/Qwen3-32B-AWQ | 13 | 16 | 11 | 1 | 12 / 17 / 11 / 1 | 0.31 | 3.12 | 1.79 | 6 |

*Scholar columns: 12 cards for 8B, 6 each for 14B and 32B on different items, so the larger models are not comparable with each other on those columns.*
*Source: runs/*/guardrail_traces.jsonl, results/error_analysis/t11_arabic_parser_revalidation.jsonl, t19_expert_ratings_long.jsonl.*
