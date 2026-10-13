# Dataset Card — IslamicEval 2025 Subtask 1 (Hallucination Detection & Correction)

- **Source:** https://github.com/qcri/IslamicEval-2025-Subtask-1 (git clone, `--depth 1`)
- **Revision (git commit):** `256e2d2d007ca5cde0f2dea6b89a45a77ee59476`, dated 2026-02-09T15:27:47+03:00
- **Acquired:** 2026-09-17, via `git clone` + manual Git-LFS object resolution (see note below),
  `scripts/download_benchmarks.py`
- **License: Apache-2.0** (explicit `LICENSE` file present in the repo — unlike Subtask 2's repo,
  which has no license file).
- **Origin:** Companion repo to `mubarak2025` (IslamicEval 2025 shared task) covering Subtask 1
  (1A: span identification of quoted Qur'an/Hadith in LLM output; 1B: citation-correctness
  validation; 1C: correction of erroneous citations to canonical text) — found via
  `sites.google.com/view/islamiceval-2025`, which links it separately from Subtask 2's GitLab repo
  (this was `data/raw/PENDING_DATASETS.md` item 3, now resolved — see that file's history).
- **Git-LFS note:** `Hadith/six_hadith_books.json` is stored via Git LFS; plain `git clone` (no
  `git-lfs` binary available in this environment — `apt install` requires a password not available
  here) only fetched the LFS *pointer* file (133 bytes). Resolved by fetching the actual object
  directly from `https://media.githubusercontent.com/media/qcri/IslamicEval-2025-Subtask-1/main/Hadith/six_hadith_books.json`
  and verifying its SHA-256 against the value declared in the LFS pointer
  (`92ba74e2847a3ac10c4ba25835bc7c16c7a449cd7594828da585437e61cca6cc`) — **match confirmed**, real
  50,444,205-byte file, not a truncated/partial download. `scripts/download_benchmarks.py`
  reproduces this exact resolution step (not a one-off manual fix).

## Contents (actually inspected, not from the README alone — README is minimal)

- **`Quran/quranic_verses.json`**: complete Qur'an, **6,236 ayahs** (the correct total count for
  the entire Qur'an — internally consistent), each `{surah_id, surah_name, ayah_id, ayah_text}`.
  Valid JSON, parsed with zero errors.
- **`Hadith/six_hadith_books.json`**: **34,994 Hadiths** across the complete canonical "Kutub
  al-Sittah" (Six Books) — BookID confirmed by inspecting each book's own title field, not
  assumed from name order:
  - BookID 1 = Sahih al-Bukhari (صحيح البخاري) — 7,410 hadiths
  - BookID 2 = Sahih Muslim (صحيح مسلم) — 7,665 hadiths
  - BookID 3 = Sunan Abi Dawud (سنن أبي داود) — 5,260 hadiths
  - BookID 4 = Jami' al-Tirmidhi (جامع الترمذي) — 4,412 hadiths
  - BookID 5 = Sunan al-Nasa'i (سنن النسائي) — 5,780 hadiths
  - BookID 6 = Sunan Ibn Majah (سنن ابن ماجه) — 4,467 hadiths
  - Row schema: `hadithID, BookID, title (book+chapter+section), hadithTxt, Matn` (`Matn` is
    `None`/empty in every row inspected so far — not populated, despite being a named field;
    worth a fuller check before relying on it).
  - **No authenticity-grading field** (no sahih/da'if/hasan label, no isnad-chain field) — this
    corpus is "the six canonically-recognized collections" as a whole, not a per-hadith graded
    corpus. **Directly relevant to DG-5 (Hadith corpus and grading policy) but does not by itself
    resolve it** — a separate grading source would be needed if per-hadith authenticity labels are
    required (e.g. for excluding da'if narrations at retrieval time). A concurrent DG-5 research
    pass (see `literature/dg5_research_notes.md`, `literature/dg5_draft_options.md`) independently
    identified `fawazahmed0/hadith-api` (Unlicense) as a candidate corpus that DOES carry real
    per-hadith multi-scholar grading — this text-only Six-Books corpus and that graded corpus are
    not yet reconciled/deduplicated against each other; that reconciliation belongs to whichever
    task actually builds the T07 corpus, not this T06 acquisition pass.
- **`dev_SubtaskA/`, `dev_SubtaskB/`, `dev_SubtaskC/`, `dev_SubtasksABC/`**: dev-set TSV+XML pairs,
  211 / 248 / 180 / 799 lines respectively (header included). Subtask A = span-level
  Ayah-vs-Hadith identification in LLM output; Subtask C includes explicit `WrongAyah`-labelled
  rows with a `Correction` column giving the canonical replacement text — **this is a ready-made,
  human-annotated misquoted-Qur'an-verse correction test set**, directly usable for `paper.md`
  §11.2 benchmark stratum #2 (deliberately misquoted Qur'an prompts) without needing to
  synthesize adversarial examples from scratch.
  - **Note:** only dev splits are present in this repo (no `test_*` directories) — test labels are
    presumably withheld by organizers, consistent with Subtask 2's withheld test qrels.
- **`Evaluation_scripts/`**: organizers' own scoring scripts for 1A/1B/1C — reusable directly.

## Relevance to this project (paper.md §11, DG-1=B, DG-5)

This is the single most directly useful acquisition in this T06 pass:
- The complete, Apache-2.0-licensed Qur'an (6,236 ayahs) and Six-Books Hadith corpus (34,994
  hadiths) are strong candidates for the **verified core** of DG-1=B's Qur'an+Hadith corpus layer
  (subject to DG-5 resolving the grading-policy question — this corpus provides the raw text, not
  a grading scheme).
- The dev-set Subtask 1A/1C data provides real (not synthetic) misquotation/hallucination examples
  with gold corrections — usable as seed material for `paper.md` §11.2 strata #2/#3/#5.
