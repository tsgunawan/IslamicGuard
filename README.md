# IslamicGuard

Code, benchmark, run records and analysis for the paper

> **IslamicGuard: A Scholar-Audited Evaluation of a Layered Guardrail for Islamic Question Answering**
> Teddy Surya Gunawan, Mira Kartiwi, Asmuliadi Lubis, Mohd Abd Wahab Fatoni Mohd Balwi, Muntaha Artalim Zaim, Rio Erismen Armen.
> Under review at the *IIUM Engineering Journal* (manuscript 4817), 2026.

IslamicGuard is a **research prototype**. Its outputs are **not fatwas** and must not be used as
religious guidance. The study's main finding is that its own validation layers do not reliably
agree with Islamic scholars.

## What the study found

A retrieval-augmented pipeline with a provenance validator, a claim–evidence faithfulness
validator, a school-plurality check and an abstention/escalation policy was run on a 41-item
English and Arabic benchmark with three Qwen3 models, and four scholars blindly rated 36 answers.

- Retrieval helps: scholars rated retrieval-augmented answers higher for factual quality
  (2.92 vs 2.29 of 5; difference 0.62, 95% CI 0.17 to 1.15; not significant after Holm
  correction), and fabricated scripture text fell from 6 of 12 answers to 1 of 12.
- The validation layers under-deliver: the entailment check flagged 32 of 36 answers regardless
  of quality, the provenance validator at first read no Arabic-form citations (sensitivity 0.11,
  and 0.44 after the fix), and the policy passed only 2 of 9 benign questions.
- Scholar review cannot be replaced by reference-existence and entailment checks.

Added in the first revision (results in `results/tables/r2_*`):

- On 60 fresh answers to 30 held-out Arabic questions, the repaired citation parser recognised
  86 of 100 hand-labelled references (the original parser: 32).
- Validator scores separate scholar-judged severe answers only weakly (AUC 0.57 to 0.70), and no
  policy threshold in a post hoc sweep achieves both high sensitivity and high specificity.
- Executing the regenerate recommendation once cleared only 1 of 13 flagged Qwen3-8B answers.
- A mixed-effects model adjusted for the 512-token cap gives a retrieval effect of 0.55 points.

## Repository layout

| Path | Contents |
|---|---|
| `src/` | Pipeline: retrieval (`rag/`), validators (`validators/`), policy (`guardrails/`), model backends (`models/`) |
| `scripts/` | Run, analysis, figure/table and audit scripts |
| `prompts/` | Prompts for conditions B0, B1 and B2 |
| `data/benchmarks/` | The 41-item benchmark, smaller evaluation sets, and the revision-2 held-out Arabic set with hand-labelled citations |
| `data/raw/*/DATASET_CARD.md` | Source, revision and licence of every third-party dataset (the data itself is not redistributed) |
| `runs/` | One directory per run: config, prompts, responses, retrieval, guardrail trace, metrics |
| `results/` | Generated tables and item-level analysis files |
| `expert_review/` | Scholar-review protocol, rating form, blinded cards, per-card ratings |
| `tests/` | Unit tests for the validators and the policy |

## Setup

```bash
conda env create -f environment.yml
conda activate islamicguard
python -m pytest -q            # 80 tests
```

`requirements.txt` pins the direct dependencies. `requirements-lock.txt` is the full freeze of the
original environment, kept as a record; it is not installable as-is.

Hardware used: one NVIDIA RTX 4090 (24 GB), Windows Server 2022 with WSL2, CUDA 13.0.

## Reproduce the analysis (no GPU needed)

The result tables and figures are regenerated from the saved records in `runs/` and `results/`.
The validators need the retrieval corpus, which is rebuilt from its public sources first
(about 80 MB of downloads, under a minute):

```bash
python scripts/download_benchmarks.py            # third-party datasets into data/raw/
python scripts/build_corpus.py                   # data/corpus/{quran,hadith,fiqh}.jsonl
python -m pytest -q                              # 80 tests

python scripts/t22_statistical_comparison.py     # paired comparisons, bootstrap CIs
python scripts/t23_error_analysis.py             # failure taxonomy
python scripts/revalidate_t11_arabic_parser.py   # provenance validator before/after the Arabic fix
python scripts/analyze_b0_token_limit.py         # 512 vs 2,048 token limit
python scripts/make_figures_tables.py            # manuscript tables and figures

# revision 2 (no GPU)
python scripts/r2_reanalysis.py                  # truncation subsets, mixed models, Wilson CIs, AUC, sweeps
python scripts/r2_fabrication_check.py           # fabricated-scripture coding vs canonical text
python scripts/r2_parser_heldout_eval.py runs/20261013-1340_Qwen__Qwen3-8B_B5_r2_heldout_arabic_s42 \
       runs/20261013-1405_Qwen__Qwen3-14B-AWQ_B5_r2_heldout_arabic_s42   # parser on held-out answers
```

In a clean copy of this repository these commands rebuilt a byte-identical corpus and reproduced
every result table exactly (checked on 2026-09-30).

## Rerun generation (GPU)

1. After the two data steps above, build the retrieval indexes: `python scripts/build_index.py`.
2. Run a condition, for example:

```bash
python scripts/run_baseline.py --model Qwen/Qwen3-8B --condition B0 --sample data/benchmarks/t15_benchmark.jsonl
python scripts/run_islamicguard_b5.py --help

# revision 2: held-out Arabic answers and one executed regeneration
python scripts/r2_build_heldout_arabic.py         # rebuilds data/benchmarks/r2_heldout_arabic.jsonl
python scripts/run_islamicguard_b5.py --model Qwen/Qwen3-8B --sample data/benchmarks/r2_heldout_arabic.jsonl
python scripts/r2_execute_regeneration.py
```

The 15 held-out questions from IslamicEval 2025 QH-QA have their text removed in this repository
(the dataset states no licence); `r2_build_heldout_arabic.py` restores it from the downloaded data.

Greedy decoding reproduced exactly for Qwen3-8B in an independent check; it did **not** for the
AWQ-quantised 14B and 32B models (see `results/tables/t27_independent_rerun.md`).

## Data and licences

Code is released under the MIT licence (`LICENSE`); the project's own data under CC BY 4.0.
Third-party data keep their own licences; see `DATA_LICENSES.md`. In particular, six benchmark items come from HalluTruthQA-4K
(CC BY-NC-ND 4.0) and may be used only non-commercially and without modification.

## Known limitations

41 benchmark items and 12 scholar-rated items; one seed; four raters who are co-authors; Sunni
sources only (Qur'an, six hadith collections, four schools); thresholds not calibrated against
scholar labels; regeneration was executed once, for the flagged Qwen3-8B answers only, and no
regenerated answer, abstention or escalation output was rated by scholars. See the paper's Section 5.4.

## Citation

See `CITATION.cff`. Until the article is published, cite the repository:
https://github.com/tsgunawan/IslamicGuard
