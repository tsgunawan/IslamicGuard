"""Revision 2 (Reviewer A #8, Reviewer B #3): citation-parser coverage on fresh, held-out answers.

Answers come from B5 runs on data/benchmarks/r2_heldout_arabic.jsonl (30 Arabic questions not in
the benchmark, the scholar cards or the parser unit tests). Reference-level ground truth is in
data/benchmarks/r2_heldout_citation_labels.jsonl, labelled by hand before the parser output was
inspected (protocol in that file's header record). A reference is a locatable Qur'an verse
(surah + verse number, numeric or named, Arabic or English form) or a hadith with collection and
number. Surah or collection names without a number are counted separately and are not targets.

Original parser = repaired code with the Arabic-form finders disabled; this reproduces the stored
pre-repair checks on all 123 saved benchmark answers (see revision2.md).

Usage: python scripts/r2_parser_heldout_eval.py RUN_DIR [RUN_DIR ...]
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from statsmodels.stats.proportion import proportion_confint

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.validators import arabic_citations as ac  # noqa: E402
from src.validators import hadith_validator as hv  # noqa: E402
from src.validators import quran_validator as qv  # noqa: E402

LABELS = ROOT / "data/benchmarks/r2_heldout_citation_labels.jsonl"
OUT_MD = ROOT / "results/tables/r2_parser_heldout.md"
_FQ, _FH = ac.find_quran_citations, ac.find_hadith_citations


def jl(p):
    return [json.loads(l) for l in Path(p).read_text(encoding="utf-8").splitlines() if l.strip()]


def parse(text, arabic=True):
    ac.find_quran_citations = _FQ if arabic else (lambda t: [])
    ac.find_hadith_citations = _FH if arabic else (lambda t: [])
    out = []
    for c in qv.validate_text(text) + hv.validate_text(text):
        p = c.parsed_reference or {}
        if c.citation_type == "quran":
            out.append(("quran", p.get("surah_id"), p.get("ayah_id"), c.flag.value))
        else:
            out.append(("hadith", p.get("collection_key"), p.get("hadith_number"), c.flag.value))
    ac.find_quran_citations, ac.find_hadith_citations = _FQ, _FH
    return out


def key(ref):
    return (ref[0], ref[1], ref[2])


def wl(k, n):
    lo, hi = proportion_confint(k, n, method="wilson") if n else (float("nan"),) * 2
    return f"{k}/{n} = {k / n:.2f} [{lo:.2f}, {hi:.2f}]" if n else "–"


def main(runs):
    labels = {(r["run"], r["item_id"]): r for r in jl(LABELS) if "item_id" in r}
    md = ["# Revision 2: citation-parser coverage on held-out Arabic answers", "",
          "Reference-level recall and precision against hand labels. Wilson 95% intervals. Answers were never used to build or test the parser.", "",
          "| Run | Answers | Answers with >= 1 labelled reference | Labelled references (Qur'an / hadith) | Name-only mentions (not targets) | Parser | Recall | Precision | Answers with >= 1 reference checked |",
          "|---|---:|---:|---|---:|---|---|---|---|"]
    detail, summary = [], {}
    for run in runs:
        run = Path(run)
        resp = {r["item_id"]: r["response_text"] for r in jl(run / "responses.jsonl")}
        tot_lab = sum(len(labels[(run.name, i)]["refs"]) for i in resp)
        nq = sum(1 for i in resp for x in labels[(run.name, i)]["refs"] if x[0] == "quran")
        names = sum(labels[(run.name, i)].get("name_only", 0) for i in resp)
        with_ref = [i for i in resp if labels[(run.name, i)]["refs"]]
        for arabic, lab in ((False, "original"), (True, "repaired")):
            tp = fp = 0; found = 0; ans_checked = 0
            for i, text in resp.items():
                gold = {key(tuple(x)) for x in labels[(run.name, i)]["refs"]}
                got = {key(x) for x in parse(text, arabic)}
                tp_i = len(gold & got)
                found += tp_i
                fp += len(got - gold)
                tp += tp_i
                ans_checked += bool(gold & got)
                if arabic:
                    detail.append((run.name[:25], i, sorted(gold - got), sorted(got - gold)))
            summary[f"{run.name}|{lab}"] = dict(answers=len(resp), with_ref=len(with_ref), refs=tot_lab, quran=nq, names=names,
                                                 found=found, tp=tp, fp=fp, ans_checked=ans_checked)
            md.append(f"| {run.name[:40]} | {len(resp)} | {len(with_ref)} | {tot_lab} ({nq} / {tot_lab - nq}) | {names} | {lab} | "
                      f"{wl(found, tot_lab)} | {wl(tp, tp + fp)} | {ans_checked}/{len(with_ref)} |")
    md += ["", "## Misses and spurious matches of the repaired parser", "", "| Run | Item | Missed labelled references | Parser references not in labels |", "|---|---|---|---|"]
    for r, i, miss, extra in detail:
        if miss or extra:
            md.append(f"| {r} | {i} | {miss} | {extra} |")
    OUT_MD.write_text("\n".join(md) + "\n", encoding="utf-8")
    OUT_MD.with_suffix(".json").write_text(json.dumps(summary, indent=1), encoding="utf-8")
    print("\n".join(md))


if __name__ == "__main__":
    main(sys.argv[1:])
