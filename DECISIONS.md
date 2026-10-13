# Decision Log

Records the outcome of every Decision Gate defined in `paper.md` §2, in the order resolved.
Each entry: gate, date, options presented, decision, rationale, and downstream consequences.
This file is the durable record — `STATUS.md` only summarizes current state.

---

## DG-1 — Islamic source corpus scope

- **Date:** 2026-09-17
- **Options presented:** A (Qur'an + Hadith only) / B (Qur'an + Hadith + narrow 4-madhhab fiqh
  layer, bounded topic set) / C (Qur'an + Hadith + broad staged fiqh corpus toward
  IslamicLegalBench-style breadth). Full evidence basis: `literature/dg1_draft_options.md`.
- **Decision: B.**
- **Rationale:** Only option that supports RQ4 (madhhab-sensitive reliability, already in-scope
  per `paper.md` §1.3) while matching this project's committed 3-scholar validation capacity
  (`paper.md` §1.5) — directly comparable to Atif et al. (2025) FiqhQA's precedent (4 madhhabs,
  achieved without large-scale scholar-labor investment), unlike Option C's IslamicLegalBench-style
  breadth (Elmahjub et al., 2026), which required 44 scholars for corpus construction alone.
- **Downstream consequences:**
  - **DG-6 (madhhab coverage) is resolved as a direct implication of this choice**: "four Sunni
    madhhabs only" (Hanafi, Maliki, Shafi'i, Hanbali) on a bounded topic set — this is Option B's
    literal scope, not a separate open question. Recorded here rather than re-litigated as its own
    gate; flagged to the user for visibility rather than silently assumed (per `paper.md` §0 rule 7).
  - Corpus construction (T07) now has a fixed target: verified Qur'an + Hadith core, plus a
    separately labelled fiqh layer bounded to 4 madhhabs on a bounded topic set (topic set itself
    still to be defined during T07/benchmark design, informed by FiqhQA's category structure).
  - RQ1–RQ4 are all now supportable within the committed scholar-validation budget.
  - Option A (Qur'an+Hadith only) and Option C (broad multi-school) are both explicitly rejected
    for this paper; Option C's staged/broader ambition is noted as a plausible follow-up-paper
    direction (see `paper.md` §1.3's out-of-scope list and DG-1 draft's Option C discussion),
    not pursued now.
  - **Still open:** DG-5 (Hadith corpus and grading policy — exact collections, translations,
    authenticity metadata, disputed-grading handling) is a separate, unresolved gate that T07
    still requires before finalizing the corpus. Not answered by this decision.

---

## DG-5 — Hadith corpus and grading policy

- **Date:** 2026-09-17
- **Options presented:** A (Sahih al-Bukhari only, no grading layer needed) / B (full six-book
  Sunni canon via `fawazahmed0/hadith-api`, Unlicense, multi-scholar grading preserved as
  metadata rather than collapsed to one label) / C (full six-book canon pre-filtered to
  Sahih/Hasan-only per one reference scholar, e.g. Al-Albani). Full evidence basis:
  `literature/dg5_research_notes.md`, `literature/dg5_draft_options.md`.
- **Decision: B.**
- **Rationale:** Matches the fiqh-layer breadth already committed under DG-1 (fiqh rulings cite
  hadith beyond Bukhari — Abu Dawud, Tirmidhi, etc.); source license and content (exact
  collections, real per-hadith multi-scholar grading, e.g. Ibn Majah's documented Al-Albani vs.
  Al-Arnaut vs. Zubair Ali Zai disagreements) were directly inspected, not assumed; keeps the
  system's guardrail role to *surfacing* authenticity/disagreement rather than *resolving* it by
  picking one muhaddith's grading over another (`paper.md` §0 rule 17).
- **Downstream consequences:**
  - T07's Hadith corpus source is fixed: `fawazahmed0/hadith-api` (six-book canon: Bukhari,
    Muslim, Abu Dawud, Tirmidhi, Nasa'i, Ibn Majah), Arabic + English, with per-hadith grading
    stored as a list-of-{scholar, grade} rather than a single field.
  - The corpus schema must support multi-value grading per hadith (a real but modest engineering
    requirement flagged in the draft options).
  - **Known limitation to carry into the manuscript**: the source's own metadata lists English
    translator attribution as `"Unknown"` for every collection — any English rendering served to
    users must be labelled "translation, translator unconfirmed," not presented as authoritative.
    Canonical Arabic text is unaffected (traces unambiguously to its classical compiler).
  - T07 should cross-check this source against the six-book Hadith corpus already bundled with
    the IslamicEval dataset acquired in T06 (34,994 hadiths, book-by-book counts verified) — use
    whichever actually carries the multi-scholar grading metadata DG-5=B requires, or merge/
    reconcile both if they diverge; do not assume they are identical without checking.
  - Option A (Bukhari-only) and Option C (single-scholar pre-filtering) are both explicitly
    rejected for this paper.

---

## DG-4 — Retrieval embedding model

- **Date:** 2026-09-17
- **Options presented:** A (BGE-M3) / B (multilingual-e5-large-instruct) / C (Qwen3-Embedding).
  Full evidence basis: `literature/dg4_research_notes.md`, `literature/dg4_draft_options.md` —
  grounded in `eltanbouly2026`'s 8-model zero-shot Arabic-fiqh-retrieval benchmark (MRR@5) and
  `bhatia2026`'s direct precedent (mE5-base beating BM25 on bilingual Qur'an RAG).
- **Decision: hybrid — B now, C's larger variants benchmarked during T08 before ruling out.**
  - **Primary retrieval embedding model: multilingual-e5-large-instruct** (MIT license).
    Strongest zero-shot MRR@5 (0.4822) among clearly-licensed candidates on the most relevant
    available benchmark, with a direct precedent in this exact project's Qur'an-RAG use case.
  - **Not closed off: Qwen3-Embedding's larger variants (4B/8B)** are explicitly unverified for
    this task (only the 0.6B size was benchmarked in `eltanbouly2026`, and it scored *below* the
    BM25 lexical baseline — a real negative signal, not just an absence of data). T08's own
    retrieval evaluation (paper.md §7's "retrieval metrics reported on a held-out query set"
    acceptance criterion) must include a real benchmark run of at least one larger Qwen3-Embedding
    variant against mE5-large-instruct on this project's actual corpus, using real measured
    numbers — not an assumption that model-size scaling will close the gap. If a larger
    Qwen3-Embedding variant outperforms mE5-large-instruct on this project's own held-out
    retrieval evaluation, that is grounds to revisit this decision; if not, mE5-large-instruct
    remains primary.
  - **Option A (BGE-M3) is not chosen as primary** — verified license and best tooling ecosystem,
    but evidenced as mid-pack (not top) zero-shot performance on the one directly relevant
    benchmark found. Not ruled out as a secondary/comparison baseline if useful during T08.
- **Downstream consequences:**
  - T08 (retrieval system) implementation should default to multilingual-e5-large-instruct for
    the embedding/index pipeline, but its evaluation step is now explicitly scoped to include a
    head-to-head comparison against at least one larger Qwen3-Embedding variant on this project's
    own corpus and query set, with results reported plainly (whichever wins).
  - Fine-tuning any candidate embedding model is out of scope for the near term — the fiqh layer
    (121 records) is far short of the ~19,000+ triplets `eltanbouly2026` used to get meaningful
    fine-tuning gains; T08 should use zero-shot models as-is.

### DG-4 REOPENED and REVISED — 2026-09-17 (same day, after T08's own evaluation)

- **Trigger:** T08's mandated head-to-head evaluation (`results/tables/t08_retrieval_eval.md`),
  run on this project's own corpus (6,236 Qur'an / 34,157 Hadith / 121 fiqh records) and a
  held-out query set (328 real query→gold pairs, honestly accounted — see T08 entry in
  `STATUS.md` for exact drop counts), found **Qwen3-Embedding-4B beats mE5-large-instruct
  decisively on every metric and every evaluated layer**: overall Recall@1 0.683 vs. 0.433;
  overall MRR@10 0.714 vs. 0.478; fiqh Recall@1 0.917 vs. 0.583. Spot-checked (not just accepted
  at face value) to rule out a pipeline bug — confirmed real. This directly contradicts the
  literature-based prediction the original DG-4 decision was grounded in (which used a different
  paper's benchmark testing only the 0.6B Qwen3-Embedding size).
- **New options presented:** A (switch primary to Qwen3-Embedding-4B outright) / B (keep
  mE5-large-instruct despite this result, pending a larger/more balanced query set) / C (switch to
  Qwen3-Embedding-4B now, treat as provisional, revisit once a hadith-layer eval set exists).
- **Decision: C.**
- **Rationale:** The evidence for fiqh/overall retrieval is real and decisive, but the eval set
  has two acknowledged gaps: it's fiqh-heavy (240/328 pairs) and **Hadith retrieval is entirely
  unevaluated** (0 hadith pairs — IslamicFaithQA's hadith citation-numbering convention doesn't
  match `fawazahmed0/hadith-api`'s internal numbering, and forcing a fuzzy match was correctly
  refused rather than fabricated). Switching now captures the real, measured fiqh/overall gain
  without pretending hadith-layer performance is known.
- **Downstream consequences:**
  - **Pipeline default is now Qwen3-Embedding-4B** for the embedding/index pipeline
    (`config/retrieval.yaml`, `scripts/build_index.py` outputs) — this needs to be made the
    actual default in code (not just documented), i.e. the RAG pipeline components built in T09+
    must default to querying the Qwen3-Embedding-4B index, not mE5's.
  - Indexing cost is higher for this model (~22 min for the hadith layer alone vs. mE5's ~82s for
    the full corpus in T08's run) and needed a batch-size/context-length workaround for a CUDA OOM
    (`max_seq_length=1024`, `batch_size=8` — documented in `src/rag/embed.py`). This is an
    accepted, not hidden, operational cost.
  - **Explicit revisit trigger**: once a reliable hadith-layer retrieval eval set exists (this
    needs either a hadith benchmark with structured collection/book/number fields, or a
    citation-number-to-source mapping table for `fawazahmed0/hadith-api`'s specific numbering —
    neither exists yet; flagged for T14+), re-run this comparison including hadith and confirm
    Qwen3-Embedding-4B still wins before treating this decision as final rather than provisional.
  - mE5-large-instruct's index/build path should remain available (already built once in T08) as
    a comparison baseline, not deleted, in case the hadith-layer re-check changes the outcome.

---

## DG-2 — Primary inference engine

- **Date:** 2026-09-18
- **Options presented:** A (Transformers-only) / B (vLLM-only) / C (hybrid — Transformers for
  debugging/validation, vLLM for high-throughput runs).
- **Decision: C (hybrid).** Confirmed explicitly after an initial ambiguous "A" answer was
  clarified with the user rather than assumed (the user's first reply answered a combined DG-2+
  DG-3 prompt with a single letter; DG-2 and DG-3 were re-confirmed separately to avoid silently
  picking the non-recommended option for DG-2).
- **Rationale:** Both Transformers and vLLM are already installed and validated working in the
  `islamicguard` conda env (T01); Transformers was already used successfully for T02's smoke
  tests. Matches paper.md's own original recommendation and avoids forcing a throughput/
  debuggability trade-off — T09's baseline pipeline should be written with a swappable backend.
- **Downstream consequences:**
  - T09 (baseline generation pipeline) should support both backends behind one interface.
  - Debugging/validator-development work (T11-T13) should default to the Transformers path for
    single-response inspection; large-scale runs (T15-T17) should default to vLLM for throughput.

---

## DG-3 — Qwen3 reasoning mode

- **Date:** 2026-09-18
- **Options presented:** A (non-thinking primary) / B (thinking primary) / C (both, reported
  separately).
- **Decision: A (non-thinking primary).**
- **Rationale:** T02's smoke tests already measured thinking mode's real cost in this
  environment: all three models generated in Qwen3's default thinking mode, and 128
  `max_new_tokens` was insufficient for any of them to finish reasoning and emit a final answer
  (see `results/tables/t02_smoke_test_summary.md`). Non-thinking as primary keeps B0-B5 answers
  comparable under one fixed generation budget; matches paper.md's original recommendation.
- **Downstream consequences:**
  - T09's baseline pipeline must explicitly force non-thinking mode via Qwen3's chat template
    (not just rely on a shorter `max_new_tokens` — the mode itself needs to be set), and record
    which mode was used in every response's generation-config metadata.
  - Thinking mode is not eliminated from the project — it remains available as a secondary
    sensitivity study (paper.md §8.6) if compute permits after the primary experiments, but must
    never be silently mixed with non-thinking results in a single headline comparison
    (paper.md §8.6's explicit prohibition).

---

## DG-7 — Benchmark size and composition

- **Date:** 2026-09-20
- **Options presented:** A (minimum viable, ~40-50 items, 6-8 high-value strata) / B (standard,
  ~120-150 items, most/all 14 candidate strata) / C (extended + adversarial, ~250-300+ items,
  full strata plus a dedicated T17 adversarial subset). Evidence basis: T09/T10/T14's real
  per-item timing (Qwen3-8B: B0 24s, B1 18s, B2/B5-gen 41.5s; 14B-AWQ/32B-AWQ numbers from T10's
  single run, flagged as unconfirmed at combined-pipeline scale).
- **Decision: A (minimum viable).**
- **Rationale:** 32B-AWQ's real combined-pipeline cost is not yet confirmed (T10's 212s/item RAG
  figure was flagged as plausible-but-unaudited); the account has already hit its spend limit
  once this session (see T10 completion in `STATUS.md`); a working minimum-viable benchmark
  end-to-end gives real numbers to decide whether to scale to B or C afterward, rather than
  committing an estimated 30-80 GPU-hours before confirming the pipeline behaves at scale.
- **Downstream consequences:**
  - **T15 (full Qwen3-8B ablation, B0-B5) and T16 (model-size experiment, B0/B2/B5 × 3 models)
    should target ~40-50 items**, stratified across 6-8 of paper.md §11.2's 14 candidate strata
    — prioritize: correct Qur'an/Hadith quotation, deliberately misquoted, fabricated
    citation/attribution, madhhab-sensitive/ikhtilaf, insufficient-context (abstention target),
    and benign-must-not-refuse (over-refusal check). The remaining strata (personal-fatwa/
    escalation, prompt-injection, source-conflict, etc.) are deferred to Option B/C scale-up or
    to T17's dedicated adversarial subset, not silently dropped from the paper's scope — they
    still need at least minimal coverage somewhere before the paper claims to address them.
  - **Explicit revisit trigger**: once T15/T16 run at this minimum-viable scale and produce real
    GPU-hour figures (especially for 32B-AWQ's actual combined-pipeline cost), the coordinator
    should re-evaluate whether scaling to B or C is practical before finalizing T17+ and the
    manuscript's benchmark-size claims. This is a deliberately staged decision, not a final one.
  - T17 (adversarial/prompt-injection evaluation) still needs its own attack taxonomy and
    success-definition decision (per paper.md §15 T17) regardless of which DG-7 tier is chosen —
    not resolved by this decision.

## DG-9 — Main statistical test

- **Date:** 2026-09-30
- **Options presented:** paired bootstrap + McNemar / mixed-effects regression / both with
  bootstrap primary.
- **Decision: item-level paired bootstrap confidence intervals + exact McNemar, Holm-corrected.**
- **Rationale:** every condition answers the same items, so comparisons are paired on item;
  resampling whole items respects the nesting (responses within items, raters within cards). At
  n=41 benchmark items and n=12 scholar-rated items, mixed-effects models would be unstable.
- **Downstream consequences:** `scripts/t22_statistical_comparison.py` fixes the comparison
  families (automated binary, automated continuous, scholar B0-vs-B5) and applies Holm within
  each. Effect sizes and absolute differences are reported alongside p-values. Intervals reflect
  item sampling only (one seed, one benchmark draw); the manuscript must say so.

## DG-10 — Final IJEEI reference formatting

- **Date:** 2026-09-30
- **Decision:** keep APA author-date in the manuscript; the user will edit manually later. The
  IJEEI template asks for numbered IEEE style, so conversion may still be needed at submission.

## DG-12 — Release scope

- **Date:** 2026-09-30
- **Decision:** no public release yet. Code, configurations, prompts, benchmark items, run outputs
  and anonymised scholar ratings are available from the corresponding author on reasonable
  request; public release may follow later. The manuscript's availability statement says this.

## Manuscript focus and title (JournalPrompt.txt revision)

- **Date:** 2026-09-30
- **Decisions by the user:** (1) build the paper around the scholar audit of the guardrail
  layers as the single strongest contribution; (2) keep the working title unchanged; (3) swap a
  few references within the 30-reference cap (4 weak ones dropped, 4 verified method references
  added; 29 total).
- **Consequence:** the draft was restructured into six sections (Introduction, Related Work,
  Methodology with formal notation and Algorithm 1, Results and Analysis, Discussion, Conclusion).
  No result changed.

### DG-12 update — 2026-09-30

The authors decided to release publicly at https://github.com/tsgunawan/IslamicGuard. The manuscript's
availability statement and `CITATION.cff` now name that URL. The repository had not been created
or pushed at the time of this entry; see `RELEASE.md` for the remaining steps and decisions.
