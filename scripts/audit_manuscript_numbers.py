"""T27 -- trace every number in manuscript/draft.md to a result artifact.

Each numeric token in the draft (outside the reference list) is looked up in the generated
result tables, the literature notes and the source files that define thresholds. Tokens are
compared after normalising signs, thousands separators and trailing zeros. A token that appears
in no source is listed for manual review; the script does not decide whether a claim is right,
only whether the number exists in an artifact.

Usage: python scripts/audit_manuscript_numbers.py
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results/tables/t27_number_audit.md"
SOURCES = (sorted((ROOT / "results/tables").glob("*.md")) + sorted((ROOT / "manuscript/tables").glob("*.md"))
           + [ROOT / "paper.md", ROOT / "environment.yml", ROOT / "literature/synthesis.md", ROOT / "literature/ethics_engineering_mapping.md", ROOT / "literature/references.bib", ROOT / "literature/gap_table.csv",
              ROOT / "src/validators/faithfulness_validator.py", ROOT / "src/validators/quran_validator.py", ROOT / "src/validators/hadith_validator.py", ROOT / "src/guardrails/madhhab_policy.py", ROOT / "scripts/t22_statistical_comparison.py", ROOT / "src/utils/text_normalize.py", ROOT / "src/guardrails/abstention_policy.py",
              ROOT / "expert_review/t20_card_manifest.md", ROOT / "expert_review/t19_scholar_review_protocol.md"]
           + sorted((ROOT / "runs").glob("20260920-*t15*/config.yaml")) + sorted((ROOT / "runs").glob("20260920-*t15*/environment.txt")))
SOURCES = [p for p in SOURCES if p.name != OUT.name]
NUM = re.compile(r"(?<![\w.])[-−+]?\d[\d,]*(?:\.\d+)?%?")
# Numbers that are structure, not results: section/table/figure numbers, years, scale endpoints, small counts.
WORDS = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9, "twelve": 12, "fifteen": 15}


# Headline claims: (phrase that must be in the draft, artifact, regex that must match in the artifact).
T = "results/tables/"
HEADLINES = [
    ("difference 0.62, 95% confidence interval 0.17 to 1.15", T + "t22_statistical_comparison.md", r"Factual quality.*\| \+0\.62 \| \[\+0\.17, \+1\.15\]"),
    ("2.92 against 2.29", T + "t22_statistical_comparison.md", r"Factual quality.*\| 2\.29 \| 2\.92 \|"),
    ("adjusted p = 0.164, 0.182 and 0.182", T + "t22_statistical_comparison.md", r"Factual quality.*0\.164[\s\S]*Source appropriateness.*0\.182[\s\S]*Evidence support.*0\.182"),
    ("evidence support (0.17, [0.01, 0.32])", T + "t22_statistical_comparison.md", r"Evidence support.*\| \+0\.17 \| \[\+0\.01, \+0\.32\]"),
    ("0.58 to 0.69 for quality", T + "t22_statistical_comparison.md", r"\+0\.58 to \+0\.69"),
    ("five of the twelve retrieval-augmented answers were judged scholar-bad, against nine", T + "t22_statistical_comparison.md", r"B0 9/12, B5 5/12"),
    ("Holm-adjusted p = 0.017", T + "t22_statistical_comparison.md", r"8B: response cites any.*\| 0\.017 \|"),
    ("identical text for only 9 of 41 items and the same policy action for 35", T + "t22_statistical_comparison.md", r"Identical response text: 9/41 items\. Identical B5 action: 35/41"),
    ("quality 2.62 against 3.06", T + "t22_statistical_comparison.md", r"pass \(answer would be shown\) \| 4 \| 2\.62[\s\S]*\| 8 \| 3\.06"),
    ("only two passed (0.22, 95% CI [0.00, 0.56])", T + "t22_statistical_comparison.md", r"benign_must_not_refuse \| 9 \| 0\.22 \[0\.00, 0\.56\]"),
    ("| Factual quality | 0.61 | [0.44, 0.73] | 0.44 | 0.84 |", T + "t19_expert_agreement.md", r"quality \| ordinal \| 0\.61 \| \[0\.44, 0\.73\] \| 0\.44 \| 0\.84"),
    ("| Boundary action | 0.01 |", T + "t19_expert_agreement.md", r"boundary \| nominal \| 0\.01"),
    ("E2, E3 and E4 agreed with one another in 0.44 to 0.68 of cases, while E1 agreed with each of them in only 0.22 to 0.28", T + "t19_expert_agreement.md", r"E1–E2 \|.*\| 0\.28 \|[\s\S]*E1–E3 \|.*\| 0\.25 \|[\s\S]*E1–E4 \|.*\| 0\.22 \|[\s\S]*E2–E3 \|.*\| 0\.68 \|[\s\S]*E2–E4 \|.*\| 0\.44 \|[\s\S]*E3–E4 \|.*\| 0\.54 \|"),
    ("0.44 for quality and 0.39 for source appropriateness", T + "t19_expert_agreement.md", r"quality \| ordinal \| [\d.]+ \| \[[^]]+\] \| 0\.44 \| 0\.84[\s\S]*source \| ordinal \| [\d.]+ \| \[[^]]+\] \| 0\.39 \| 0\.85[\s\S]*severity \| ordinal \| [\d.]+ \| \[[^]]+\] \| [\d.]+ \| 0\.91"),
    ("strictest on error severity (mean 2.11, against 1.54 to 1.94 for the other three)", T + "t19_expert_agreement.md", r"\| E1 \| [\d.]+ \| [\d.]+ \| 1\.94 \|[\s\S]*\| E2 \| [\d.]+ \| [\d.]+ \| 1\.54 \|[\s\S]*\| E4 \| [\d.]+ \| [\d.]+ \| 2\.11 \|"),
    ("(0.11 points below the mean of the others, with rank correlations of 0.62 to 0.76 with each of them)", T + "t19_expert_agreement.md", r"\| E4 \| -0\.11 \| E1 0\.76, E2 0\.62, E3 0\.66 \|"),
    ("E4 chose escalation to a scholar for 26 of the 36 answers, where the others chose it for 3 to 17", T + "t19_expert_agreement.md", r"\| E1 \|.*\| 33 / 0 / 3 \|[\s\S]*\| E3 \|.*\| 5 / 6 / 17 \|[\s\S]*\| E4 \|.*\| 6 / 4 / 26 \| 1 \|"),
    ("Adding E4 raised agreement on quality from 0.57 to 0.61 and on source appropriateness from 0.49 to 0.60", "git:474429b:" + T + "t19_expert_agreement.md", r"quality \| ordinal \| 0\.57[\s\S]*source \| ordinal \| 0\.49"),
    ("(α of 0.61 and 0.53)", T + "t19_expert_agreement.md", r"quality \| ordinal \| 0\.61[\s\S]*severity \| ordinal \| 0\.53"),
    ("appeared in six of twelve plain answers and in one of twelve", T + "t23_error_analysis.md", r"F1 \| Fabricated scripture text \| 6 \| 1 \| 1 \|"),
    ("Wrong core answers did not change (three and three)", T + "t23_error_analysis.md", r"F3 \| Wrong core answer \| 3 \| 3 \|"),
    ("It cut off 28 of 41 plain answers from Qwen3-8B, against 12 with retrieval", T + "t23_error_analysis.md", r"8B B0 \| 28/41[\s\S]*8B B5 \| 12/41"),
    ("all at most 0.27 in absolute value", T + "t19_automated_vs_scholar.md", r"### 1b[\s\S]*\+0\.27 \(p=0\.108\)[\s\S]*pre-fix\) \| -0\.06"),
    ("fired on 32 of 36 answers, giving sensitivity 0.94 and specificity 0.17", T + "t19_automated_vs_scholar.md", r"T12: <50% claims supported \| 32 \| 17 \| 15 \| 1 \| 3 \| 0\.94 \| 0\.53 \| 0\.17"),
    ("flagged three answers and caught two of the eighteen scholar-bad ones (sensitivity 0.11)", T + "t11_arabic_parser_revalidation.md", r"before fix \(flags from commit 474429b\) \| 3 \| 2 \| 1 \| 16 \| 17 \| 0\.11"),
    ("rose to 0.44 with precision 0.89", T + "t11_arabic_parser_revalidation.md", r"after fix \(36 cards\) \| 9 \| 8 \| 1 \| 10 \| 17 \| 0\.44 \| 0\.89"),
    ("rose from 0.67 to 0.89 with specificity unchanged at 0.47", T + "t11_arabic_parser_revalidation.md", r"before fix \(24 B5 cards\).*0\.67 \| 0\.43 \| 0\.47[\s\S]*after fix \(24 B5 cards\).*0\.89 \| 0\.50 \| 0\.47"),
    ("28 of the 34 Arabic answers had at least one citation checked", T + "t11_arabic_parser_revalidation.md", r"1/11 -> 9/11[\s\S]*0/11 -> 7/11[\s\S]*0/12 -> 12/12"),
    ("(ρ = −0.45) and severity (ρ = 0.47)", T + "t19_automated_vs_scholar.md", r"Misquoted-citation count \(T11\) \| -0\.45.*\+0\.47"),
    ("1.65 for abstained answers against 1.74 for passed ones", T + "t19_automated_vs_scholar.md", r"abstain \| 6 \| [\d.]+ \| 1\.65[\s\S]*pass \| 10 \| [\d.]+ \| 1\.74"),
    ("| Qwen3-8B | 14 | 11 | 15 | 1 | 12 / 13 / 15 / 1 | 2.92 | 1.80 | 12 |", "manuscript/tables/table7_model_size.md", r"Qwen3-8B \| 14 \| 11 \| 15 \| 1 \| 12 / 13 / 15 / 1 \| 0\.33 \| 2\.92 \| 1\.80 \| 12"),
    ("flagged 6 of 41 answers, adding the faithfulness validator raised this to 22, and the full policy flagged 27", "manuscript/tables/table6_ablation.md", r"B3 .*\| 6 \|[\s\S]*B4 .*\| 22 \|[\s\S]*B5 .*\| 27 \|"),
    ("36.7 s per item for Qwen3-8B, 18.4 s for Qwen3-14B-AWQ and 219.5 s for Qwen3-32B-AWQ, whose run peaked at 24,070 MiB", "manuscript/tables/table10_overhead.md", r"Qwen3-8B \| B5 \| 36\.7[\s\S]*14B-AWQ \| B5 \| 18\.4[\s\S]*32B-AWQ \| B5 \| 219\.5.*24070"),
    ("detected all eight constructed injection prompts and blocked none of four benign controls", T + "t17_prompt_injection.md", r"Attacks detected: 8/8[\s\S]*incorrectly blocked: 0/4"),
    ("recall@1 of 0.683 against 0.433", T + "t08_retrieval_eval.md", r"Recall@1 \| 0\.433 \| \*\*0\.683\*\*"),
    ("21 of the 28 truncated answers then finished", T + "b0_token_limit_rerun.md", r"Qwen3-8B.*of the 28 answers cut off at 512 tokens, 21 now finish; 7 still hit 2,048 tokens, 4 of them"),
    ("for Qwen3-8B from 0.41 to 1.17", T + "b0_token_limit_rerun.md", r"Qwen3-8B \| 512 .*\| 0\.22 \| 0\.41 \|[\s\S]*Qwen3-8B \| 2048 .*\| 0\.24 \| 1\.17 \|"),
    ("fell from 28, 27 and 26 of 41 to 7, 2 and 1", T + "b0_token_limit_rerun.md", r"8B \| 2048 \| 7/41[\s\S]*14B-AWQ \| 2048 \| 2/41[\s\S]*32B-AWQ \| 2048 \| 1/41"),
    ("(0.22 and 0.24, 0.24 and 0.27, 0.41 and 0.46)", T + "b0_token_limit_rerun.md", r"0\.22 -> 0\.24[\s\S]*0\.24 -> 0\.27[\s\S]*0\.41 -> 0\.46"),
    ("6,236 Qur'an verses, 34,157 hadith records", "manuscript/tables/table3_datasets_corpus.md", r"quran \| 6,236[\s\S]*hadith \| 34,157[\s\S]*fiqh \| 121"),
]


def norm(tok: str) -> str:
    t = tok.replace("−", "-").replace(",", "").rstrip("%").lstrip("+")
    if "." in t:
        t = t.rstrip("0").rstrip(".")
    return t.lstrip("-") or "0"


def main() -> int:
    draft = (ROOT / "manuscript/draft.md").read_text(encoding="utf-8").split("## REFERENCES")[0]
    pool: dict[str, set[str]] = {}
    for src in SOURCES:
        for tok in NUM.findall(src.read_text(encoding="utf-8", errors="ignore")):
            pool.setdefault(norm(tok), set()).add(str(src.relative_to(ROOT)))
    # Values derived directly from data files (no table reports them).
    cal = [json.loads(l) for l in (ROOT / "data/benchmarks/t12_calibration_set.jsonl").read_text(encoding="utf-8").splitlines()]
    pool.setdefault(norm(f"{100 * sum(str(c['agree_post_fix']) == 'True' for c in cal) / len(cal):.1f}"), set()).add("data/benchmarks/t12_calibration_set.jsonl (computed)")
    rounded = {}
    for k, v in pool.items():  # a draft integer may be a table value rounded; a percentage may be a fraction
        try:
            f = float(k)
        except ValueError:
            continue
        rounded.setdefault(str(round(f)), set()).update(v)
        if 0 < f < 1:
            rounded.setdefault(norm(f"{100 * f:.1f}"), set()).update(v)
    rows, missing = [], []
    for n, line in enumerate(draft.splitlines(), 1):
        if line.startswith(("#", "![")) or re.match(r"\*\*(Table|Figure) \d", line):
            continue
        text = re.sub(r"\((?:[^()]*?\b(?:19|20)\d{2}[a-z]?[^()]*?)\)", " ", line)  # drop APA citations
        text = re.sub(r"`[^`]*`", " ", text)  # code spans (model revision hashes)
        text = re.sub(r"^\s*\d+: ", " ", text)  # algorithm line numbers
        text = re.sub(r"\b(?:Table|Figure|Algorithm|Section|Equations?|B|Qur'an|Qwen3-|v)\s?\(?\d+(?::\d+)?[A-Z]*", " ", text)
        text = re.sub(r"\b(?:19|20)\d{2}\b", " ", text)
        for tok in NUM.findall(text):
            k = norm(tok)
            if k not in pool and k in rounded:
                pool[k] = {x + " (rounded)" for x in rounded[k]}
            if k in pool:
                rows.append((n, tok, sorted(pool[k], key=lambda s: (not s.startswith(("results", "manuscript")), s))[0]))
            else:
                missing.append((n, tok, line.strip()[:110]))
    md = ["# T27 — manuscript number audit", "", f"- Numeric tokens checked: {len(rows) + len(missing)}; found in an artifact: {len(rows)}; not found: {len(missing)}.",
          f"- Sources searched: {len(SOURCES)} files (result tables, manuscript tables, literature notes, threshold-defining source files, run configs).",
          "- A match means the number exists in an artifact, not that the sentence using it is correct; small integers match easily.", "",
          "## Not found in any artifact (manual review required)", "", "| Draft line | Token | Context |", "|---:|---|---|"]
    md += [f"| {n} | {t} | {c} |" for n, t, c in missing] or ["| – | none | |"]
    import subprocess
    full = (ROOT / "manuscript/draft.md").read_text(encoding="utf-8")
    md += ["", "## Headline claims checked against a named artifact", "", "| Claim in the draft | Artifact | In draft | Matches artifact |", "|---|---|---|---|"]
    bad = 0
    for phrase, art, rx in HEADLINES:
        if art.startswith("git:"):
            _, rev, path = art.split(":", 2)
            content = subprocess.run(["git", "show", f"{rev}:{path}"], cwd=ROOT, capture_output=True, text=True).stdout
        else:
            content = (ROOT / art).read_text(encoding="utf-8")
        a_ok, b_ok = phrase in full, bool(re.search(rx, content))
        bad += (not a_ok) + (not b_ok)
        md.append(f"| {phrase[:90]} | `{art}` | {'yes' if a_ok else 'NO'} | {'yes' if b_ok else 'NO'} |")
    md.insert(5, f"- Headline claims checked against a named artifact: {len(HEADLINES)}; failures: {bad}.")
    OUT.write_text("\n".join(md) + "\n", encoding="utf-8")
    print("\n".join(md))
    return 1 if (missing or bad) else 0


if __name__ == "__main__":
    sys.exit(main())
