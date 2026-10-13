# T19 Google Form: simple step-by-step guide

You do **not** need programming experience. The ready script already contains the 36 blinded
review cards, the bilingual Malay–English questions, and every answer option.

## Part A — create the form

1. Open [T19_Google_Form_READY_TO_PASTE.gs](T19_Google_Form_READY_TO_PASTE.gs) in this project.
   Select everything (`Ctrl+A`) and copy it (`Ctrl+C`). Do not edit the text.
2. In a browser, go to [script.google.com](https://script.google.com/) and sign in with the Google
   account that should own the form.
3. Choose **New project**. Delete the short example code already shown in the editor.
4. Paste the copied text (`Ctrl+V`). Click the floppy-disk icon or press `Ctrl+S`. You may name
   the project `IslamicGuard T19`.
5. At the top of the editor, open the function drop-down (it may say `myFunction`) and choose
   `createT19ScholarReviewForm`. Click **Run**.
6. On the first run, Google asks for permission because the script creates a Form in your account.
   Choose **Review permissions**, select your Google account, then choose **Allow**. If Google
   displays an “unverified app” warning, choose **Advanced** then **Go to IslamicGuard T19**;
   this is expected because the script is your own private project, not a published Google app.
7. Wait for “Execution completed.” Open **Execution log** at the bottom. Copy the two links:
   - **Edit URL** — private; use it to inspect or edit the form.
   - **Response URL** — send this to scholars.

The form has 36 cards, so creation can take a minute or two. Run the function only once; running
it again creates a second form.

## Part B — check before sending

Open the private Edit URL and check the first card. It should show the question, anonymous
answer, bilingual rating options, and comment field. The form intentionally does **not** show
model name, condition, run ID, or guardrail action.

In **Settings**:

- Ensure **Collect email addresses** is off.
- Ensure responders are not required to sign in, unless your ethics process requires it.
- Do not add name, institution, or contact fields.
- Keep the anonymous reviewer-code question. Give each scholar a random code separately, such as
  `RATER-A`, `RATER-B`, and `RATER-C`.

Before inviting scholars, submit one test response yourself. Check that the response is recorded,
then delete that test response in the Form’s **Responses** tab before sharing the live form.

## Part C — collect responses

1. Send scholars the **Response URL**, not the Edit URL.
2. Send their anonymous reviewer code in a separate message.
3. Keep the Form’s **Responses** tab open to monitor how many reviews have been submitted; do not
   inspect results by card/model while ratings are still being collected.
4. When collection is finished, open **Responses** and turn off **Accepting responses**. This
   freezes the ratings before experimental labels are unlocked.

## Part D — give the data to this project for analysis

From the Form’s **Responses** tab, click the green Google Sheets icon to create/open its response
spreadsheet. In that spreadsheet select **File → Download → Microsoft Excel (.xlsx)**.

Place the downloaded file here, using exactly this name:

```text
expert_review/incoming/T19_google_form_responses.xlsx
```

Alternatively, download a CSV and name it:

```text
expert_review/incoming/T19_google_form_responses.csv
```

That folder is ignored by Git so raw scholar ratings will not be accidentally committed. Tell me
once the file is present; I can parse it locally, check missingness, join it to the separate
blinding key only after ratings are frozen, and produce the T21 agreement/analysis outputs.
