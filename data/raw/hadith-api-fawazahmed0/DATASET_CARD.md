# Dataset Card — fawazahmed0/hadith-api (six-book canon, graded)

- **Source:** https://github.com/fawazahmed0/hadith-api, fetched via the project's own jsDelivr
  CDN mirror (`cdn.jsdelivr.net/gh/fawazahmed0/hadith-api@1/...`), which is the access method the
  project's own README documents for bulk use.
- **License:** Unlicense (public domain dedication) — stated in the source repository.
- **Acquired:** 2026-09-17, via `scripts/build_corpus.py` (direct HTTPS fetch, `curl`).
- **Files:** `editions.json` (edition/collection index) + 12 per-book files: `{eng,ara}-{bukhari,
  muslim,abudawud,tirmidhi,nasai,ibnmajah}.json`. SHA-256 of every file in `MANIFEST.sha256`.
- **Why this source (DG-5 decision):** Selected in Decision Gate DG-5 (`DECISIONS.md`) specifically
  because it carries real per-hadith **multi-scholar grading** (a `grades: [{name, grade}, ...]`
  array), verified directly here, not assumed:
  - Bukhari: 7,589 hadiths, **0 with any grading** (`grades: []` on every record) — consistent
    with Bukhari/Muslim being treated as collection-authenticated by consensus rather than
    individually graded by later muhaddithin.
  - Ibn Majah: 4,343 hadiths; spot-checked hadith #1 carries 4 scholars' grades (Al-Albani,
    Muhammad Fouad Abd al-Baqi, Shuaib Al-Arnaut, Zubair Ali Zai — all "Sahih"), hadith #6 shows
    real disagreement in wording ("Sahih" vs. "Isnaad Sahih" across scholars) — grading is
    genuinely per-hadith and genuinely multi-scholar, not a single collapsed label.
- **Known limitation (documented in DG-5, carried here):** every edition's `author` field in
  `editions.json` is literally `"Unknown"` for the English translations — translator attribution
  is unconfirmed. Arabic text traces unambiguously to the classical compilation; English rendering
  does not carry a named, verifiable translator. `data/corpus/hadith.jsonl` records
  `translator: "unknown"` on every English field per this finding — not omitted, not presented as
  authoritative.
- **Cross-check against `data/raw/islamiceval_subtask1/Hadith/six_hadith_books.json` (T06):**
  performed in `scripts/build_corpus.py` / documented in `data/corpus/SCHEMA.md` — book-level
  hadith counts do **not** match exactly between the two sources (e.g. this source's Bukhari =
  7,589 vs. IslamicEval bundle's Bukhari = 7,410), consistent with different chapter-numbering/
  de-duplication conventions across hadith digitization projects, not a data-quality defect in
  either. This source (fawazahmed0) is used as the corpus base because it is the only one of the
  two carrying grading metadata; the IslamicEval bundle's Arabic hadith text is used as an
  independent cross-check sample only, not merged wholesale (see `data/corpus/SCHEMA.md` for the
  reconciliation approach actually taken).
