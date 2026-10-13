# Pending Datasets / Unresolved Access (T06)

Mirrors the spirit of `literature/pending_downloads.md` — datasets identified as relevant via the
literature corpus that could not be lawfully/fully obtained in this pass. Not silently dropped.

## 1. IslamicMMLU (Abdelaal et al., 2026 — `abdelaal2026` in `literature/references.csv`)

- **What's public:** a live leaderboard Space at
  `https://huggingface.co/spaces/islamicmmlu/leaderboard`, and a small `islamicmmlu/results`
  dataset repo (287 downloads, parquet, `size_categories:n<1K`) containing **leaderboard result
  rows** (per-model scores), not the underlying 10,013-question MCQ item bank itself.
- **What's NOT public (as far as this search could determine):** the actual question/answer/option
  content for the 10,013 MCQs (2,013 Qur'an / 4,000 Hadith / 4,000 Fiqh tracks) described in the
  paper. Checked: `huggingface.co/islamicmmlu` org (only the `results` and `leaderboard` repos
  exist), the paper's own PDF text (only the leaderboard Space URL appears, no dataset repo URL).
- **Why this matters:** this is exactly the kind of benchmark DG-1=B's chosen corpus scope (4
  madhhabs, Qur'an+Hadith+fiqh) would want to draw on or compare against, and a live/blind
  leaderboard-only release (no public test set) is a deliberate contamination-prevention design
  choice by the authors, not an oversight — worth noting in the eventual manuscript's
  data-leakage discussion (`paper.md` §11.4) as a design pattern to consider adopting.
- **Next step if needed:** contact the authors (emails likely in the PDF's author block, not
  extracted in this pass) to request research access to a held-out subset, or use the public
  leaderboard API purely as an external comparison point (model scores only, no item-level data)
  rather than as a corpus/benchmark source.

## 2. IslamicLegalBench public dev-set release (Elmahjub et al., 2026 — `elmahjub2026legalbench`)

- **What the paper states:** "We release 20% of IslamicLegalBench publicly as a development set,
  maintaining 80% held-out to preserve evaluation integrity and prevent data contamination"
  (verified quote, extracted directly from the PDF).
- **What could not be found:** no URL, GitHub/HuggingFace repo, or supplementary-materials link
  for this release was found anywhere in the PDF's extracted text (checked all `http`/`www.`
  occurrences in the reference list and body). The paper may link it via a footnote/hyperlink not
  captured by `pdftotext -layout`, an anonymous-review supplementary link not yet deanonymized, or
  a release that postdates this PDF snapshot.
- **Next step if needed:** re-check the paper's actual rendered PDF for embedded hyperlinks
  (`pdftotext`'s text-layer extraction can miss link annotations that have no visible URL text),
  or search HuggingFace/GitHub directly for "IslamicLegalBench" by name in a follow-up pass.
- **Relevance:** this is the broader 7-school, 38-text, 718-instance benchmark that DG-1 explicitly
  decided NOT to match in scope (Option C was rejected in favor of Option B's narrower 4-madhhab
  layer) — so obtaining this is lower priority than IslamicMMLU/FiqhQA, useful mainly as an
  external comparison/stress-test set, not as this project's primary corpus source.

## 3. IslamicEval 2025 Subtask 1 — RESOLVED

Initially thought missing; found and obtained during this same T06 pass by checking the shared
task's own site (`sites.google.com/view/islamiceval-2025`), which links Subtask 1's data
separately from Subtask 2's GitLab repo: `https://github.com/qcri/IslamicEval-2025-Subtask-1`
(Apache-2.0 licensed). See `data/raw/islamiceval_subtask1/DATASET_CARD.md` for full details —
includes a complete 6,236-ayah Qur'an, a 34,994-hadith Six-Books corpus, and dev-set
misquotation/correction examples. Kept here (struck through in spirit, not deleted) for audit-trail
continuity: the third-party mirror `github.com/sakher/IslamicEval-BurhanAI-Public` mentioned during
the search was NOT used once the organizers' own repo was found.
