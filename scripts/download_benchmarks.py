"""T06: reproducibly acquire the benchmark datasets identified in the literature review.

Downloads into data/raw/<dataset_name>/ (gitignored except DATASET_CARD.md — see .gitignore).
Run from the repo root with the `islamicguard` conda environment active:

    conda activate islamicguard
    python scripts/download_benchmarks.py

Idempotent: re-running skips datasets whose target directory already has a DATASET_CARD.md.
Does not fabricate a successful download — any failure is printed and the script continues with
the remaining datasets rather than silently skipping (see paper.md §0).
"""

from __future__ import annotations

import hashlib
import shutil
import subprocess
import sys
from pathlib import Path

import requests
from huggingface_hub import snapshot_download

REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_RAW = REPO_ROOT / "data" / "raw"

HF_DATASETS: list[str] = [
    "MBZUAI/FiqhQA",
    "QCRI/IslamicFaithQA",
    "Bekhouche/HalluTruthQA-4K",
]

GIT_REPOS: dict[str, str] = {
    "islamiceval_quran_hadith_qa_2025": "https://gitlab.com/bigirqu/quran-hadith-qa-2025.git",
    "islamiceval_subtask1": "https://github.com/qcri/IslamicEval-2025-Subtask-1.git",
}

# github.com/qcri/IslamicEval-2025-Subtask-1's Hadith/six_hadith_books.json is stored via Git LFS.
# git-lfs was not installable in the original acquisition environment (no passwordless sudo), so
# the LFS object is fetched directly from the media endpoint and its SHA-256 verified against the
# hash declared in the LFS pointer file, rather than trusting an un-verified download.
LFS_OBJECTS: list[dict[str, str]] = [
    {
        "repo_dir": "islamiceval_subtask1",
        "path": "Hadith/six_hadith_books.json",
        "media_url": (
            "https://media.githubusercontent.com/media/qcri/"
            "IslamicEval-2025-Subtask-1/main/Hadith/six_hadith_books.json"
        ),
        "expected_sha256": "92ba74e2847a3ac10c4ba25835bc7c16c7a449cd7594828da585437e61cca6cc",
    },
]


_RECORD_FILES = {"DATASET_CARD.md", "MANIFEST.sha256"}


def already_done(target_dir: Path) -> bool:
    """True only if the directory holds dataset files. The dataset card and manifest are tracked
    in git, so on a fresh clone they exist while the data does not; they must not count."""
    return target_dir.exists() and any(p.name not in _RECORD_FILES for p in target_dir.iterdir())


def download_hf_datasets() -> None:
    for repo_id in HF_DATASETS:
        target_dir = DATA_RAW / repo_id.split("/")[-1]
        if already_done(target_dir):
            print(f"[skip] {repo_id}: data already present at {target_dir}")
            continue
        print(f"[download] {repo_id} -> {target_dir}")
        try:
            snapshot_download(repo_id=repo_id, repo_type="dataset", local_dir=str(target_dir))
        except Exception as exc:  # noqa: BLE001 - report and continue, don't abort the whole run
            print(f"[FAILED] {repo_id}: {exc}", file=sys.stderr)


def clone_git_repos() -> None:
    for dir_name, url in GIT_REPOS.items():
        target_dir = DATA_RAW / dir_name
        if already_done(target_dir):
            print(f"[skip] {dir_name}: data already present")
            continue
        print(f"[clone] {url} -> {target_dir}")
        # Clone beside the target, then copy in: the target already holds the tracked dataset card,
        # and git refuses to clone into a non-empty directory. The nested .git is not kept.
        tmp_dir = target_dir.with_name(target_dir.name + ".clone_tmp")
        shutil.rmtree(tmp_dir, ignore_errors=True)
        result = subprocess.run(["git", "clone", "--depth", "1", url, str(tmp_dir)], capture_output=True, text=True)
        if result.returncode != 0:
            print(f"[FAILED] git clone {url}: {result.stderr}", file=sys.stderr)
            continue
        shutil.copytree(tmp_dir, target_dir, dirs_exist_ok=True,
                        ignore=lambda d, names: [n for n in names if n == ".git" or (Path(d) == tmp_dir and n in _RECORD_FILES)])
        shutil.rmtree(tmp_dir, ignore_errors=True)


def resolve_lfs_objects() -> None:
    for obj in LFS_OBJECTS:
        target_path = DATA_RAW / obj["repo_dir"] / obj["path"]
        if not target_path.exists():
            print(f"[skip] LFS object {target_path}: repo not cloned yet")
            continue
        content = target_path.read_bytes()
        if content.startswith(b"version https://git-lfs.github.com/spec/v1"):
            print(f"[resolve-lfs] {target_path} is an LFS pointer; fetching real object")
            response = requests.get(obj["media_url"], timeout=120)
            response.raise_for_status()
            digest = hashlib.sha256(response.content).hexdigest()
            if digest != obj["expected_sha256"]:
                print(
                    f"[FAILED] {target_path}: SHA-256 mismatch "
                    f"(got {digest}, expected {obj['expected_sha256']}) — NOT writing file",
                    file=sys.stderr,
                )
                continue
            target_path.write_bytes(response.content)
            print(f"[ok] {target_path}: SHA-256 verified, {len(response.content)} bytes written")
        else:
            print(f"[ok] {target_path}: already a real file (not an LFS pointer)")


if __name__ == "__main__":
    DATA_RAW.mkdir(parents=True, exist_ok=True)
    download_hf_datasets()
    clone_git_repos()
    resolve_lfs_objects()
    print(
        "\nDone. Dataset cards (data/raw/*/DATASET_CARD.md) document license, size, and "
        "provenance for each dataset actually obtained. See data/raw/PENDING_DATASETS.md for "
        "anything that could not be lawfully/fully acquired."
    )
