"""T23 -- error analysis: failure taxonomy over the 36 scholar-rated cards plus pipeline-level
checks over all 41 benchmark items in every major configuration.

Two kinds of content, kept separate in the output:
  * EVIDENCE: counts computed here from saved artifacts, and scholar ratings/comments.
  * CODING: `CARD_CODES` below is a manual content coding of each rated card, done by the project's
    coding agent (one coder, not a scholar) from the answer text and the scholars' comments. It is
    an organising device for the scholars' findings, not an independent expert judgment.
Causal statements are labelled as hypotheses in the report.

Usage: python scripts/t23_error_analysis.py
"""
from __future__ import annotations

import collections
import json
import re
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.validators import hadith_validator, quran_validator  # noqa: E402

OUT_MD = ROOT / "results/tables/t23_error_analysis.md"
OUT_CODES = ROOT / "results/error_analysis/t23_card_codes.jsonl"
SEV = {"none": 0, "minor": 1, "moderate": 2, "major": 3}

TAXONOMY = {
    "F1": ("Fabricated scripture text", "Wording presented as a Qur'an verse or hadith that is not the text of the cited source."),
    "F2": ("Wrong-but-real citation", "A reference that exists but does not say what the answer claims, or concerns a different event or person."),
    "F3": ("Wrong core answer", "The main factual answer is incorrect (wrong verse, wrong prophet, or a false claim about what the Qur'an addresses)."),
    "F4": ("Omission of the directly relevant evidence", "Answer is incomplete or leaves out the text a scholar considers the primary evidence."),
    "F5": ("Source-type or source-identity confusion", "Qur'an called hadith, al-Fatihah called al-Baqarah, Biblical or internal-dataset sources used as the Islamic reference."),
    "F6": ("Fiqh misstatement or overgeneralisation", "School positions misstated, false consensus claimed, or a legal category confused."),
    "F7": ("Unsupported attribution or accepted false premise", "Views credited to a named authority without a source, or a ruling asserted for a body whose position is unknown."),
    "F8": ("Degenerate or truncated generation", "Repetition loop, or answer cut off at the token limit before its conclusion."),
    "F9": ("Added narrative detail or mistranslation", "Invented story details, inaccurate translation/transliteration, or a garbled retelling."),
}
GUARD = {
    "G1": "False pass: scholars judged the answer bad (mean severity >= 2) and B5 passed it.",
    "G2": "Intervention on an acceptable answer: B5 abstained or asked for regeneration although scholars did not judge it bad (answers that themselves decline are excluded).",
    "G3": "Verified wrong citation: the validator marked a wrong-but-real citation as verified.",
}
# card_id -> (codes, one-line basis). Guardrail codes G1/G2 are derived from data, not coded here.
CARD_CODES = {
    "T19-001": (["F3", "F2", "F9"], "Gives 30:1-5 for a question scholars tie to 33:12; 'Persians (i.e., the Romans)'."),
    "T19-014": (["F3", "F2"], "Same wrong verse; E1: conflates two different events."),
    "T19-015": (["F1", "F3", "F8"], "Invented text attributed to al-Tawbah 120 and al-Fath 10; repeats itself and is cut off."),
    "T19-002": (["F7", "F8"], "Principles credited to al-Ghazali without a work or passage; cut off."),
    "T19-007": ([], "Appropriate 'not found' answer; scholars note only a missing historical remark."),
    "T19-023": ([], "Appropriate 'not found' answer."),
    "T19-003": (["F2", "G3"], "Correct prophet, but 10:73 and 7:64 concern Nuh; validator marked both verified."),
    "T19-010": (["F2", "G3"], "Same two verses misapplied; validator marked both verified."),
    "T19-031": (["F5"], "Correct, but sourced from the Bible rather than the Qur'an."),
    "T19-004": (["F4"], "Correct prophet; cites 21:60-71 and 26:69-224 instead of 2:258."),
    "T19-019": (["F1"], "Correct prophet; text given as 2:258 is not that verse."),
    "T19-036": (["F9"], "Correct and well sourced; retelling of the sun argument is garbled."),
    "T19-005": ([], "Accurate account of the disagreement."),
    "T19-017": (["F6", "F8"], "Equates the discerning child with the legally accountable; Hanafi position misstated; cut off."),
    "T19-034": (["F5"], "Accurate, but cites the internal dataset ID 'FiqhQA #18' as its source."),
    "T19-006": (["F4", "F6", "F8"], "Omits the 'except the graveyard and the bathhouse' report; overgeneralises; cut off."),
    "T19-024": (["F1", "F6"], "Hadith wording attributed to Sahih Muslim that does not match; claims four-school consensus."),
    "T19-026": (["F6"], "Overgeneralises Hanafi/Maliki/Shafi'i positions as 'permissible'."),
    "T19-008": ([], "Correct and well sourced; one scholar notes confusion over hadith numbers."),
    "T19-025": (["F1", "F8"], "Text attributed to 7:187 and 54:1-2 is not those verses; long repetition loop."),
    "T19-029": (["F9"], "Correct; transliteration of 31:34 inaccurate."),
    "T19-009": (["F1", "F3", "F4", "F8"], "Invented wording for 24:2 and 17:32; says the Qur'an does not address it; omits the Lut verses; cut off."),
    "T19-018": (["F1", "F3", "F4"], "Says the Qur'an is not explicit; omits the Lut verses; hadith wording not authentic."),
    "T19-030": (["F1", "F3", "F4", "F8"], "Invented hadith wording for Ibn Majah; omits the Lut verses; repeats and is cut off."),
    "T19-011": (["F5"], "Calls al-Fatihah 'Surah Al-Baqarah, chapter 1'; cites internal FiqhQA IDs."),
    "T19-032": (["F7"], "Asserts the prayer is valid 'according to' a council whose ruling is unknown."),
    "T19-033": (["F5", "G3"], "Calls the opening chapter 'Al-Baqarah 2:255'; validator marked the reference verified."),
    "T19-012": (["F3", "F2", "F9"], "Names Ibrahim/Isma'il instead of Zakariyya; places the verse in al-Anbiya'; invented narrative."),
    "T19-013": (["F3"], "Names Isma'il instead of Zakariyya; surah reference is right."),
    "T19-027": (["F9"], "Correct prophet and verse; adds details not in the text and misinterprets 19:4's ending."),
    "T19-016": (["F1", "F5", "F8"], "Invented text attributed to Luqman 17; calls the verses hadith; repetition loop."),
    "T19-022": (["F4"], "Accurate but lists two counsels only."),
    "T19-028": (["F5", "F4", "F8"], "Quotes real verses but classifies them as Prophetic hadith; incomplete; cut off."),
    "T19-020": ([], "Correct and relevant."),
    "T19-021": (["F6"], "Correct; describes the beard as 'simply sunnah'."),
    "T19-035": (["F6"], "Correct; scholar notes many jurists hold the beard obligatory."),
}
RUNS = {
    "8B B0": "20260920-0426_Qwen__Qwen3-8B_B0_t15_benchmark_s42",
    "8B B1": "20260920-0441_Qwen__Qwen3-8B_B1_t15_benchmark_s42",
    "8B B5": "20260920-0732_Qwen__Qwen3-8B_B5_t15benchmark_s42",
    "14B B0": "20260920-0804_Qwen__Qwen3-14B-AWQ_B0_t15_benchmark_s42",
    "14B B5": "20260920-0825_Qwen__Qwen3-14B-AWQ_B5_t15benchmark_s42",
    "32B B0": "20260920-0840_Qwen__Qwen3-32B-AWQ_B0_t15_benchmark_s42",
    "32B B5": "20260920-1220_Qwen__Qwen3-32B-AWQ_B5_t15benchmark_s42",
}
# Answers that themselves say the evidence is missing: an abstain action agrees with them, so not G2.
SELF_DECLINING = {"T19-007", "T19-023"}
AR = re.compile(r"[؀-ۿ]")


def jl(p):
    return [json.loads(l) for l in Path(p).read_text(encoding="utf-8").splitlines() if l.strip()]


def is_arabic(t):
    return len(AR.findall(t)) > 0.3 * len(t)


def has_loop(t):
    parts = [x.strip() for x in re.split(r"[\n.؟]", t) if len(x.strip()) > 25]
    return max(collections.Counter(parts).values(), default=0) >= 3


def main():
    key = {k["card_id"]: k for k in jl(ROOT / "expert_review/t20_blinding_key.jsonl")}
    r = pd.DataFrame(jl(ROOT / "results/error_analysis/t19_expert_ratings_long.jsonl"))
    sev = r[(r.field == "severity") & r.value.notna()].assign(v=lambda d: d.value.map(SEV)).groupby("card_id").v.mean()
    qual = r[(r.field == "quality") & r.value.notna()].assign(v=lambda d: d.value.astype(float)).groupby("card_id").v.mean()
    rows = []
    for cid, (codes, basis) in CARD_CODES.items():
        k = key[cid]
        trace = {t["item_id"]: t for t in jl(ROOT / f"runs/{k['run_id']}/guardrail_traces.jsonl")}[k["item_id"]]
        action = trace["action"] if "claims" in trace else None
        bad = sev[cid] >= 2.0
        codes = list(codes)
        if action == "pass" and bad:
            codes.append("G1")
        if action in ("abstain", "regenerate_with_evidence") and not bad and cid not in SELF_DECLINING:
            codes.append("G2")
        rows.append(dict(card_id=cid, item_id=k["item_id"], stratum=k["stratum"], run_label=k["run_label"],
                         condition=k["run_label"].split("_")[1], b5_action=action, scholar_quality=round(qual[cid], 2),
                         scholar_severity=round(sev[cid], 2), scholar_bad=bool(bad), codes=codes, basis=basis))
    df = pd.DataFrame(rows)
    OUT_CODES.write_text("\n".join(json.dumps(x, ensure_ascii=False) for x in rows) + "\n", encoding="utf-8")

    md = ["# T23 — Error analysis", "",
          "Scope: (1) a failure taxonomy applied to the 36 scholar-rated cards (12 items x 8B B0, 8B B5, one 14B/32B B5);",
          "(2) pipeline-level checks over all 41 benchmark items in seven configurations.",
          "",
          "**How to read this.** Counts and scholar ratings are evidence. The category assigned to each card is a manual coding by the",
          "project's coding agent (one coder, not a scholar), based on the answer text and the scholars' comments; a card can carry several codes.",
          "Statements under 'Hypotheses' are explanations that the data are consistent with but do not establish.", "",
          "## 1. Taxonomy", "", "| Code | Failure type | Definition |", "|---|---|---|"]
    md += [f"| {c} | {n} | {d} |" for c, (n, d) in TAXONOMY.items()]
    md += [f"| {c} | Guardrail: {d.split(':')[0]} | {d.split(': ', 1)[1]} |" for c, d in GUARD.items()]

    md += ["", "## 2. Failure counts on the scholar-rated cards (evidence + coding)", "",
           "| Code | Failure type | 8B B0 (12 cards) | 8B B5 (12) | 14B/32B B5 (12) | All (36) | Mean scholar severity when present | When absent |",
           "|---|---|---:|---:|---:|---:|---:|---:|"]
    grp = lambda d: "8B B0" if d.run_label == "8B_B0" else ("8B B5" if d.run_label == "8B_B5" else "big B5")
    df["grp"] = df.apply(grp, axis=1)
    for c, (n, _) in TAXONOMY.items():
        has = df.codes.map(lambda x: c in x)
        cnt = [int(has[df.grp == g].sum()) for g in ("8B B0", "8B B5", "big B5")]
        md.append(f"| {c} | {n} | {cnt[0]} | {cnt[1]} | {cnt[2]} | {int(has.sum())} | {df.scholar_severity[has].mean():.2f} | {df.scholar_severity[~has].mean():.2f} |")
    none = df.codes.map(lambda x: not [c for c in x if c.startswith("F")])
    md.append(f"| – | No content failure coded | {int(none[df.grp == '8B B0'].sum())} | {int(none[df.grp == '8B B5'].sum())} | {int(none[df.grp == 'big B5'].sum())} | {int(none.sum())} | {df.scholar_severity[none].mean():.2f} | {df.scholar_severity[~none].mean():.2f} |")
    md += ["", "Severity: 0 = none, 3 = major, mean of the scholars' ratings."]

    b5 = df[df.b5_action.notna()]
    md += ["", "## 3. Guardrail outcomes on the 24 rated B5 cards (evidence)", "",
           "| B5 action | Cards | Scholar-bad | Not scholar-bad |", "|---|---:|---:|---:|"]
    for a, g in b5.groupby("b5_action"):
        md.append(f"| {a} | {len(g)} | {int(g.scholar_bad.sum())} | {int((~g.scholar_bad).sum())} |")
    g1 = b5[b5.codes.map(lambda x: "G1" in x)]; g2 = b5[b5.codes.map(lambda x: "G2" in x)]; g3 = df[df.codes.map(lambda x: "G3" in x)]
    fmt = lambda d: ", ".join(f"{x.card_id} ({x.run_label.replace('_', ' ')}; {'+'.join(c for c in x.codes if c.startswith('F')) or 'no content failure'})" for x in d.itertuples()) or "none"
    md += ["", f"- **G1 false passes ({len(g1)}):** {fmt(g1)}.",
           f"- **G2 interventions on acceptable answers ({len(g2)}):** {fmt(g2)}.",
           f"- **G3 wrong-but-real citations marked verified ({len(g3)}):** {fmt(g3)}.",
           "- Two of the G2 cards (T19-020, T19-035) were sent for regeneration because madhhab plurality was not surfaced; E1's comment on T19-035 makes the same point (many jurists hold the beard obligatory), so that flag has scholar support even though the answers were rated acceptable.",
           "- T19-007 and T19-023 were abstentions on answers that themselves said the evidence was missing; they are not counted as G2.",
           "- Both `escalate` cards were the personal-ruling item. All four scholars chose escalation for T19-033 and one did for T19-011. Both answers contain a source-identity error (F5); T19-011 was judged bad, and T19-033 fell just below the threshold."]

    # ---- pipeline-level checks over all 41 items ----
    bench = {b["item_id"]: b for b in jl(ROOT / "data/benchmarks/t15_benchmark.jsonl")}
    md += ["", "## 4. Pipeline-level checks on all 41 items per configuration (evidence)", "",
           "| Configuration | Hit the 512-token limit | Repetition loop | Arabic answers | Arabic answers with zero citations extracted by T11 | English-question answers with zero citations extracted |",
           "|---|---:|---:|---:|---:|---:|"]
    for lab, run in RUNS.items():
        R = jl(ROOT / f"runs/{run}/responses.jsonl")
        T = {t["item_id"]: t for t in jl(ROOT / f"runs/{run}/guardrail_traces.jsonl")}
        trunc = sum(x["completion_tokens"] >= 512 for x in R); loops = sum(has_loop(x["response_text"]) for x in R)
        ar = [x for x in R if is_arabic(x["response_text"])]
        en = [x for x in R if bench[x["item_id"]]["language"] == "en"]
        if lab.endswith("B5"):
            z_ar = f"{sum(len(T[x['item_id']]['quotation_checks']) == 0 for x in ar)}/{len(ar)}"
            z_en = f"{sum(len(T[x['item_id']]['quotation_checks']) == 0 for x in en)}/{len(en)}"
        else:
            z_ar = z_en = "n/a (no stored trace)"
        md.append(f"| {lab} | {trunc}/41 | {loops}/41 | {len(ar)} | {z_ar} | {z_en} |")
    probes = ["سورة الأنعام، الآية 151", "(لقمان: 17)", "سُنن ابن ماجه #2568", "حديث البخاري (5885)", "Qur'an 6:151", "Sunan Ibn Majah #2568"]
    md += ["", "The citation columns read the stored B5 traces, i.e. the parser as it was when those runs were made (English forms only).",
           "When this analysis was first run (commit 7a3c83d) the probe below returned 0 for all four Arabic strings; that finding led to",
           "`src/validators/arabic_citations.py`. The probe now shows the current parser; see `t11_arabic_parser_revalidation.md` for the effect.",
           "", "Direct probe of the current T11 citation parsers on citation strings taken from the rated answers:", "", "| Citation string | Citations extracted |", "|---|---:|"]
    for p in probes:
        md.append(f"| `{p}` | {len(quran_validator.validate_text(p) + hadith_validator.validate_text(p))} |")

    md += ["", "## 5. Qualitative examples (scholar comments are quoted from the translated response file)", ""]
    ex = [("F1", "T19-015", "8B B0", "Invented Arabic text given as al-Tawbah 120 and al-Fath 10. E1: \"The text attributed to Surah al-Tawbah (120) is not the text of verse 120 of that surah.\" All four scholars: major."),
          ("F2 + G3", "T19-003", "8B B5", "Correct prophet (Yunus) supported with Qur'an 10:73 and 7:64. E1: those verses \"do not describe Yunus being swallowed by the fish\"; the relevant passage is 37:139-145. T11 marked both references verified."),
          ("F3", "T19-013", "8B B5", "Names Isma'il as the speaker of 19:4. E1: the speaker is Zakariyya, named two verses earlier. B5 abstained here (insufficient evidence coverage)."),
          ("F5 + G1", "T19-028", "8B B5", "Quotes real verses of Surah Luqman but calls them Prophetic hadith. E1: \"they are not Prophetic traditions\". Two of the four scholars: major. B5 passed it; T11 extracted no citation from the Arabic answer."),
          ("F1 + F3 + G1", "T19-030", "8B B5", "Arabic 'hadith' wording attributed to Ibn Majah #2568/#2550 and a claim that the Qur'an does not address the question. E1: \"fundamentally inaccurate\". B5 passed it with no flags."),
          ("F7", "T19-032", "8B B0", "Opens \"Yes, according to the specific fatwa council of your local mosque, your prayer is valid.\" E1: it should not state this \"when no ruling or information from that council has been provided\"."),
          ("F8", "T19-025", "8B B0", "A correct conclusion followed by a repetition loop presented as Qur'an 54:1-2 until the token limit. Three of the four scholars: major."),
          ("G2", "T19-029", "8B B5", "Scholar quality 4.67, severity 0.33. B5 asked for regeneration because T11 found no match for one hadith reference.")]
    md += ["| Code | Card | Config | What happened |", "|---|---|---|---|"] + [f"| {a} | {b} | {c} | {d} |" for a, b, c, d in ex]

    md += ["", "## 6. Hypotheses (not established by these data)", "",
           "1. **Retrieval changes the kind of citation error rather than removing it.** Evidence: F1 appears on 6 of 12 B0 cards and 1 of 12 8B B5 cards, while F2 and F5 persist under B5. Hypothesis: with passages in context the model copies real references, including retrieved but irrelevant ones (10:73 and 7:64 were in the retrieved set for the Yunus question), instead of inventing text. Untested: no run isolates retrieval relevance.",
           "2. **T11 had an Arabic blind spot (since confirmed and fixed).** Evidence: the zero-citation column in section 4; all G1 false passes on Arabic answers had an empty citation-check list. Hypothesis at the time: the parsers matched English-form references only. Confirmed by the parser probe, then fixed; after the fix two of the three false passes (T19-018, T19-030) are caught and T19-028 is not (`t11_arabic_parser_revalidation.md`).",
           "3. **The 512-token limit inflates B0 error severity.** Evidence: most B0 answers hit the limit, and F8 cards have high severity. Hypothesis: part of the B0-to-B5 quality gap is answer length and truncation rather than grounding (T22 found RAG answers significantly shorter). Untested: no run varies the limit.",
           "4. **Abstention is driven by evidence-coverage scoring, not answer quality.** Evidence: the G2 cards and T21's finding that the NLI check labels most claims 'not addressed'. Hypothesis: `insufficient_evidence_coverage` fires on correct answers whose claims paraphrase rather than restate retrieved text.",
           "5. **Wrong core answers on Arabic tafsir questions are a model-knowledge limit of the 8B model.** Evidence: 8B is wrong on both fabricated-citation-risk items in both conditions, while 32B B5 identifies Zakariyya correctly. One item, one larger-model card: suggestive only.",
           "", "## 7. Limits", "",
           "- 36 cards from 12 items; every count above is small and item-clustered.",
           "- One non-expert coder, no second coder, so no coding reliability figure. Codes follow the scholars' comments where a comment exists; E1 and E4 commented on every card, E2 and E3 rarely. E4's comments arrived after the coding was done; they were read against the codes and support them, and no code was changed.",
           "- B1-B4 and the 14B/32B B0 runs have no scholar ratings, so only section 4 covers them.",
           "- Scholars rated the generated B5 answer, not the guardrail's final output (see T22 section F)."]
    OUT_MD.write_text("\n".join(md) + "\n", encoding="utf-8")
    print("\n".join(md[md.index("## 2. Failure counts on the scholar-rated cards (evidence + coding)"):md.index("## 5. Qualitative examples (scholar comments are quoted from the translated response file)")]))


if __name__ == "__main__":
    main()
