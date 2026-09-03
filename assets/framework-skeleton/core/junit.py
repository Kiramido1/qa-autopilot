"""JUnit XML report (reports/<run-id>/junit.xml) for CI dashboards.

Status mapping: PASS -> passed · FAIL -> <failure> · ERROR -> <error> ·
FLAKY -> <failure type="FLAKY"> (a flaky test is still a red test) · SKIP -> <skipped>.
"""

from __future__ import annotations

from pathlib import Path
from xml.etree import ElementTree as ET


def write_junit(path: Path, run: dict, results: list[dict]) -> Path:
    suite = ET.Element(
        "testsuite",
        name="qa",
        tests=str(len(results)),
        failures=str(sum(1 for r in results if r["status"] in ("FAIL", "FLAKY"))),
        errors=str(sum(1 for r in results if r["status"] == "ERROR")),
        skipped=str(sum(1 for r in results if r["status"] == "SKIP")),
        time=str(run.get("duration_s", 0)),
        timestamp=str(run.get("started", "")),
    )
    properties = ET.SubElement(suite, "properties")
    env = run.get("environment", {})
    for key in ("env_name", "base_url", "browser", "headless"):
        ET.SubElement(properties, "property", name=key, value=str(env.get(key)))
    build = run.get("build") or {}
    for key in ("build_id", "git_sha", "git_branch"):
        if build.get(key):
            ET.SubElement(properties, "property", name=key, value=str(build[key]))
    browser = run.get("browser") or {}
    if browser.get("version"):
        ET.SubElement(properties, "property", name="browser_version", value=str(browser["version"]))

    for r in results:
        case = ET.SubElement(
            suite,
            "testcase",
            classname=r.get("module", ""),
            name=f"{r['id']} {r['name']}",
            time=str(r.get("duration_s", 0)),
        )
        message = (r.get("message") or "").strip()
        if r["status"] == "FAIL":
            ET.SubElement(case, "failure", message=message.splitlines()[0] if message else "", type="AssertionFailure").text = message
        elif r["status"] == "FLAKY":
            ET.SubElement(case, "failure", message=message, type="FLAKY").text = message
        elif r["status"] == "ERROR":
            ET.SubElement(case, "error", message=message.splitlines()[0] if message else "", type="Error").text = message
        elif r["status"] == "SKIP":
            ET.SubElement(case, "skipped", message=message)
        evidence_lines = []
        for attempt in r.get("attempts", []):
            for kind, value in attempt.get("evidence", {}).items():
                evidence_lines.append(f"attempt {attempt['attempt']} {kind}: {value}")
            for attachment in attempt.get("attachments", []):
                evidence_lines.append(f"attempt {attempt['attempt']} attachment: {attachment}")
        if evidence_lines:
            ET.SubElement(case, "system-out").text = "\n".join(evidence_lines)

    tree = ET.ElementTree(suite)
    try:
        ET.indent(tree, space="  ")
    except AttributeError:  # Python < 3.9
        pass
    tree.write(path, encoding="utf-8", xml_declaration=True)
    return path
