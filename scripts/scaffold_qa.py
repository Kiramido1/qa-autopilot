#!/usr/bin/env python3
"""Copy the framework skeleton (and optionally the qa-artifacts templates)
into a target repository.

    python scripts/scaffold_qa.py /path/to/repo                    # -> /path/to/repo/qa/
    python scripts/scaffold_qa.py /path/to/repo --dest tests/qa     # custom location
    python scripts/scaffold_qa.py /path/to/repo --with-artifacts    # also /path/to/repo/qa-artifacts/

Existing files are never overwritten (they are reported as skipped), so
re-running after adapting the framework is safe.
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parent.parent
SKELETON = SKILL_ROOT / "assets" / "framework-skeleton"
ARTIFACT_TEMPLATES = SKILL_ROOT / "assets" / "artifact-templates"
IGNORED = {"__pycache__", "reports", ".pyc", ".cache", ".mypy_cache", ".ruff_cache", ".env"}


def copy_tree(source: Path, target: Path) -> tuple[int, int]:
    created = skipped = 0
    for path in sorted(source.rglob("*")):
        if any(part in IGNORED for part in path.parts) or path.suffix in IGNORED:
            continue
        destination = target / path.relative_to(source)
        if path.is_dir():
            destination.mkdir(parents=True, exist_ok=True)
            continue
        if destination.exists():
            skipped += 1
            print(f"  skip   {destination}")
            continue
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, destination)
        created += 1
        print(f"  create {destination}")
    return created, skipped


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("repo", help="path to the repository under test")
    parser.add_argument("--dest", default="qa", help="framework directory relative to the repo (default: qa)")
    parser.add_argument("--with-artifacts", action="store_true", help="also create qa-artifacts/ from the templates")
    args = parser.parse_args(argv)

    repo = Path(args.repo).resolve()
    if not repo.is_dir():
        print(f"not a directory: {repo}")
        return 2
    if not SKELETON.is_dir():
        print(f"skeleton missing: {SKELETON}")
        return 2

    qa_dir = repo / args.dest
    print(f"Framework -> {qa_dir}")
    created, skipped = copy_tree(SKELETON, qa_dir)
    totals = [f"framework: {created} created, {skipped} skipped"]

    if args.with_artifacts:
        artifacts_dir = repo / "qa-artifacts"
        print(f"Artifacts -> {artifacts_dir}")
        a_created, a_skipped = copy_tree(ARTIFACT_TEMPLATES, artifacts_dir)
        totals.append(f"artifacts: {a_created} created, {a_skipped} skipped")

    print("\n" + " | ".join(totals))
    print(
        "\nNext steps:\n"
        f"  cd {qa_dir}\n"
        "  pip install -r requirements.txt\n"
        "  cp .env.example .env      # fill URLs and disposable test accounts\n"
        "  python run_tests.py --selftest      # prove the runner before trusting a result\n"
        "  python run_tests.py --list\n"
        "  python run_tests.py --smoke         # Gate 0 exit criterion: ENV-* executed\n"
        "Then replace the EXAMPLE page objects, flows and tests with the real ones, and\n"
        "regenerate the matrix with: python run_tests.py --traceability"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
