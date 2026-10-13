# Corpus Schema (T07)

Three JSONL files under `data/corpus/`, built by `scripts/build_corpus.py` from datasets acquired
in T06 and the sources fixed by DG-1 (`DECISIONS.md`, Option B: Qur'an + Hadith + narrow 4-madhhab
fiqh layer) and DG-5 (`DECISIONS.md`, Option B: full six-book Hadith canon with multi-scholar
grading preserved). Per `paper.md` §18: canonical text fields are never altered; every normalized
field is a separate, clearly-named derived field.

Not committed to git as raw JSONL (see `.gitignore` — mirrors the `data/raw/` policy of tracking
cards/manifests, not bulk third-party-derived content); reproduce with
`python scripts/build_corpus.py`.

## `quran.jsonl` — 6,236 records (one per ayah; matches the known total ayah count for the
complete Qur'an)

| Field | Type | Notes |
|---|---|---|
| `id` | str | `quran:<surah_id>:<ayah_id>` |
| `surah_id` | int | 1–114 |
| `surah_name` | str | Arabic surah name as given by the source |
| `ayah_id` | int | Ayah number within the surah |
| `text_ar` | str | **Canonical, immutable** Arabic ayah text, untouched from source |
| `text_ar_normalized` | str | Diacritics-stripped, tatweel-stripped, whitespace-normalized — for fuzzy/matching use only, never a substitute for `text_ar` |
| `provenance.dataset` | str | Source dataset name |
| `provenance.source_file` | str | Path within the source repo |
| `provenance.source_git_commit` | str | Exact commit hash of the source repo at acquisition time |
| `provenance.source_sha256` | str | SHA-256 of the raw source file |
| `provenance.license` | str | Apache-2.0 |

Source: `data/raw/islamiceval_subtask1/Quran/quranic_verses.json` (from Mubarak et al., 2025,
IslamicEval 2025 Subtask 1 companion repo — see its `DATASET_CARD.md`). 0 records dropped.

## `hadith.jsonl` — 34,157 records written, 375 dropped (see below), across the full six-book
Sunni canon

| Field | Type | Notes |
|---|---|---|
| `id` | str | `hadith:<collection_key>:<hadith_number>` |
| `collection` | str | Full collection name, e.g. "Sunan Ibn Majah" |
| `collection_key` | str | Short key: `bukhari`, `muslim`, `abudawud`, `tirmidhi`, `nasai`, `ibnmajah` |
| `book_section` | str | Section/chapter title from the source's own section index |
| `hadith_number` | int | Sequential hadith number within the collection (source's `hadithnumber`) |
| `arabic_number` | int\|null | Source's `arabicnumber` field, where present |
| `text_ar` | str\|null | **Canonical, immutable** Arabic text. `null` only when the Arabic edition has no matching `hadithnumber` (rare; not observed in this build — every English record found a matching Arabic record) |
| `text_ar_normalized` | str\|null | Diacritics-stripped normalized form, derived only, never replaces `text_ar` |
| `text_en` | str | English rendering |
| `translator` | str | **Always `"unknown"`** — the source's own metadata lists every English edition's translator as `"Unknown"` (see `data/raw/hadith-api-fawazahmed0/DATASET_CARD.md` and `DECISIONS.md` DG-5). English text must not be presented as an authoritative translation without this caveat. |
| `grading` | list\|str | Either a list of `{"scholar": ..., "grade": ...}` objects (multi-scholar grading, **not** collapsed to one label — DG-5's explicit requirement), or the literal string `"collection-authenticated (no individual grading in source)"` for Bukhari/Muslim, which carry no individual grading in this source |
| `provenance.dataset` | str | `fawazahmed0/hadith-api` |
| `provenance.source_files` | list[str] | The eng/ara edition filenames used |
| `provenance.source_sha256` | dict | SHA-256 per source file |
| `provenance.license` | str | Unlicense |

Source: `data/raw/hadith-api-fawazahmed0/{eng,ara}-{book}.json` (fetched live by
`scripts/build_corpus.py`, per DG-5's Option-B decision). Per-book record counts and drop counts:

| Book | fawazahmed0 EN count | Written | Dropped (empty `text`) |
|---|---:|---:|---:|
| Bukhari | 7,589 | 7,580 | 9 |
| Muslim | 7,563 | 7,360 | 203 |
| Abu Dawud | 5,274 | 5,272 | 2 |
| Tirmidhi | 3,998 | 3,926 | 72 |
| Nasa'i | 5,765 | 5,679 | 86 |
| Ibn Majah | 4,343 | 4,340 | 3 |
| **Total** | **34,532** | **34,157** | **375** |

**Dropped rows are a real, verified source-data property, not a bug in this build**: spot-checked
directly against `data/raw/hadith-api-fawazahmed0/eng-muslim.json` — e.g. hadith numbers 1, 2, 5
in Muslim have `"text": ""` in the source itself (confirmed by direct inspection). Not silently
discarded — counted here per `paper.md` §18's "no silent dataset-row dropping" requirement.

### Cross-check against the IslamicEval T06 bundle (`data/raw/islamiceval_subtask1/Hadith/six_hadith_books.json`)

Per `DECISIONS.md` DG-5's explicit instruction to check rather than assume the two Hadith sources
are identical:

| Book | fawazahmed0 (this corpus) | IslamicEval bundle (T06) |
|---|---:|---:|
| Bukhari | 7,589 | 7,410 |
| Muslim | 7,563 | 7,665 |
| Abu Dawud | 5,274 | 5,260 |
| Tirmidhi | 3,998 | 4,412 |
| Nasa'i | 5,765 | 5,780 |
| Ibn Majah | 4,343 | 4,467 |

**Counts do not match exactly for any book.** This is consistent with different hadith
digitization projects using different chapter-splitting/de-duplication conventions (both are
legitimate digitizations of the same six canonical works, not evidence either is corrupted) — not
independently confirmed further in this pass (would require a hadith-by-hadith text-similarity
match, out of scope for T07). **Decision made here:** the corpus uses `fawazahmed0/hadith-api` as
the sole base (per DG-5=B, chosen specifically for its grading metadata, which the IslamicEval
bundle lacks entirely — see its own `DATASET_CARD.md`: "No authenticity-grading field"). The
IslamicEval bundle is *not* merged in, to avoid silently mixing two different digitization
conventions into one corpus; it remains available in `data/raw/` as an independent source, e.g.
for cross-validating the provenance validator (T11) against a differently-sourced text.

## `fiqh.jsonl` — 121 records (one per FiqhQA ruling), 0 dropped

| Field | Type | Notes |
|---|---|---|
| `id` | str | `fiqh:<row_index>` |
| `category` | str | One of: Prayer, Purity, Marriage, Fast, Hajj/Omra, Zakat (the "bounded topic set" DG-1=B specifies) |
| `title_ar` / `statement_ar` | str | Original Arabic ruling title/statement, manually extracted from the Kuwaiti Fiqh Encyclopedia by the FiqhQA authors — treat as **secondary/curated**, not a raw primary-source scan (see `FIQH_LAYER_NOTES.md`) |
| `statement_ar_normalized` | str | Derived normalized form of `statement_ar` |
| `title_en` / `statement_en` | str | English rendering (dataset-provided) |
| `agreement` | str | `"Agreement"` or `"Disagreement"` — whether the 4 madhhabs concur on this ruling (ready-made ikhtilaf label) |
| `question_en` / `question_ar` | str | The benchmark question form |
| `madhhab_positions` | list | One entry per madhhab with an available answer: `{"madhhab": ..., "position_en": ..., "position_ar": ...}`. **`position_en`/`position_ar` are GPT-4o-generated text, native-speaker reviewed — not verbatim primary-source quotations.** |
| `provenance.dataset` | str | `FiqhQA (Atif et al., 2025)` |
| `provenance.primary_source` | str | Kuwaiti Fiqh Encyclopedia |
| `provenance.content_generation_note` | str | Explicit statement of the generation pipeline (see above) |
| `provenance.source_sha256` | dict | SHA-256 of the two source CSVs |
| `provenance.license` | str | MIT |

Source: `data/raw/FiqhQA/FiqhQA - {English,Arabic}.csv`. See `FIQH_LAYER_NOTES.md` for the
important provenance-depth caveat on this layer.

## Normalization function

`normalize_arabic()` in `scripts/build_corpus.py`: NFC-normalizes, strips Arabic diacritics
(harakat) in range U+064B–U+0652 plus related combining marks, strips tatweel (U+0640), and
collapses whitespace. Applied only to produce `*_normalized` fields; never mutates the canonical
`text_ar`/`statement_ar` fields (`paper.md` §18).
