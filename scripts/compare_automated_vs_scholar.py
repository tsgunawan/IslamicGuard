"""T19/T20 follow-up: card-level comparison of the automated validators (T11 provenance, T12
faithfulness, B5 action) against the unblinded scholar ratings. Exploratory; n=36 cards / 12 items.

Automated signals are RECOMPUTED for every card from its response text with the same validators
(so B0 cards, which have no stored guardrail trace, are scored the same way as B5 cards), using
the query's B5 retrieval passages as evidence. For B5 cards the recomputed values are checked
against the stored traces.
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import mannwhitneyu, spearmanr

ROOT = Path(__file__).resolve().parents[1]
import sys
sys.path.insert(0, str(ROOT))
from src.validators import hadith_validator, quran_validator  # noqa: E402
from src.validators.claim_segmenter import segment_claims  # noqa: E402
from src.validators.faithfulness_validator import check_claim, evidence_texts_from_retrieval_entry  # noqa: E402

RATINGS = ROOT / "results/error_analysis/t19_expert_ratings_long.jsonl"
KEY = ROOT / "expert_review/t20_blinding_key.jsonl"
OUT_MD = ROOT / "results/tables/t19_automated_vs_scholar.md"
OUT_JSONL = ROOT / "results/error_analysis/t19_automated_vs_scholar_cards.jsonl"
RETR_RUN = "20260920-0732_Qwen__Qwen3-8B_B5_t15benchmark_s42"  # retrieval is query-only; same for all models
SEV = {"none": 0, "minor": 1, "moderate": 2, "major": 3}


def jl(p):
    return [json.loads(l) for l in Path(p).read_text().splitlines()]


def main():
    key = pd.DataFrame(jl(KEY))
    retr = {r["item_id"]: r for r in jl(ROOT / f"runs/{RETR_RUN}/retrieval.jsonl")}
    rows = []
    for k in key.itertuples():
        resp = {r["item_id"]: r["response_text"] for r in jl(ROOT / f"runs/{k.run_id}/responses.jsonl")}[k.item_id]
        trace = {t["item_id"]: t for t in jl(ROOT / f"runs/{k.run_id}/guardrail_traces.jsonl")}[k.item_id]
        qc = quran_validator.validate_text(resp) + hadith_validator.validate_text(resp)
        ev = evidence_texts_from_retrieval_entry(retr[k.item_id])
        cl = [check_claim(c.text, ev) for c in segment_claims(resp)]
        verdicts = [c.verdict.value for c in cl]
        n = max(len(cl), 1)
        row = dict(
            card_id=k.card_id, item_id=k.item_id, stratum=k.stratum, run_label=k.run_label,
            n_citations=len(qc), n_misquoted=sum(q.flag.value == "misquoted" if hasattr(q.flag, "value") else q.flag == "misquoted" for q in qc),
            n_claims=len(cl), frac_supported=verdicts.count("supported") / n,
            frac_contradicted=verdicts.count("contradicted") / n,
            mean_entail=float(np.mean([c.entailment_prob for c in cl if c.entailment_prob is not None] or [0])),
            stored_action=trace["action"] if "claims" in trace else None,
        )
        row["any_misquote"] = int(row["n_misquoted"] > 0)
        if "claims" in trace:  # consistency check vs stored B5 trace
            row["stored_misquoted"] = sum(q["flag"] == "misquoted" for q in trace["quotation_checks"])
            row["stored_supported"] = sum(c["verdict"] == "supported" for c in trace["claims"]) / max(len(trace["claims"]), 1)
        rows.append(row)
    auto = pd.DataFrame(rows)

    r = pd.DataFrame(jl(RATINGS))
    r = r[r.value.notna()]
    def piv(field, conv=lambda x: x):
        x = r[r.field == field].copy(); x["v"] = x.value.map(conv).astype(float)
        return x.groupby("card_id").v
    sch = pd.DataFrame({"quality": piv("quality").mean(), "source": piv("source").mean(),
                        "severity": piv("severity", SEV.get).mean(),
                        "n_major": piv("severity", lambda s: SEV[s] == 3).sum()})
    df = auto.merge(sch, on="card_id")
    df["scholar_bad"] = (df.severity >= 2.0).astype(int)  # declared threshold: mean severity >= moderate
    df.to_json(OUT_JSONL, orient="records", lines=True, force_ascii=False)

    md = ["# T19 follow-up — automated validators vs scholar ratings (exploratory)", "",
          f"- {len(df)} cards (12 items x 3 responses). Automated signals recomputed from response text; evidence = B5 retrieval for the query (same for all models).",
          f"- Scholar reference = mean over {r.rater.nunique()} raters. 'Scholar-bad' = mean error severity >= 2.0 (moderate); threshold set before looking at detection rates.",
          "- Cards from the same item are not independent; treat p-values as descriptive.", ""]
    chk = df.dropna(subset=["stored_misquoted"])
    md += [f"Consistency with stored B5 traces ({len(chk)} cards): misquote count identical on "
           f"{(chk.n_misquoted == chk.stored_misquoted).sum()}/{len(chk)}; supported-claim share identical (±0.01) on "
           f"{(np.abs(chk.frac_supported - chk.stored_supported) < 0.01).sum()}/{len(chk)}.", "",
           "## 1. Rank correlation with scholar means (Spearman, n=36)", "",
           "| Automated signal | vs quality | vs source | vs severity |", "|---|---|---|---|"]
    for col, lab in [("frac_supported", "Share of claims 'supported' (T12)"), ("mean_entail", "Mean entailment prob (T12)"),
                     ("frac_contradicted", "Share of claims 'contradicted' (T12)"), ("n_misquoted", "Misquoted-citation count (T11)")]:
        cells = []
        for s in ("quality", "source", "severity"):
            rho, p = spearmanr(df[col], df[s]); cells.append(f"{rho:+.2f} (p={p:.3f})")
        md.append(f"| {lab} | " + " | ".join(cells) + " |")
    # Same correlations with the automated signals as they were before the Arabic-parser fix
    # (per-card signals saved at commit 474429b), against the current scholar means.
    # pre-fix per-card signals, saved from commit 474429b so no git history is needed
    old = (ROOT / "results/error_analysis/t19_automated_vs_scholar_cards_prefix_474429b.jsonl").read_text(encoding="utf-8")
    pre = pd.DataFrame([json.loads(l) for l in old.splitlines()]).drop(columns=["quality", "source", "severity", "n_major", "scholar_bad"], errors="ignore")
    pre = pre.merge(df[["card_id", "quality", "source", "severity"]], on="card_id")
    md += ["", "### 1b. Same, with the automated signals as computed before the Arabic-parser fix (commit 474429b)", "",
           "| Automated signal | vs quality | vs source | vs severity |", "|---|---|---|---|"]
    for col, lab in [("frac_supported", "Share of claims 'supported' (T12)"), ("mean_entail", "Mean entailment prob (T12)"),
                     ("frac_contradicted", "Share of claims 'contradicted' (T12)"), ("n_misquoted", "Misquoted-citation count (T11, pre-fix)")]:
        cells = []
        for sc in ("quality", "source", "severity"):
            rho, pv = spearmanr(pre[col], pre[sc]); cells.append(f"{rho:+.2f} (p={pv:.3f})")
        md.append(f"| {lab} | " + " | ".join(cells) + " |")
    md += ["", "## 2. Detecting scholar-bad responses (severity >= 2.0)", "",
           f"Base rate: {df.scholar_bad.sum()}/{len(df)} cards scholar-bad.", "",
           "| Automated rule | Flagged | TP | FP | FN | TN | Sensitivity | Precision | Specificity |", "|---|---|---|---|---|---|---|---|---|"]
    def det(name, flag, sub=df):
        y = sub.scholar_bad.values; f = flag.loc[sub.index].values.astype(bool)
        tp, fp, fn, tn = int((f & (y == 1)).sum()), int((f & (y == 0)).sum()), int((~f & (y == 1)).sum()), int((~f & (y == 0)).sum())
        d = lambda a, b: f"{a / b:.2f}" if b else "–"
        md.append(f"| {name} | {int(f.sum())} | {tp} | {fp} | {fn} | {tn} | {d(tp, tp + fn)} | {d(tp, tp + fp)} | {d(tn, tn + fp)} |")
    det("T11: any misquoted citation", df.n_misquoted > 0)
    det("T12: <50% claims supported", df.frac_supported < 0.5)
    det("T11 or T12 (either)", (df.n_misquoted > 0) | (df.frac_supported < 0.5))
    b5 = df[df.stored_action.notna()]
    det(f"B5 action != pass (B5 cards only, n={len(b5)})", b5.stored_action.ne("pass"), b5)
    b5b = b5.copy(); b5b["x"] = b5b.stored_action.eq("pass")
    md += ["", "## 3. Scholar ratings by B5 action (B5 cards only)", "", "| B5 action | Cards | Mean quality | Mean severity | Scholar-bad |", "|---|---|---|---|---|"]
    for a, g in b5.groupby("stored_action"):
        md.append(f"| {a} | {len(g)} | {g.quality.mean():.2f} | {g.severity.mean():.2f} | {g.scholar_bad.sum()}/{len(g)} |")
    md += ["", "## 4. Scholar ratings by T11 misquote flag (all cards)", "", "| Misquote flag | Cards | Mean quality | Mean severity | Mean source |", "|---|---|---|---|---|"]
    for a, g in df.groupby("any_misquote"):
        md.append(f"| {'flagged' if a else 'not flagged'} | {len(g)} | {g.quality.mean():.2f} | {g.severity.mean():.2f} | {g.source.mean():.2f} |")
    u = mannwhitneyu(df[df.any_misquote == 1].quality, df[df.any_misquote == 0].quality)
    md.append(f"\nMann-Whitney on quality (flagged vs not): p={u.pvalue:.3f}.")
    md += ["", "## 5. Cards scholars judged bad but no automated rule flagged (T11 or T12)", ""]
    miss = df[(df.scholar_bad == 1) & ~((df.n_misquoted > 0) | (df.frac_supported < 0.5))]
    md.append(", ".join(f"{c.card_id} ({c.run_label}, q={c.quality:.1f}, sev={c.severity:.1f})" for c in miss.itertuples()) or "none")
    OUT_MD.write_text("\n".join(md) + "\n")
    print("\n".join(md))


if __name__ == "__main__":
    main()
