"""Derived traceability matrix.

Feature → Behavior → Test case → Automation → Result, regenerated from three
sources that already exist instead of a fourth one maintained by hand:

  qa-artifacts/test-cases.md        "## TC-AUTH-001 — title" sections with "test id in code: `AUTH-001`"
  the @test registry                id, feature, priority, module/file
  reports/<run-id>/report.json      last status per id (latest run unless --from-run)
  qa-artifacts/execution-report.md  the classification written for each FAIL/ERROR/FLAKY
                                    (a block that names the test id and a triage category)

    python run_tests.py --traceability                  # writes qa-artifacts/traceability-matrix.md
    python run_tests.py --traceability --from-run 20260903-101500
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

_SECTION = re.compile(r"^##\s+(TC-[A-Z0-9-]+)\s+[—–-]\s+(.+?)\s*$", re.MULTILINE)
_CODE_ID = re.compile(r"test id in code:\s*`?([A-Z][A-Z0-9]*-\d+)`?", re.IGNORECASE)
_FEATURE = re.compile(r"-\s*Feature:\s*([^|\n]*)")
_PRIORITY = re.compile(r"Priority:\s*(P[0-3])")
_TEST_ID = re.compile(r"\b([A-Z][A-Z0-9]*-\d{3,})\b")
CATEGORIES = (
    "REAL_APPLICATION_BUG",
    "AUTOMATION_BUG",
    "LOCATOR_FAILURE",
    "SYNCHRONIZATION_FAILURE",
    "TEST_DATA_FAILURE",
    "AUTHENTICATION_FAILURE",
    "AUTHORIZATION_FAILURE",
    "ENVIRONMENT_FAILURE",
    "NETWORK_FAILURE",
    "INFRASTRUCTURE_FAILURE",
    "DEPENDENCY_FAILURE",
    "FLAKY_TEST",
    "UNKNOWN",
)


def parse_test_cases(path: Path) -> list[dict]:
    if not path.is_file():
        return []
    text = path.read_text(encoding="utf-8")
    matches = list(_SECTION.finditer(text))
    cases = []
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        body = text[match.end() : end]
        feature = _FEATURE.search(body)
        priority = _PRIORITY.search(body)
        cases.append(
            {
                "tc_id": match.group(1),
                "title": match.group(2).strip(),
                "feature": feature.group(1).strip() if feature else "",
                "priority": priority.group(1) if priority else "",
                "automation_ids": [m.upper() for m in _CODE_ID.findall(body)],
            }
        )
    return cases


def parse_classifications(path: Path) -> dict[str, str]:
    """Test id -> category from the consolidated execution report.

    A block is a top-level bullet or heading plus its indented continuation
    lines. When a block names test ids and a category, every id in it gets
    that category; a later block overrides an earlier one (re-triage wins).
    """
    if not path.is_file():
        return {}
    blocks: list[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            blocks.append("")
        elif line.startswith((" ", "\t")) and blocks and blocks[-1]:
            blocks[-1] += "\n" + line
        else:
            blocks.append(line)
    found: dict[str, str] = {}
    for block in blocks:
        ids = {i for i in _TEST_ID.findall(block) if not i.startswith("BUG-")}
        category = next((c for c in CATEGORIES if c in block), None)
        if ids and category:
            for test_id in ids:
                found[test_id] = category
    return found


def latest_report(reports_dir: Path) -> Optional[Path]:
    candidates = sorted(reports_dir.glob("*/report.json")) if reports_dir.is_dir() else []
    return candidates[-1] if candidates else None


def load_results(report_path: Optional[Path]) -> tuple[dict, str]:
    if not report_path or not report_path.is_file():
        return {}, ""
    report = json.loads(report_path.read_text(encoding="utf-8"))
    return {r["id"]: r for r in report.get("results", [])}, report.get("run", {}).get("run_id", "")


def build_matrix(tests, test_cases_path: Path, reports_dir: Path, qa_root: Path, run_id: Optional[str] = None) -> str:
    cases = parse_test_cases(test_cases_path)
    registry = {t.id: t for t in tests}
    report_path = reports_dir / run_id / "report.json" if run_id else latest_report(reports_dir)
    results, run_label = load_results(report_path)
    triage = parse_classifications(test_cases_path.parent / "execution-report.md")

    rows: list[str] = []
    covered_ids: set[str] = set()
    uncovered: list[str] = []
    for case in cases:
        if not case["automation_ids"]:
            uncovered.append(f"- {case['tc_id']} — {case['title']} → no automation id declared")
            rows.append(f"| {case['feature']} | {case['title']} | {case['tc_id']} | — | — | not automated |")
            continue
        for auto_id in case["automation_ids"]:
            covered_ids.add(auto_id)
            registered = registry.get(auto_id)
            result = results.get(auto_id)
            automation = (
                f"`{auto_id}` · {_relative(registered.file, qa_root)}" if registered else f"`{auto_id}` · **not found in registry**"
            )
            last = f"{result['status']} ({run_label})" if result else "not run"
            note = ""
            if result and result.get("classification"):
                note = triage.get(auto_id) or result["classification"]
            elif registered and registered.priority and case["priority"] and registered.priority != case["priority"]:
                note = f"priority mismatch: case {case['priority']} vs code {registered.priority}"
            rows.append(
                f"| {case['feature'] or (registered.feature if registered else '')} | {case['title']} | {case['tc_id']} | {automation} | {last} | {note} |"
            )

    orphans = [t for t in tests if t.id not in covered_ids]
    for t in sorted(orphans, key=lambda x: x.id):
        result = results.get(t.id)
        last = f"{result['status']} ({run_label})" if result else "not run"
        rows.append(
            f"| {t.feature} | {t.description or t.name} | — | `{t.id}` · {_relative(t.file, qa_root)} | {last} | automation without a test case |"
        )

    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = [
        "# Traceability matrix",
        "",
        f"> Generated {stamp} by `run_tests.py --traceability` from `{test_cases_path.name}`, the @test registry"
        + (f", run `{run_label}`" if run_label else " (no run results yet)")
        + (" and the classifications in `execution-report.md`." if triage else "."),
        "> Do not edit by hand — regenerate after adding test cases or running the suite.",
        "",
        "| Feature | Behavior / rule | Test case | Automation id · file | Last result (run) | Notes |",
        "|---|---|---|---|---|---|",
        *rows,
        "",
        "## Summary",
        "",
        f"- Test cases: {len(cases)} · automated: {sum(1 for c in cases if c['automation_ids'])} · not automated: {len(uncovered)}",
        f"- Registered tests: {len(tests)} · without a test case: {len(orphans)}",
        f"- Results from run: {run_label or 'none'}",
        "",
        "## Uncovered behaviors",
        "",
        *(uncovered or ["- none"]),
        "",
    ]
    return "\n".join(lines)


def _relative(file: str, root: Path) -> str:
    if not file:
        return ""
    try:
        return Path(file).resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return Path(file).name
