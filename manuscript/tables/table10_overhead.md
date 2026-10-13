# Table 10 — Computational overhead (41 items, single 24 GB GPU)

| Model | Condition | Generation s/item | Total generation (s) | Validation s/item | Mean completion tokens | Peak GPU memory (MiB) |
|---|---|---:|---:|---:|---:|---:|
| Qwen/Qwen3-8B | B0 | 21.1 | 866 | – | 463 | not captured |
| Qwen/Qwen3-8B | B1 | 17.0 | 699 | – | 348 | not captured |
| Qwen/Qwen3-8B | B5 | 36.7 | 1505 | 3.2 | 370 | not captured |
| Qwen/Qwen3-14B-AWQ | B0 | 29.2 | 1196 | – | 442 | not captured |
| Qwen/Qwen3-14B-AWQ | B5 | 18.4 | 754 | 2.9 | 279 | not captured |
| Qwen/Qwen3-32B-AWQ | B0 | 44.2 | 1812 | – | 424 | not captured |
| Qwen/Qwen3-32B-AWQ | B5 | 219.5 | 8999 | 3.9 | 374 | 24070 |

*B5 generation time is the retrieval-augmented generation step; validation is the guardrail stack run afterwards. 'not captured' = no automated GPU sampling for that run.*
*Source: runs/*/responses.jsonl, guardrail_traces.jsonl, gpu_samples.jsonl.*
