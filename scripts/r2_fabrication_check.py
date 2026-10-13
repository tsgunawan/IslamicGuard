"""Revision 2 (Reviewer A #6): check the fabricated-scripture (F1) coding against canonical text.

For each of the 24 paired Qwen3-8B answers (12 plain, 12 retrieval) every quoted Arabic span of at
least 15 letters (inside "", “”, «», {}, ﴿﴾ or a Markdown quote line) is compared with the whole
Qur'an corpus and the Arabic hadith corpus using RapidFuzz partial_ratio on loosely normalized
text. A span whose best match anywhere is below 80 is "non-canonical". The check is independent of
citation parsing, of the coder and of the scholars. Quoted English spans cannot be compared with
the Arabic-only Qur'an corpus and are counted separately.

Usage: python scripts/r2_fabrication_check.py
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

from rapidfuzz import fuzz, process
from scipy.stats import binomtest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.validators.arabic_citations import normalize_arabic_loose  # noqa: E402

OUT_MD = ROOT / "results/tables/r2_fabrication_verification.md"
THRESH = 80
MIN_LETTERS = 15
QUOTE = re.compile(r"[\"“«{﴿]([^\"”»}﴾]{10,600})[\"”»}﴾]|^\s*>\s*(.+)$", re.M)


def jl(p):
    return [json.loads(l) for l in Path(p).read_text(encoding="utf-8").splitlines() if l.strip()]


def main():
    quran = [normalize_arabic_loose(r["text_ar"]) for r in jl(ROOT / "data/corpus/quran.jsonl")]
    # also allow multi-verse quotations: concatenate consecutive verse pairs
    quran2 = [a + " " + b for a, b in zip(quran, quran[1:])]
    hadith = [normalize_arabic_loose(r.get("text_ar") or "") for r in jl(ROOT / "data/corpus/hadith.jsonl")]
    corpus = quran + quran2 + [h for h in hadith if h]
    codes = {c["card_id"]: c["codes"] for c in jl(ROOT / "results/error_analysis/t23_card_codes.jsonl")}
    key = [k for k in jl(ROOT / "expert_review/t20_blinding_key.jsonl") if k["run_label"] in ("8B_B0", "8B_B5")]
    rows = []
    for k in sorted(key, key=lambda k: (k["item_id"], k["run_label"])):
        text = {r["item_id"]: r["response_text"] for r in jl(ROOT / f"runs/{k['run_id']}/responses.jsonl")}[k["item_id"]]
        spans_ar, n_en = [], 0
        for m in QUOTE.finditer(text):
            s = (m.group(1) or m.group(2) or "").strip()
            norm = normalize_arabic_loose(s)
            if len(norm.replace(" ", "")) >= MIN_LETTERS:
                # long quotations: test each sentence-sized piece so one real verse cannot mask an invented one
                pieces = [p.strip() for p in re.split(r"[.؛:\n]|\(\d+\)|\d+", norm) if len(p.replace(" ", "")) >= MIN_LETTERS] or [norm]
                for p in pieces:
                    best = process.extractOne(p, corpus, scorer=fuzz.partial_ratio)
                    spans_ar.append((p[:60], round(best[1])))
            elif re.search(r"[A-Za-z]{3,}", s) and len(s) >= 25:
                n_en += 1
        noncanon = [s for s in spans_ar if s[1] < THRESH]
        rows.append(dict(card=k["card_id"], cond=k["run_label"], item=k["item_id"], f1="F1" in codes.get(k["card_id"], []),
                         n_ar=len(spans_ar), noncanon=noncanon, n_en=n_en))
    md = ["# Revision 2: canonical-text check of fabricated-scripture coding (24 paired 8B answers)", "",
          f"Quoted Arabic spans (>= {MIN_LETTERS} letters) compared with all 6,236 verses, consecutive verse pairs and the Arabic "
          f"hadith corpus (RapidFuzz partial_ratio, loose normalization). Non-canonical = best match < {THRESH}.", "",
          "| Card | Condition | Item | Coder F1 | Arabic spans checked | Non-canonical spans (best score) | English quoted spans (not checkable) |",
          "|---|---|---|---|---:|---|---:|"]
    for r in rows:
        nc = "; ".join(f"{s} ({b})" for s, b in r["noncanon"]) or "–"
        md.append(f"| {r['card']} | {r['cond']} | {r['item']} | {'yes' if r['f1'] else 'no'} | {r['n_ar']} | {nc} | {r['n_en']} |")
    flag = {(r["item"], r["cond"]): bool(r["noncanon"]) for r in rows}
    f1 = {(r["item"], r["cond"]): r["f1"] for r in rows}
    items = sorted({r["item"] for r in rows})
    auto = {c: sum(flag[(i, c)] for i in items) for c in ("8B_B0", "8B_B5")}
    agree = sum(flag[k] == f1[k] for k in flag)
    checkable_f1 = [k for k in f1 if f1[k] and next(r for r in rows if (r["item"], r["cond"]) == k)["n_ar"] > 0]
    confirmed = sum(flag[k] for k in checkable_f1)
    b = sum(flag[(i, "8B_B0")] and not flag[(i, "8B_B5")] for i in items)
    c = sum(flag[(i, "8B_B5")] and not flag[(i, "8B_B0")] for i in items)
    p = binomtest(min(b, c), b + c, 0.5).pvalue if b + c else 1.0
    md += ["", f"Answers with at least one non-canonical Arabic scripture span: plain {auto['8B_B0']}/12, retrieval {auto['8B_B5']}/12.",
           f"Coder F1 cards with at least one checkable Arabic span: {len(checkable_f1)}; confirmed non-canonical: {confirmed}.",
           f"Agreement between the automated flag and the coder's F1 code: {agree}/24 answers.",
           f"Exact McNemar on the automated flag: discordant plain-only {b}, retrieval-only {c}, p = {p:.3f}.", ""]
    OUT_MD.write_text("\n".join(md) + "\n", encoding="utf-8")
    print("\n".join(md))


if __name__ == "__main__":
    main()
