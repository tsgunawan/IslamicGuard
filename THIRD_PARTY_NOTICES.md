# Third-party notices

The project MIT license and original-data CC BY 4.0 license do not replace
third-party licenses. Source cards in `data/raw/*/DATASET_CARD.md` record the
versions used. Publications are listed in `literature/references.bib`.

| Material | Source and attribution | License |
|---|---|---|
| IslamicFaithQA excerpts | Bhatia et al., 2026; [QCRI/IslamicFaithQA](https://huggingface.co/datasets/QCRI/IslamicFaithQA) | [Apache 2.0](LICENSES/Apache-2.0.txt) |
| FiqhQA excerpts | Farah Atif, Nursultan Askarbekuly, Kareem Darwish and Monojit Choudhury, 2025; [MBZUAI/FiqhQA](https://huggingface.co/datasets/MBZUAI/FiqhQA) | [MIT](LICENSES/MIT.txt); source declaration and attribution in [FiqhQA-README.md](LICENSES/FiqhQA-README.md) |
| IslamicEval 2025 Subtask 1 excerpts | Mubarak et al., 2025; [QCRI/IslamicEval-2025-Subtask-1](https://github.com/qcri/IslamicEval-2025-Subtask-1) | [Apache 2.0](LICENSES/Apache-2.0.txt) |
| HalluTruthQA-4K excerpts | Bekhouche et al., 2026; [Bekhouche/HalluTruthQA-4K](https://huggingface.co/datasets/Bekhouche/HalluTruthQA-4K) | [CC BY-NC-ND 4.0](LICENSES/CC-BY-NC-ND-4.0.txt) |

IslamicGuard selects source questions and reference answers and stores them in its
own JSONL schema with item identifiers, strata and evaluation metadata. These
changes to selection, packaging and project metadata do not transfer ownership of
source text. HalluTruthQA question and reference-answer text is retained unmodified;
project annotations and model outputs are separate fields or records. Its source
text may be shared only under its original attribution, noncommercial and
no-derivatives conditions.

The upstream IslamicFaithQA dataset card, including its attribution and use
recommendations, is preserved in [IslamicFaithQA-README.md](LICENSES/IslamicFaithQA-README.md).
The FiqhQA source version supplies `license: mit` in its dataset card and no
separate copyright or license file; its supplied attribution is preserved here.

Unlicensed IslamicEval 2025 QH-QA question fields are withheld; only identifiers
and study outputs are included. Some generated answers quote their input question,
as recorded in `DATA_LICENSES.md`. Downloaded datasets, canonical corpora and model
weights are excluded from the release and retain their upstream terms.
