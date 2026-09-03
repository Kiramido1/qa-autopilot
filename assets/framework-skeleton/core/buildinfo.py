"""Build identity for the run metadata: a result without a build id is not reproducible."""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Optional


def _git(repo: Path, *args: str) -> Optional[str]:
    try:
        output = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, timeout=5, check=False)
    except (OSError, subprocess.SubprocessError):
        return None
    return output.stdout.strip() if output.returncode == 0 else None


def app_build_info(repo: Path, build_id: Optional[str] = None) -> dict:
    sha = _git(repo, "rev-parse", "HEAD")
    branch = _git(repo, "rev-parse", "--abbrev-ref", "HEAD")
    dirty = None
    if sha:
        status = _git(repo, "status", "--porcelain")
        dirty = bool(status) if status is not None else None
    return {
        "build_id": build_id,
        "repo": str(repo),
        "git_sha": sha,
        "git_branch": branch,
        "git_dirty": dirty,
    }
