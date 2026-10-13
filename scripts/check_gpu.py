"""Validate that PyTorch sees the RTX 4090 with CUDA support (paper.md section 7.7).

Run inside the ``islamicguard`` conda environment:

    conda activate islamicguard
    python scripts/check_gpu.py
"""

from __future__ import annotations

import sys

import torch


def main() -> int:
    print("torch:", torch.__version__)
    cuda_available = torch.cuda.is_available()
    print("cuda available:", cuda_available)
    print("torch cuda:", torch.version.cuda)

    if not cuda_available:
        print("FAIL: torch.cuda.is_available() is False; do not proceed to model downloads.")
        return 1

    print("gpu:", torch.cuda.get_device_name(0))
    print("bf16 supported:", torch.cuda.is_bf16_supported())

    x = torch.randn(4096, 4096, device="cuda", dtype=torch.bfloat16)
    y = x @ x
    torch.cuda.synchronize()
    print("cuda matmul check: ok, result dtype", y.dtype, "device", y.device)
    print(
        "allocated_mb:",
        round(torch.cuda.memory_allocated() / (1024**2), 2),
        "reserved_mb:",
        round(torch.cuda.memory_reserved() / (1024**2), 2),
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
