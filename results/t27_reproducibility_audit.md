# T27 independent reproducibility audit

Audited on 2026-09-30 against `manuscript/draft.md` at commit `648c40b`. The manuscript did not change between that commit and `3587d03`, when this report was written. I read [STATUS.md](../STATUS.md) and [paper.md §15](../paper.md), but did not use `scripts/audit_manuscript_numbers.py` or rely on its output. Sections 1–5 below document the **historical three-rater snapshot** and must not be read as current four-rater results. A fresh four-rater audit after E4 was added appears in §6. This is a report of findings; no manuscript or code fixes were made.

## 1. Environment and tests

- Created a fresh Python 3.11 environment at `/tmp/islamicguard-t27` with `conda env create -f environment.yml -p /tmp/islamicguard-t27`.
- `environment.yml` specifies Python but no test or runtime dependencies. Before installing any other packages, `python -m pytest` failed with `No module named pytest`.
- Installing the complete [requirements-lock.txt](../requirements-lock.txt) failed dependency resolution. It pins `protobuf==7.36.1`, while its `nvidia-cutlass-dsl-libs-*==4.6.2` packages require `protobuf>=6.30.2,<7`. The pre-existing `islamicguard` environment also fails `pip check` on the same four CUTLASS/protobuf conflicts. Thus the exact full lock cannot be recreated by a resolving installer.
- Installed the test dependencies and a working inference stack in the fresh environment (`pytest==9.1.1`, `RapidFuzz==3.14.6`, `torch==2.13.0`, `transformers==5.17.0`, `accelerate==1.15.0`, `GPTQModel==7.5.0`, `numpy==2.2.6`, with resolved transitive dependencies). This is **not** an installation of the complete lock. The fresh environment has `protobuf==7.36.2` and `pip check` reports no broken requirements.
- Ran `/tmp/islamicguard-t27/bin/python -m pytest -q -p no:cacheprovider`: **80 passed** (5.95 s after runtime installation).

## 2. Independent generation comparison

Selected [four T15 items](../data/benchmarks/t27_t15_sample.jsonl): one English correct-quotation item, one Arabic misquoted-Qur'an item, one Arabic fabricated-citation-risk item, and one English madhhab item. Ran `scripts/run_baseline.py --condition B0 --sample data/benchmarks/t27_t15_sample.jsonl` once per model with the fresh interpreter. The saved run configurations and new responses agree on model revision, seed 42, greedy decoding, thinking disabled, and 512-token limit. Compared full response text by unique T15 `item_id` against the original September 20 T15 B0 runs.

| Model | Exact text matches | New run | Saved run |
|---|---:|---|---|
| Qwen3-8B | 4/4 | [responses](../runs/20260930-1229_Qwen__Qwen3-8B_B0_t27_t15_sample_s42/responses.jsonl) | [responses](../runs/20260920-0426_Qwen__Qwen3-8B_B0_t15_benchmark_s42/responses.jsonl) |
| Qwen3-14B-AWQ | 1/4 | [responses](../runs/20260930-1231_Qwen__Qwen3-14B-AWQ_B0_t27_t15_sample_s42/responses.jsonl) | [responses](../runs/20260920-0804_Qwen__Qwen3-14B-AWQ_B0_t15_benchmark_s42/responses.jsonl) |
| Qwen3-32B-AWQ | 1/4 | [responses](../runs/20260930-1234_Qwen__Qwen3-32B-AWQ_B0_t27_t15_sample_s42/responses.jsonl) | [responses](../runs/20260920-0840_Qwen__Qwen3-32B-AWQ_B0_t15_benchmark_s42/responses.jsonl) |

An additional four-item [T09 sample](../data/benchmarks/t27_repro_sample.jsonl) in the fresh environment matched the saved T09 text at 4/4, 2/4, and 4/4 for 8B, 14B-AWQ, and 32B-AWQ respectively. These are exact-text checks, not accuracy estimates. The original [T09 sample](../data/benchmarks/t09_pipeline_sample.jsonl) uses `faithqa_MIZAN-002_en` for two different questions (lines 2 and 3); comparisons must use the question text or row position as well as the ID.

**Artifact logging defect.** [run_baseline.py](../scripts/run_baseline.py) invokes the shell command `pip freeze` rather than `sys.executable -m pip freeze`. Its new `environment.txt` files therefore captured the older environment on `PATH`, including `protobuf==7.36.1`, although the fresh interpreter used for generation has `protobuf==7.36.2`. The new response files correctly record the model revisions and generation settings, but their package manifests cannot establish the actual package environment.

## 3. Manuscript numerical-claim trace

I read the claims in [draft.md](../manuscript/draft.md) against their source files directly. Main reported counts, means, confidence intervals, policy totals, parser revalidation, token-limit results, and efficiency results agree with the files below, subject to the discrepancies in §4.

| Draft material | Independently checked source |
|---|---|
| Corpus sizes (6,236 Qur'an verses; 34,157 hadith; 121 fiqh), benchmark 41 items/28 English/13 Arabic/five constructed and six strata | Line counts in [quran.jsonl](../data/corpus/quran.jsonl), [hadith.jsonl](../data/corpus/hadith.jsonl), [fiqh.jsonl](../data/corpus/fiqh.jsonl); records in [t15_benchmark.jsonl](../data/benchmarks/t15_benchmark.jsonl) |
| Retrieval k=3 per layer; 328 retrieval-evaluation queries; overall recall@1 0.683/0.433 and Qur'an recall@1 0.045/0.023 | [generate.py](../src/rag/generate.py), [retrieval evaluation](tables/t08_retrieval_eval.md), original B5 traces |
| Validator and policy thresholds (0.55, 0.5, two schools, 0.8, 0.3), 27-item calibration and 55.6% agreement | [faithfulness_validator.py](../src/validators/faithfulness_validator.py), [madhhab_policy.py](../src/guardrails/madhhab_policy.py), [abstention_policy.py](../src/guardrails/abstention_policy.py), [calibration set](../data/benchmarks/t12_calibration_set.jsonl) |
| Three raters, 36 cards, rating means, error counts, agreement, confidence intervals and paired comparisons | [rating rows](error_analysis/t19_expert_ratings_long.jsonl), [card codes](error_analysis/t23_card_codes.jsonl), [agreement](tables/t19_expert_agreement.md), [statistical comparison](tables/t22_statistical_comparison.md), [error analysis](tables/t23_error_analysis.md). The pre-correction correlation statement also traces to the historical `t19_automated_vs_scholar.md` at commit `474429b`. |
| 41-item B0/B1/B5 citation shares, token means and policy actions; 32B repeat-run 9/41 text and 35/41 action agreement | [item-level outcomes](error_analysis/t22_item_level_outcomes.jsonl), [statistical comparison](tables/t22_statistical_comparison.md) |
| Arabic parser 33/34 before and 28/34 after; sensitivity 0.11 to 0.42; two of three false passes caught | [parser revalidation](tables/t11_arabic_parser_revalidation.md) |
| Token-limit counts and rates, timing and GPU memory, eight injections and four benign controls | [token-limit rerun](tables/b0_token_limit_rerun.md), [efficiency profile](tables/t18_efficiency_profile.md), [injection evaluation](tables/t17_prompt_injection.md) |
| External study figures (Aftina 18,407 and 210; Ansari 34; Zizzo 15; IslamicLegalBench 21.25%) | Saved primary papers in `ref/`, including the [Aftina PDF](../ref/Mohammed2025_Aftina_Enhancing%20stability%20and%20preventing%20hallucination%20in%20AI-based%20Islamic%20fatwa%20generation%20using%20LLMs%20and%20RAG.pdf), [Ansari PDF](../ref/Kadous2026_Ansari_A_Retrieval-Grounded_Islamic_AI_Assistant_Architecture_Deployment_and_Lessons_from_140000_Conversations.pdf), and [IslamicLegalBench preprint](../ref/Elmahjub2026_IslamicLegalBench_Evaluating_LLMs_Knowledge_and_Reasoning_of_Islamic_Law_Across_1200_Years_of_Islamic_Pluralist_Legal_Traditions.pdf) |
| Author-biography years and percentages | University profiles for [Gunawan](https://www.iium.edu.my/staff-profile/NTU4OA/), [Kartiwi](https://www.iium.edu.my/staff-profile/NjMyNg/), and [Zaim](https://www.iium.edu.my/my/staff/show/7555); one unsupported percentage is listed below |

## 4. Discrepancies and claims requiring narrower wording

1. **“44 qualified scholars” is unsupported.** [Draft line 27](../manuscript/draft.md) attributes that count to IslamicLegalBench. Its saved preprint and [published methods](https://link.springer.com/article/10.1007/s10506-026-09535-4) say **two independent experts** graded a stratified subset of **140** responses. The “(44)” near “qualified Islamic scholars” in the preprint is a reference number. The cited preprint supports the draft's “six of nine” misleading-premise figure; the [published version](https://link.springer.com/article/10.1007/s10506-026-09535-4) says **five of nine** under few-shot prompting. This is source-version drift, not a DOI metadata mismatch.
2. **Scope of scholar audit is overstated.** The abstract and conclusion say **every layer** was audited against three scholars. The [rating data](error_analysis/t19_expert_ratings_long.jsonl) cover 36 generated answers: B0 and B5 for 8B plus B5 from one larger model per item. Scholars did not rate B1–B4 outputs or final abstention/regeneration messages. The draft's limitations acknowledge the latter.
3. **Ablation scope is ambiguous.** The introduction says 41 questions went through “each condition” in a six-condition, three-model account. The methods correctly say only 8B ran all six; 14B and 32B ran B0, B2 and B5.
4. **Equation (3) is not the implemented quotation matcher.** [Qur'an](../src/validators/quran_validator.py) and [hadith](../src/validators/hadith_validator.py) matching require minimum quote lengths and include partial-match routes (Qur'an 92%, Arabic hadith 88% for sufficiently long text). The draft equation specifies only containment or whole-string 85%/80% similarity.
5. **Configuration and source-provenance wording are incomplete.** Table 3 lists AutoAWQ installed for quantised weights but omits GPTQModel, which the AWQ loading path uses. The statement that **every table and figure** is regenerated from run records is too broad: the literature comparison draws on `literature/gap_table.csv`, and conceptual/configuration tables have other sources. The separate `environment.txt` logging defect is described in §2.
6. **Severity comparison does not prove threshold impossibility.** The discussion correctly gives scholar severity **1.47** for abstained versus **1.65** for passed answers, but this small descriptive sample does not establish that abstention is independent of answer quality or that no threshold can be useful.
7. **Qur'an recall does not measure scholar citation choice.** The discussion uses recall@1 **0.045** to say retrieved verses were usually not those a scholar would cite and to infer a downstream causal chain. [T08](tables/t08_retrieval_eval.md) tested exact gold verse IDs on separate queries, warned that passage-level relevance may be undercounted, and did not measure what scholars would cite.
8. **Answer-length effect is not isolated.** The [longer-answer rerun](tables/b0_token_limit_rerun.md) supports **0.41 to 1.17** unverified citations per answer for 8B. It does not isolate the claim that a policy prompt or retrieval context reduces fabricated-text exposure *independently of any validator*.
9. **“Every Arabic citation” is too broad.** The conclusion says the original validator missed every Arabic citation. [T11](tables/t11_arabic_parser_revalidation.md) reports **33 of 34 Arabic answers** with no citation checked before correction; the supported description concerns Arabic-form citations.
10. **One biography percentage remains unverified.** Kartiwi's [IIUM profile](https://www.iium.edu.my/staff-profile/NjMyNg/) supports the **2004** and **2007** award years but does not substantiate the draft's **“World's Top 5% Scientists by SciRank Global”** claim. I found the ranking operator's general registry, but no individual entry confirming her inclusion. Gunawan's dated claims match his [IIUM profile](https://www.iium.edu.my/staff-profile/NTU4OA/); Zaim's **since 2017** editorship matches his [IIUM directory](https://www.iium.edu.my/my/staff/show/7555).
11. **T09 item IDs are not unique.** The duplicate `faithqa_MIZAN-002_en` appears on distinct questions in [t09_pipeline_sample.jsonl](../data/benchmarks/t09_pipeline_sample.jsonl). It is a comparison-key risk; the T15 sample used for the primary rerun has unique IDs.

## 5. DOI resolution and metadata comparison

Resolved every DOI in the current [reference list](../manuscript/draft.md) through `doi.org` with CSL JSON metadata. For all **25/25**, the resolved title, ordered author identities, and publication year agree with the entry, allowing capitalization and name-particle formatting. No DOI metadata discrepancy was found. Non-DOI references were outside the requested DOI check.

| Reference | DOI | Title | Authors | Year |
|---|---|:---:|:---:|:---:|
| Abbas | [10.48550/arXiv.2603.08501](https://doi.org/10.48550/arXiv.2603.08501) | ✓ | ✓ | ✓ |
| Abdelaal | [10.48550/arXiv.2603.23750](https://doi.org/10.48550/arXiv.2603.23750) | ✓ | ✓ | ✓ |
| Aghajani Asl | [10.48550/arXiv.2510.25621](https://doi.org/10.48550/arXiv.2510.25621) | ✓ | ✓ | ✓ |
| Akbar | [10.48550/arXiv.2607.28237](https://doi.org/10.48550/arXiv.2607.28237) | ✓ | ✓ | ✓ |
| Ali | [10.1007/s13347-025-00922-4](https://doi.org/10.1007/s13347-025-00922-4) | ✓ | ✓ | ✓ |
| Atif | [10.48550/arXiv.2508.08287](https://doi.org/10.48550/arXiv.2508.08287) | ✓ | ✓ | ✓ |
| Bekhouche | [10.48550/arXiv.2608.03966](https://doi.org/10.48550/arXiv.2608.03966) | ✓ | ✓ | ✓ |
| Bhatia | [10.18653/v1/2026.findings-acl.1317](https://doi.org/10.18653/v1/2026.findings-acl.1317) | ✓ | ✓ | ✓ |
| Dong (2025) | [10.1007/s10462-025-11389-2](https://doi.org/10.1007/s10462-025-11389-2) | ✓ | ✓ | ✓ |
| El Amrani | [10.5614/itbj.ict.res.appl.2025.19.1.4](https://doi.org/10.5614/itbj.ict.res.appl.2025.19.1.4) | ✓ | ✓ | ✓ |
| Elmahjub (2023) | [10.1007/s13347-023-00668-x](https://doi.org/10.1007/s13347-023-00668-x) | ✓ | ✓ | ✓ |
| Elmahjub et al. (2026 preprint) | [10.48550/arXiv.2602.21226](https://doi.org/10.48550/arXiv.2602.21226) | ✓ | ✓ | ✓ |
| Eltanbouly | [10.48550/arXiv.2608.20246](https://doi.org/10.48550/arXiv.2608.20246) | ✓ | ✓ | ✓ |
| Hu | [10.48550/arXiv.2408.08959](https://doi.org/10.48550/arXiv.2408.08959) | ✓ | ✓ | ✓ |
| Kadous | [10.48550/arXiv.2608.20390](https://doi.org/10.48550/arXiv.2608.20390) | ✓ | ✓ | ✓ |
| Khalila | [10.48550/arXiv.2503.16581](https://doi.org/10.48550/arXiv.2503.16581) | ✓ | ✓ | ✓ |
| Krippendorff | [10.4135/9781071878781](https://doi.org/10.4135/9781071878781) | ✓ | ✓ | ✓ |
| Laban | [10.1162/tacl_a_00453](https://doi.org/10.1162/tacl_a_00453) | ✓ | ✓ | ✓ |
| Lewis | [10.48550/arXiv.2005.11401](https://doi.org/10.48550/arXiv.2005.11401) | ✓ | ✓ | ✓ |
| Min | [10.18653/v1/2023.emnlp-main.741](https://doi.org/10.18653/v1/2023.emnlp-main.741) | ✓ | ✓ | ✓ |
| Mohammed | [10.1007/s00521-025-11229-y](https://doi.org/10.1007/s00521-025-11229-y) | ✓ | ✓ | ✓ |
| Mubarak | [10.18653/v1/2025.arabicnlp-sharedtasks.67](https://doi.org/10.18653/v1/2025.arabicnlp-sharedtasks.67) | ✓ | ✓ | ✓ |
| Yao | [10.48550/arXiv.2504.09593](https://doi.org/10.48550/arXiv.2504.09593) | ✓ | ✓ | ✓ |
| Ziani | [10.48550/arXiv.2608.03720](https://doi.org/10.48550/arXiv.2608.03720) | ✓ | ✓ | ✓ |
| Zizzo | [10.48550/arXiv.2502.15427](https://doi.org/10.48550/arXiv.2502.15427) | ✓ | ✓ | ✓ |

The IslamicLegalBench journal article appeared on 17 September 2026 at [10.1007/s10506-026-09535-4](https://doi.org/10.1007/s10506-026-09535-4). The draft cites the matching arXiv-preprint DOI, so the newer article is a version-choice question and a source for the changed false-premise result, not a DOI mismatch.

## 6. Four-rater re-audit after E4 (2026-10-01)

Audited [draft.md](../manuscript/draft.md) at commit `f15a11a`, concentrating on §§3.10, 4.1, 4.2, 4.4, 4.5 and 5, and scanned its abstract, conclusion, ethics statement, supporting manuscript tables and working Word file for rater counts. No E4-driven manuscript text or result-table changes occurred between commits `7545c77` and `f15a11a`. This addendum supersedes the three-rater scholar statistics and related discrepancy descriptions in §§3–4 above; it does not repeat the clean-environment or DOI checks.

### E4 source and recalculation checks

- The processed four-rater workbook `expert_review/incoming/IslamicGuardresponse4v2.xlsx` has the same header and E1–E3 response rows as the earlier `IslamicGuardresponsesv2.xlsx` (255 cells per row, no changed cells in those rows) and adds E4's row. These workbooks are git-ignored; this report does not reproduce personal data or free-text comments.
- [Long-form ratings](error_analysis/t19_expert_ratings_long.jsonl) contain **864 rows = 36 cards × 4 raters × 6 fields**, with exactly one entry for each rater/field/card. The workbook's translation log has **48 entries: 10 Arabic and 38 Malay**, of which **36** are E4 comments. These counts support §3.10.
- Independently grouping the rating rows by card and model label yields mean factual quality **2.29/2.92** for 8B B0/B5, **3.29** for 14B B5 and **3.12** for 32B B5; source scores **2.12/2.79** for 8B B0/B5; severity **2.19/1.80** for 8B B0/B5. Under the stated mean-severity ≥2 definition, 8B has **9/12** scholar-bad B0 cards and **5/12** scholar-bad B5 cards. These agree with [T19](tables/t19_expert_agreement.md), [T22](tables/t22_statistical_comparison.md) and the draft.
- I checked the new paired estimates, CIs and Holm-adjusted p-values in §4.2 against [T22 section E](tables/t22_statistical_comparison.md): quality difference **+0.62 [0.17, 1.15]**, adjusted p **0.164**; source **+0.67 [0.09, 1.31]**, p **0.182**; evidence **+0.17 [0.01, 0.32]**, p **0.182**; severity **−0.39 [−0.90, +0.10]**. The draft correctly distinguishes the unadjusted bootstrap intervals from Holm-corrected tests.
- The initial and post-parser validation figures in §4.4 agree with [T19 automated comparison](tables/t19_automated_vs_scholar.md) and [T11 replay](tables/t11_arabic_parser_revalidation.md): 18/36 scholar-bad, 32/36 faithfulness flags (17 TP, 15 FP; sensitivity **0.94**, specificity **0.17**), initial provenance 2/18 (**0.11**), corrected provenance 8/18 (**0.44**, precision 8/9 = **0.89**), and B5 intervention sensitivity 6/9 to 8/9 (**0.67** to **0.89**) at specificity 7/15 = **0.47**. The pre-fix correlations are correctly identified as pre-fix; current misquote correlations **−0.45** with quality and **+0.47** with severity match the table.
- The B5 policy counts and model-specific rating means in §4.5 agree with [T11 replay](tables/t11_arabic_parser_revalidation.md), [T22 section F](tables/t22_statistical_comparison.md), and [T23](tables/t23_error_analysis.md). The counts **14/11/15/1** for 8B and **12/13/15/1** after parser correction are correct. Four passed 8B cards average quality **2.62** versus **3.06** for eight intervened-on 8B cards. The discussion's **1.65** severity for abstained versus **1.74** for passed B5 cards agrees with [T19](tables/t19_automated_vs_scholar.md).

### Discrepancies and wording needing clarification

1. **§4.1 mixes rating scales.** [Draft §4.1](../manuscript/draft.md) says that on the “five-point scales” ratings fall within one point in **0.84 to 0.91** of pairs. The two five-point fields are quality (**0.84**) and source appropriateness (**0.85**). **0.91** is error severity, which has a **0–3** scale. The range is correct for all three ordered fields, not for the five-point fields alone. [T19 agreement](tables/t19_expert_agreement.md) supplies the field values.
2. **§4.1's “fourth” rater is easy to misidentify.** Direct pairwise recalculation from the long-form ratings confirms that **E2, E3 and E4** agree with one another on boundary action in **0.44–0.68** of assessable pairs, whereas **E1** agrees with each of them in **0.22–0.28**. The draft's numbers are correct, but “the fourth” is **E1**, not the newly added E4; naming the codes would prevent a mistaken reading.
3. **§4.5 leaves the “five interventions” denominator unclear.** Direct grouping of the [card-level data](error_analysis/t19_automated_vs_scholar_cards.jsonl) gives **8** interventions on non-scholar-bad answers among all **24** rated B5 cards, but **5** among the **12** 8B B5 cards. [T23](tables/t23_error_analysis.md) also lists **five G2** cases across models after excluding two answers that themselves decline and not counting the personal-ruling escalation as an inappropriate intervention. The draft says simply “On the rated answers, five interventions fell on answers the scholars found acceptable,” which can be read as all 24 B5 cards without the G2 exclusions. It needs the 8B scope or the G2 definition stated.
4. **§5.1 infers an untested absence of association.** [Draft discussion](../manuscript/draft.md) says abstention “showed no relation to answer quality” and predicts how threshold tuning would behave. [T19's action table](tables/t19_automated_vs_scholar.md) gives descriptive means for six abstained and ten passed B5 cards; it does not report a formal association or threshold analysis. The draft's “small sample” caveat is appropriate, but the asserted lack of relation is stronger than the table establishes.
5. **§5.1 treats scholar disagreement as a ceiling on policy agreement.** Alpha **0.61/0.53/0.01** matches [T19](tables/t19_expert_agreement.md), but “a policy cannot be expected to match [a scholar] better than scholars match each other” is not a bound demonstrated by alpha or a comparison in the result tables. A policy could, in principle, match a consensus target differently from pairwise agreement.
6. **§5.2 compares benefits on unlike measures.** The statement that retrieval's benefit is “smaller when scholars judge it than when automated scores do” is not directly established by [T22](tables/t22_statistical_comparison.md): scholar quality is a 1–5 rating on 12 items, whereas automated outcomes include citation rates on 41 items. The supported points are the direction of the scholar rating difference, its adjusted p-value, and **5/12** B5 answers still classified scholar-bad.
7. **Supporting files retain three-rater wording.** The draft and working `IslamicGuard_IJEEI.docx` use four scholars, but [table1_literature_gap.md](../manuscript/tables/table1_literature_gap.md) says “3 scholars,” and [table3_datasets_corpus.md](../manuscript/tables/table3_datasets_corpus.md) says “3 raters.” [table8_scholar_agreement.md](../manuscript/tables/table8_scholar_agreement.md) has four-rater values yet cites the *old* `IslamicGuardresponsesv2.xlsx` as its source. The stale text is hard-coded in [make_figures_tables.py](../scripts/make_figures_tables.py), so regenerating these tables will reproduce it. The older §§3–4 of this audit file are explicitly historical; they are not current four-rater statements.

The remaining four-rater wording in the draft's abstract, introduction, §3.10, Table 5, Figure 2 caption, §4.2, §4.4, §4.5, limitations, conclusion and ethics statement is consistent with the current rating rows and result tables. I made no manuscript, supporting-table, or analysis-code fixes in this re-audit.

## 7. Re-audit after fixes in 806e903 (2026-10-01)

This recheck is against commit `806e903`, which includes the changes identified in §6. I reread §§3.10, 4.1, 4.2, 4.4, 4.5 and 5 of [the draft](../manuscript/draft.md) against the current [T19 agreement](tables/t19_expert_agreement.md), [T19 automated comparison](tables/t19_automated_vs_scholar.md), [T22 statistical comparison](tables/t22_statistical_comparison.md), [T23 error analysis](tables/t23_error_analysis.md), and the underlying long-form rating rows. This section supersedes §6 wherever §6 describes a discrepancy fixed by 806e903. I made no manuscript or analysis changes; this section is the only addition in this recheck.

### E4 profile paragraph in §5.1

I checked every numerical statement in the paragraph beginning “The rater who joined last” against [T19's rater profiles and tendencies](tables/t19_expert_agreement.md) and independently grouped `results/error_analysis/t19_expert_ratings_long.jsonl` by rater, field, and card:

- E4 rated 36 cards and has one not-assessable cell across all six fields.
- Mean severity is 2.11 for E4 and 1.54–1.94 for E1–E3; on the stated 0–3 scale, E4 is the strictest by this mean.
- E4's mean quality is 0.11 below the mean of the other three raters on the same cards; the three pairwise quality Spearman correlations are 0.62, 0.66, and 0.76.
- E4 selected escalation on 26 cards; E1, E2, and E3 selected it on 3, 14, and 17 cards, respectively.
- T19's four-rater quality/source alpha values are 0.61/0.60. The archived three-rater table at commit `474429b` gives 0.57/0.49. Boundary alpha is 0.01 with four raters and −0.01 in that three-rater snapshot. Thus the “adding E4 raised” figures and “stayed near zero” statement are accurate descriptions of those tables.

The paragraph's numbers and the direction of its comparison are supported. One sentence overstates the interpretation: “The scholars converge on whether an answer is right but not on what should be done with it.” Quality alpha of 0.61 is moderate, not evidence of convergence in a strong sense; boundary alpha of 0.01 does support essentially absent agreement on the action. The data support saying agreement is higher for quality than for boundary action, while remaining moderate for quality. The final clause that boundary action is what the policy automates is consistent with the policy definition and the study design. This is a residual wording concern, not a numerical discrepancy.

### Status of the seven §6 findings

| §6 finding | Recheck against 806e903 |
|---|---|
| §4.1 conflated five-point and four-level scales | Resolved: the draft gives 0.84/0.85 for the two five-point fields and 0.91 for severity separately. |
| §4.1's “fourth” rater could be mistaken for E4 | Resolved: it names E2, E3 and E4 as the higher-agreement cluster and contrasts E1. |
| §4.5 omitted the denominator/scope for five interventions | Resolved: it specifies 8 of 12 rated Qwen3-8B answers were intervened on and 5 of those were not judged bad. |
| §5.1 claimed abstention had no relation to quality | Resolved: the passage labels the six-versus-ten comparison descriptive, says it cannot show no relation, and says threshold tuning was not tested. |
| §5.1 treated inter-scholar agreement as a cap on policy agreement | Resolved: the unsupported cap is removed; the text describes individual ratings as uncertain references and calls for a larger-panel consensus label. |
| §5.2 compared retrieval benefit across unlike automated and scholar measures | Resolved: it now reports the scholar-scale difference, corrected significance, midpoint, and 5/12 severity count without claiming a relative effect size across measures. |
| Supporting tables/generator had stale three-rater wording/source | Resolved: Tables 1 and 3 say four scholars/raters; Table 8 cites the processed four-rater source; the table generator derives raters from the long-form data. The current working DOCX also contains four-scholar wording and no stale three-rater wording. |

### Remaining section and wording checks

- The E4 addition is consistent with §3.10: 36 cards, four coded raters, E4 completing ratings after E1–E3, and the stated translation counts are supported by the rating workbook/log described in §6. The “three answers” on each item means three model-condition outputs, not three raters.
- §4.1's agreement coefficients, within-one-point rates, rater pair comparisons, and severity scale match T19. The added wording distinguishes E1 from E2–E4 correctly.
- §4.2's paired estimates, item-bootstrap intervals and Holm-adjusted p-values match T22 section E. The text distinguishes the intervals from corrected significance tests.
- §4.4's bad-answer count, faithfulness counts, provenance sensitivity before/after the parser correction, and policy sensitivity/specificity match the cited T19/T11 tables. The current misquote correlations are −0.45 for quality and +0.47 for severity.
- §4.5's policy counts, subset scope and model-specific means match T11, T22 and T23. The five non-bad interventions is correctly scoped to the 8B B5 subset, rather than all rated B5 answers.
- Apart from the “converge” sentence identified above, §5's revised claims about abstention, consensus, and retrieval's modest measured benefit now track the cited data and state the relevant limits.
- The four-rater wording scan across the current draft, manuscript tables, results tables, generator and working DOCX found no stale active three-rater claim. References to “three answers” or “three models” describe experimental structure. Earlier dated audit/administrative notes retain historical three-rater descriptions, which are explicitly historical rather than current manuscript claims.

No manuscript, result table, or script was changed during this recheck. The E4 paragraph should be considered numerically verified with the single interpretation caveat above.
