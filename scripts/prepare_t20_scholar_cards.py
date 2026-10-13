"""Create blinded T20 scholar-review cards from completed T15/T16 artifacts.

The shareable JSON contains no model, condition, run ID, or guardrail-action metadata.  The
separate key is ignored by Git and must not be provided to raters.
"""
from __future__ import annotations

import json
import random
import re
from collections import defaultdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
BENCHMARK = REPO_ROOT / "data/benchmarks/t15_benchmark.jsonl"
OUT_DIR = REPO_ROOT / "expert_review"
FORM_TEMPLATE = OUT_DIR / "create_t19_google_form.gs"

RUNS = {
    "8B_B0": "20260920-0426_Qwen__Qwen3-8B_B0_t15_benchmark_s42",
    "8B_B5": "20260920-0732_Qwen__Qwen3-8B_B5_t15benchmark_s42",
    "14B_B5": "20260920-0825_Qwen__Qwen3-14B-AWQ_B5_t15benchmark_s42",
    "32B_B5": "20260920-1220_Qwen__Qwen3-32B-AWQ_B5_t15benchmark_s42",
}

# These display-only corrections improve readability for scholar review. The source benchmark is
# deliberately not modified: it remains an unaltered licensed evaluation artifact.
QUESTION_OVERRIDES = {
    "hallutruthqa_islamicHallucination_104": (
        "مَا الْآيَةُ الَّتِي نَزَلَتْ حِينَ وَعَدَ النَّبِيُّ ﷺ أَصْحَابَهُ بِفَتْحِ "
        "فَارِسَ وَالرُّومِ، فَقَالَ الْمُنَافِقُونَ: هَيْهَاتَ؟"
    ),
}


def jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def plain_google_forms_text(text: str) -> str:
    """Google Forms help text has no Markdown renderer, so remove saved answer markup."""
    lines = []
    for line in text.splitlines():
        line = re.sub(r"^#{1,6}\s+", "", line.strip())
        line = re.sub(r"^>\s*", "", line)
        line = line.replace("**", "")
        line = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"\1", line)
        lines.append(line.rstrip())
    return "\n".join(lines)


def main() -> int:
    items = jsonl(BENCHMARK)
    by_stratum: dict[str, list[dict]] = defaultdict(list)
    for item in items:
        by_stratum[item["stratum"]].append(item)
    selected = []
    for stratum in sorted(by_stratum):
        candidates = sorted(by_stratum[stratum], key=lambda item: item["item_id"])
        if len(candidates) < 2:
            raise ValueError(f"{stratum} has fewer than two items")
        selected.extend(candidates[:2])

    answers = {
        label: {row["item_id"]: row["response_text"] for row in jsonl(REPO_ROOT / "runs" / run_id / "responses.jsonl")}
        for label, run_id in RUNS.items()
    }
    candidates: list[dict] = []
    for item in selected:
        # Core paired comparison: B0 vs B5 on the 8B primary model (24 cards).
        for label in ("8B_B0", "8B_B5"):
            candidates.append({"item": item, "label": label})
    # Secondary size comparison: rotate one B5 card per stratum to each larger model (12 cards).
    for index, item in enumerate(selected):
        candidates.append({"item": item, "label": "14B_B5" if index % 2 == 0 else "32B_B5"})

    rng = random.Random(42)
    rng.shuffle(candidates)
    cards, key = [], []
    for number, candidate in enumerate(candidates, start=1):
        item, label = candidate["item"], candidate["label"]
        answer = answers[label].get(item["item_id"])
        if answer is None:
            raise KeyError(f"missing {item['item_id']} in {label}")
        card_id = f"T19-{number:03d}"
        cards.append({
            "id": card_id,
            "language": item["language"],
            "question": QUESTION_OVERRIDES.get(item["item_id"], item["query"]),
            "answer": answer,
            "citations": "No separate evidence packet is supplied; assess only citations naturally present in the answer.",
        })
        key.append({"card_id": card_id, "item_id": item["item_id"], "stratum": item["stratum"],
                    "run_label": label, "run_id": RUNS[label]})

    OUT_DIR.mkdir(exist_ok=True)
    (OUT_DIR / "t20_google_form_cards.json").write_text(json.dumps(cards, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    display_cards = [{**card, "answer": plain_google_forms_text(card["answer"])} for card in cards]
    (OUT_DIR / "t20_google_form_display_cards.json").write_text(
        json.dumps(display_cards, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    template = FORM_TEMPLATE.read_text(encoding="utf-8")
    ready_script = template.replace(
        "const REVIEW_CARDS = [];",
        "const REVIEW_CARDS = " + json.dumps(display_cards, ensure_ascii=False, indent=2) + ";",
        1,
    )
    if ready_script == template:
        raise RuntimeError("Google Form template marker was not found")
    (OUT_DIR / "T19_Google_Form_READY_TO_PASTE.gs").write_text(ready_script, encoding="utf-8")
    (OUT_DIR / "t20_blinding_key.jsonl").write_text(
        "\n".join(json.dumps(row) for row in key) + "\n", encoding="utf-8"
    )
    (OUT_DIR / "t20_card_manifest.md").write_text(
        "# T20 — blinded scholar-review cards\n\n"
        "- 36 randomized cards: 12 items (two per T15 stratum).\n"
        "- Core paired comparison: 8B B0 and 8B B5 for every item (24 cards).\n"
        "- Secondary model-size comparison: one additional B5 card per item, alternating 14B and 32B (12 cards).\n"
        "- `T19_Google_Form_READY_TO_PASTE.gs` is the ready-to-paste script for the form creator. `t20_google_form_cards.json` preserves original text for the PDF; `t20_google_form_display_cards.json` removes Markdown markers because Google Forms cannot render Markdown.\n"
        "- The separately generated blinding key is ignored by Git and must not be sent to raters.\n"
        "- Original English/Arabic response text is preserved. The Google Form interface is bilingual Malay–English; no unvalidated translation has been introduced into rated answers.\n",
        encoding="utf-8",
    )
    print(f"wrote {len(cards)} blinded cards and a separate key")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
