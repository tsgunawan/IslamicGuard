"""One-off sanity check (T11): run the deterministic Qur'an/Hadith validators against
the real B2 (standard RAG) responses from T10, to see whether the models' actual
generations contain parseable citations, and if so, what the validators find.

Not exhaustive and not a benchmark (that's T14+) -- just confirms the validators
have something real to bite on before they're wired into the B3 pipeline, and
reports honestly if a given run's responses don't contain parseable citations.
"""

from __future__ import annotations

import glob
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from src.validators.hadith_validator import validate_text as validate_hadith  # noqa: E402
from src.validators.quran_validator import validate_text as validate_quran  # noqa: E402

run_dirs = sorted(glob.glob(str(REPO_ROOT / "runs" / "*_B2_*")))
print(f"Found {len(run_dirs)} B2 run directories: {[Path(d).name for d in run_dirs]}\n")

total_responses = 0
quran_hits, hadith_hits = 0, 0
quran_flags: dict[str, int] = {}
hadith_flags: dict[str, int] = {}

for run_dir in run_dirs:
    resp_path = Path(run_dir) / "responses.jsonl"
    if not resp_path.exists():
        continue
    with resp_path.open(encoding="utf-8") as f:
        for line in f:
            rec = json.loads(line)
            total_responses += 1
            text = rec.get("response_text", "")
            qchecks = validate_quran(text)
            hchecks = validate_hadith(text)
            if qchecks:
                quran_hits += 1
                for c in qchecks:
                    quran_flags[c.flag.value] = quran_flags.get(c.flag.value, 0) + 1
                    print(f"[QURAN] {Path(run_dir).name} / {rec['item_id']}: {c.to_dict()}")
            if hchecks:
                hadith_hits += 1
                for c in hchecks:
                    hadith_flags[c.flag.value] = hadith_flags.get(c.flag.value, 0) + 1
                    print(f"[HADITH] {Path(run_dir).name} / {rec['item_id']}: {c.to_dict()}")

print(f"\n--- Summary ---")
print(f"Total responses scanned: {total_responses}")
print(f"Responses with >=1 parseable Qur'an citation: {quran_hits} ({quran_flags})")
print(f"Responses with >=1 parseable Hadith citation: {hadith_hits} ({hadith_flags})")
