#!/usr/bin/env python3
"""Objective assertions over a finished (or in-progress) engagement.

    python evals/check_engagement.py /path/to/repo                       # qa-artifacts/ + qa/ + qa/reports/
    python evals/check_engagement.py assets/examples/demo-app-engagement \
        --qa assets/framework-skeleton --reports assets/examples/demo-app-engagement/runs

Every check is mechanical and prints PASS/FAIL with the evidence it looked at;
the exit code is 1 when any check fails. These are the assertions used by
evals/evals.json and by Gate 17 (audit). They cannot judge whether a
classification is *right* — only whether the work was done in the required
shape: executed, evidenced, classified, traced, and not weakened in the
obvious mechanical ways.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

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
ARTIFACTS = (
    "environment-map.md",
    "repository-recon.md",
    "feature-inventory.md",
    "test-strategy.md",
    "traceability-matrix.md",
    "test-cases.md",
    "execution-report.md",
    "defects.md",
    "regression-report.md",
    "coverage-gaps.md",
)
DEFECT_FIELDS = (
    "BUG ID",
    "TITLE",
    "SEVERITY",
    "PRIORITY",
    "FEATURE",
    "ENVIRONMENT",
    "STEPS TO REPRODUCE",
    "EXPECTED",
    "ACTUAL",
    "EVIDENCE",
    "ROOT CAUSE",
    "REGRESSION TEST",
)


class Report:
    def __init__(self) -> None:
        self.failed = 0
        self.total = 0

    def check(self, name: str, ok: bool, detail: str = "") -> None:
        self.total += 1
        if not ok:
            self.failed += 1
        print(f"  {'PASS' if ok else 'FAIL'}  {name}" + (f" — {detail}" if detail and not ok else ""))


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace") if path.is_file() else ""


def code_lines(path: Path) -> str:
    """Source without comment lines and docstring lines, for the grep-style checks."""
    triple = ('"' * 3, "'" * 3)
    kept = []
    in_doc = False
    for line in read(path).splitlines():
        stripped = line.strip()
        if stripped.startswith(triple):
            if stripped.count(triple[0]) == 2 or stripped.count(triple[1]) == 2:
                continue
            in_doc = not in_doc
            continue
        if in_doc or stripped.startswith("#"):
            continue
        kept.append(line.split("  # ")[0])
    return "\n".join(kept)


def classified_ids(execution_report: str) -> dict[str, str]:
    """Test id -> category, from blocks (bullet/heading + indented continuation) naming both."""
    blocks: list[str] = []
    for line in execution_report.splitlines():
        if not line.strip():
            blocks.append("")
        elif line.startswith((" ", "\t")) and blocks and blocks[-1]:
            blocks[-1] += "\n" + line
        else:
            blocks.append(line)
    found: dict[str, str] = {}
    for block in blocks:
        ids = {i for i in re.findall(r"\b([A-Z][A-Z0-9]*-\d{3,})\b", block) if not i.startswith("BUG-")}
        category = next((c for c in CATEGORIES if c in block), None)
        if ids and category:
            for test_id in ids:
                found[test_id] = category
    return found


def py_files(root: Path):
    for path in root.rglob("*.py"):
        if any(part in ("reports", ".venv", "__pycache__", ".cache") for part in path.parts):
            continue
        yield path


def latest_report(reports_dir: Path, run_id: str | None) -> Path | None:
    if run_id:
        candidate = reports_dir / run_id / "report.json"
        return candidate if candidate.is_file() else None
    candidates = sorted(reports_dir.glob("*/report.json")) if reports_dir.is_dir() else []
    return candidates[-1] if candidates else None


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("repo", help="repository (or engagement directory) to check")
    parser.add_argument("--artifacts", default=None, help="qa-artifacts directory (default <repo>/qa-artifacts)")
    parser.add_argument("--qa", default=None, help="framework directory (default <repo>/qa)")
    parser.add_argument("--reports", default=None, help="reports directory (default <qa>/reports)")
    parser.add_argument("--run", default=None, help="run id to check instead of the latest")
    args = parser.parse_args(argv)

    repo = Path(args.repo).resolve()
    artifacts = Path(args.artifacts).resolve() if args.artifacts else repo / "qa-artifacts"
    qa = Path(args.qa).resolve() if args.qa else repo / "qa"
    reports = Path(args.reports).resolve() if args.reports else qa / "reports"
    r = Report()
    print(f"Engagement check — artifacts={artifacts} qa={qa} reports={reports}")

    # ---- executed ------------------------------------------------------------
    report_path = latest_report(reports, args.run)
    r.check("tests were executed (report.json exists)", report_path is not None, str(reports))
    results: list[dict] = []
    run_meta: dict = {}
    if report_path:
        data = json.loads(report_path.read_text(encoding="utf-8"))
        results = data.get("results", [])
        run_meta = data.get("run", {})
        r.check("every selected test has a status", all(x.get("status") in ("PASS", "FAIL", "ERROR", "FLAKY", "SKIP") for x in results))
        browser = run_meta.get("browser") or {}
        r.check("run metadata records the browser version", bool(browser.get("version")), json.dumps(browser))
        build = run_meta.get("build") or {}
        r.check(
            "run metadata records a build identifier (git sha or build id)",
            bool(build.get("git_sha") or build.get("build_id")),
            json.dumps(build),
        )
        problems = [x for x in results if x.get("status") in ("FAIL", "ERROR", "FLAKY")]
        for x in problems:
            evidence = [a.get("evidence", {}) for a in x.get("attempts", [])]
            r.check(f"{x['id']} ({x['status']}) has evidence on disk", any(e.get("exception") for e in evidence), str(evidence)[:120])
        junit = report_path.parent / "junit.xml"
        r.check("junit.xml written next to report.json", junit.is_file())
        text = read(report_path)
        r.check(
            "evidence paths are relative (no absolute paths in report.json)",
            not re.search(r'"(?:screenshot|exception|page_source)": "/', text),
        )

    # ---- suite hygiene --------------------------------------------------------
    files = list(py_files(qa)) if qa.is_dir() else []
    r.check("qa/ directory with Python files exists", bool(files), str(qa))
    sleeps = [f"{p.relative_to(qa)}" for p in files if re.search(r"\btime\.sleep\(", code_lines(p)) and "selftest" not in p.name]
    r.check("no time.sleep in the suite", not sleeps, ", ".join(sleeps))
    absolute = [f"{p.relative_to(qa)}" for p in files if re.search(r"[\"']/html/body", code_lines(p))]
    r.check("no absolute XPath", not absolute, ", ".join(absolute))
    generated = [f"{p.relative_to(qa)}" for p in files if re.search(r"[\"'.](?:css|sc)-[A-Za-z0-9]{5,}", code_lines(p))]
    r.check("no generated class-name selectors", not generated, ", ".join(generated))
    pytest_use = [
        f"{p.relative_to(qa)}"
        for p in files
        if re.search(r"^\s*(import pytest|from pytest|import unittest|from unittest)", read(p), re.MULTILINE)
    ]
    r.check("no pytest / unittest in the suite (bundled runner)", not pytest_use, ", ".join(pytest_use))
    registry_ids = set()
    for p in files:
        registry_ids.update(re.findall(r"@test\(\s*id\s*=\s*[\"']([A-Z][A-Z0-9]*-\d+)[\"']", read(p)))
    r.check("tests are registered with @test(id=...)", bool(registry_ids), f"{len(registry_ids)} ids")

    # ---- artifacts ------------------------------------------------------------
    texts = {name: read(artifacts / name) for name in ARTIFACTS}
    missing = [n for n, t in texts.items() if not t]
    r.check("all ten qa-artifacts exist", not missing, ", ".join(missing))
    leftovers = [
        n
        for n, t in texts.items()
        if re.search(r"\bEXAMPLE\b", "\n".join(line for line in t.splitlines() if not line.lstrip().startswith(">")))
    ]
    r.check("no EXAMPLE markers left in artifacts", not leftovers, ", ".join(leftovers))

    # execution report: every problem result classified
    exec_report = texts["execution-report.md"]
    problem_ids = [x["id"] for x in results if x.get("status") in ("FAIL", "ERROR", "FLAKY")]
    classifications = classified_ids(exec_report)
    for pid in problem_ids:
        r.check(f"{pid} is classified in execution-report.md", pid in classifications, "no block names this id together with a category")
    flaky_entries = re.findall(r"FLAKY_TEST[^\n]*", exec_report)
    if flaky_entries:
        r.check(
            "every FLAKY_TEST entry has a frequency (n/m)",
            all(re.search(r"\d+\s*/\s*\d+", e) for e in flaky_entries),
            str(flaky_entries)[:200],
        )
    r.check(
        "execution report states browser and build",
        bool(re.search(r"(chrome|firefox|edge)\s*\d", exec_report, re.I)) and ("build" in exec_report.lower()),
    )

    # test cases: P0 for every Critical feature; expected results have a source
    inventory = texts["feature-inventory.md"]
    critical = [row for row in inventory.splitlines() if row.startswith("|") and re.search(r"\|\s*\**Critical\**\s*\|?\s*$", row)]
    cases = texts["test-cases.md"]
    case_sections = re.split(r"^##\s+", cases, flags=re.MULTILINE)[1:]
    p0_features = {
        m.group(1).strip().lower() for s in case_sections for m in [re.search(r"Feature:\s*([^|\n]+)\|\s*Priority:\s*P0", s)] if m
    }
    for row in critical:
        cells = [c.strip().strip("*") for c in row.strip("|").split("|")]
        feature_id, feature_name = cells[0], cells[1] if len(cells) > 1 else ""
        words = {w[:4].lower() for w in re.findall(r"[A-Za-z]{4,}", feature_name)}
        covered = any(any(f.startswith(w) or w in f for w in words) for f in p0_features) or feature_id.lower() in cases.lower()
        r.check(
            f"P0 case exists for Critical feature {feature_id} ({feature_name[:40]})",
            covered,
            f"P0 features in cases: {sorted(p0_features)}",
        )
    ids_in_cases = set(re.findall(r"test id in code:\s*`?([A-Z][A-Z0-9]*-\d+)`?", cases))
    r.check("test-cases.md links cases to code ids", bool(ids_in_cases), f"{len(ids_in_cases)} ids")
    unknown = sorted(ids_in_cases - registry_ids) if registry_ids else []
    r.check("every code id in test-cases.md exists in the registry", not unknown, ", ".join(unknown))
    sourced = sum(
        1 for s in case_sections if re.search(r"Expected result:.*?(source:|assumed expected|app\.py|\.py:\d+|requirement)", s, re.S | re.I)
    )
    r.check(
        "expected results name their source (oracle rule)",
        case_sections and sourced >= max(1, int(0.8 * len(case_sections))),
        f"{sourced}/{len(case_sections)}",
    )

    # traceability generated and consistent
    matrix = texts["traceability-matrix.md"]
    r.check("traceability matrix is generated (--traceability), not hand-written", "Generated" in matrix and "--traceability" in matrix)
    r.check("no automation id missing from the registry in the matrix", "not found in registry" not in matrix)

    # defects: format and severity rubric
    defects = texts["defects.md"]
    blocks = re.findall(r"```(.*?)```", defects, re.S)
    real_bugs = [b for b in blocks if re.search(r"BUG ID:\s*BUG-\d+", b)]
    if "REAL_APPLICATION_BUG" in exec_report:
        r.check("defects.md has an entry for the confirmed bug(s)", bool(real_bugs))
    for b in real_bugs:
        bug_id = re.search(r"BUG ID:\s*(\S+)", b).group(1)
        empty = [f for f in DEFECT_FIELDS if not re.search(rf"{re.escape(f)}:\s*\S", b)]
        r.check(f"{bug_id}: every required field is filled", not empty, ", ".join(empty))
        r.check(f"{bug_id}: severity uses the rubric", bool(re.search(r"SEVERITY:\s*(Critical|High|Medium|Low)\b", b)))
        r.check(f"{bug_id}: evidence cites files", bool(re.search(r"EVIDENCE:(?:.|\n)*?(artifacts/|runs/|\.png|\.json)", b)))

    # coverage gaps honest
    gaps = texts["coverage-gaps.md"]
    r.check(
        "coverage-gaps.md lists at least one gap or accepted risk",
        bool(re.search(r"\|\s*[^|]*\|\s*[^|]+\|\s*[^|]+\|", gaps)) and "Accepted risks" in gaps,
    )

    print(f"\n{r.total - r.failed}/{r.total} checks passed")
    return 1 if r.failed else 0


if __name__ == "__main__":
    sys.exit(main())
