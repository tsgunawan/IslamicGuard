# Dataset Card — IslamicEval 2025 (Qur'an/Hadith QA Subtask 2)

- **Source:** https://gitlab.com/bigirqu/quran-hadith-qa-2025 (git clone, `--depth 1`)
- **Revision (git commit):** `f9555bd89bf86a75ce82912387db921f99e7f4fe`, dated 2025-10-03T10:49:34Z
- **Acquired:** 2026-09-17, via `git clone`, `scripts/download_benchmarks.py`
- **License: none explicitly stated.** No `LICENSE` file in the repo. The README asks users to
  cite `HowToCite_QuranHadith-QA_Subtask2.bib` when using the data — treat as "available for
  research/benchmarking with mandatory citation," NOT as an open-license grant to redistribute or
  relicense. This repository's data files are kept local-only (gitignored, like `ref/*.pdf`), only
  this card + hash manifest are tracked in git, consistent with `paper.md` §0's "use lawfully,
  don't assume rights beyond what's granted."
- **Origin paper:** Mubarak, H. et al. (2025), *IslamicEval 2025: The First Shared Task of
  Capturing LLMs Hallucination in Islamic Content*, ACL Anthology 2025.arabicnlp-sharedtasks.67
  (`mubarak2025` in `literature/references.csv` — this IS the benchmark `paper.md` §5.10 calls
  "IslamicEval"). This specific repo is Subtask 2 (Qur'an/Hadith passage retrieval); the shared
  task's Subtask 1 (hallucination detection/correction) data was not found at this URL — see
  "Known gaps" below.
- **Contents (actually counted):**
  - `data/QH-QA-25_Subtask2_ayatec_v1.3_{train,dev,test}.tsv`: 210 / 40 / 71 questions (AyaTEC
    v1.3, Qur'an-passage QA questions; 44 of these are deliberately zero-answer/unanswerable
    questions per the README — directly useful for `paper.md` §11.2 stratum #9,
    insufficient-context questions).
  - `data/Sahih-Bukhari/QH-QA-25_Subtask2_Sahih-Bukhari_v1.0.jsonl`: 2,254 Hadiths (redundant
    Hadiths/Arabic commentary/narrator-chain removed per README; only "authenticated Hadiths with
    a continuous chain of narrators" included — no further authenticity-grading detail than that
    given in the README; relevant input for DG-5, not a resolution of it).
    **Format quirk (not a data error):** despite the `.jsonl` extension, each line is a
    Python-dict literal with single-quoted keys (`{'hadith_id': 1, 'hadith': '...', ...}`), not
    strict JSON — `json.loads` fails on every line (2,254/2,254), but `ast.literal_eval` parses
    all 2,254 lines successfully with zero malformed rows. Document this when writing any loader.
  - `data/Thematic_QPC/QH-QA-25_Subtask2_QPC_v1.1.tsv`: 1,266 thematic Qur'anic passages covering
    the full Qur'an (segmented per the "Thematic Holy Qur'an" scheme, text sourced from Tanzil
    1.0.2 normalized simple-clean style).
  - `data/qrels/*_qrels_{dev,train}.gold`: TREC-format relevance judgments for dev/train only.
    **Test-set qrels are deliberately withheld by the organizers** ("will not be released" per
    README) — this repo's test split is unlabeled by design, not an extraction failure.
  - `Evaluation/`: the organizers' own format checker + `trec_eval`-based scorer scripts —
    reusable directly for this project's own evaluation pipeline instead of reimplementing one.
- **Relevance to this project (paper.md §11, DG-1=B, DG-5):** The Sahih al-Bukhari collection here
  is a concrete, small, lawfully-obtained Hadith source candidate directly relevant to the still-open
  DG-5 (Hadith corpus and grading policy) — feed into that gate's evidence base, not a resolution
  of it (single collection, one authenticity-inclusion criterion, no graded/disputed-Hadith
  handling described). The Qur'an QPC + AyaTEC data are directly usable for provenance-validator
  test cases (`paper.md` §11.2 strata #1–3, #9).
- **Known gaps:** Subtask 1 (hallucination detection/correction — the other half of IslamicEval
  2025, and arguably more directly relevant to this project than Subtask 2's retrieval task) was
  not located at this URL. Also referenced in the paper: `codabench.org/competitions/9939` (the
  shared-task competition page) — not yet fetched/verified in this pass; follow up before relying
  on this being the complete IslamicEval 2025 release.
