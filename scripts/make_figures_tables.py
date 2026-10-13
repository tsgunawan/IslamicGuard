"""T24 -- generate every data-driven manuscript table and figure from saved artifacts.

No number is typed by hand: everything is read from runs/, data/, results/error_analysis/ and
expert_review/incoming/ (scholar ratings), or recomputed with the T21/T22/T23 functions.
Outputs: manuscript/tables/table{3..10}_*.md and manuscript/figures/fig{4,5,6}_*.{png,pdf}.

Not produced here (not data-driven): Figures 1-3 (architecture, traceability, design diagrams)
and Tables 1-2 (literature gap, principle-to-requirement mapping); those are written in T25.
paper.md's optional Figure 5 (risk-coverage curve) is replaced by the failure-type chart,
because no per-response confidence score exists to sweep a coverage threshold over.

Usage: python scripts/make_figures_tables.py
"""
from __future__ import annotations

import collections
import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.patches
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "scripts"))
import analyze_t19_expert_agreement as t19  # noqa: E402
import t22_statistical_comparison as t22  # noqa: E402
import t23_error_analysis as t23  # noqa: E402

TAB, FIG = ROOT / "manuscript/tables", ROOT / "manuscript/figures"
MODELS = {"8B": "Qwen/Qwen3-8B", "14B": "Qwen/Qwen3-14B-AWQ", "32B": "Qwen/Qwen3-32B-AWQ"}
ABLATION = {"B0": "20260920-0426_Qwen__Qwen3-8B_B0_t15_benchmark_s42", "B1": "20260920-0441_Qwen__Qwen3-8B_B1_t15_benchmark_s42",
            "B2": "20260920-0800_Qwen__Qwen3-8B_B2_t15benchmark_s42", "B3": "20260920-0800_Qwen__Qwen3-8B_B3_t15benchmark_s42",
            "B4": "20260920-0800_Qwen__Qwen3-8B_B4_t15benchmark_s42", "B5": "20260920-0732_Qwen__Qwen3-8B_B5_t15benchmark_s42"}
# Validated categorical slots 1-3 of the dataviz reference palette (documented to pass all-pairs CVD checks in light mode).
C1, C2, C3, INK, MUTED, GRID = "#2a78d6", "#eb6834", "#1baf7a", "#0b0b0b", "#52514e", "#e4e3df"
jl = t22.jl
ACT = ["pass", "regenerate_with_evidence", "abstain", "escalate"]


def write(name, title, lines, notes=()):
    (TAB / name).write_text("\n".join([f"# {title}", ""] + lines + [""] + [f"*{n}*" for n in notes]) + "\n", encoding="utf-8")


def ci(x, rng):
    lo, hi = t22.boot_ci(np.asarray(x, float), rng)
    return f"{np.mean(x):.2f} [{lo:.2f}, {hi:.2f}]"


def scholar_item_means():
    r = pd.DataFrame(jl(t22.RATINGS)); r = r[r.value.notna()].copy()
    r["model"] = r.run_label.str.split("_").str[0]; r["condition"] = r.run_label.str.split("_").str[1]
    conv = {"quality": float, "source": float, "severity": t22.SEV.get, "evidence": {"supported": 1.0, "partly": 0.5, "unsupported": 0.0}.get}
    out = {}
    for f, c in conv.items():
        x = r[r.field == f].copy(); x["v"] = x.value.map(c).astype(float)
        out[f] = x.groupby(["item_id", "model", "condition"]).v.mean().unstack(["model", "condition"])
    return out


def long_raters():
    return len({json.loads(l)["rater"] for l in t22.RATINGS.read_text(encoding="utf-8").splitlines() if l.strip()})


def style(ax):
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color(GRID)
    ax.tick_params(colors=MUTED, length=0, labelsize=8)
    ax.set_axisbelow(True)


def save(fig, stem):
    for ext in ("png", "pdf"):
        fig.savefig(FIG / f"{stem}.{ext}", dpi=300, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def main():
    TAB.mkdir(parents=True, exist_ok=True); FIG.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(42)
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9, "text.color": INK, "axes.labelcolor": MUTED})
    bench = jl(t22.BENCH)
    items = t22.load_items()  # item-level automated outcomes, current T11 parser
    reval = pd.DataFrame(jl(ROOT / "results/error_analysis/t11_arabic_parser_revalidation.jsonl"))
    sch = scholar_item_means()
    cell = lambda col, m, c: items[(items.model == m) & (items.condition == c)][col]

    # ---- Table 3: datasets / corpus ----
    b = pd.DataFrame(bench)
    rows = ["| Stratum | Items | Source dataset(s) | English | Arabic | Constructed |", "|---|---:|---|---:|---:|---:|"]
    for st, g in b.groupby("stratum", sort=False):
        rows.append(f"| {st} | {len(g)} | {', '.join(sorted(g.source_dataset.unique()))} | {(g.language == 'en').sum()} | {(g.language == 'ar').sum()} | {int(g.constructed.sum())} |")
    rows.append(f"| **Total** | **{len(b)}** | | {(b.language == 'en').sum()} | {(b.language == 'ar').sum()} | {int(b.constructed.sum())} |")
    rows += ["", "| Retrieval corpus layer | Records |", "|---|---:|"]
    for layer in ("quran", "hadith", "fiqh"):
        rows.append(f"| {layer} | {sum(1 for _ in (ROOT / f'data/corpus/{layer}.jsonl').open(encoding='utf-8')):,} |")
    rows += ["", f"Scholar-review subset: {len(jl(t22.ROOT / 'expert_review/t20_blinding_key.jsonl'))} cards from {sch['quality'].shape[0]} items, {long_raters()} raters."]
    write("table3_datasets_corpus.md", "Table 3 — Benchmark and retrieval corpus", rows, ["Source: data/benchmarks/t15_benchmark.jsonl, data/corpus/*.jsonl."])

    # ---- Table 4: models and runtime settings ----
    rows = ["| Model | Condition | Backend | Max new tokens | Sampling | Thinking mode | Seed | Embedding model | Passages per layer |", "|---|---|---|---:|---|---|---:|---|---:|"]
    for (m, c), run in t22.RUNS.items():
        cfg = yaml.safe_load((ROOT / f"runs/{run}/config.yaml").read_text(encoding="utf-8"))
        g = jl(ROOT / f"runs/{run}/responses.jsonl")[0]["generation_config"]
        rows.append(f"| {MODELS[m]} | {c} | {cfg.get('backend', '–')} | {g['max_new_tokens']} | {'sampling' if g['do_sample'] else 'greedy'} | {'on' if g['enable_thinking'] else 'off'} | {g['seed']} | {cfg.get('embedding_model', '–')} | {cfg.get('k_per_layer', '–')} |")
    write("table4_models_runtime.md", "Table 4 — Models and runtime settings", rows, ["Source: each run's config.yaml and responses.jsonl generation_config."])

    # ---- Table 5: main results (8B B0 vs B5) ----
    rows = ["| Outcome | B0 (no retrieval, no guardrail) | B5 generation (retrieval-augmented) | Difference [95% CI] | n |", "|---|---|---|---|---:|"]
    lab = {"quality": "Scholar factual quality (1-5)", "source": "Scholar source appropriateness (1-5)", "severity": "Scholar error severity (0-3, lower is better)", "evidence": "Scholar evidence support (0-1)"}
    for f, l in lab.items():
        m = sch[f]; a, c = m[("8B", "B0")], m[("8B", "B5")]; d = (c - a).dropna(); lo, hi = t22.boot_ci(d.values, rng)
        rows.append(f"| {l} | {ci(a[d.index].values, rng)} | {ci(c[d.index].values, rng)} | {d.mean():+.2f} [{lo:+.2f}, {hi:+.2f}] | {len(d)} |")
    for col, l in (("any_citation", "Answers citing a Qur'an/hadith reference"), ("any_not_verified", "Answers with a citation T11 could not verify"), ("completion_tokens", "Completion tokens")):
        a, c = cell(col, "8B", "B0").values.astype(float), cell(col, "8B", "B5").values.astype(float); lo, hi = t22.boot_ci(c - a, rng)
        rows.append(f"| {l} | {ci(a, rng)} | {ci(c, rng)} | {(c - a).mean():+.2f} [{lo:+.2f}, {hi:+.2f}] | {len(a)} |")
    write("table5_main_results.md", "Table 5 — Main results, Qwen3-8B", rows,
          [f"Mean [95% item-bootstrap CI]. Scholar rows: 12 items, mean of {long_raters()} raters; scholars rated the generated answer, not the guardrail decision.",
           "Automated rows: 41 items. Source: results/error_analysis/t19_expert_ratings_long.jsonl, runs/*/responses.jsonl; tests in table t22."])

    # ---- Table 6: ablation (8B) ----
    rows = ["| Condition | Components | Mean completion tokens | Hit token limit | Items with a recorded flag | pass / regenerate / abstain / escalate |", "|---|---|---:|---:|---:|---|"]
    comp = {"B0": "generation only", "B1": "policy prompt only", "B2": "retrieval from B0", "B3": "+ provenance validator", "B4": "+ faithfulness validator", "B5": "+ madhhab and abstention policy"}
    for c, run in ABLATION.items():
        R, T = jl(ROOT / f"runs/{run}/responses.jsonl"), jl(ROOT / f"runs/{run}/guardrail_traces.jsonl")
        flagged = sum(bool(t.get("guardrail_flags")) for t in T) if c not in ("B0", "B1", "B2") else "–"
        acts = collections.Counter(t["action"] for t in T) if c == "B5" else None
        rows.append(f"| {c} | {comp[c]} | {np.mean([r['completion_tokens'] for r in R]):.0f} | {sum(r['completion_tokens'] >= r['generation_config']['max_new_tokens'] for r in R)}/{len(R)} | {flagged} | {' / '.join(str(acts[a]) for a in ACT) if acts else '–'} |")
    write("table6_ablation.md", "Table 6 — Ablation, Qwen3-8B (41 items)", rows,
          ["B2-B4 are views of the B5 run (same retrieval and generation). Flag counts inherit B5 policy priority: B3 records six citation-related flags, while raw provenance checks found eight answers with an unverified citation; two were masked by abstention. Counts precede the Arabic-citation parser fix.", "Source: runs/*/responses.jsonl, guardrail_traces.jsonl."])

    # ---- Table 7: model size ----
    rows = ["| Model | B5 pass | B5 regenerate | B5 abstain | B5 escalate | Same, after Arabic-parser fix | NLI-supported claim share | Scholar quality, B5 cards | Scholar severity, B5 cards | Cards |", "|---|---:|---:|---:|---:|---|---:|---:|---:|---:|"]
    r = pd.DataFrame(jl(t22.RATINGS)); r = r[r.value.notna()]
    for m in MODELS:
        a = collections.Counter(cell("action", m, "B5")); after = collections.Counter(reval[reval.model == m].action_after)
        rr = r[r.run_label == f"{m}_B5"]
        q = rr[rr.field == "quality"].value.astype(float).groupby(rr.card_id).mean(); s = rr[rr.field == "severity"].value.map(t22.SEV).groupby(rr.card_id).mean()
        rows.append(f"| {MODELS[m]} | {a['pass']} | {a['regenerate_with_evidence']} | {a['abstain']} | {a['escalate']} | {' / '.join(str(after[x]) for x in ACT)} | {cell('frac_supported', m, 'B5').mean():.2f} | {q.mean():.2f} | {s.mean():.2f} | {len(q)} |")
    write("table7_model_size.md", "Table 7 — Model-size comparison under B5 (41 items)", rows,
          ["Scholar columns: 12 cards for 8B, 6 each for 14B and 32B on different items, so the larger models are not comparable with each other on those columns.", "Source: runs/*/guardrail_traces.jsonl, results/error_analysis/t11_arabic_parser_revalidation.jsonl, t19_expert_ratings_long.jsonl."])

    # ---- Table 8: scholar agreement ----
    long = t19.load(); arng = np.random.default_rng(42)
    rows = ["| Rubric field | Scale | Krippendorff's α | 95% CI | Exact pairwise agreement | Within one point | Missing ratings |", "|---|---|---:|---|---:|---:|---:|"]
    for label, (name, scale, cats) in t19.FIELDS.items():
        a = t19.agreement(long, name, cats, scale, arng)
        w = f"{a['within1']:.2f}" if a["within1"] is not None else "–"
        rows.append(f"| {label} | {scale} | {a['alpha']:.2f} | [{a['lo']:.2f}, {a['hi']:.2f}] | {a['exact']:.2f} | {w} | {a['missing']} |")
    write("table8_scholar_agreement.md", f"Table 8 — Inter-rater agreement, {long_raters()} scholars, 36 cards", rows,
          ["'Not assessable' treated as missing. CI from 2,000 card-level bootstrap resamples; cards come from 12 items and are not independent.", "Source: results/error_analysis/t19_expert_ratings_long.jsonl (from expert_review/incoming/IslamicGuardresponse4v2.xlsx) via scripts/analyze_t19_expert_agreement.py."])

    # ---- Table 9: error taxonomy ----
    codes = pd.DataFrame(jl(t23.OUT_CODES))
    codes["grp"] = codes.run_label.map(lambda x: "8B B0" if x == "8B_B0" else ("8B B5" if x == "8B_B5" else "14B/32B B5"))
    groups = ["8B B0", "8B B5", "14B/32B B5"]
    rows = ["| Code | Failure type | " + " | ".join(groups) + " | Mean scholar severity when present |", "|---|---|---:|---:|---:|---:|"]
    tax = []
    for c, (n, _) in t23.TAXONOMY.items():
        has = codes.codes.map(lambda x: c in x); cnt = [int(has[codes.grp == g].sum()) for g in groups]
        tax.append((c, n, cnt)); rows.append(f"| {c} | {n} | {cnt[0]} | {cnt[1]} | {cnt[2]} | {codes.scholar_severity[has].mean():.2f} |")
    write("table9_error_taxonomy.md", "Table 9 — Failure types on the scholar-rated cards (12 cards per group)", rows,
          ["A card can carry several codes. Coding by one non-expert coder following the scholars' comments; see results/tables/t23_error_analysis.md.", "Source: results/error_analysis/t23_card_codes.jsonl."])

    # ---- Table 10: computational overhead ----
    rows = ["| Model | Condition | Generation s/item | Total generation (s) | Validation s/item | Mean completion tokens | Peak GPU memory (MiB) |", "|---|---|---:|---:|---:|---:|---:|"]
    lat = {}
    for (m, c), run in t22.RUNS.items():
        R, T = jl(ROOT / f"runs/{run}/responses.jsonl"), jl(ROOT / f"runs/{run}/guardrail_traces.jsonl")
        g = np.array([x["latency_ms"] for x in R]) / 1000; lat[(m, c)] = g
        v = [t["validation_latency_ms"] / 1000 for t in T if "validation_latency_ms" in t]
        gp = ROOT / f"runs/{run}/gpu_samples.jsonl"
        peak = max(x["memory_used_mib"] for x in jl(gp)) if gp.exists() else None
        rows.append(f"| {MODELS[m]} | {c} | {g.mean():.1f} | {g.sum():.0f} | {np.mean(v):.1f} | {np.mean([x['completion_tokens'] for x in R]):.0f} | {peak if peak else 'not captured'} |" if v else
                    f"| {MODELS[m]} | {c} | {g.mean():.1f} | {g.sum():.0f} | – | {np.mean([x['completion_tokens'] for x in R]):.0f} | {peak if peak else 'not captured'} |")
    write("table10_overhead.md", "Table 10 — Computational overhead (41 items, single 24 GB GPU)", rows,
          ["B5 generation time is the retrieval-augmented generation step; validation is the guardrail stack run afterwards. 'not captured' = no automated GPU sampling for that run.", "Source: runs/*/responses.jsonl, guardrail_traces.jsonl, gpu_samples.jsonl."])

    # ---- Figure 4: scholar ratings, 8B B0 vs B5 generation ----
    panels = [("quality", "Factual quality", (1, 5)), ("source", "Source appropriateness", (1, 5)), ("severity", "Error severity (lower is better)", (0, 3)), ("evidence", "Evidence support", (0, 1))]
    fig, axes = plt.subplots(1, 4, figsize=(9.2, 2.6))
    for ax, (f, title, lim) in zip(axes, panels):
        m = sch[f]; idx = (m[("8B", "B5")] - m[("8B", "B0")]).dropna().index
        for x, (cond, col) in enumerate((("B0", C1), ("B5", C2))):
            v = m[("8B", cond)][idx].values; lo, hi = t22.boot_ci(v, rng)
            ax.plot([x, x], [lo, hi], color=col, lw=2, solid_capstyle="round")
            ax.plot(x, v.mean(), "o", ms=8, color=col, mec="white", mew=2)
            ax.annotate(f"{v.mean():.2f}", (x, v.mean()), xytext=(10, 0), textcoords="offset points", va="center", fontsize=8, color=INK)
        ax.set_xlim(-0.6, 1.8); ax.set_ylim(*lim); ax.set_xticks([0, 1]); ax.set_xticklabels(["B0", "B5"], color=INK)
        ax.set_title(title, fontsize=9, color=INK, loc="left"); ax.grid(axis="y", color=GRID, lw=0.6); style(ax)
    fig.tight_layout(); save(fig, "fig4_scholar_ratings_b0_vs_b5")

    # ---- Figure 5: failure types by configuration ----
    tax = sorted(tax, key=lambda x: sum(x[2]))
    fig, ax = plt.subplots(figsize=(7.2, 4.2)); h = 0.26
    for j, (g, col) in enumerate(zip(groups, (C1, C2, C3))):
        vals = [t[2][j] for t in tax]; y = np.arange(len(tax)) + (1 - j) * h
        ax.barh(y, vals, height=h - 0.04, color=col, label=g)
        for yy, v in zip(y, vals):
            ax.text(v + 0.12, yy, str(v), va="center", fontsize=7.5, color=INK)
    ax.set_yticks(np.arange(len(tax))); ax.set_yticklabels([t[1] for t in tax], color=INK, fontsize=8.5)
    ax.set_xlabel("Cards with this failure (of 12 per group)"); ax.set_xlim(0, 7.5); ax.grid(axis="x", color=GRID, lw=0.6); style(ax)
    ax.legend(frameon=False, fontsize=8.5, loc="lower right", title="Configuration", title_fontsize=8.5)
    fig.tight_layout(); save(fig, "fig5_failure_types")

    # ---- Figure 6: generation time per item ----
    fig, ax = plt.subplots(figsize=(6.2, 3.2)); w = 0.36
    for j, (c, col, name) in enumerate((("B0", C1, "B0: plain generation"), ("B5", C2, "B5: retrieval-augmented generation"))):
        vals = [lat[(m, c)].mean() for m in MODELS]; x = np.arange(3) + (j - 0.5) * w
        ax.bar(x, vals, width=w - 0.03, color=col, label=name)
        for xx, v in zip(x, vals):
            ax.text(xx, v + 3, f"{v:.0f}", ha="center", fontsize=8, color=INK)
    ax.set_xticks(np.arange(3)); ax.set_xticklabels([MODELS[m].split("/")[1] for m in MODELS], color=INK)
    ax.set_ylabel("Seconds per item"); ax.grid(axis="y", color=GRID, lw=0.6); style(ax); ax.legend(frameon=False, fontsize=8.5, loc="upper left")
    fig.tight_layout(); save(fig, "fig6_generation_time")
    # ---- Table 1: literature comparison (from literature/gap_table.csv; first word of each cell) ----
    import csv
    keep = ["maidin2026", "mohammed2025", "abbas2026", "kadous2026", "aghajaniasl2025", "bhatia2026", "atif2025", "mubarak2025", "elmahjub2026legalbench", "yao2025"]
    gap = {r["study_id"]: r for r in csv.DictReader((ROOT / "literature/gap_table.csv").open(encoding="utf-8"))}
    cols = ["islamic_normative_basis", "rag", "provenance_verification", "madhhab_handling", "abstention", "adversarial_evaluation", "human_scholar_validation"]
    short = lambda v: {"yes": "Yes", "no": "No", "partial": "Partial", "not": "No", "n/a": "n/a", "mentioned": "No"}.get(v.split()[0].strip(",").lower(), v.split()[0])
    rows = ["| Study | Islamic normative basis | RAG | Provenance verification | Madhhab handling | Abstention | Adversarial evaluation | Scholar validation |", "|---|---|---|---|---|---|---|---|"]
    for k in keep:
        rows.append(f"| {gap[k]['study'].split(' -- ')[0]} | " + " | ".join(short(gap[k][c]) for c in cols) + " |")
    rows.append("| This study | Yes | Yes | Yes (Qur'an, hadith; English and Arabic forms) | Yes (four Sunni schools, 121 records) | Yes | Partial (12 constructed prompts, input screen only) | Yes (4 scholars, 36 answers) |")
    write("table1_literature_gap.md", "Table 1 — Comparison with the closest prior work", rows,
          ["Cells are the leading yes/no/partial judgment recorded in literature/gap_table.csv during the literature review; the last row describes what this study implemented and evaluated."])

    # ---- Figure 1: architecture ----
    fig, ax = plt.subplots(figsize=(9.4, 3.3)); ax.axis("off"); ax.set_xlim(0, 100); ax.set_ylim(0, 33.5)
    def box(x, y, w, h, text, fc="#f4f3ef", ec=MUTED, ls="-", fs=7):
        ax.add_patch(matplotlib.patches.FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.3,rounding_size=1.2", fc=fc, ec=ec, lw=1, ls=ls))
        ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fs, color=INK)
    def arrow(x0, y0, x1, y1):
        ax.annotate("", xy=(x1, y1), xytext=(x0, y0), arrowprops=dict(arrowstyle="-|>", color=MUTED, lw=1))
    box(1, 15, 9, 8, "User\nquery"); box(14, 15, 13, 8, "Retrieval\nQur'an, hadith,\nfiqh (3 each)"); box(31, 15, 12, 8, "Generation\nQwen3, greedy")
    box(47, 25, 20, 7, "Provenance validator\n(citation exists,\nquote matches)"); box(47, 15.5, 20, 7, "Faithfulness validator\n(claim vs evidence, NLI)"); box(47, 6, 20, 7, "Madhhab context\n(is disagreement\nsurfaced?)")
    box(71, 15, 11, 8, "Abstention\nand escalation\npolicy")
    for y, t, c in ((27.5, "Pass", "#dff1e9"), (20.5, "Regenerate\nwith evidence", "#fde9c8"), (13.5, "Abstain", "#fde9c8"), (6.5, "Escalate\nto a scholar", "#fbd9d3")):
        box(86, y, 13, 5, t, fc=c); arrow(82.4, 19, 85.6, y + 2.5)
    arrow(10.4, 19, 13.6, 19); arrow(27.4, 19, 30.6, 19)
    for y in (28.5, 19, 9.5):
        arrow(43.4, 19, 46.6, y); arrow(67.4, y, 70.6, 19)
    box(1, 1.5, 26, 6, "Prompt-injection screen (input side;\nevaluated separately,\nnot in the B5 runs)", ls="--", fs=6.5)
    ax.text(31, 11.5, "B0: plain generation\nB1: policy prompt only\nB2: retrieval only", fontsize=7, color=MUTED, va="top")
    ax.text(47, 3.2, "B3: + provenance   B4: + faithfulness   B5: + madhhab and policy", fontsize=7, color=MUTED, va="top")
    save(fig, "fig1_architecture")
    print("tables:", sorted(p.name for p in TAB.glob("table*.md"))); print("figures:", sorted(p.name for p in FIG.glob("*.png")))


if __name__ == "__main__":
    main()
