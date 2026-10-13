# Dataset Card — HalluTruthQA-4K

- **Source:** https://huggingface.co/datasets/Bekhouche/HalluTruthQA-4K
- **Revision (dataset commit SHA):** `e6e2b14733effc8da7b87fa79230a20cc4b7336b` (last modified 2026-08-25T20:02:35Z)
- **Acquired:** 2026-09-17, via `huggingface_hub.snapshot_download`, `scripts/download_benchmarks.py`
- **License:** **CC-BY-NC-ND-4.0** (from repo tags: `license:cc-by-nc-nd-4.0`) — non-commercial,
  no-derivatives. This project's use (academic research benchmarking, unmodified) fits the
  non-commercial term; the no-derivatives term means we may NOT publish a modified/re-annotated
  version of this dataset. If IslamicGuard's eventual release (`paper.md` DG-12) would include a
  derived/relabelled version of this data, that is NOT permitted under this license — flag before
  any such release.
- **Origin — resolved (verified via arXiv abstract fetch, not guessed):**
  - `arxiv:2608.03966` = **Bekhouche, S. E., Bouchekif, A., Telli, H., Zighem, M.-E.-N., & Hadid, A.
    (2026?). "HalluTruthQA-4K: A Fine-Grained Corpus and Annotation Process for Arabic
    Hallucination Detection and Truth Verification."** This is the exact origin paper of the
    dataset in this directory (4,000 expert-annotated QA pairs; 1,643 hallucinated / 2,357
    non-hallucinated instances; 1,843 marked erroneous spans) — author list matches the HF repo
    owner (`Bekhouche`).
  - `arxiv:2607.20219` = a related, earlier/smaller predecessor: **Bouchekif, A. et al.,
    "HalluTruthQA: A Fine-Grained Benchmark for Hallucination Detection, Localization, and
    Explanation in Arabic Question Answering"** (2,400 examples). Shares co-authors with
    `2608.03966` — same research group, not the same dataset as this directory's files.
  - **Neither arXiv ID has a `literature/references.csv` row yet.** This is a real gap found
    during T06, not resolved here (adding ledger rows is a literature-track task, out of this
    fork's directive) — flagged as an action item for the next literature-track pass, including
    checking whether `bouchekif2025` already in the ledger (a *different* paper, "Assessing Large
    Language Models on Islamic Legal Reasoning") shares an author with this Bouchekif, A. by
    coincidence or is the same person working across both areas.
- **IMPORTANT scope correction:** despite being found via an Islamic-QA hallucination search, this
  dataset is **NOT Islamic-only**. Per the origin paper's own abstract, its 4,000 QA pairs span
  "Islamic knowledge, history, science, and geography" — four domains, not one. Using the full
  4K file as an "Islamic hallucination benchmark" would silently mix in non-Islamic content. Any
  future use of this dataset for this project (T07+) must first filter to the Islamic-studies
  subset only.
  - **Filter mechanism confirmed by row inspection:** each row's `id` field is prefixed by domain
    (`islamicHallucination_*` / `islamic_*` vs. `geographyHallucination_*`, `ScienceHallucination_*`,
    `historicHallucination_*`, `historic_*`, `historicNoHallucination_*`). Counted across all three
    splits: `geographyHallucination`=1000, `ScienceHallucination`=1000, `islamicHallucination`=976,
    `historicHallucination`=944, `historic`=55, `islamic`=24, `historicNoHallucination`=1. **The
    Islamic-studies subset is ~1,000 rows** (`islamicHallucination` + `islamic` prefixes), not the
    full 4,000 — record this distinction if this dataset is used in T07/benchmark composition.
  - Row schema (from inspection): `id, question, generated_answer, gold_answer, generator_model,
    label, options (A–F multiple-choice), answer, hallucinations (span list), split,
    truncated, needs_human_review, level, gold_match, historical_note, data_note, quality_note`.
    `generator_model` recorded per row includes at least `QCRI/Fanar-1-9B-Instruct` (worth noting:
    this is the same `QCRI` organization that released `IslamicFaithQA` above — possible shared
    infrastructure/model across these Qatar-based Islamic-NLP efforts, not yet investigated further).
- **Language:** Arabic only.
- **Size (actually counted, all valid JSON):** `train.jsonl` 1,600 rows, `dev.jsonl` 800 rows,
  `test.jsonl` 1,600 rows = 4,000 total (matches the "4K" in the dataset name, and the paper's
  1,643+2,357=4,000 hallucinated/non-hallucinated split).
- **Task type:** text-classification / question-answering / multiple-choice — fine-grained
  hallucination detection, span-level localization, and explanation generation, across 4 Arabic
  knowledge domains (only one of which is Islamic studies — see scope correction above).
- **Format:** JSONL, includes a `prepare.py` script from the original authors.
- **Relevance to this project (paper.md §11, §12.1):** Directly relevant to hallucination-rate
  metrics and possibly reusable as an additional Arabic hallucination-detection eval set. Not yet
  integrated into `data/benchmarks/` — T07's job, and the origin-paper cross-reference above should
  be resolved first.

- **Update 2026-09-30:** origin paper PDF (arXiv v2, 13 Aug 2026) archived in `ref/` and read.
  Its abstract reports 1,789 hallucinated / 2,211 non-hallucinated responses and 2,419 erroneous
  spans, and 1,000 instances per domain; the counts quoted above came from an earlier abstract
  version. Fourth author is Mohammed-En-Nadhir Zighem.
