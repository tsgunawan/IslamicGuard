# T20 — blinded scholar-review cards

- 36 randomized cards: 12 items (two per T15 stratum).
- Core paired comparison: 8B B0 and 8B B5 for every item (24 cards).
- Secondary model-size comparison: one additional B5 card per item, alternating 14B and 32B (12 cards).
- `T19_Google_Form_READY_TO_PASTE.gs` is the ready-to-paste script for the form creator. `t20_google_form_cards.json` preserves original text for the PDF; `t20_google_form_display_cards.json` removes Markdown markers because Google Forms cannot render Markdown.
- The separately generated blinding key is ignored by Git and must not be sent to raters.
- Original English/Arabic response text is preserved. The Google Form interface is bilingual Malay–English; no unvalidated translation has been introduced into rated answers.
