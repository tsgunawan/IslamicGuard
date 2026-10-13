# T19 Google Form setup

1. First obtain the blinded cards from T20. Each card must contain only `id`, `language`,
   `question`, `answer`, and `citations`; exclude model, condition, run ID, action, researcher
   notes, and any rater identity. Preserve the original answer language: do not add an
   unvalidated Malay translation that could change the object being rated. The form interface and
   rubric are bilingual academic Malay–English.
2. Open [Google Apps Script](https://script.google.com/), create a new project, and paste the
   contents of `create_t19_google_form.gs`.
3. Replace the two `CARD-EXAMPLE-*` entries in `REVIEW_CARDS` with the blinded card list. The
   script intentionally refuses to create a form if example cards remain.
4. Run `createT19ScholarReviewForm`. Google will request permission to create and manage the
   form in the project owner's Google account. Copy the logged **edit URL** and **response URL**.
5. In the Google Form settings, verify that email collection is off, response receipts are off,
   and “limit to one response” is off unless your institution requires authenticated collection.
   Do not add a name or institution field. Provide anonymous reviewer codes separately.
6. Pilot the form with placeholder cards only. After checking its readability, delete that pilot
   form and create the final form from the frozen card list. Do not change questions after real
   ratings start.
7. Export responses to a restricted spreadsheet. Keep the card-ID linkage and reviewer-code
   linkage separately; unlock model/condition labels only after ratings are frozen.

The form implements the rubric in `t19_scholar_review_protocol.md` in parallel academic Malay
and English. It creates one page per response card and prefixes every item title with the
anonymous card ID, so spreadsheet columns remain machine-readable without exposing experimental
identifiers to raters.
