"""T27 -- compare the independent regeneration runs (made in a separate session on
2026-09-30) with the saved runs. Reads saved artefacts only.

Usage: python scripts/analyze_t27_reruns.py
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results/tables/t27_independent_rerun.md"
ORIG_T15 = {"8B": "20260920-0426_Qwen__Qwen3-8B_B0_t15_benchmark_s42", "14B-AWQ": "20260920-0804_Qwen__Qwen3-14B-AWQ_B0_t15_benchmark_s42",
            "32B-AWQ": "20260920-0840_Qwen__Qwen3-32B-AWQ_B0_t15_benchmark_s42"}
ORIG_T09 = {"8B": "20260917-2320_Qwen__Qwen3-8B_B0_t09sample_s42", "14B-AWQ": "20260918-0955_Qwen__Qwen3-14B-AWQ_B0_t09sample_s42",
            "32B-AWQ": "20260918-1621_Qwen__Qwen3-32B-AWQ_B0_t09sample_s42"}


def load(run):
    return {r["item_id"]: r for r in map(json.loads, (ROOT / "runs" / run / "responses.jsonl").read_text(encoding="utf-8").splitlines())}


def model_of(name):
    return name.split("Qwen3-")[1].split("_B0")[0]


def same(a, b):
    ids = [i for i in a if i in b]
    return sum(a[i]["response_text"] == b[i]["response_text"] for i in ids), len(ids)


def main():
    runs = sorted(p.name for p in (ROOT / "runs").glob("20260930-*_t27_*"))
    t15 = [r for r in runs if "t27_t15_sample" in r]
    rep = [r for r in runs if "t27_repro_sample" in r]
    md = ["# T27 — independent regeneration check", "",
          "Runs made on 2026-09-30 by a separate session, B0, greedy decoding, seed 42, 512 new tokens, same model revisions.",
          "This table only compares their saved responses with the earlier saved runs; that session left no written report in the repository.", "",
          "## Four T15 benchmark items regenerated and compared with the original T15 B0 runs", "",
          "| Model | Revision matches | Identical responses | Same completion-token counts |", "|---|---|---:|---:|"]
    for r in t15:
        m = model_of(r); new, old = load(r), load(ORIG_T15[m]); k, n = same(new, old)
        rev = all(new[i]["model_revision"] == old[i]["model_revision"] for i in new)
        tok = sum(new[i]["completion_tokens"] == old[i]["completion_tokens"] for i in new)
        md.append(f"| Qwen3-{m} | {'yes' if rev else 'NO'} | {k}/{n} | {tok}/{n} |")
    md += ["", "## Four other items (from the T09 sample) run twice in that session, and compared with the September 2026 T09 runs", "",
           "| Model | Run 1 vs run 2 identical | Run 1 vs original T09 run identical |", "|---|---:|---:|"]
    for m in ORIG_T15:
        pair = [r for r in rep if f"Qwen3-{m}_B0" in r]
        a, b = load(pair[0]), load(pair[1]); k1, n1 = same(a, b); k2, n2 = same(a, load(ORIG_T09[m]))
        md.append(f"| Qwen3-{m} | {k1}/{n1} | {k2}/{n2} |")
    md += ["", "## Reading", "",
           "- Qwen3-8B reproduced the four T15 answers exactly. The two AWQ-quantised models reproduced one of four; the others start identically and then diverge, with the same token counts where the limit was reached.",
           "- This agrees with the manuscript's statement that greedy decoding was not reproducible on the quantised models (two identical 32B runs matched on 9 of 41 items) and extends it to the 14B model.",
           "- Consequence already stated in the paper: single-item differences for the quantised models are within run-to-run variation. Results for Qwen3-8B, which carries the scholar comparison, are reproducible at the text level on this sample.",
           "- One Qwen3-8B answer differs from the 17 September T09 run while matching itself across two same-day runs, so full-precision output is stable within an environment but not guaranteed across dates; the cause (library or driver change) was not investigated.",
           "- Not covered by these runs: retrieval-augmented conditions, a clean-environment rebuild, DOI resolution, and a claim-by-claim reading of the manuscript."]
    OUT.write_text("\n".join(md) + "\n", encoding="utf-8"); print("\n".join(md))


if __name__ == "__main__":
    main()
