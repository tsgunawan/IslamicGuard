# T23 — Error analysis

Scope: (1) a failure taxonomy applied to the 36 scholar-rated cards (12 items x 8B B0, 8B B5, one 14B/32B B5);
(2) pipeline-level checks over all 41 benchmark items in seven configurations.

**How to read this.** Counts and scholar ratings are evidence. The category assigned to each card is a manual coding by the
project's coding agent (one coder, not a scholar), based on the answer text and the scholars' comments; a card can carry several codes.
Statements under 'Hypotheses' are explanations that the data are consistent with but do not establish.

## 1. Taxonomy

| Code | Failure type | Definition |
|---|---|---|
| F1 | Fabricated scripture text | Wording presented as a Qur'an verse or hadith that is not the text of the cited source. |
| F2 | Wrong-but-real citation | A reference that exists but does not say what the answer claims, or concerns a different event or person. |
| F3 | Wrong core answer | The main factual answer is incorrect (wrong verse, wrong prophet, or a false claim about what the Qur'an addresses). |
| F4 | Omission of the directly relevant evidence | Answer is incomplete or leaves out the text a scholar considers the primary evidence. |
| F5 | Source-type or source-identity confusion | Qur'an called hadith, al-Fatihah called al-Baqarah, Biblical or internal-dataset sources used as the Islamic reference. |
| F6 | Fiqh misstatement or overgeneralisation | School positions misstated, false consensus claimed, or a legal category confused. |
| F7 | Unsupported attribution or accepted false premise | Views credited to a named authority without a source, or a ruling asserted for a body whose position is unknown. |
| F8 | Degenerate or truncated generation | Repetition loop, or answer cut off at the token limit before its conclusion. |
| F9 | Added narrative detail or mistranslation | Invented story details, inaccurate translation/transliteration, or a garbled retelling. |
| G1 | Guardrail: False pass | scholars judged the answer bad (mean severity >= 2) and B5 passed it. |
| G2 | Guardrail: Intervention on an acceptable answer | B5 abstained or asked for regeneration although scholars did not judge it bad (answers that themselves decline are excluded). |
| G3 | Guardrail: Verified wrong citation | the validator marked a wrong-but-real citation as verified. |

## 2. Failure counts on the scholar-rated cards (evidence + coding)

| Code | Failure type | 8B B0 (12 cards) | 8B B5 (12) | 14B/32B B5 (12) | All (36) | Mean scholar severity when present | When absent |
|---|---|---:|---:|---:|---:|---:|---:|
| F1 | Fabricated scripture text | 6 | 1 | 1 | 8 | 2.62 | 1.66 |
| F2 | Wrong-but-real citation | 1 | 2 | 2 | 5 | 2.48 | 1.77 |
| F3 | Wrong core answer | 3 | 3 | 2 | 8 | 2.66 | 1.65 |
| F4 | Omission of the directly relevant evidence | 1 | 3 | 3 | 7 | 2.17 | 1.80 |
| F5 | Source-type or source-identity confusion | 2 | 3 | 1 | 6 | 2.04 | 1.84 |
| F6 | Fiqh misstatement or overgeneralisation | 3 | 2 | 1 | 6 | 1.58 | 1.93 |
| F7 | Unsupported attribution or accepted false premise | 2 | 0 | 0 | 2 | 2.04 | 1.86 |
| F8 | Degenerate or truncated generation | 6 | 3 | 0 | 9 | 2.41 | 1.69 |
| F9 | Added narrative detail or mistranslation | 1 | 3 | 1 | 5 | 1.68 | 1.90 |
| – | No content failure coded | 0 | 1 | 4 | 5 | 0.85 | 2.04 |

Severity: 0 = none, 3 = major, mean of the scholars' ratings.

## 3. Guardrail outcomes on the 24 rated B5 cards (evidence)

| B5 action | Cards | Scholar-bad | Not scholar-bad |
|---|---:|---:|---:|
| abstain | 6 | 2 | 4 |
| escalate | 2 | 1 | 1 |
| pass | 10 | 3 | 7 |
| regenerate_with_evidence | 6 | 3 | 3 |

- **G1 false passes (3):** T19-018 (32B B5; F1+F3+F4), T19-030 (8B B5; F1+F3+F4+F8), T19-028 (8B B5; F5+F4+F8).
- **G2 interventions on acceptable answers (5):** T19-036 (8B B5; F9), T19-029 (8B B5; F9), T19-027 (32B B5; F9), T19-020 (14B B5; no content failure), T19-035 (8B B5; F6).
- **G3 wrong-but-real citations marked verified (3):** T19-003 (8B B5; F2), T19-010 (14B B5; F2), T19-033 (8B B5; F5).
- Two of the G2 cards (T19-020, T19-035) were sent for regeneration because madhhab plurality was not surfaced; E1's comment on T19-035 makes the same point (many jurists hold the beard obligatory), so that flag has scholar support even though the answers were rated acceptable.
- T19-007 and T19-023 were abstentions on answers that themselves said the evidence was missing; they are not counted as G2.
- Both `escalate` cards were the personal-ruling item. All four scholars chose escalation for T19-033 and one did for T19-011. Both answers contain a source-identity error (F5); T19-011 was judged bad, and T19-033 fell just below the threshold.

## 4. Pipeline-level checks on all 41 items per configuration (evidence)

| Configuration | Hit the 512-token limit | Repetition loop | Arabic answers | Arabic answers with zero citations extracted by T11 | English-question answers with zero citations extracted |
|---|---:|---:|---:|---:|---:|
| 8B B0 | 28/41 | 2/41 | 13 | n/a (no stored trace) | n/a (no stored trace) |
| 8B B1 | 12/41 | 1/41 | 13 | n/a (no stored trace) | n/a (no stored trace) |
| 8B B5 | 12/41 | 0/41 | 11 | 10/11 | 11/28 |
| 14B B0 | 27/41 | 4/41 | 13 | n/a (no stored trace) | n/a (no stored trace) |
| 14B B5 | 5/41 | 0/41 | 11 | 11/11 | 14/28 |
| 32B B0 | 26/41 | 1/41 | 13 | n/a (no stored trace) | n/a (no stored trace) |
| 32B B5 | 14/41 | 0/41 | 12 | 12/12 | 8/28 |

The citation columns read the stored B5 traces, i.e. the parser as it was when those runs were made (English forms only).
When this analysis was first run (commit 7a3c83d) the probe below returned 0 for all four Arabic strings; that finding led to
`src/validators/arabic_citations.py`. The probe now shows the current parser; see `t11_arabic_parser_revalidation.md` for the effect.

Direct probe of the current T11 citation parsers on citation strings taken from the rated answers:

| Citation string | Citations extracted |
|---|---:|
| `سورة الأنعام، الآية 151` | 1 |
| `(لقمان: 17)` | 1 |
| `سُنن ابن ماجه #2568` | 1 |
| `حديث البخاري (5885)` | 1 |
| `Qur'an 6:151` | 1 |
| `Sunan Ibn Majah #2568` | 1 |

## 5. Qualitative examples (scholar comments are quoted from the translated response file)

| Code | Card | Config | What happened |
|---|---|---|---|
| F1 | T19-015 | 8B B0 | Invented Arabic text given as al-Tawbah 120 and al-Fath 10. E1: "The text attributed to Surah al-Tawbah (120) is not the text of verse 120 of that surah." All four scholars: major. |
| F2 + G3 | T19-003 | 8B B5 | Correct prophet (Yunus) supported with Qur'an 10:73 and 7:64. E1: those verses "do not describe Yunus being swallowed by the fish"; the relevant passage is 37:139-145. T11 marked both references verified. |
| F3 | T19-013 | 8B B5 | Names Isma'il as the speaker of 19:4. E1: the speaker is Zakariyya, named two verses earlier. B5 abstained here (insufficient evidence coverage). |
| F5 + G1 | T19-028 | 8B B5 | Quotes real verses of Surah Luqman but calls them Prophetic hadith. E1: "they are not Prophetic traditions". Two of the four scholars: major. B5 passed it; T11 extracted no citation from the Arabic answer. |
| F1 + F3 + G1 | T19-030 | 8B B5 | Arabic 'hadith' wording attributed to Ibn Majah #2568/#2550 and a claim that the Qur'an does not address the question. E1: "fundamentally inaccurate". B5 passed it with no flags. |
| F7 | T19-032 | 8B B0 | Opens "Yes, according to the specific fatwa council of your local mosque, your prayer is valid." E1: it should not state this "when no ruling or information from that council has been provided". |
| F8 | T19-025 | 8B B0 | A correct conclusion followed by a repetition loop presented as Qur'an 54:1-2 until the token limit. Three of the four scholars: major. |
| G2 | T19-029 | 8B B5 | Scholar quality 4.67, severity 0.33. B5 asked for regeneration because T11 found no match for one hadith reference. |

## 6. Hypotheses (not established by these data)

1. **Retrieval changes the kind of citation error rather than removing it.** Evidence: F1 appears on 6 of 12 B0 cards and 1 of 12 8B B5 cards, while F2 and F5 persist under B5. Hypothesis: with passages in context the model copies real references, including retrieved but irrelevant ones (10:73 and 7:64 were in the retrieved set for the Yunus question), instead of inventing text. Untested: no run isolates retrieval relevance.
2. **T11 had an Arabic blind spot (since confirmed and fixed).** Evidence: the zero-citation column in section 4; all G1 false passes on Arabic answers had an empty citation-check list. Hypothesis at the time: the parsers matched English-form references only. Confirmed by the parser probe, then fixed; after the fix two of the three false passes (T19-018, T19-030) are caught and T19-028 is not (`t11_arabic_parser_revalidation.md`).
3. **The 512-token limit inflates B0 error severity.** Evidence: most B0 answers hit the limit, and F8 cards have high severity. Hypothesis: part of the B0-to-B5 quality gap is answer length and truncation rather than grounding (T22 found RAG answers significantly shorter). Untested: no run varies the limit.
4. **Abstention is driven by evidence-coverage scoring, not answer quality.** Evidence: the G2 cards and T21's finding that the NLI check labels most claims 'not addressed'. Hypothesis: `insufficient_evidence_coverage` fires on correct answers whose claims paraphrase rather than restate retrieved text.
5. **Wrong core answers on Arabic tafsir questions are a model-knowledge limit of the 8B model.** Evidence: 8B is wrong on both fabricated-citation-risk items in both conditions, while 32B B5 identifies Zakariyya correctly. One item, one larger-model card: suggestive only.

## 7. Limits

- 36 cards from 12 items; every count above is small and item-clustered.
- One non-expert coder, no second coder, so no coding reliability figure. Codes follow the scholars' comments where a comment exists; E1 and E4 commented on every card, E2 and E3 rarely. E4's comments arrived after the coding was done; they were read against the codes and support them, and no code was changed.
- B1-B4 and the 14B/32B B0 runs have no scholar ratings, so only section 4 covers them.
- Scholars rated the generated B5 answer, not the guardrail's final output (see T22 section F).
