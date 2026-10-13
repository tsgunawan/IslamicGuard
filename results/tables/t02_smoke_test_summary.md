# T02 — Qwen3 smoke-test summary (Transformers backend)

Generated from raw run files under `runs/smoke/`. Single-sequence, batch=1, greedy decoding
(`do_sample=False`), `max_new_tokens=128`, one English + one Arabic benign prompt per model.
Numbers below are read directly from the saved JSON, not estimated.

| Model | Revision | Precision / quant | Context requested | Load time (s) | VRAM allocated (MB) | VRAM reserved (MB) | Peak allocated (MB) | Latency EN (ms) | Latency AR (ms) | Status | Raw file |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---|---|
| Qwen/Qwen3-8B | `b968826d9c46dd6066d109eabc6255188de91218` | BF16 | default (no limit set) | 6.0 | 15,630.7 | 15,674.0 | 15,653.7 | 17,854.1 | 6,097.5 | **pass** | `runs/smoke/20260917T092309Z_Qwen__Qwen3-8B.json` |
| Qwen/Qwen3-14B-AWQ | `31c69efc29464b6bb0aee1398b5a7b50a99340c3` | 4-bit AWQ (Marlin kernel) | default (no limit set) | 203.5 † | 9,523.0 | 9,636.0 | 9,567.3 | 16,936.7 | 8,265.2 | **pass** | `runs/smoke/20260917T092546Z_Qwen__Qwen3-14B-AWQ.json` |
| Qwen/Qwen3-32B-AWQ | `0499c3ac83fdef8810b907a23894ba91e95eddd8` | 4-bit AWQ (Marlin kernel) | 4,096 | 330.1 † | 18,440.1 | 18,690.0 | 18,508.4 | 27,580.7 | 13,065.3 | **pass** | `runs/smoke/20260917T093024Z_Qwen__Qwen3-32B-AWQ.json` |

† Load time includes a one-time Marlin FP16 JIT-kernel compilation (~96 s observed for 14B) that
is cached under `~/.cache/gptqmodel/torch_extensions/` after the first run; subsequent loads on
this machine should be faster. Not re-measured in this pass — record as a caveat, not a number.

## Reading this table

- **32B-AWQ fits on the RTX 4090** at 4,096 context / batch=1: 18.5 GB peak allocated against
  24,564 MiB total, ~6 GB headroom. This was the §8.3 "measure, don't assume" item — measured,
  passes, no mitigation steps from §8.3's OOM ladder were needed.
- None of these numbers reflect batched/concurrent throughput, longer contexts, or vLLM serving
  (§8.5) — only single-request Transformers smoke tests per §8.4's acceptance criterion. Full
  throughput/latency profiling under realistic batch sizes and the eventual RAG-augmented prompt
  lengths is out of scope for T02 and belongs to T18 (efficiency profiling).
- All three models generated in Qwen3's default **thinking** mode (chat template default),
  producing `<think>...</think>` reasoning traces. `max_new_tokens=128` was not enough for any of
  the three to finish the reasoning trace and emit a final answer — this is expected for a smoke
  test (the acceptance bar is "loads, runs on GPU, produces a real generation," which all three
  meet) but means these responses are NOT representative of final-answer quality or of the
  non-thinking-mode protocol proposed as the DG-3 default. Do not use these smoke-test outputs as
  evidence for any accuracy/reliability claim.
- Two of the three raw outputs include unverified religious citations generated mid-reasoning
  (e.g., a specific surah/ayah number). This is exactly the class of claim the IslamicGuard
  provenance validators (T11) are meant to check — it is noted here as a raw observation from an
  uncontrolled smoke test, not as a validated or refuted claim about accuracy.
- AWQ loading required installing `gptqmodel` in addition to `autoawq` — the currently installed
  `transformers` (5.17.0) routes AWQ loading through `gptqmodel`, not `autoawq` directly (AutoAWQ
  itself is upstream-deprecated; see `requirements-lock.txt` and `STATUS.md`). This was the
  documented, official-error-message-driven fix, not a workaround.
