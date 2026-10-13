# T27 — independent regeneration check

Runs made on 2026-09-30 by a separate session, B0, greedy decoding, seed 42, 512 new tokens, same model revisions.
This table only compares their saved responses with the earlier saved runs; that session left no written report in the repository.

## Four T15 benchmark items regenerated and compared with the original T15 B0 runs

| Model | Revision matches | Identical responses | Same completion-token counts |
|---|---|---:|---:|
| Qwen3-8B | yes | 4/4 | 4/4 |
| Qwen3-14B-AWQ | yes | 1/4 | 4/4 |
| Qwen3-32B-AWQ | yes | 1/4 | 4/4 |

## Four other items (from the T09 sample) run twice in that session, and compared with the September 2026 T09 runs

| Model | Run 1 vs run 2 identical | Run 1 vs original T09 run identical |
|---|---:|---:|
| Qwen3-8B | 4/4 | 3/4 |
| Qwen3-14B-AWQ | 2/4 | 2/4 |
| Qwen3-32B-AWQ | 3/4 | 2/4 |

## Reading

- Qwen3-8B reproduced the four T15 answers exactly. The two AWQ-quantised models reproduced one of four; the others start identically and then diverge, with the same token counts where the limit was reached.
- This agrees with the manuscript's statement that greedy decoding was not reproducible on the quantised models (two identical 32B runs matched on 9 of 41 items) and extends it to the 14B model.
- Consequence already stated in the paper: single-item differences for the quantised models are within run-to-run variation. Results for Qwen3-8B, which carries the scholar comparison, are reproducible at the text level on this sample.
- One Qwen3-8B answer differs from the 17 September T09 run while matching itself across two same-day runs, so full-precision output is stable within an environment but not guaranteed across dates; the cause (library or driver change) was not investigated.
- Not covered by these runs: retrieval-augmented conditions, a clean-environment rebuild, DOI resolution, and a claim-by-claim reading of the manuscript.
