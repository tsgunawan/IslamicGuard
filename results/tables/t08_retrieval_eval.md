# T08 — Retrieval evaluation: multilingual-e5-large-instruct vs. Qwen3-Embedding-4B

Real, measured results on this project's own corpus (`data/corpus/{quran,hadith,fiqh}.jsonl`)
and held-out query set (`data/benchmarks/retrieval_eval_queries.jsonl`, 328 query→gold pairs).
Per DECISIONS.md DG-4, this head-to-head comparison was explicitly required before ruling out
Qwen3-Embedding as an alternative to the literature-recommended primary
(multilingual-e5-large-instruct). Raw JSON: `t08_retrieval_eval_me5-large-instruct.json`,
`t08_retrieval_eval_qwen3-embedding-4b.json`.

## Query set construction (honest accounting — no silent dropping)

- **Qur'an**: 88 pairs, from IslamicEval `dev_SubtaskC` "WrongAyah" rows (real human-annotated
  misquotation-correction items). Query = the item's own original question (extracted from
  `dev_SubtaskC.xml`); gold = the canonical ayah(s) named in its `Correction` column, matched to
  `data/corpus/quran.jsonl` by normalized-text containment. **36 of 124 candidate WrongAyah rows
  were dropped** — no confident normalized-text match found (short/ambiguous correction spans) or
  no parseable query text for that `Question_ID`.
- **Fiqh**: 240 pairs, directly from `data/corpus/fiqh.jsonl`'s own `question_en`/`question_ar`
  fields (121 records × up to 2 languages; 2 records lack `question_ar`, so 240 not 242 — no
  records dropped, just 2 fewer language-specific pairs).
- **Hadith**: **0 pairs — investigated and explicitly excluded**, not an oversight. IslamicFaithQA
  gold answers sometimes cite hadith by number (e.g., "Sahih al-Bukhari (1285)"), but spot-checking
  4 such citations against `data/corpus/hadith.jsonl` (built from `fawazahmed0/hadith-api` per
  DG-5) by both `hadith_number` and `arabic_number` found **0/4 topically matched** — the popular
  citation-numbering convention used in IslamicFaithQA's answers is not the same numbering scheme
  as the corpus source. Forcing this match would violate the "do not guess a fuzzy match and call
  it gold" instruction, so Hadith retrieval quality is **not evaluated in this pass**. This is a
  real limitation of T08, not of the retrieval system — see "Open item" below.

## Results

| Layer | Metric | me5-large-instruct | Qwen3-Embedding-4B | Winner |
|---|---|---:|---:|---|
| **Overall** | Recall@1 | 0.433 | **0.683** | Qwen3-Embedding-4B |
| | Recall@5 | 0.546 | **0.753** | Qwen3-Embedding-4B |
| | Recall@10 | 0.598 | **0.756** | Qwen3-Embedding-4B |
| | MRR@10 | 0.478 | **0.714** | Qwen3-Embedding-4B |
| **Qur'an** (n=88) | Recall@1 | 0.023 | **0.045** | Qwen3-Embedding-4B (both weak) |
| | Recall@10 | 0.057 | **0.114** | Qwen3-Embedding-4B (both weak) |
| **Fiqh** (n=240) | Recall@1 | 0.583 | **0.917** | Qwen3-Embedding-4B |
| | Recall@10 | 0.796 | **0.992** | Qwen3-Embedding-4B |

**Qwen3-Embedding-4B wins decisively and consistently, on every metric and every layer, on this
project's own data.** This contradicts the DG-4 literature-based recommendation (which favored
mE5-large-instruct based on `eltanbouly2026`'s benchmark, where the only tested Qwen3-Embedding
size was 0.6B and scored below BM25). **Per DECISIONS.md DG-4's own explicit instruction, this is
grounds to revisit the primary embedding model choice — flagged to the coordinator, not
silently changed here.**

## Sanity check performed (not just a raw number)

The very low Qur'an-layer recall for both models was manually spot-checked, not assumed to be a
pipeline bug: for the query "ما هي وصايا لقمان لابنه؟" ("What is Luqman's advice to his son?"),
mE5-large-instruct's top-1 result is `quran:31:13` — the literal opening verse of the same
Luqman-advice passage the question asks about ("And [mention] when Luqman said to his son...").
The query's gold label is `quran:31:18`, a *later* verse in that same multi-ayah passage (matched
via the benchmark's own "Correction" span, which happened to quote verses 18–19specifically). The
retrieval is behaving sensibly; the harsh single-ayah exact-ID gold-matching metric under-credits
correct-passage-wrong-specific-verse hits. **This affects both models equally** (same query set,
same gold labels), so it does not bias the head-to-head comparison above, but it means the
absolute Qur'an-layer recall numbers should not be read as "the system fails 90%+ of the time" —
they measure single-verse-exact-match, a stricter bar than passage-level relevance.

## Open items for the coordinator

1. **DG-4 should be revisited with the user**: Qwen3-Embedding-4B beats mE5-large-instruct
   decisively on this project's own corpus/queries. DECISIONS.md anticipated exactly this
   possibility and requires the coordinator (not this task) to decide whether to switch the
   pipeline's primary model.
2. **Hadith retrieval is entirely unevaluated** in this pass — no reliable gold-linked Hadith
   query set could be built from currently-acquired benchmark data (see "Query set construction"
   above). Building one would need either a hadith benchmark with structured
   collection/book/number fields (not just free-text citations), or a citation-number-to-source
   mapping table for `fawazahmed0/hadith-api`'s numbering specifically — neither exists in the
   currently-acquired data. Flagged for whoever next touches retrieval evaluation (T14+).
3. **Qur'an-layer recall is low for both models even accounting for the passage-vs-verse
   granularity issue** — worth considering whether embedding both `text_ar` and a translation
   (the corpus currently embeds Qur'an on `text_ar` alone, unlike Hadith/Fiqh which embed both
   languages — see `src/rag/corpus.py`) would help; not attempted here as it's a corpus/config
   change beyond a head-to-head model comparison, but worth a follow-up experiment.
