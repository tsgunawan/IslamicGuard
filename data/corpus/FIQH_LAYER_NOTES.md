# Fiqh Layer — Provenance Depth Notes (T07)

DG-1 (Option B, `DECISIONS.md`) commits this project to "a narrow, curated fiqh/madhhab layer
scoped to the 4 major Sunni schools on a bounded topic set." This note records exactly what that
layer's provenance actually is, honestly, per `paper.md` §0 rule 1 (no fabrication) and §18
(sacred/source text immutability — extended here in spirit to fiqh source text).

## What the fiqh layer actually is

The fiqh layer (`data/corpus/fiqh.jsonl`) is built entirely from **FiqhQA** (Atif et al., 2025,
`atif2025` in `literature/references.csv`). Verified directly from the paper's own text
(`ref/Atif2025_...pdf`, "Dataset construction" section):

1. The authors chose the **Kuwaiti Fiqh Encyclopedia** (الموسوعة الفقهية الكويتية) as their
   primary source — described in the paper as an authoritative reference covering rulings across
   the four Sunni madhhabs.
2. Rulings were **manually extracted** from the encyclopedia by the authors, scoped to *Fiqh
   al-'Ibadat* (acts of worship), across six categories (Prayer, Fasting, Purification, Marriage
   and divorce, Hajj/Umrah, Zakat — matching the `Category` field's 6 values in the released CSV).
   This extraction step is where `Title_original` and `statement_original` come from.
3. **GPT-4o then generated question–answer pairs** for each extracted ruling, capturing each
   madhhab's position. This generated Arabic content was reviewed and validated by native Arabic
   speakers. The English version was produced by GPT-4o-translating the Arabic QA pairs, with
   subsequent manual verification/correction by human annotators.

## What this means for this project's corpus

- `title_ar` / `statement_ar` in `data/corpus/fiqh.jsonl` are the closest thing to a primary-source
  anchor this layer has — manually extracted from the encyclopedia by domain-expert-consulted
  annotators, per the origin paper. They are **not**, however, independently re-verified against
  the encyclopedia itself by this project — we have not obtained or checked the Kuwaiti Fiqh
  Encyclopedia directly.
- `madhhab_positions[].position_en` / `.position_ar` (the actual per-madhhab ruling text) are
  **LLM-generated (GPT-4o), human-reviewed paraphrases/summaries of each school's position** —
  they are not verbatim quotations from any classical fiqh text. This is a materially different
  provenance tier from `quran.jsonl`'s and `hadith.jsonl`'s canonical text fields, and the
  manuscript must not describe the fiqh layer's content the same way it describes Qur'an/Hadith
  provenance.
- Every `fiqh.jsonl` record's `provenance.content_generation_note` field states this explicitly,
  so any downstream guardrail/validator (T11–T13) that treats fiqh-layer text as "verified source
  text" the way it treats Qur'an/Hadith text would be **overclaiming** — this needs to be a
  deliberate design decision in T11–T13, not an oversight. A reasonable design (not yet decided —
  belongs to T11/T13, not T07) would be to treat `madhhab_positions` entries as "benchmark
  reference answers for evaluation" rather than "ground-truth citable source text" the way ayahs
  and hadith are.

## Open question this reveals (flagged, not resolved here)

DG-1's phrasing ("curated fiqh/madhhab layer... bounded topic set") is satisfied by what FiqhQA
provides — 121 rulings across 6 bounded categories, 4-madhhab-labelled. But if the eventual
manuscript wants to claim the guardrail performs "provenance validation" on fiqh-layer answers in
the same sense it does for Qur'an/Hadith citations, that claim would need either (a) explicit
scoping language distinguishing "citation-grade provenance" (Qur'an/Hadith) from
"benchmark-reference-grade correctness checking" (fiqh), or (b) a separate future effort to obtain
a genuine primary-source fiqh corpus (which DG-1's Option C explicitly declined, per
`DECISIONS.md`, due to the scholar-labor cost evidenced by `elmahjub2026legalbench`). This is not
a corpus-construction defect — DG-1 already anticipated and accepted this bound — but it is a
distinction the next tasks (T11 provenance validators, T13 madhhab policy) and eventually the
manuscript's Section 3.5–3.7 need to state explicitly rather than blur.
