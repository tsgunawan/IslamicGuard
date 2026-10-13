"""T19/T20: parse the 3-scholar Google Form export, compute inter-rater agreement,
then unblind (via t20_blinding_key.jsonl) for an exploratory B0-vs-B5 comparison.

Usage: python scripts/analyze_t19_expert_agreement.py [xlsx]
"""
import itertools
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import wilcoxon

ROOT = Path(__file__).resolve().parents[1]
XLSX = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "expert_review/incoming/IslamicGuardresponse4v2.xlsx"
KEY = ROOT / "expert_review/t20_blinding_key.jsonl"
OUT_MD = ROOT / "results/tables/t19_expert_agreement.md"
OUT_JSONL = ROOT / "results/error_analysis/t19_expert_ratings_long.jsonl"

FIELDS = {  # English label -> (name, scale, ordered categories or None)
    "Religious-factual quality": ("quality", "ordinal", [1, 2, 3, 4, 5]),
    "Source appropriateness": ("source", "ordinal", [1, 2, 3, 4, 5]),
    "Evidence support": ("evidence", "ordinal", ["unsupported", "partly", "supported"]),
    "Representation of legitimate disagreement": ("ikhtilaf", "nominal", ["omission", "appropriate", "n/a"]),
    "Appropriate boundary action": ("boundary", "nominal", ["appropriate", "escalate", "abstain"]),
    "Error severity": ("severity", "ordinal", ["none", "minor", "moderate", "major"]),
}
MAP = {
    "unsupported": "unsupported", "partly supported": "partly", "supported": "supported",
    "omission or overgeneralization": "omission", "appropriate": "appropriate", "not applicable": "n/a",
    "answer as given is appropriate": "appropriate", "should escalate to a qualified scholar": "escalate",
    "should abstain": "abstain", "none": "none", "minor": "minor", "moderate": "moderate", "major": "major",
}


def norm(name, v):
    if pd.isna(v):
        return None
    full = str(v).strip()
    s = full.split(" / ")[-1].strip()
    if s.lower() == "not assessable":
        return None
    if name in ("quality", "source"):
        return int(float(full.split(" ")[0]))
    return MAP[s.lower()]


def load():
    if not XLSX.exists():
        # Public copies of the repository do not include the raw form export. The long-format
        # file written by this script holds the same ratings (one row per card, rater and field).
        long = pd.DataFrame([json.loads(l) for l in OUT_JSONL.read_text(encoding="utf-8").splitlines()])
        return long[["card_id", "rater", "field", "value"]]
    df = pd.read_excel(XLSX)
    rows = []
    for _, r in df.iterrows():
        rater = r.iloc[2]
        for col in df.columns[3:]:
            cid, rest = col.split(" — ", 1)
            label = rest.split(" / ")[-1]
            if label not in FIELDS:
                continue
            name = FIELDS[label][0]
            rows.append({"card_id": cid, "rater": rater, "field": name, "value": norm(name, r[col])})
    return pd.DataFrame(rows)


def alpha(mat, cats, scale):
    """Krippendorff's alpha. mat: cards x raters, None = missing."""
    idx = {c: i for i, c in enumerate(cats)}
    k = len(cats)
    o = np.zeros((k, k))
    for row in mat:
        vals = [idx[v] for v in row if v is not None]
        m = len(vals)
        if m < 2:
            continue
        for a, b in itertools.permutations(range(m), 2):
            o[vals[a], vals[b]] += 1 / (m - 1)
    n_c = o.sum(1)
    n = n_c.sum()
    if n <= 1:
        return np.nan
    if scale == "nominal":
        d = 1 - np.eye(k)
    else:
        cum = np.cumsum(n_c)
        d = np.zeros((k, k))
        for i in range(k):
            for j in range(k):
                if i != j:
                    lo, hi = min(i, j), max(i, j)
                    d[i, j] = (cum[hi] - (cum[lo] - n_c[lo]) - (n_c[lo] + n_c[hi]) / 2) ** 2
    d_o = (o * d).sum() / n
    d_e = (np.outer(n_c, n_c) * d).sum() / (n * (n - 1))
    return np.nan if d_e == 0 else 1 - d_o / d_e


def agreement(long, name, cats, scale, rng):
    p = long[long.field == name].pivot(index="card_id", columns="rater", values="value")
    p = p.astype(object).where(p.notna(), None)
    mat = p.values.tolist()
    a = alpha(mat, cats, scale)
    boots = []
    for _ in range(2000):
        s = rng.integers(0, len(mat), len(mat))
        b = alpha([mat[i] for i in s], cats, scale)
        if not np.isnan(b):
            boots.append(b)
    ci = (np.percentile(boots, 2.5), np.percentile(boots, 97.5)) if boots else (np.nan, np.nan)
    ex, w1, n = 0, 0, 0
    for row in mat:
        for x, y in itertools.combinations(row, 2):
            if x is None or y is None:
                continue
            n += 1
            ex += x == y
            if scale == "ordinal":
                w1 += abs(cats.index(x) - cats.index(y)) <= 1
    occ = pd.Series([v for r in mat for v in r if v is not None]).value_counts()
    return dict(alpha=a, lo=ci[0], hi=ci[1], exact=ex / n, within1=w1 / n if scale == "ordinal" else None,
                n_cards=len(mat), missing=sum(v is None for r in mat for v in r), min_cat=int(occ.min()), n_cats=len(occ))


def main():
    rng = np.random.default_rng(42)
    long = load()
    raters = sorted(long.rater.unique())
    key = pd.DataFrame([json.loads(l) for l in KEY.read_text().splitlines()])
    md = ["# T19 — scholar-review agreement and unblinded comparison", "",
          f"- Raters: {', '.join(raters)} ({len(raters)}); cards: {long.card_id.nunique()}.",
          "- 'Not assessable' treated as missing (never as a favourable score).",
          "- Krippendorff's alpha (ordinal metric for ordered fields, nominal otherwise); 95% CI from 2000 card-level bootstrap resamples.",
          "- With 36 cards from 12 items (3 responses per item), cards are not fully independent; CIs are indicative only.", "",
          "## 1. Inter-rater agreement", "",
          "| Field | Scale | α | 95% CI | Exact pairwise | Within ±1 | Missing cells | Thinnest category n |",
          "|---|---|---|---|---|---|---|---|"]
    for label, (name, scale, cats) in FIELDS.items():
        r = agreement(long, name, cats, scale, rng)
        w = f"{r['within1']:.2f}" if r["within1"] is not None else "–"
        md.append(f"| {name} | {scale} | {r['alpha']:.2f} | [{r['lo']:.2f}, {r['hi']:.2f}] | {r['exact']:.2f} | {w} | {r['missing']} | {r['min_cat']} |")
    md += ["", "### Pairwise exact agreement by rater pair", "", "| Pair | " + " | ".join(v[0] for v in FIELDS.values()) + " |",
           "|---|" + "---|" * len(FIELDS)]
    for a, b in itertools.combinations(raters, 2):
        cells = []
        for name, _, _ in FIELDS.values():
            p = long[long.field == name].pivot(index="card_id", columns="rater", values="value")[[a, b]].dropna()
            cells.append(f"{(p[a] == p[b]).mean():.2f}")
        md.append(f"| {a}–{b} | " + " | ".join(cells) + " |")
    md += ["", "### Rater tendencies (mean score; higher = more favourable)", "", "| Rater | quality | source | severity (0=none…3=major) |", "|---|---|---|---|"]
    sev = {"none": 0, "minor": 1, "moderate": 2, "major": 3}
    for rt in raters:
        q = long[(long.rater == rt) & (long.field == "quality")].value.dropna().astype(float).mean()
        s = long[(long.rater == rt) & (long.field == "source")].value.dropna().astype(float).mean()
        e = long[(long.rater == rt) & (long.field == "severity")].value.dropna().map(sev).mean()
        md.append(f"| {rt} | {q:.2f} | {s:.2f} | {e:.2f} |")
    # Per-rater profile: offset from the other raters, rank agreement on quality, boundary choices,
    # and use of "not assessable" (missing) across all fields.
    from scipy.stats import spearmanr
    qw = long[long.field == "quality"].pivot(index="card_id", columns="rater", values="value").astype(float)
    md += ["", "### Rater profiles", "",
           "| Rater | Quality minus mean of the other raters | Spearman rho on quality with each other rater | Boundary: appropriate / abstain / escalate | Not-assessable cells (all fields) |",
           "|---|---:|---|---|---:|"]
    for rt in raters:
        others = [x for x in raters if x != rt]
        off = (qw[rt] - qw[others].mean(axis=1)).mean()
        rhos = ", ".join(f"{o} {spearmanr(qw[rt], qw[o], nan_policy='omit')[0]:.2f}" for o in others)
        b = long[(long.rater == rt) & (long.field == "boundary")].value
        na = int(long[long.rater == rt].value.isna().sum())
        md.append(f"| {rt} | {off:+.2f} | {rhos} | {(b == 'appropriate').sum()} / {(b == 'abstain').sum()} / {(b == 'escalate').sum()} | {na} |")

    # ---- unblinding (post-freeze) ----
    wide = long.pivot_table(index=["card_id", "rater"], columns="field", values="value", aggfunc="first").reset_index()
    wide["severity_n"] = wide.severity.map(sev)
    for f in ("quality", "source"):
        wide[f] = pd.to_numeric(wide[f])
    wide["supported"] = wide.evidence.map({"supported": 1, "partly": 0.5, "unsupported": 0}).astype(float)
    wide["escalate_or_abstain"] = wide.boundary.map(lambda x: np.nan if x is None or pd.isna(x) else float(x != "appropriate"))
    card = wide.groupby("card_id")[["quality", "source", "severity_n", "supported", "escalate_or_abstain"]].mean().reset_index().merge(key, on="card_id")
    card["condition"] = card.run_label.str.split("_").str[1]
    card["model"] = card.run_label.str.split("_").str[0]
    long.merge(key, on="card_id").to_json(OUT_JSONL, orient="records", lines=True, force_ascii=False)

    metrics = [("quality", "Factual quality (1–5, ↑)"), ("source", "Source appropriateness (1–5, ↑)"),
               ("severity_n", "Error severity (0–3, ↓)"), ("supported", "Evidence support (0–1, ↑)"),
               ("escalate_or_abstain", "Share of raters wanting escalate/abstain")]
    md += ["", f"## 2. Unblinded comparison (exploratory; card-level means over the {len(raters)} raters)", "",
           "### 2a. Core paired comparison: 8B B0 vs 8B B5 (12 items)", "",
           "| Metric | B0 mean | B5 mean | Δ (B5−B0) | items B5 better / tie / worse | Wilcoxon p |", "|---|---|---|---|---|---|"]
    pv = card[card.model == "8B"].pivot(index="item_id", columns="condition", values=[m for m, _ in metrics])
    for m, lab in metrics:
        b0, b5 = pv[(m, "B0")], pv[(m, "B5")]
        d = (b5 - b0).dropna()
        better = (d < 0) if m == "severity_n" else (d > 0)
        worse = (d > 0) if m == "severity_n" else (d < 0)
        try:
            p = wilcoxon(d).pvalue if (d != 0).sum() > 0 else float("nan")
        except ValueError:
            p = float("nan")
        md.append(f"| {lab} | {b0.mean():.2f} | {b5.mean():.2f} | {d.mean():+.2f} | {better.sum()} / {(d == 0).sum()} / {worse.sum()} | {p:.3f} |")
    md += ["", "### 2b. By stratum (8B B0 → B5, mean factual quality / error severity)", "",
           "| Stratum | Items | Quality B0 → B5 | Severity B0 → B5 |", "|---|---|---|---|"]
    c8 = card[card.model == "8B"]
    for st, g in c8.groupby("stratum"):
        q = g.groupby("condition").quality.mean()
        s = g.groupby("condition").severity_n.mean()
        md.append(f"| {st} | {g.item_id.nunique()} | {q['B0']:.2f} → {q['B5']:.2f} | {s['B0']:.2f} → {s['B5']:.2f} |")
    md += ["", "### 2c. Secondary: B5 by model size (one card per item; different items per size)", "",
           "| Model (B5) | Cards | Quality | Source | Severity |", "|---|---|---|---|---|"]
    for mdl, g in card[card.condition == "B5"].groupby("model"):
        md.append(f"| {mdl} | {len(g)} | {g.quality.mean():.2f} | {g.source.mean():.2f} | {g.severity_n.mean():.2f} |")
    md += ["", "### 2d. Per-item card means (quality / severity)", "", "| Item | Stratum | 8B B0 | 8B B5 | 14B/32B B5 |", "|---|---|---|---|---|"]
    for it, g in card.groupby("item_id"):
        def f(mask):
            x = g[mask]
            return "; ".join(f"{r.quality:.1f}/{r.severity_n:.1f}" for r in x.itertuples()) or "–"
        md.append(f"| {it} | {g.stratum.iloc[0]} | {f(g.run_label == '8B_B0')} | {f(g.run_label == '8B_B5')} | {f(g.model.isin(['14B', '32B']))} |")
    OUT_MD.write_text("\n".join(md) + "\n")
    print("\n".join(md))


if __name__ == "__main__":
    main()
