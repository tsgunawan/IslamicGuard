#!/usr/bin/env python
"""Build FAISS indexes for all three corpus layers (quran/hadith/fiqh) using a
given embedding model. Per DG-4 (DECISIONS.md), this is run for both the
primary model (multilingual-e5-large-instruct) and the comparison model
(Qwen3-Embedding) so T08's evaluation can report both.

Usage:
    python scripts/build_index.py --model me5-large-instruct
    python scripts/build_index.py --model qwen3-embedding-4b
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.rag.corpus import CorpusLayer, load_corpus
from src.rag.embed import MODELS, Embedder
from src.rag.index import build_index

LAYERS: list[CorpusLayer] = ["quran", "hadith", "fiqh"]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True, choices=sorted(MODELS.keys()))
    parser.add_argument("--layers", nargs="+", default=LAYERS, choices=LAYERS)
    parser.add_argument("--batch-size", type=int, default=32)
    args = parser.parse_args()

    spec = MODELS[args.model]
    print(f"Loading embedding model {spec.hf_repo} ...")
    t0 = time.time()
    embedder = Embedder(spec)
    print(f"  loaded in {time.time() - t0:.1f}s")

    for layer in args.layers:
        print(f"[{args.model}] layer={layer}: loading corpus ...")
        records = load_corpus(layer)
        print(f"  {len(records)} records")
        texts = [r.embed_text for r in records]
        ids = [r.id for r in records]

        t0 = time.time()
        embeddings = embedder.encode_passages(texts, batch_size=args.batch_size)
        dt = time.time() - t0
        print(f"  embedded {len(texts)} records in {dt:.1f}s ({len(texts) / dt:.1f}/s)")

        build_index(embeddings, ids, model_slug=args.model, layer=layer)
        print(f"  index saved: data/corpus/index/{args.model}/{layer}.faiss")


if __name__ == "__main__":
    main()
