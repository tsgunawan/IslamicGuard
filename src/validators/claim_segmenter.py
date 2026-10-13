"""Claim segmentation for claim-evidence faithfulness checking (T12, condition B4).

Splits a generated response into discrete, checkable factual-claim sentences, filtering
out questions, meta-commentary, and hedges that are not themselves verifiable factual
assertions. This is deliberately a simple, sentence-level heuristic -- not a semantic
parser, and it does not split compound sentences into sub-claims. Documented limitation,
not a hidden one: a sentence containing two independent factual assertions ("X is
permissible and Y is required") is treated as one claim, which can blur a
partially-right/partially-wrong response into a single verdict. A future revision could
add sub-sentence clause splitting; out of scope for this pass.

Separate from T11's quotation validators (src/validators/quran_validator.py,
hadith_validator.py), which check citation existence and quote accuracy -- this module
identifies claims for T12's faithfulness_validator.py to then check against retrieved
evidence, per paper.md Sec 9.1's "separate source existence from source supports claim."
"""

from __future__ import annotations

import re
from dataclasses import dataclass

# Sentence boundary: '.', '!', '?', Arabic '؟' (question) and '؛' (semicolon), followed
# by whitespace. Deliberately simple regex splitting, not a full sentence tokenizer
# (e.g. spaCy) -- avoids adding a heavy new dependency for what only needs to be a
# defensible, documented heuristic at this stage.
#
# Also split on ": " when followed by a capital letter -- real bug found while testing on
# actual B2 responses: "Based on the retrieved passages... the answer is: No, ablution is
# not required..." was being kept as ONE sentence (no period before the real claim), which
# then got the whole thing filtered out because it starts with the hedge prefix "based on
# the retrieved" -- silently dropping the actual claim that follows the colon. Splitting on
# ": <Capital>" separates the hedge lead-in from the answer it introduces.
_SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?؟؛])\s+|:\s+(?=[A-Z])")

MIN_CLAIM_LEN = 20  # chars; shorter fragments are rarely a standalone checkable claim

# Sentence-initial hedges/meta-commentary that are not themselves factual claims about
# Islamic knowledge -- filtered so the faithfulness checker isn't asked to verify e.g.
# "I am unsure" against retrieved evidence, which is a category error.
_HEDGE_PREFIXES = [
    "i am unsure",
    "i'm unsure",
    "i am not sure",
    "i'm not sure",
    "it is important to note",
    "it's important to note",
    "as an ai",
    "please note",
    "please consult",
    "in summary",
    "to summarize",
    "note that",
    "i cannot",
    "i can't",
    "based on the information",
    "based on the retrieved",
    "disclaimer",
    "however,",
    "that said",
    "in conclusion",
]


@dataclass
class Claim:
    text: str
    start: int
    end: int

    def to_dict(self) -> dict:
        return {"text": self.text, "start": self.start, "end": self.end}


def _is_claim_like(sentence: str) -> bool:
    s = sentence.strip()
    if len(s) < MIN_CLAIM_LEN:
        return False
    if s.endswith("?") or s.endswith("؟"):
        return False  # questions are not claims
    low = s.lower().lstrip("*- ")
    if any(low.startswith(h) for h in _HEDGE_PREFIXES):
        return False
    # Require at least a few alphabetic characters (filters stray markdown bullets,
    # numbering artifacts, etc. left over after sentence splitting).
    if sum(ch.isalpha() for ch in s) < 10:
        return False
    return True


def segment_claims(text: str) -> list[Claim]:
    """Split `text` into claim-like sentences with their original character spans."""
    if not text:
        return []
    claims: list[Claim] = []
    search_from = 0
    for raw_sentence in _SENTENCE_SPLIT_RE.split(text):
        sentence = raw_sentence.strip()
        if not sentence:
            continue
        start = text.find(sentence, search_from)
        if start == -1:
            # Shouldn't normally happen (split() preserves substrings), but don't crash
            # the pipeline over a span-tracking edge case -- fall back to no-span-found.
            start = search_from
        end = start + len(sentence)
        search_from = end
        if _is_claim_like(sentence):
            claims.append(Claim(text=sentence, start=start, end=end))
    return claims
