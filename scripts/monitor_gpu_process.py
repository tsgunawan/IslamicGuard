"""Record GPU-memory and utilization samples for one long-running experiment process.

This is intentionally a standalone monitor: inference scripts can be interrupted or run under
an external scheduler, but the efficiency report still needs machine-collected (not manually
transcribed) peak-memory evidence.  It appends JSONL samples until the target PID exits.

Usage:
    python scripts/monitor_gpu_process.py --pid 1234 --out runs/<run_id>/gpu_samples.jsonl
"""

from __future__ import annotations

import argparse
import json
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path


def process_exists(pid: int) -> bool:
    """Check the GPU process list instead of signalling a cross-namespace PID.

    On WSL2 the process ID reported by ``nvidia-smi`` can be visible to the GPU driver but not
    to this monitor's Linux PID namespace.  ``os.kill(pid, 0)`` would then falsely report that
    an otherwise-active experiment exited.
    """
    result = subprocess.run(
        ["nvidia-smi", "--query-compute-apps=pid", "--format=csv,noheader,nounits"],
        capture_output=True,
        check=True,
        text=True,
    )
    return str(pid) in {line.strip() for line in result.stdout.splitlines() if line.strip()}


def gpu_snapshot() -> dict[str, int | None]:
    """Return the device-wide state for the single-GPU experiment host."""
    result = subprocess.run(
        [
            "nvidia-smi",
            "--query-gpu=memory.total,memory.used,utilization.gpu",
            "--format=csv,noheader,nounits",
        ],
        capture_output=True,
        check=True,
        text=True,
    )
    fields = [field.strip() for field in result.stdout.splitlines()[0].split(",")]
    return {
        "memory_total_mib": int(fields[0]),
        "memory_used_mib": int(fields[1]),
        "gpu_utilization_pct": int(fields[2]),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pid", required=True, type=int, help="Experiment process ID")
    parser.add_argument("--out", required=True, type=Path, help="JSONL output path")
    parser.add_argument("--interval-seconds", type=float, default=5.0)
    args = parser.parse_args()
    if args.interval_seconds <= 0:
        parser.error("--interval-seconds must be positive")

    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("a", encoding="utf-8") as handle:
        while process_exists(args.pid):
            sample = {
                "timestamp_utc": datetime.now(timezone.utc).isoformat(),
                "pid": args.pid,
                **gpu_snapshot(),
            }
            handle.write(json.dumps(sample) + "\n")
            handle.flush()
            time.sleep(args.interval_seconds)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
