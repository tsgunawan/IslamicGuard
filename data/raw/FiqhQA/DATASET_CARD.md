# Dataset Card — FiqhQA

- **Source:** https://huggingface.co/datasets/MBZUAI/FiqhQA
- **Revision (dataset commit SHA):** `084fa4857d56a1d5c46df3645e13520de824ed3b` (last modified 2025-08-13T11:27:58Z)
- **Acquired:** 2026-09-17, via `huggingface_hub.snapshot_download`, `scripts/download_benchmarks.py`
- **License:** MIT (from repo `README.md` YAML front matter: `license: mit`)
- **Origin paper:** Atif, F., Askarbekuly, N., Darwish, K., & Choudhury, M. (2025). *Sacred or
  Synthetic? Evaluating LLM Reliability and Abstention for Religious Questions.* arXiv:2508.08287.
  (`atif2025` in `literature/references.csv`; this is the paper `paper.md` §5.10 refers to as the
  "FiqhQA" benchmark.)
- **Languages:** Arabic, English (separate configs/files, same 121 underlying questions).
- **Size (actually counted, not from the paper's rounded claim):** 121 rows per language CSV
  (`FiqhQA - Arabic.csv`, `FiqhQA - English.csv`), i.e. 121 questions, each with per-madhhab answer
  columns (`maliki_ans`, `hanafi_ans`, `shafeii_ans`, `hanbali_ans`) for all 4 major Sunni schools.
  The paper's abstract figure of "960 QA pairs" = 120 questions × 2 languages × 4 madhhab-answers;
  the released files have 121 rows (off-by-one from the paper's stated 120 — not investigated
  further here, noted for the audit trail rather than silently rounded to match the paper).
- **Format:** CSV (primary, used above for the row count) + equivalent HF `datasets`-loadable
  Parquet per language config.
- **Columns:** `Category`, `Title_original`, `statement_original` (original Arabic fiqh-manual
  statement), `Agreement` (whether the 4 madhhabs agree or disagree on this ruling), per-language
  `question_*`, and 4 per-madhhab answer columns.
- **Relevance to this project (paper.md §11, §1.4 DG-1=B):** Directly matches DG-1's chosen corpus
  scope (Qur'an+Hadith + narrow 4-madhhab fiqh layer). Candidate source for benchmark strata #7
  (madhhab-sensitive questions) and #8 (legitimate ikhtilaf) in `paper.md` §11.2 — the `Agreement`
  column is a ready-made ikhtilaf/consensus label. Not yet integrated into `data/benchmarks/` or
  `data/corpus/` — that is T07's job, not T06's.
- **Known limitation:** Only 121 items; likely too small to be the *sole* madhhab-sensitivity
  benchmark and will need supplementing (see `literature/gap_table.csv` for what other papers in
  the corpus offer at larger scale, e.g. `elmahjub2026legalbench`'s 718-instance, 7-school
  benchmark — though that is broader than DG-1=B's 4-madhhab scope).
