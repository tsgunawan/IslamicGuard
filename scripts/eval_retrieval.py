#!/usr/bin/env python
"""Retrieval evaluation (T08). Computes Recall@1/5/10 and MRR@10 for a given
embedding model against data/benchmarks/retrieval_eval_queries.jsonl, using
the indexes built by scripts/build_index.py.

Per DECISIONS.md DG-4, this script is run for BOTH multilingual-e5-large-instruct
(the primary) and at least one Qwen3-Embedding variant (the mandated comparison)
so the choice is validated on this project's own data, not just literature.

Usage:
    python scripts/eval_retrieval.py --model me5-large-instruct
    python scripts/eval_retrieval.py --model qwen3-embedding-4b
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.rag.embed import MODELS, Embedder
from src.rag.index import load_index

REPO_ROOT = Path(__file__).resolve().parents[1]
QUERIES_PATH = REPO_ROOT / "data" / "benchmarks" / "retrieval_eval_queries.jsonl"


def load_queries() -> list[dict]:
    with QUERIES_PATH.open(encoding="utf-8") as f:
        return [json.loads(line) for line in f]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True, choices=sorted(MODELS.keys()))
    parser.add_argument("--ks", nargs="+", type=int, default=[1, 5, 10])
    args = parser.parse_args()

    queries = load_queries()
    by_layer: dict[str, list[dict]] = defaultdict(list)
    for q in queries:
        by_layer[q["gold_layer"]].append(q)

    spec = MODELS[args.model]
    print(f"Loading embedding model {spec.hf_repo} ...")
    embedder = Embedder(spec)

    max_k = max(args.ks)
    overall_ranks: list[int | None] = []  # rank (1-indexed) of gold, or None if not found
    per_layer_ranks: dict[str, list[int | None]] = defaultdict(list)

    for layer, layer_queries in by_layer.items():
        print(f"Evaluating layer={layer} ({len(layer_queries)} queries) ...")
        idx = load_index(args.model, layer)
        texts = [q["query"] for q in layer_queries]
        query_vecs = embedder.encode_queries(texts, batch_size=32)
        results = idx.search(query_vecs, k=max_k)
        for q, res in zip(layer_queries, results):
            retrieved_ids = [rid for rid, _ in res]
            if q["gold_id"] in retrieved_ids:
                rank = retrieved_ids.index(q["gold_id"]) + 1
            else:
                rank = None
            overall_ranks.append(rank)
            per_layer_ranks[layer].append(rank)

    def metrics(ranks: list[int | None]) -> dict[str, float]:
        n = len(ranks)
        out = {}
        for k in args.ks:
            hits = sum(1 for r in ranks if r is not None and r <= k)
            out[f"recall@{k}"] = hits / n if n else float("nan")
        mrr_k = max(args.ks)
        rr_sum = sum((1.0 / r) for r in ranks if r is not None and r <= mrr_k)
        out[f"mrr@{mrr_k}"] = rr_sum / n if n else float("nan")
        out["n"] = n
        return out

    print(f"\n=== Results: model={args.model} ===")
    overall = metrics(overall_ranks)
    print("Overall:", json.dumps(overall, indent=2))
    per_layer_metrics = {}
    for layer, ranks in per_layer_ranks.items():
        m = metrics(ranks)
        per_layer_metrics[layer] = m
        print(f"{layer}:", json.dumps(m, indent=2))

    out_path = REPO_ROOT / "results" / "tables" / f"t08_retrieval_eval_{args.model}.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        json.dumps({"model": args.model, "overall": overall, "per_layer": per_layer_metrics}, indent=2),
        encoding="utf-8",
    )
    print(f"\nSaved: {out_path}")


if __name__ == "__main__":
    main()
