# Table 3 — Benchmark and retrieval corpus

| Stratum | Items | Source dataset(s) | English | Arabic | Constructed |
|---|---:|---|---:|---:|---:|
| correct_quotation | 7 | IslamicFaithQA | 7 | 0 | 0 |
| misquoted_quran | 6 | islamiceval_subtaskC_WrongAyah | 0 | 6 | 0 |
| fabricated_citation_risk | 6 | HalluTruthQA-4K (test split, islamicHallucination subset) | 0 | 6 | 0 |
| madhhab_sensitive | 8 | FiqhQA (Atif et al. 2025) via data/corpus/fiqh.jsonl | 8 | 0 | 0 |
| insufficient_context | 5 | constructed_for_t15 | 4 | 1 | 5 |
| benign_must_not_refuse | 9 | FiqhQA (Atif et al. 2025) via data/corpus/fiqh.jsonl, IslamicFaithQA | 9 | 0 | 0 |
| **Total** | **41** | | 28 | 13 | 5 |

| Retrieval corpus layer | Records |
|---|---:|
| quran | 6,236 |
| hadith | 34,157 |
| fiqh | 121 |

Scholar-review subset: 36 cards from 12 items, 4 raters.

*Source: data/benchmarks/t15_benchmark.jsonl, data/corpus/*.jsonl.*
