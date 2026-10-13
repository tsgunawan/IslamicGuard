# Third-party data and licences

The MIT licence in `LICENSE` covers the code written for this project. The project's own data (the
constructed benchmark and prompt-injection items, the scholar ratings and comments, the run outputs,
and the generated tables and figures) is released under the **Creative Commons Attribution 4.0
International licence (CC BY 4.0)**, https://creativecommons.org/licenses/by/4.0/. Neither licence
covers the third-party material below. Licences are as recorded in each `data/raw/*/DATASET_CARD.md` at download time;
check the source before reuse. This file is a record, not legal advice.

| Source | Used for | Licence recorded | In this repository |
|---|---|---|---|
| IslamicFaithQA (Bhatia et al., 2026) | 12 benchmark items | Apache-2.0 | question and reference answer of the 12 items |
| FiqhQA (Atif et al., 2025) | 12 benchmark items; fiqh corpus layer | MIT | question and reference answer of the 12 items |
| IslamicEval 2025, Subtask 1 repository (Mubarak et al., 2025) | 6 benchmark items; Qur'an corpus text | Apache-2.0 | question and reference answer of the 6 items |
| HalluTruthQA-4K (Bekhouche et al., 2026) | 6 benchmark items | **CC BY-NC-ND 4.0** | question and reference answer of the 6 items, unmodified |
| fawazahmed0/hadith-api | hadith corpus layer | Unlicense | not redistributed |
| IslamicEval 2025 Qur'an/Hadith QA repository | explored only | no licence stated | not redistributed |
| IslamicEval 2025 QH-QA Subtask 2, test split | 15 held-out Arabic questions (revision 2) | no licence stated | item ids only; question text removed (6 model answers repeat their question) |
| HalluTruthQA-4K, test split | 15 held-out Arabic questions (revision 2) | **CC BY-NC-ND 4.0** | question text, unmodified |
| Constructed for this study | 5 benchmark items, 12 prompt-injection items | CC BY 4.0 (this project) | full text |

Also derived from the sources above and present in the repository: model answers to the benchmark
questions (`runs/*/responses.jsonl`), the scholar-review cards (`expert_review/t20_*.json`) and
the per-card ratings and comments. The corpus files themselves (`data/corpus/*.jsonl`) and the
downloaded datasets (`data/raw/*/`) are not redistributed; `scripts/download_benchmarks.py` and
`scripts/build_corpus.py` rebuild them.

**HalluTruthQA-4K.** Its licence forbids commercial use and modified versions. The six benchmark items and the 15 held-out items are
reproduced verbatim, with attribution, for non-commercial research, and they remain under CC BY-NC-ND
4.0, not CC BY 4.0. Anyone reusing the benchmark file must keep those six items unmodified and
non-commercial, or drop them.
