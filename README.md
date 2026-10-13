# IslamicGuard

Code, benchmark, run records and analysis for the paper

> **IslamicGuard: A Scholar-Audited Evaluation of a Layered Guardrail for Islamic Question Answering**
> Teddy Surya Gunawan, Mira Kartiwi, Asmuliadi Lubis, Mohd Abd Wahab Fatoni Mohd Balwi, Muntaha Artalim Zaim, Rio Erismen Armen.
> *IIUM Engineering Journal*, Vol. 28, No. 1, January 2027. Page numbers pending.
> DOI: [10.31436/iiumej.v28i1.4817](https://doi.org/10.31436/iiumej.v28i1.4817).

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

## Installation (Linux or Windows with WSL 2)

The experiments used Python 3.11 on Windows Server 2022 with WSL 2, CUDA 13.0,
and one NVIDIA RTX 4090 (24 GB). Use a Linux environment; on Windows, run the
commands below inside Ubuntu on WSL 2. Saved-result analysis runs on CPU;
fresh model generation requires an NVIDIA GPU for the documented workflow.

### 1. Set up WSL on Windows

In **PowerShell as Administrator**, install Ubuntu, then restart if prompted:

```powershell
wsl --install -d Ubuntu
wsl --update
wsl --list --verbose
```

Confirm Ubuntu uses WSL 2. If it uses version 1, run
`wsl --set-version Ubuntu 2`. Open Ubuntu and complete its user setup.
Linux users can continue to step 2.
See [Microsoft's WSL installation guide](https://learn.microsoft.com/en-us/windows/wsl/install).

For GPU generation, install an NVIDIA driver on **Windows** that supports CUDA
in WSL, then check `nvidia-smi` inside Ubuntu. See
[Microsoft's CUDA on WSL guide](https://learn.microsoft.com/en-us/windows/ai/directml/gpu-cuda-in-wsl).

### 2. Clone and install dependencies

Install a **Linux** Conda distribution inside Ubuntu if `conda` is unavailable;
see the [Conda installation guide](https://docs.conda.io/projects/conda/en/stable/user-guide/install/index.html).
Then run these commands in the Ubuntu/Linux terminal:

```bash
sudo apt update
sudo apt install -y git build-essential
mkdir -p ~/projects
cd ~/projects
git clone https://github.com/tsgunawan/IslamicGuard.git
cd IslamicGuard
conda env create -f environment.yml
conda activate islamicguard
python -m pip check
```

Run all subsequent commands from the repository root with this environment active.
The environment installs the dependencies in `requirements.txt` automatically.
`requirements-lock.txt` is an archival freeze of the original environment;
it has dependency conflicts and must not be used as the installation requirements.
The full environment includes generation packages even when only analyzing saved results.
Model weights, retrieval indexes and downloaded corpora are fetched or built locally.

### 3. Download data and check the validators

```bash
python scripts/download_benchmarks.py
python scripts/build_corpus.py
python -m pytest -q
```

The scripts populate `data/raw/` and rebuild `data/corpus/{quran,hadith,fiqh}.jsonl`.
Internet access is required for acquisition; these files are excluded from Git.
The recorded validator test suite contains 80 tests. Check download messages for
failures before continuing to corpus construction.

## Reproduce the analysis (no GPU needed)

The result tables and figures are regenerated from the saved records in `runs/` and `results/`.
The validators need the retrieval corpus, which is rebuilt from its public sources first
(download size and time depend on the upstream sources and network):

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

After installing dependencies and rebuilding the corpus, check GPU access and
build the three retrieval layers with the embedding model used by B5:

```bash
nvidia-smi
python -c "import torch; print('CUDA available:', torch.cuda.is_available())"
python scripts/build_index.py --model qwen3-embedding-4b
```

The index builder downloads `Qwen/Qwen3-Embedding-4B` and writes indexes under
`data/corpus/index/qwen3-embedding-4b/`. The generation scripts download their
model weights on first use. The documented 8B workflow was run on a 24 GB GPU;
other GPU configurations have not been established by these instructions.

Start with the small sample, then run the full benchmark:

```bash
python scripts/run_islamicguard_b5.py --model Qwen/Qwen3-8B --sample data/benchmarks/t13_pipeline_sample.jsonl
python scripts/run_islamicguard_b5.py --model Qwen/Qwen3-8B --sample data/benchmarks/t15_benchmark.jsonl
```

Each run writes a timestamped directory under `runs/` containing `responses.jsonl`,
`guardrail_traces.jsonl`, configuration and metrics. The command accepts a JSONL
sample file rather than an interactive chat prompt. For your own questions, supply
one JSON object per line with `item_id`, `language` (`en` or `ar`), `query`,
`source_dataset` and `source_category`, then pass that file using `--sample`.
For example:

```json
{"item_id":"custom_001","language":"en","query":"What is zakat?","source_dataset":"custom","source_category":"fiqh"}
```

For a baseline comparison and the revision-2 experiments:

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

Original code, prompts and documentation use [MIT](LICENSE); original research data use
[CC BY 4.0](LICENSE-DATA.md). Bundled license texts and source attributions are in
[THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
Third-party data keep their own licences; see `DATA_LICENSES.md`. In particular, six benchmark items come from HalluTruthQA-4K
(CC BY-NC-ND 4.0) and may be used only non-commercially and without modification.

## Known limitations

41 benchmark items and 12 scholar-rated items; one seed; four raters who are co-authors; Sunni
sources only (Qur'an, six hadith collections, four schools); thresholds not calibrated against
scholar labels; regeneration was executed once, for the flagged Qwen3-8B answers only, and no
regenerated answer, abstention or escalation output was rated by scholars. See the paper's Section 5.4.

## Citation

Gunawan, T. S., Kartiwi, M., Lubis, A., Mohd Balwi, M. A. W. F., Zaim, M. A.,
& Armen, R. E. (2027). IslamicGuard: A Scholar-Audited Evaluation of a Layered
Guardrail for Islamic Question Answering. *IIUM Engineering Journal, 28*(1).
https://doi.org/10.31436/iiumej.v28i1.4817

Page numbers will be added when available. The issue is January 2027.

```bibtex
@article{gunawan2027islamicguard,
  author = {Gunawan, Teddy Surya and Kartiwi, Mira and Lubis, Asmuliadi and
            Mohd Balwi, Mohd Abd Wahab Fatoni and Zaim, Muntaha Artalim and
            Armen, Rio Erismen},
  title = {{IslamicGuard}: A Scholar-Audited Evaluation of a Layered Guardrail for Islamic Question Answering},
  journal = {IIUM Engineering Journal},
  year = {2027},
  volume = {28},
  number = {1},
  month = jan,
  doi = {10.31436/iiumej.v28i1.4817},
  url = {https://doi.org/10.31436/iiumej.v28i1.4817}
}
```

[CITATION.cff](CITATION.cff) provides machine-readable software and article metadata.
Repository: https://github.com/tsgunawan/IslamicGuard

## Upload to GitHub

See [GITHUB_UPLOAD.md](GITHUB_UPLOAD.md) for the initial upload and tagged release steps.
