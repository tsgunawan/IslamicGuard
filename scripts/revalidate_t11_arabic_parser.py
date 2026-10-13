"""Re-run T11 provenance checks and the B5 policy on SAVED responses after the Arabic-citation
parser fix (src/validators/arabic_citations.py). No generation and no NLI: claim checks and
madhhab context are read back from each run's stored guardrail trace, so only the provenance
input to `decide_action` changes. Original run directories are not modified.

Usage: python scripts/revalidate_t11_arabic_parser.py
"""
from __future__ import annotations

import collections
import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.guardrails.abstention_policy import decide_action  # noqa: E402
from src.guardrails.madhhab_policy import MadhhabContext  # noqa: E402
from src.validators import hadith_validator, quran_validator  # noqa: E402
from src.validators.faithfulness_validator import ClaimCheck, ClaimVerdict  # noqa: E402
from src.validators.schema import FlagCategory, MatchTier, QuotationCheck  # noqa: E402

B5_RUNS = {
    "8B": "20260920-0732_Qwen__Qwen3-8B_B5_t15benchmark_s42",
    "14B": "20260920-0825_Qwen__Qwen3-14B-AWQ_B5_t15benchmark_s42",
    "32B": "20260920-1220_Qwen__Qwen3-32B-AWQ_B5_t15benchmark_s42",
}
OUT_MD = ROOT / "results/tables/t11_arabic_parser_revalidation.md"
OUT_JSONL = ROOT / "results/error_analysis/t11_arabic_parser_revalidation.jsonl"
SEV = {"none": 0, "minor": 1, "moderate": 2, "major": 3}


def jl(p):
    return [json.loads(l) for l in Path(p).read_text(encoding="utf-8").splitlines() if l.strip()]


def stored_checks(trace):
    return [QuotationCheck(citation_raw=q["citation_raw"], citation_type=q["citation_type"], exists=q["exists"],
                           match_tier=MatchTier(q["match_tier"]), flag=FlagCategory(q["flag"])) for q in trace["quotation_checks"]]


def decide(query, text, checks, trace):
    claims = [ClaimCheck(claim_text=c["claim_text"], verdict=ClaimVerdict(c["verdict"])) for c in trace["claims"]]
    return decide_action(query=query, response_text=text, quotation_checks=checks, claim_checks=claims,
                         madhhab_context=MadhhabContext(**trace["madhhab_context"]), n_retrieved=len(trace["retrieved_sources"]))


def main():
    bench = {b["item_id"]: b for b in jl(ROOT / "data/benchmarks/t15_benchmark.jsonl")}
    rows, md = [], ["# T11 Arabic-parser fix — re-validation of saved B5 responses", "",
                    "Provenance checks re-run with the Arabic-form citation parser; claim checks and madhhab context reused from the stored traces;",
                    "B5 action recomputed with the unchanged policy. No text was regenerated.", ""]
    md += ["## 1. Effect on the 41-item benchmark", "",
           "| Model | Policy replay reproduces stored action | Arabic answers with >=1 citation checked (before -> after) | Citations checked, all items (before -> after) | Items whose action changed | Action counts before | Action counts after |",
           "|---|---:|---|---|---:|---|---|"]
    for model, run in B5_RUNS.items():
        resp = {r["item_id"]: r["response_text"] for r in jl(ROOT / f"runs/{run}/responses.jsonl")}
        n_same = n_changed = ar_before = ar_after = ar_n = c_before = c_after = 0
        before, after = collections.Counter(), collections.Counter()
        for t in jl(ROOT / f"runs/{run}/guardrail_traces.jsonl"):
            iid, text = t["item_id"], resp[t["item_id"]]
            replay = decide(bench[iid]["query"], text, stored_checks(t), t)
            n_same += replay.action.value == t["action"]
            new_checks = quran_validator.validate_text(text) + hadith_validator.validate_text(text)
            new = decide(bench[iid]["query"], text, new_checks, t)
            is_ar = sum("؀" <= ch <= "ۿ" for ch in text) > 0.3 * len(text)
            if is_ar:
                ar_n += 1; ar_before += bool(t["quotation_checks"]); ar_after += bool(new_checks)
            c_before += len(t["quotation_checks"]); c_after += len(new_checks)
            before[t["action"]] += 1; after[new.action.value] += 1
            n_changed += new.action.value != t["action"]
            rows.append(dict(model=model, item_id=iid, stratum=bench[iid]["stratum"], arabic_answer=is_ar,
                             action_before=t["action"], action_after=new.action.value, flags_after=new.guardrail_flags,
                             n_checks_before=len(t["quotation_checks"]), quotation_checks_after=[q.to_dict() for q in new_checks]))
        f = lambda c: ", ".join(f"{k.replace('regenerate_with_evidence', 'regenerate')} {v}" for k, v in sorted(c.items()))
        md.append(f"| {model} | {n_same}/41 | {ar_before}/{ar_n} -> {ar_after}/{ar_n} | {c_before} -> {c_after} | {n_changed} | {f(before)} | {f(after)} |")
    df = pd.DataFrame(rows)
    OUT_JSONL.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n", encoding="utf-8")

    ch = df[df.action_before != df.action_after]
    md += ["", "## 2. Items whose B5 action changed", "", "| Model | Item | Stratum | Before | After | New flags | New non-verified citations |", "|---|---|---|---|---|---|---|"]
    for r in ch.itertuples():
        bad = "; ".join(f"{q['citation_raw']} ({q['flag']})" for q in r.quotation_checks_after if q["flag"] != "verified")
        md.append(f"| {r.model} | {r.item_id} | {r.stratum} | {r.action_before} | {r.action_after} | {', '.join(r.flags_after)} | {bad} |")
    allq = [q for r in rows if r["arabic_answer"] for q in r["quotation_checks_after"]]
    md += ["", f"Citations now checked in Arabic answers, by flag: {dict(collections.Counter(q['flag'] for q in allq))}; "
           f"by match tier: {dict(collections.Counter(q['match_tier'] for q in allq))}."]

    # ---- scholar-rated cards ----
    key = jl(ROOT / "expert_review/t20_blinding_key.jsonl")
    r = pd.DataFrame(jl(ROOT / "results/error_analysis/t19_expert_ratings_long.jsonl"))
    sev = r[(r.field == "severity") & r.value.notna()].assign(v=lambda d: d.value.map(SEV)).groupby("card_id").v.mean()
    cards = []
    for k in key:
        text = {x["item_id"]: x["response_text"] for x in jl(ROOT / f"runs/{k['run_id']}/responses.jsonl")}[k["item_id"]]
        new_checks = quran_validator.validate_text(text) + hadith_validator.validate_text(text)
        model = k["run_label"].split("_")[0]
        hit = df[(df.model == model) & (df.item_id == k["item_id"])] if k["run_label"].endswith("B5") else None
        cards.append(dict(card_id=k["card_id"], run_label=k["run_label"], bad=sev[k["card_id"]] >= 2.0,
                          flagged=any(q.flag != FlagCategory.VERIFIED for q in new_checks),
                          before=hit.action_before.iloc[0] if hit is not None else None,
                          after=hit.action_after.iloc[0] if hit is not None else None))
    c = pd.DataFrame(cards)
    # Pre-fix T11 flag per card, as computed by the comparison script before the parser fix.
    # pre-fix per-card signals, saved from commit 474429b so no git history is needed
    old = (ROOT / "results/error_analysis/t19_automated_vs_scholar_cards_prefix_474429b.jsonl").read_text(encoding="utf-8")
    pre = {x["card_id"]: x["any_misquote"] for x in map(json.loads, old.splitlines())}
    fp_before = None
    def det(flag, sub):
        tp = int((flag & sub.bad).sum()); fp = int((flag & ~sub.bad).sum()); fn = int((~flag & sub.bad).sum()); tn = int((~flag & ~sub.bad).sum())
        d = lambda a, b: f"{a / b:.2f}" if b else "–"
        return f"{int(flag.sum())} | {tp} | {fp} | {fn} | {tn} | {d(tp, tp + fn)} | {d(tp, tp + fp)} | {d(tn, tn + fp)}"
    b5 = c[c.before.notna()]
    fp_before = b5[(b5.before == "pass") & b5.bad]
    md += ["", f"## 3. Against the scholar ratings (36 cards; scholar-bad = mean severity >= 2.0, {int(c.bad.sum())} cards)", "",
           "| Rule | Flagged | TP | FP | FN | TN | Sensitivity | Precision | Specificity |", "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
           f"| T11 any non-verified citation, before fix (flags from commit 474429b) | {det(c.card_id.map(pre).astype(bool), c)} |",
           f"| T11 any non-verified citation, after fix (36 cards) | {det(c.flagged, c)} |",
           f"| B5 action != pass, before fix (24 B5 cards) | {det(b5.before != 'pass', b5)} |",
           f"| B5 action != pass, after fix (24 B5 cards) | {det(b5.after != 'pass', b5)} |", "",
           "Rated cards whose B5 action changed: " + (", ".join(f"{x.card_id} ({x.run_label}: {x.before} -> {x.after}; scholar-bad={x.bad})" for x in b5[b5.before != b5.after].itertuples()) or "none") + ".",
           f"Scholar-bad cards that B5 passed before the fix ({len(fp_before)}): " + (", ".join(f"{x.card_id} -> {x.after}" for x in fp_before.itertuples()) or "none") + ".",
           "", "## Limits", "",
           "- The scholar cards were used to find the blind spot, and two real card excerpts are now unit tests, so section 3 is not an independent test of the fixed parser.",
           "- Still not detected: a real reference cited for the wrong content with no quotation (T21's main finding), and source-type errors such as Qur'an verses described as hadith (T19-028).",
           "- Quote-to-citation pairing is nearest-by-distance, as in the English path, and can misattribute when several citations share a paragraph.",
           "- Hadith numbering follows this corpus only; an Arabic citation using another numbering scheme is reported as not found or misquoted."]
    OUT_MD.write_text("\n".join(md) + "\n", encoding="utf-8")
    print("\n".join(md))


if __name__ == "__main__":
    main()
