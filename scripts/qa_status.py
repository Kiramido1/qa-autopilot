#!/usr/bin/env python3
"""Resume helper for the selenium-qa-automation skill.

    python scripts/qa_status.py /path/to/repo            # qa-artifacts/ + qa/reports/ of that repo
    python scripts/qa_status.py /path/to/repo --json     # machine-readable

Reads qa-artifacts/ and the latest qa/reports/<run-id>/report.json and prints,
per artifact, whether it is missing, still a template (EXAMPLE markers or empty
sections) or finished, plus the first gate whose deliverable is not finished.
The resume protocol in SKILL.md starts from that gate. Exit code 0 always —
this is information, not a check.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

# (artifact, gate label, order) — the order is the gate order, so the first
# unfinished entry is where work resumes.
ARTIFACTS = [
    ("environment-map.md", "Gate 0"),
    ("repository-recon.md", "Gate 1"),
    ("feature-inventory.md", "Gate 2"),
    ("test-strategy.md", "Gate 3"),
    ("test-cases.md", "Gate 4"),
    ("execution-report.md", "Gate 13"),
    ("defects.md", "Gate 14"),
    ("regression-report.md", "Gates 15-16"),
    ("coverage-gaps.md", "Gate 21"),
    ("traceability-matrix.md", "generated (run_tests.py --traceability)"),
]
EXAMPLE_MARKER = re.compile(r"\bEXAMPLE\b")
EMPTY_FIELD = re.compile(r"^\s*-\s*[^:\n]+:\s*(<!--.*-->)?\s*$", re.MULTILINE)


def artifact_state(path: Path) -> tuple[str, str]:
    if not path.is_file():
        return "missing", "not created (scaffold_qa.py --with-artifacts, or write it)"
    text = path.read_text(encoding="utf-8", errors="replace")
    body = "\n".join(line for line in text.splitlines() if not line.lstrip().startswith(">"))
    examples = len(EXAMPLE_MARKER.findall(body))
    empties = len(EMPTY_FIELD.findall(body))
    words = len(re.findall(r"\w+", body))
    if path.name == "traceability-matrix.md" and "Generated" in text and "--traceability" in text:
        return "generated", "regenerate after the next run"
    if examples:
        return "template", f"{examples} EXAMPLE marker(s) still present"
    if words < 60:
        return "template", "too short to be a filled artifact"
    if empties > 3:
        return "partial", f"{empties} empty fields"
    return "finished", ""


def latest_run(reports_dir: Path) -> dict | None:
    candidates = sorted(reports_dir.glob("*/report.json")) if reports_dir.is_dir() else []
    if not candidates:
        return None
    report = json.loads(candidates[-1].read_text(encoding="utf-8"))
    results = report.get("results", [])
    unclassified = [r["id"] for r in results if r.get("classification") == "UNCLASSIFIED"]
    return {
        "run_id": report.get("run", {}).get("run_id", candidates[-1].parent.name),
        "totals": report.get("totals", {}),
        "unclassified": unclassified,
        "path": str(candidates[-1]),
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("repo", help="repository under test")
    parser.add_argument("--artifacts", default="qa-artifacts", help="artifacts directory relative to the repo")
    parser.add_argument("--qa", default="qa", help="framework directory relative to the repo")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    repo = Path(args.repo).resolve()
    artifacts_dir = repo / args.artifacts
    rows = []
    resume_at = None
    for name, gate in ARTIFACTS:
        state, detail = artifact_state(artifacts_dir / name)
        rows.append({"artifact": name, "gate": gate, "state": state, "detail": detail})
        if resume_at is None and state in ("missing", "template", "partial") and name != "traceability-matrix.md":
            resume_at = gate
    run = latest_run(repo / args.qa / "reports")

    if args.json:
        print(json.dumps({"repo": str(repo), "artifacts": rows, "latest_run": run, "resume_at": resume_at or "Gate 21 review"}, indent=2))
        return 0

    print(f"QA status for {repo}")
    if not artifacts_dir.is_dir():
        print(f"  {artifacts_dir} does not exist — nothing has been started; begin at Gate 0.")
    width = max(len(r["artifact"]) for r in rows)
    for r in rows:
        print(f"  {r['artifact']:<{width}}  {r['state']:<9}  {r['gate']}" + (f" — {r['detail']}" if r["detail"] else ""))
    if run:
        totals = run["totals"]
        print(
            f"\nLatest run {run['run_id']}: {totals.get('PASS', 0)} pass · {totals.get('FAIL', 0)} fail · "
            f"{totals.get('ERROR', 0)} error · {totals.get('FLAKY', 0)} flaky · {totals.get('SKIP', 0)} skip"
        )
        if run["unclassified"]:
            print(f"  UNCLASSIFIED results to triage (Gate 14): {', '.join(run['unclassified'])}")
    else:
        print("\nNo runs found under qa/reports/ — Gate 13 has not executed yet.")
    print(f"\nResume at: {resume_at or 'Gate 21 review (every artifact is finished)'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
