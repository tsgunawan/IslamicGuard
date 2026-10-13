"""Compare the original 512-token B0 runs with the 2,048-token B0 reruns (truncation confound
raised in T23). Reads saved runs only. Reruns that do not exist yet are reported as pending.

Usage: python scripts/analyze_b0_token_limit.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "scripts"))
import t22_statistical_comparison as t22  # noqa: E402
import t23_error_analysis as t23  # noqa: E402
from src.validators import hadith_validator, quran_validator  # noqa: E402

OUT = ROOT / "results/tables/b0_token_limit_rerun.md"
MODELS = {"8B": "Qwen3-8B", "14B": "Qwen3-14B-AWQ", "32B": "Qwen3-32B-AWQ"}


def find_rerun(tag: str) -> Path | None:
    for d in sorted((ROOT / "runs").glob(f"*_Qwen__{tag}_B0_t15_benchmark_s42")):
        r = d / "responses.jsonl"
        if r.exists() and json.loads(r.read_text(encoding="utf-8").splitlines()[0])["generation_config"]["max_new_tokens"] == 2048:
            return d
    return None


def stats(run: Path):
    R = t22.jl(run / "responses.jsonl")
    lim = R[0]["generation_config"]["max_new_tokens"]
    chk = [quran_validator.validate_text(r["response_text"]) + hadith_validator.validate_text(r["response_text"]) for r in R]
    flag = lambda q: getattr(q.flag, "value", q.flag)
    return dict(
        ids=[r["item_id"] for r in R], text={r["item_id"]: r["response_text"] for r in R},
        tokens=np.array([r["completion_tokens"] for r in R], float), lat=np.array([r["latency_ms"] / 1000 for r in R]),
        trunc=np.array([r["completion_tokens"] >= lim for r in R], float),
        loop=np.array([t23.has_loop(r["response_text"]) for r in R], float),
        cite=np.array([len(c) > 0 for c in chk], float),
        unver=np.array([any(flag(q) != "verified" for q in c) for c in chk], float),
        n_unver=np.array([sum(flag(q) != "verified" for q in c) for c in chk], float))


def main():
    md = ["# B0 rerun with a 2,048-token limit", "",
          "The original B0 runs used a 512-token limit, which cut off most answers (T23). B0 was rerun with 2,048 tokens and otherwise",
          "identical settings (greedy, seed 42, non-thinking). The 512-token runs are kept. The reruns have no scholar ratings.", "",
          "| Model | Limit | Hit the limit | Repetition loop | Mean tokens | Median tokens | s/item | Cites a reference | Has an unverified citation | Unverified citations per answer |",
          "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|"]
    notes = []
    for m, tag in MODELS.items():
        old = stats(ROOT / "runs" / t22.RUNS[(m, "B0")])
        new_dir = find_rerun(tag)
        row = lambda lim, s: (f"| {tag} | {lim} | {int(s['trunc'].sum())}/41 | {int(s['loop'].sum())}/41 | {s['tokens'].mean():.0f} | {np.median(s['tokens']):.0f} | "
                              f"{s['lat'].mean():.1f} | {s['cite'].mean():.2f} | {s['unver'].mean():.2f} | {s['n_unver'].mean():.2f} |")
        md.append(row(512, old))
        if new_dir is None:
            md.append(f"| {tag} | 2048 | pending | | | | | | | |"); continue
        new = stats(new_dir); assert new["ids"] == old["ids"]
        md.append(row(2048, new))
        was_trunc = old["trunc"] == 1
        same_prefix = sum(new["text"][i].startswith(old["text"][i][: max(50, len(old["text"][i]) - 5)]) for i in old["ids"])
        d = new["unver"] - old["unver"]; lo, hi = t22.boot_ci(d)
        n10, n01, p = t22.mcnemar(old["unver"], new["unver"])
        notes += [f"- **{tag}** (`{new_dir.name}`): of the {int(was_trunc.sum())} answers cut off at 512 tokens, {int((new['trunc'][was_trunc] == 0).sum())} now finish; "
                  f"{int(new['trunc'].sum())} still hit 2,048 tokens, {int((new['trunc'] * new['loop']).sum())} of them in a repetition loop. "
                  f"The 2,048-token answer begins with the 512-token answer for {same_prefix}/41 items. "
                  f"Answers with an unverified citation: {old['unver'].mean():.2f} -> {new['unver'].mean():.2f} (difference {d.mean():+.2f}, 95% CI [{lo:+.2f}, {hi:+.2f}]; "
                  f"McNemar discordant {n10}/{n01}, p={p:.3f})."]
    md += [""] + notes + ["", "## Reading", "",
           "- 'Unverified citation' uses the current T11 parser (English and Arabic forms). It is a lower bound on citation error.",
           "- Longer answers have more room to cite and to err, so per-answer citation rates are not comparable across limits without that caveat.",
           "- Whether scholars would rate the untruncated answers higher is not known: the scholar study rated the 512-token answers only."]
    OUT.write_text("\n".join(md) + "\n", encoding="utf-8"); print("\n".join(md))


if __name__ == "__main__":
    main()
