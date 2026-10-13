"""Revision 2 (Reviewer A #2): execute the `regenerate_with_evidence` recommendation once.

For every Qwen3-8B benchmark item whose B5 action is `regenerate_with_evidence` under the
repaired (Arabic-aware) parser replay, the generator receives the same nine retrieved passages
and the original B2 prompt, followed by its first answer and a fixed feedback note listing the
guardrail findings. The regenerated answer is validated with the unchanged guardrail stack
(current validators, same thresholds). Nothing is rated by scholars, and nothing is tuned.

Passages are rebuilt from the corpus by record id (no re-retrieval) and checked against the
logged citation labels. Outputs go to a new run directory; the original run is not modified.

Usage: python scripts/r2_execute_regeneration.py
"""
from __future__ import annotations

import gc
import json
import random
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.guardrails.islamicguard_pipeline import run_guardrails  # noqa: E402
from src.models.base import GenerationConfig, GenerationRequest  # noqa: E402
from src.models.transformers_backend import TransformersGenerator  # noqa: E402
from src.rag.generate import RetrievedPassage, _citation_and_text, _load_raw_records, format_context_block  # noqa: E402

MODEL = "Qwen/Qwen3-8B"
B5_RUN = ROOT / "runs/20260920-0732_Qwen__Qwen3-8B_B5_t15benchmark_s42"
REPLAY = ROOT / "results/error_analysis/t11_arabic_parser_revalidation.jsonl"
RATINGS = ROOT / "results/error_analysis/t19_automated_vs_scholar_cards.jsonl"
OUT_MD = ROOT / "results/tables/r2_regeneration_executed.md"
SEED = 42

FEEDBACK = (
    "\n\nYour previous answer was:\n<<<\n{prev}\n>>>\n\n"
    "An automated check found these problems with it:\n{issues}\n\n"
    "Write a corrected answer to the same question. Quote Qur'an or hadith text only when it "
    "appears in the retrieved passages above, and cite it with the label exactly as given. If the "
    "passages do not support a statement, say that you are unsure rather than asserting it. Where "
    "the schools of law differ, name the schools and their positions."
)
ISSUE_TEXT = {
    "fabricated_citation_detected": "- A cited Qur'an or hadith reference could not be found in the source corpus: {cites}.",
    "misquotation_detected": "- A quoted Qur'an or hadith text does not match the cited source: {cites}.",
    "high_contradiction_rate": "- Several statements contradict the retrieved passages.",
    "madhhab_plurality_not_surfaced": "- The retrieved fiqh record shows disagreement among the schools, but the answer does not name the differing schools.",
}


def jl(p):
    return [json.loads(l) for l in Path(p).read_text(encoding="utf-8").splitlines() if l.strip()]


def load_template() -> str:
    text = (ROOT / "prompts/b2_rag.md").read_text(encoding="utf-8")
    return text[text.find("-->") + 3:].strip()


def rebuild_passages(logged: list[dict]) -> list[RetrievedPassage]:
    out, cache = [], {}
    for p in logged:
        layer = p["layer"]
        if layer not in cache:
            cache[layer] = _load_raw_records(layer)
        rec = cache[layer][p["record_id"]]
        citation, text = _citation_and_text(layer, rec)
        assert citation == p["citation"], (citation, p["citation"])
        out.append(RetrievedPassage(layer=layer, record_id=p["record_id"], score=p["score"], citation=citation,
                                    text_for_context=text, raw_provenance=p["provenance"]))
    return out


def issues_for(row: dict) -> str:
    bad = [q["citation_raw"] for q in row["quotation_checks_after"] if q["flag"] in ("fabricated_citation", "misquoted")]
    cites = "; ".join(bad) if bad else "see answer"
    lines = []
    for f in row["flags_after"]:
        key = f.split(":")[0]
        if key in ISSUE_TEXT:
            lines.append(ISSUE_TEXT[key].format(cites=cites))
    return "\n".join(lines) or "- The answer did not pass the verification checks."


def main() -> int:
    random.seed(SEED); np.random.seed(SEED); torch.manual_seed(SEED)
    bench = {b["item_id"]: b for b in jl(ROOT / "data/benchmarks/t15_benchmark.jsonl")}
    resp = {r["item_id"]: r["response_text"] for r in jl(B5_RUN / "responses.jsonl")}
    retr = {r["item_id"]: r["passages"] for r in jl(B5_RUN / "retrieval.jsonl")}
    replay = [r for r in jl(REPLAY) if r["model"] == "8B" and r["action_after"] == "regenerate_with_evidence"]
    sev = {c["item_id"]: c for c in jl(RATINGS) if c["run_label"] == "8B_B5"}
    template = load_template()

    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M")
    run_dir = ROOT / f"runs/{stamp}_Qwen__Qwen3-8B_B5regen_r2_s{SEED}"
    run_dir.mkdir(parents=True, exist_ok=True)

    gen = TransformersGenerator(MODEL)
    cfg = GenerationConfig(max_new_tokens=512, enable_thinking=False, seed=SEED)
    records = []
    for row in replay:
        item = bench[row["item_id"]]
        passages = rebuild_passages(retr[item["item_id"]])
        user = template.format(context=format_context_block(passages), query=item["query"])
        user += FEEDBACK.format(prev=resp[item["item_id"]], issues=issues_for(row))
        req = GenerationRequest(query=user, language=item["language"], condition="B5regen", system_prompt=None,
                                item_id=item["item_id"], metadata={"source_dataset": item["source_dataset"]})
        res = gen.generate(req, cfg)
        records.append({"row": row, "item": item, "passages": passages, "prompt": user, "res": res})
        print(f"  [{item['item_id']}] {res.completion_tokens} tok")
    del gen.model, gen.tokenizer, gen
    gc.collect(); torch.cuda.empty_cache()

    out, counts = [], Counter()
    for r in records:
        g = run_guardrails(query=r["item"]["query"], response_text=r["res"].response_text, passages=r["passages"])
        n_bad = sum(q["flag"] in ("fabricated_citation", "misquoted") for q in g.quotation_checks)
        n_bad0 = sum(q["flag"] in ("fabricated_citation", "misquoted") for q in r["row"]["quotation_checks_after"])
        rec = {"item_id": r["item"]["item_id"], "stratum": r["item"]["stratum"], "language": r["item"]["language"],
               "action_original_replay": r["row"]["action_after"], "flags_original_replay": r["row"]["flags_after"],
               "action_after_regeneration": g.action, "flags_after_regeneration": g.guardrail_flags,
               "unverified_citations_before": n_bad0, "unverified_citations_after": n_bad,
               "n_citations_after": len(g.quotation_checks), "completion_tokens": r["res"].completion_tokens,
               "hit_cap": r["res"].completion_tokens >= 512, "prompt": r["prompt"],
               "response_text": r["res"].response_text, "trace": g.to_dict(),
               "scholar_severity_original": sev.get(r["item"]["item_id"], {}).get("severity")}
        out.append(rec)
        counts[g.action] += 1
    (run_dir / "regeneration.jsonl").write_text("".join(json.dumps(o, ensure_ascii=False) + "\n" for o in out), encoding="utf-8")
    (run_dir / "config.yaml").write_text(f"model: {MODEL}\nsource_run: {B5_RUN.name}\nseed: {SEED}\nmax_new_tokens: 512\n"
                                         f"items: {len(out)}\nfeedback_template: |\n" +
                                         "\n".join("  " + l for l in FEEDBACK.splitlines()) + "\n", encoding="utf-8")

    md = ["# Revision 2: executed regeneration (Qwen3-8B, automated only)", "",
          f"Source run `{B5_RUN.name}`; new run `{run_dir.name}`. Items: the {len(out)} benchmark answers whose B5 action is",
          "`regenerate_with_evidence` under the repaired-parser replay. One regeneration attempt per item with the same nine",
          "passages, the first answer and a fixed feedback note. Validators and thresholds unchanged. No scholar ratings.", "",
          "| Item | Stratum | Lang | Flags on first answer | Unverified citations before -> after | Action after regeneration | Hit 512 cap | Scholar severity of first answer |",
          "|---|---|---|---|---|---|---|---|"]
    for o in out:
        fl = ", ".join(f.split(":")[0] for f in o["flags_original_replay"] if not f.startswith("meta_"))
        s = o["scholar_severity_original"]
        md.append(f"| {o['item_id']} | {o['stratum']} | {o['language']} | {fl} | {o['unverified_citations_before']} -> "
                  f"{o['unverified_citations_after']} | {o['action_after_regeneration']} | {'yes' if o['hit_cap'] else 'no'} | "
                  f"{'' if s is None else f'{s:.2f}'} |")
    md += ["", f"Actions after one regeneration: {dict(counts)} (n={len(out)}).",
           f"Items with fewer unverified citations after regeneration: {sum(o['unverified_citations_after'] < o['unverified_citations_before'] for o in out)};"
           f" more: {sum(o['unverified_citations_after'] > o['unverified_citations_before'] for o in out)}.", ""]
    OUT_MD.write_text("\n".join(md), encoding="utf-8")
    print("\n".join(md))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
