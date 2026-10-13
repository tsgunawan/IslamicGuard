"""Evaluate the bounded T17 pre-retrieval injection screen on its declared test set."""
from __future__ import annotations
import json
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))
from src.guardrails.prompt_injection_policy import screen_prompt_injection  # noqa: E402


def main() -> int:
    sample = REPO_ROOT / "data/benchmarks/t17_prompt_injection.jsonl"
    rows = [json.loads(line) for line in sample.read_text(encoding="utf-8").splitlines()]
    results = []
    for row in rows:
        screen = screen_prompt_injection(row["query"])
        results.append({**row, "detected": screen.detected, "detected_categories": screen.categories,
                        "correct": screen.detected == row["expected_detected"]})
    attacks = [r for r in results if r["expected_detected"]]
    controls = [r for r in results if not r["expected_detected"]]
    out = REPO_ROOT / "results/error_analysis/t17_prompt_injection_results.jsonl"
    out.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in results) + "\n", encoding="utf-8")
    report = REPO_ROOT / "results/tables/t17_prompt_injection.md"
    report.write_text(
        "# T17 — Prompt-injection evaluation\n\n"
        "All items are constructed, explicitly labelled attack/control cases. This evaluation measures the "
        "pre-retrieval screen only: a detection is a candidate safe-block decision for a caller to enforce. "
        "It is not an end-to-end model jailbreak claim or evidence of general robustness.\n\n"
        f"- Attacks detected: {sum(r['detected'] for r in attacks)}/{len(attacks)}\n"
        f"- Benign controls incorrectly blocked: {sum(r['detected'] for r in controls)}/{len(controls)}\n"
        f"- Overall exact policy outcome: {sum(r['correct'] for r in results)}/{len(results)}\n",
        encoding="utf-8")
    print(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
