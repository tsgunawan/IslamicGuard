<!--
B2 — Standard RAG condition (paper.md §10 ablation table).

Retrieval + generation, nothing else. No provenance validator, no claim-evidence check, no
madhhab policy, no abstention logic -- those are B3-B5 (T11-T13). The model is simply given
retrieved passages and asked to answer using them if relevant; whether it uses them correctly,
cites them faithfully, or hallucinates alongside them is NOT checked at this stage -- that is
exactly the gap B3 (provenance validation) and B4 (claim-evidence check) are meant to close,
and the point of keeping B2 unvalidated is to measure that gap in later ablation analysis.

The `{context}` placeholder below is filled per-request with the actual retrieved passages
(see src/rag/generate.py:format_context_block) and sent as part of the user-turn content
(not the system prompt), so the model attends to it as retrieved evidence rather than as a
policy instruction. No system prompt is used for B2 (matching B0's "no system prompt"
baseline) -- only the retrieval augmentation is added relative to B0, isolating retrieval's
effect for the ablation.

Exact template follows below this comment block.
-->
{context}

Question: {query}

Answer the question above. Use the retrieved passages if they are relevant and helpful; if
they are not relevant, you may rely on your own knowledge, or say you are unsure. Do not
assume every retrieved passage is relevant just because it was retrieved.
