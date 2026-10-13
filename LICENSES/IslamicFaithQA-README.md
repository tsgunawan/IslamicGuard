---
license: apache-2.0
configs:
- config_name: arabic
  data_files:
  - split: test
    path: arabic/dataset_with_difficulty_clean_updated.jsonl
- config_name: english
  data_files:
  - split: test
    path: english/dataset_with_difficulty_clean_updated.jsonl
language:
- ar
- en
size_categories:
- 1K<n<10K
---

# IslamicFaithQA

**IslamicFaithQA** is a bilingual (Arabic/English) *generative* Islamic question answering benchmark designed for faithfulness-oriented evaluation. The dataset is intended to support research on correctness, hallucination reduction, and abstention behavior in Islamic QA, including retrieval-augmented and agentic approaches.

This dataset accompanies the paper:

- *From RAG to Agentic RAG for Faithful Islamic Question Answering* (arxiv.org/abs/2601.07528)

## Dataset summary

- **Languages:** Arabic and English (separate configurations).
- **Split:** `test` only.
- **Format:** JSONL files in the repository (typically auto-converted to Parquet by the Hub for efficient viewing).
- **Goal:** Evaluate free-form (generative) answers with an emphasis on faithfulness and controlled hallucination.

## Configurations

The dataset provides two configurations:

- `arabic`: Arabic questions and answers
- `english`: English questions and answers

Each configuration contains a single split:

- `test`

## Data fields

Each example contains the following fields:

- `id` *(string)*: Unique example identifier.
- `category` *(string)*: Fine-grained topic/category label.
- `question` *(string)*: The question text (Arabic or English depending on config).
- `gold_answer` *(string)*: A single gold answer intended to be short/atomic.
- `source` *(string)*: Source label indicating the upstream resource the item was derived from.
- `difficulty` *(int)*: Difficulty rating on a 1–5 scale.
- `reasoning` *(bool)*: Whether the question requires reasoning (binary flag).
- `multi_step` *(bool)*: Whether the question requires multiple steps (binary flag).
- `category_type` *(string)*: Higher-level category grouping.
- `error` *(nullable)*: Optional field, typically null.

## Intended use

### Recommended use cases
- Benchmarking **generative** Islamic QA systems under strict or judge-based evaluation.
- Studying **hallucination** and **faithfulness** in a high-stakes domain.
- Evaluating **abstention** behavior (e.g., when a model should say it does not know).
- Stratified analysis by difficulty, reasoning requirement, and multi-step requirement.

### Not recommended
- Treating the dataset (or model outputs evaluated on it) as a replacement for qualified scholarly guidance.
- Deploying systems trained or tuned on this dataset as religious authority tools without robust safeguards.

## How to load

```python
from datasets import load_dataset

ds_ar = load_dataset("QCRI/IslamicFaithQA", "arabic")
ds_en = load_dataset("QCRI/IslamicFaithQA", "english")

print(ds_ar["test"][0])

questions = [x["question"] for x in ds_ar["test"]]
answers   = [x["gold_answer"] for x in ds_ar["test"]]
```

## Citation

If you use this dataset, please cite:

```bibtex
@inproceedings{bhatia-etal-2026-rag-agentic-rag,
  title     = {From {RAG} to Agentic {RAG} for Faithful Islamic Question Answering},
  author    = {Bhatia, Gagan and
               Mubarak, Hamdy and
               Jarrar, Mustafa and
               Mikros, George and
               Zaraket, Fadi and
               Alhirthani, Mahmoud and
               Al-Khatib, Mutaz and
               Cochrane, Logan and
               Darwish, Kareem and
               Yahiaoui, Rashid and
               Alam, Firoj},
  booktitle = {Proceedings of the 64th Annual Meeting of the Association for Computational Linguistics},
  month     = jul,
  year      = {2026},
  address   = {San Diego, California, United States},
  publisher = {Association for Computational Linguistics},
  note      = {Accepted to ACL 2026}
}
```
