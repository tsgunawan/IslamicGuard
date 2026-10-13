"""T22 -- statistical comparison (DG-9: item-level paired bootstrap + exact McNemar, Holm-corrected).

Unit of analysis is always the benchmark ITEM (41 automated; 12 scholar-rated), so every
comparison is paired on item and the bootstrap resamples whole items. Reads saved run artifacts
and scholar ratings only; no generation. T11 provenance checks are re-run deterministically on
the saved response text so B0/B1 (which have no stored trace) are scored like B5.

Usage: python scripts/t22_statistical_comparison.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import binomtest, wilcoxon

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.validators import hadith_validator, quran_validator  # noqa: E402

RUNS = {
    ("8B", "B0"): "20260920-0426_Qwen__Qwen3-8B_B0_t15_benchmark_s42",
    ("8B", "B1"): "20260920-0441_Qwen__Qwen3-8B_B1_t15_benchmark_s42",
    ("8B", "B5"): "20260920-0732_Qwen__Qwen3-8B_B5_t15benchmark_s42",
    ("14B", "B0"): "20260920-0804_Qwen__Qwen3-14B-AWQ_B0_t15_benchmark_s42",
    ("14B", "B5"): "20260920-0825_Qwen__Qwen3-14B-AWQ_B5_t15benchmark_s42",
    ("32B", "B0"): "20260920-0840_Qwen__Qwen3-32B-AWQ_B0_t15_benchmark_s42",
    ("32B", "B5"): "20260920-1220_Qwen__Qwen3-32B-AWQ_B5_t15benchmark_s42",
}
RERUN_32B = "20260920-0911_Qwen__Qwen3-32B-AWQ_B5_t15benchmark_s42"
BENCH = ROOT / "data/benchmarks/t15_benchmark.jsonl"
RATINGS = ROOT / "results/error_analysis/t19_expert_ratings_long.jsonl"
OUT_MD = ROOT / "results/tables/t22_statistical_comparison.md"
OUT_ITEMS = ROOT / "results/error_analysis/t22_item_level_outcomes.jsonl"
N_BOOT, SEED = 10000, 42
N_RATERS = len({json.loads(l)["rater"] for l in RATINGS.read_text(encoding="utf-8").splitlines() if l.strip()})
SEV = {"none": 0, "minor": 1, "moderate": 2, "major": 3}


def jl(p):
    return [json.loads(l) for l in Path(p).read_text(encoding="utf-8").splitlines() if l.strip()]


def flag_of(q):
    return getattr(q.flag, "value", q.flag)


def boot_ci(d, rng=None, stat=np.mean):
    """Percentile bootstrap CI. Seeded per call (the `rng` argument is ignored) so the same data
    give the same interval in every script and table that reports it."""
    d = np.asarray(d, float)
    rng = np.random.default_rng(SEED)
    idx = rng.integers(0, len(d), (N_BOOT, len(d)))
    b = stat(d[idx], axis=1)
    return np.percentile(b, 2.5), np.percentile(b, 97.5)


def mcnemar(a, b):
    """Exact McNemar on paired binary vectors; returns (a-only, b-only, p)."""
    a, b = np.asarray(a, bool), np.asarray(b, bool)
    n10, n01 = int((a & ~b).sum()), int((~a & b).sum())
    p = binomtest(n10, n10 + n01, 0.5).pvalue if n10 + n01 else 1.0
    return n10, n01, p


def holm(ps):
    ps = np.asarray(ps, float)
    order = np.argsort(ps)
    adj = np.empty(len(ps))
    run = 0.0
    for rank, i in enumerate(order):
        run = max(run, (len(ps) - rank) * ps[i])
        adj[i] = min(run, 1.0)
    return adj


def load_items():
    bench = {b["item_id"]: b for b in jl(BENCH)}
    rows = []
    for (model, cond), run in RUNS.items():
        resp = {r["item_id"]: r for r in jl(ROOT / f"runs/{run}/responses.jsonl")}
        trace = {t["item_id"]: t for t in jl(ROOT / f"runs/{run}/guardrail_traces.jsonl")}
        for iid, b in bench.items():
            text = resp[iid]["response_text"]
            qc = quran_validator.validate_text(text) + hadith_validator.validate_text(text)
            flags = [flag_of(q) for q in qc]
            t = trace[iid]
            claims = t.get("claims") or []
            rows.append(dict(
                item_id=iid, stratum=b["stratum"], language=b["language"], model=model, condition=cond,
                n_citations=len(qc), n_not_verified=sum(f != "verified" for f in flags),
                any_not_verified=int(any(f != "verified" for f in flags)),
                any_citation=int(len(qc) > 0),
                completion_tokens=resp[iid]["completion_tokens"], latency_s=resp[iid]["latency_ms"] / 1000,
                action=t["action"] if cond == "B5" else None,
                frac_supported=(sum(c["verdict"] == "supported" for c in claims) / len(claims)) if claims else np.nan,
            ))
    return pd.DataFrame(rows)


def main():
    rng = np.random.default_rng(SEED)
    df = load_items()
    df.to_json(OUT_ITEMS, orient="records", lines=True, force_ascii=False)
    W = lambda col, m, c: df[(df.model == m) & (df.condition == c)].set_index("item_id")[col]
    md = ["# T22 — Statistical comparison", "",
          "DG-9 (resolved 2026-09-30): item-level paired bootstrap CIs + exact McNemar, Holm-corrected within each family.",
          f"Percentile bootstrap, {N_BOOT} resamples of whole items, seed {SEED}. Differences are always second minus first.",
          f"Automated outcomes: n=41 items (single seed, greedy decoding). Scholar outcomes: n=12 items, mean of {N_RATERS} raters.",
          "T11 'not verified' = a Qur'an/Hadith citation the deterministic validator could not verify (misquoted or non-existent);",
          "T21 showed this validator misses wrong-but-real citations, so it is a lower bound on citation error, not a correctness measure.",
          "Citation rows use the current T11 parser, which reads Arabic-form citations since the 2026-09-30 fix; B5 action rows use the",
          "actions stored in the runs (pre-fix). Post-fix actions are in `t11_arabic_parser_revalidation.md` (1-2 items change per model).", ""]

    # ---- Family A: automated, paired binary ----
    fam = []
    def binrow(label, a, b):
        a, b = a.align(b, join="inner")
        n10, n01, p = mcnemar(a.values, b.values)
        lo, hi = boot_ci((b - a).values, rng)
        fam.append([label, len(a), a.mean(), b.mean(), b.mean() - a.mean(), lo, hi, n10, n01, p])
    for m in ("8B", "14B", "32B"):
        binrow(f"{m}: response has an unverified citation, B0 vs RAG (B2/B5 generation)", W("any_not_verified", m, "B0"), W("any_not_verified", m, "B5"))
    binrow("8B: response has an unverified citation, B0 vs B1", W("any_not_verified", "8B", "B0"), W("any_not_verified", "8B", "B1"))
    for m in ("8B", "14B", "32B"):
        binrow(f"{m}: response cites any Qur'an/Hadith reference, B0 vs RAG", W("any_citation", m, "B0"), W("any_citation", m, "B5"))
    P = lambda m: (W("action", m, "B5") == "pass").astype(int)
    A = lambda m: (W("action", m, "B5") == "abstain").astype(int)
    for a, b in (("8B", "14B"), ("8B", "32B"), ("14B", "32B")):
        binrow(f"B5 action = pass, {a} vs {b}", P(a), P(b))
    for a, b in (("8B", "14B"), ("8B", "32B"), ("14B", "32B")):
        binrow(f"B5 action = abstain, {a} vs {b}", A(a), A(b))
    adj = holm([f[-1] for f in fam])
    md += ["## A. Automated paired binary outcomes (n=41 items)", "",
           "| Comparison | n | First | Second | Δ | 95% CI | Discordant (first-only / second-only) | McNemar p | Holm p |",
           "|---|---:|---:|---:|---:|---|---|---:|---:|"]
    for f, ap in zip(fam, adj):
        md.append(f"| {f[0]} | {f[1]} | {f[2]:.2f} | {f[3]:.2f} | {f[4]:+.2f} | [{f[5]:+.2f}, {f[6]:+.2f}] | {f[7]} / {f[8]} | {f[9]:.3f} | {ap:.3f} |")

    # ---- Family B: automated, paired continuous ----
    fam = []
    def controw(label, a, b):
        a, b = a.align(b, join="inner")
        d = (b - a).dropna()
        lo, hi = boot_ci(d.values, rng)
        p = wilcoxon(d.values).pvalue if (d != 0).any() else 1.0
        dz = d.mean() / d.std(ddof=1) if d.std(ddof=1) > 0 else np.nan
        fam.append([label, len(d), a[d.index].mean(), b[d.index].mean(), d.mean(), lo, hi, dz, p])
    controw("8B completion tokens, B0 vs B1", W("completion_tokens", "8B", "B0"), W("completion_tokens", "8B", "B1"))
    controw("8B latency (s), B0 vs B1", W("latency_s", "8B", "B0"), W("latency_s", "8B", "B1"))
    for m in ("8B", "14B", "32B"):
        controw(f"{m} completion tokens, B0 vs RAG", W("completion_tokens", m, "B0"), W("completion_tokens", m, "B5"))
    for a, b in (("8B", "14B"), ("8B", "32B"), ("14B", "32B")):
        controw(f"B5 share of claims NLI-supported, {a} vs {b}", W("frac_supported", a, "B5"), W("frac_supported", b, "B5"))
    adj = holm([f[-1] for f in fam])
    md += ["", "## B. Automated paired continuous outcomes (n=41 items)", "",
           "| Comparison | n | First mean | Second mean | Δ | 95% CI | Effect size dz | Wilcoxon p | Holm p |", "|---|---:|---:|---:|---:|---|---:|---:|---:|"]
    for f, ap in zip(fam, adj):
        md.append(f"| {f[0]} | {f[1]} | {f[2]:.2f} | {f[3]:.2f} | {f[4]:+.2f} | [{f[5]:+.2f}, {f[6]:+.2f}] | {f[7]:+.2f} | {f[8]:.3f} | {ap:.3f} |")

    # ---- C: B5 action rates by stratum, with item-bootstrap CIs ----
    md += ["", "## C. B5 outcome rates by stratum (8B; bootstrap 95% CI over items in the stratum)", "",
           "| Stratum | n | Pass | Abstain | Regenerate | Escalate | Unverified citation |", "|---|---:|---|---|---|---|---|"]
    b5 = df[(df.model == "8B") & (df.condition == "B5")]
    def rate(x):
        x = np.asarray(x, float); lo, hi = boot_ci(x, rng)
        return f"{x.mean():.2f} [{lo:.2f}, {hi:.2f}]"
    for st, g in list(b5.groupby("stratum")) + [("ALL", b5)]:
        md.append(f"| {st} | {len(g)} | " + " | ".join(rate(g.action == a) for a in ("pass", "abstain", "regenerate_with_evidence", "escalate")) + f" | {rate(g.any_not_verified)} |")
    md += ["", "Strata have 5-9 items each, so these intervals are wide by construction; stratum differences are descriptive, not tested."]

    # ---- D: run-to-run reproducibility (two 32B B5 runs, same seed/config) ----
    t1 = {t["item_id"]: t["action"] for t in jl(ROOT / f"runs/{RUNS[('32B', 'B5')]}/guardrail_traces.jsonl")}
    t2 = {t["item_id"]: t["action"] for t in jl(ROOT / f"runs/{RERUN_32B}/guardrail_traces.jsonl")}
    r1 = {r["item_id"]: r["response_text"] for r in jl(ROOT / f"runs/{RUNS[('32B', 'B5')]}/responses.jsonl")}
    r2 = {r["item_id"]: r["response_text"] for r in jl(ROOT / f"runs/{RERUN_32B}/responses.jsonl")}
    same_a = sum(t1[i] == t2[i] for i in t1); same_t = sum(r1[i] == r2[i] for i in r1)
    md += ["", "## D. Run-to-run reproducibility (two independent 32B-AWQ B5 runs, identical config and seed)", "",
           f"- Identical response text: {same_t}/41 items. Identical B5 action: {same_a}/41 items.",
           "- Items whose action changed: " + (", ".join(f"{i} ({t2[i]} -> {t1[i]})" for i in t1 if t1[i] != t2[i]) or "none") + ".",
           "- This is the only test-retest evidence available; greedy decoding was not bit-reproducible on this AWQ model, so single-item differences between conditions should not be over-read."]

    # ---- E: scholar ratings, paired by item ----
    r = pd.DataFrame(jl(RATINGS)); r = r[r.value.notna()].copy()
    r["model"] = r.run_label.str.split("_").str[0]; r["condition"] = r.run_label.str.split("_").str[1]
    conv = {"quality": float, "source": float, "severity": SEV.get,
            "evidence": {"supported": 1.0, "partly": 0.5, "unsupported": 0.0}.get}
    def item_means(field, raters=None):
        x = r[r.field == field].copy()
        if raters is not None:
            x = x[x.rater.isin(raters)]
        x["v"] = x.value.map(conv[field]).astype(float)
        return x.groupby(["item_id", "model", "condition"]).v.mean().unstack(["model", "condition"])
    labels = {"quality": "Factual quality (1-5, higher better)", "source": "Source appropriateness (1-5, higher better)",
              "severity": "Error severity (0-3, lower better)", "evidence": "Evidence support (0-1, higher better)"}
    fam = []
    raters = sorted(r.rater.unique())
    for f in conv:
        m = item_means(f)
        d = (m[("8B", "B5")] - m[("8B", "B0")]).dropna()
        lo, hi = boot_ci(d.values, rng)
        p = wilcoxon(d.values).pvalue if (d != 0).any() else 1.0
        dz = d.mean() / d.std(ddof=1)
        loo = []
        for out in raters:
            mm = item_means(f, [x for x in raters if x != out])
            loo.append((mm[("8B", "B5")] - mm[("8B", "B0")]).mean())
        fam.append([labels[f], len(d), m[("8B", "B0")][d.index].mean(), m[("8B", "B5")][d.index].mean(), d.mean(), lo, hi, dz, p, min(loo), max(loo)])
    adj = holm([x[8] for x in fam])
    md += ["", f"## E. Scholar ratings: 8B B0 vs 8B B5, paired by item (n=12 items, mean of {N_RATERS} raters)", "",
           "| Outcome | n | B0 | B5 | Δ | 95% CI | dz | Wilcoxon p | Holm p | Δ range leaving one rater out |", "|---|---:|---:|---:|---:|---|---:|---:|---:|---|"]
    for f, ap in zip(fam, adj):
        md.append(f"| {f[0]} | {f[1]} | {f[2]:.2f} | {f[3]:.2f} | {f[4]:+.2f} | [{f[5]:+.2f}, {f[6]:+.2f}] | {f[7]:+.2f} | {f[8]:.3f} | {ap:.3f} | {f[9]:+.2f} to {f[10]:+.2f} |")
    sev = item_means("severity")
    bad0, bad5 = (sev[("8B", "B0")] >= 2).astype(int), (sev[("8B", "B5")] >= 2).astype(int)
    n10, n01, p = mcnemar(bad0.values, bad5.values)
    md += ["", f"Scholar-bad (mean severity >= 2.0): B0 {bad0.sum()}/12, B5 {bad5.sum()}/12; discordant {n10} (B0 only) / {n01} (B5 only); exact McNemar p={p:.3f}.",
           "", "### Model size under B5 (scholar ratings; each larger model was rated on only 6 of the 12 items)", "",
           "| Comparison | n items | Quality Δ | 95% CI | Severity Δ | 95% CI |", "|---|---:|---:|---|---:|---|"]
    q = item_means("quality")
    for big in ("14B", "32B"):
        dq = (q[(big, "B5")] - q[("8B", "B5")]).dropna(); ds = (sev[(big, "B5")] - sev[("8B", "B5")]).dropna()
        a, b = boot_ci(dq.values, rng); c, e = boot_ci(ds.values, rng)
        md.append(f"| {big} B5 vs 8B B5 | {len(dq)} | {dq.mean():+.2f} | [{a:+.2f}, {b:+.2f}] | {ds.mean():+.2f} | [{c:+.2f}, {e:+.2f}] |")
    md += ["", "n=6 per comparison and the two larger models were rated on different items, so 14B and 32B cannot be compared with each other here."]
    # ---- F: what the scholar "B5" cards actually are ----
    act = W("action", "8B", "B5")
    items12 = q.index
    passed = [i for i in items12 if act[i] == "pass"]
    held = [i for i in items12 if act[i] != "pass"]
    g = lambda ids, m: m[("8B", "B5")][ids]
    md += ["", "## F. Caveat on the scholar 'B5' cards: they show the generated answer, not the guardrail's decision", "",
           "`scripts/prepare_t20_scholar_cards.py` put each run's raw `response_text` on the card. For B5 that is the retrieval-augmented",
           "generation before the abstain/regenerate/escalate policy is applied. Section E is therefore a comparison of plain generation (B0)",
           "with retrieval-augmented generation, not a measurement of the full guardrail's effect on what a user would see.", "",
           "| 8B B5 action on the 12 rated items | Items | Scholar quality of the generated answer | Scholar severity | Scholar-bad |", "|---|---:|---:|---:|---|",
           f"| pass (answer would be shown) | {len(passed)} | {g(passed, q).mean():.2f} | {g(passed, sev).mean():.2f} | {int((g(passed, sev) >= 2).sum())}/{len(passed)} |",
           f"| abstain / regenerate / escalate (answer withheld or redone) | {len(held)} | {g(held, q).mean():.2f} | {g(held, sev).mean():.2f} | {int((g(held, sev) >= 2).sum())}/{len(held)} |",
           "", "No scholar rated an abstention message or a regenerated answer, so the user-facing quality of B5 is not measured by this study."]
    md += [
           "", "## Reading guide", "",
           "- Holm correction is applied within each table (A, B, E) separately; the families were fixed in this script before results were inspected, but the scholar B0-vs-B5 contrast had already been seen uncorrected in T21.",
           "- One seed and one benchmark draw: intervals reflect item sampling only, not seed or prompt variance.",
           "- Percentile bootstrap intervals are known to be too narrow at n=12; treat section E intervals as optimistic."]
    OUT_MD.write_text("\n".join(md) + "\n", encoding="utf-8")
    print("\n".join(md))


if __name__ == "__main__":
    main()
