---
license: mit
task_categories:
- question-answering
language:
- en
- ar
tags:
- QA
- Question
- Islam
- Ethics
- Religion
- LLM
pretty_name: FiqhQA
size_categories:
- n<1K
dataset_info:
- config_name: arabic
  features:
  - name: Category
    dtype: string
  - name: Title_original
    dtype: string
  - name: statement_original
    dtype: string
  - name: Agreement
    dtype: string
  - name: question_ar
    dtype: string
  - name: maliki_ans
    dtype: string
  - name: hanafi_ans
    dtype: string
  - name: shafeii_ans
    dtype: string
  - name: hanbali_ans
    dtype: string
  splits:
  - name: train
    num_bytes: 380248
    num_examples: 121
  download_size: 184666
  dataset_size: 380248
- config_name: english
  features:
  - name: Category
    dtype: string
  - name: Title_original
    dtype: string
  - name: statement_original
    dtype: string
  - name: Agreement
    dtype: string
  - name: title_en
    dtype: string
  - name: statement_en
    dtype: string
  - name: question_en
    dtype: string
  - name: maliki_ans
    dtype: string
  - name: hanafi_ans
    dtype: string
  - name: shafeii_ans
    dtype: string
  - name: hanbali_ans
    dtype: string
  splits:
  - name: train
    num_bytes: 357493
    num_examples: 121
  download_size: 187173
  dataset_size: 357493
configs:
- config_name: arabic
  data_files:
  - split: train
    path: arabic/train-*
- config_name: english
  data_files:
  - split: train
    path: english/train-*
---

# Dataset Card for Dataset Name

<!-- Provide a quick summary of the dataset. -->

Paper: Sacred or Synthetic? Evaluating LLM Reliability and Abstention for Religious Questions

## Dataset Details

### Dataset Description

<!-- Provide a longer summary of what this dataset is. -->

We introduce a novel benchmark FiqhQA focused on the LLM generated Islamic rulings explicitly categorized by
the four major Sunni schools of thought, in both Arabic and English.

- **Curated by:** [Farah Atif, Nursultan Askarbekuly, Kareem Darwish and Monojit Choudhury]
- **Language(s) (NLP):** [ARABIC, ENGLISH]



- **Paper Link :** https://arxiv.org/pdf/2508.08287

## Citation [optional]

<!-- If there is a paper or blog post introducing the dataset, the APA and Bibtex information for that should go in this section. -->

**BibTeX:**

@misc{atif2025sacredsyntheticevaluatingllm,
      title={Sacred or Synthetic? Evaluating LLM Reliability and Abstention for Religious Questions}, 
      author={Farah Atif and Nursultan Askarbekuly and Kareem Darwish and Monojit Choudhury},
      year={2025},
      eprint={2508.08287},
      archivePrefix={arXiv},
      primaryClass={cs.CL},
      url={https://arxiv.org/abs/2508.08287}, 
}


## Dataset Card Contact

[farah.atif@mbzuai.ac.ae]