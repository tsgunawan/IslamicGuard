# Table 6 — Ablation, Qwen3-8B (41 items)

| Condition | Components | Mean completion tokens | Hit token limit | Items with a recorded flag | pass / regenerate / abstain / escalate |
|---|---|---:|---:|---:|---|
| B0 | generation only | 463 | 28/41 | – | – |
| B1 | policy prompt only | 348 | 12/41 | – | – |
| B2 | retrieval from B0 | 370 | 12/41 | – | – |
| B3 | + provenance validator | 370 | 12/41 | 6 | – |
| B4 | + faithfulness validator | 370 | 12/41 | 22 | – |
| B5 | + madhhab and abstention policy | 370 | 12/41 | 27 | 14 / 11 / 15 / 1 |

*B2-B4 are views of the B5 run (same retrieval and generation). Flag counts inherit B5 policy priority: B3 records six citation-related flags, while raw provenance checks found eight answers with an unverified citation; two were masked by abstention. Counts precede the Arabic-citation parser fix.*
*Source: runs/*/responses.jsonl, guardrail_traces.jsonl.*
