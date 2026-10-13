# Dataset Card — IslamicFaithQA

- **Source:** https://huggingface.co/datasets/QCRI/IslamicFaithQA
- **Revision (dataset commit SHA):** `a525f5d47a04f9290e6aecaf34668c23a4431d63` (last modified 2026-04-30T12:26:40Z)
- **Acquired:** 2026-09-17, via `huggingface_hub.snapshot_download`, `scripts/download_benchmarks.py`
- **License:** Apache-2.0 (from repo `README.md` YAML front matter: `license: apache-2.0`)
- **Origin paper:** Bhatia et al. (2026), *From RAG to Agentic RAG for Faithful Islamic Question
  Answering*, Findings of ACL 2026 (`bhatia2026` in `literature/references.csv`). The dataset's own
  README cites an arXiv preprint of the same title at arXiv:2601.07528 — same paper, preprint vs.
  camera-ready venue; not investigated further, noted for the audit trail.
- **Languages:** Arabic, English (separate configs).
- **Size (actually counted):**
  - `arabic/dataset_with_difficulty_clean_updated.jsonl`: 3,810 lines, all valid JSON.
  - `english/dataset_with_difficulty_clean_updated.jsonl`: 3,808 lines, all valid JSON.
  - These are the dataset's documented `test` split (per the HF `configs:` block — only a `test`
    split is declared for `arabic`/`english`).
  - Two additional root-level files, `sft_training_data.jsonl` (25,000 lines) and
    `rl_training_data.jsonl` (5,000 lines), are present in the repo but NOT part of the declared
    `arabic`/`english` test configs — appear to be training data for the paper's own model, not
    labelled as this project's benchmark; not yet used, flagged for T07 review before any use as
    eval data (mixing train/eval risks contamination).
- **Format:** JSONL.
- **Relevance to this project (paper.md §11):** Bilingual generative faithfulness-oriented QA —
  directly relevant to benchmark strata #6 (unsupported religious factual claims) and general
  hallucination/grounding metrics (§12.1). Not yet integrated into `data/benchmarks/` — T07's job.
- **Known limitation / contamination risk:** Same first-author lineage as `bhatia2026`'s own
  proposed agentic-RAG system; using this benchmark to evaluate IslamicGuard risks favorable bias
  toward architectures similar to the origin paper's. Flag for `paper.md` §11.4 (data leakage)
  discussion in the eventual manuscript.
