# B0 rerun with a 2,048-token limit

The original B0 runs used a 512-token limit, which cut off most answers (T23). B0 was rerun with 2,048 tokens and otherwise
identical settings (greedy, seed 42, non-thinking). The 512-token runs are kept. The reruns have no scholar ratings.

| Model | Limit | Hit the limit | Repetition loop | Mean tokens | Median tokens | s/item | Cites a reference | Has an unverified citation | Unverified citations per answer |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Qwen3-8B | 512 | 28/41 | 2/41 | 463 | 512 | 21.1 | 0.34 | 0.22 | 0.41 |
| Qwen3-8B | 2048 | 7/41 | 6/41 | 899 | 761 | 46.2 | 0.37 | 0.24 | 1.17 |
| Qwen3-14B-AWQ | 512 | 27/41 | 4/41 | 442 | 512 | 29.2 | 0.32 | 0.24 | 0.34 |
| Qwen3-14B-AWQ | 2048 | 2/41 | 6/41 | 706 | 645 | 48.3 | 0.34 | 0.27 | 0.76 |
| Qwen3-32B-AWQ | 512 | 26/41 | 1/41 | 424 | 512 | 44.2 | 0.49 | 0.41 | 0.61 |
| Qwen3-32B-AWQ | 2048 | 1/41 | 4/41 | 725 | 660 | 75.6 | 0.54 | 0.46 | 0.80 |

- **Qwen3-8B** (`20260930-0856_Qwen__Qwen3-8B_B0_t15_benchmark_s42`): of the 28 answers cut off at 512 tokens, 21 now finish; 7 still hit 2,048 tokens, 4 of them in a repetition loop. The 2,048-token answer begins with the 512-token answer for 41/41 items. Answers with an unverified citation: 0.22 -> 0.24 (difference +0.02, 95% CI [+0.00, +0.07]; McNemar discordant 0/1, p=1.000).
- **Qwen3-14B-AWQ** (`20260930-0935_Qwen__Qwen3-14B-AWQ_B0_t15_benchmark_s42`): of the 27 answers cut off at 512 tokens, 25 now finish; 2 still hit 2,048 tokens, 1 of them in a repetition loop. The 2,048-token answer begins with the 512-token answer for 23/41 items. Answers with an unverified citation: 0.24 -> 0.27 (difference +0.02, 95% CI [-0.05, +0.12]; McNemar discordant 1/2, p=1.000).
- **Qwen3-32B-AWQ** (`20260930-1008_Qwen__Qwen3-32B-AWQ_B0_t15_benchmark_s42`): of the 26 answers cut off at 512 tokens, 25 now finish; 1 still hit 2,048 tokens, 1 of them in a repetition loop. The 2,048-token answer begins with the 512-token answer for 26/41 items. Answers with an unverified citation: 0.41 -> 0.46 (difference +0.05, 95% CI [+0.00, +0.12]; McNemar discordant 0/2, p=0.500).

## Reading

- 'Unverified citation' uses the current T11 parser (English and Arabic forms). It is a lower bound on citation error.
- Longer answers have more room to cite and to err, so per-answer citation rates are not comparable across limits without that caveat.
- Whether scholars would rate the untruncated answers higher is not known: the scholar study rated the 512-token answers only.
