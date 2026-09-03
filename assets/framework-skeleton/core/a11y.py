"""Optional axe-core scan (--a11y) for Gate 19 observations.

Findings are recorded as observations next to the test result; they never
change the status. Do not report them as WCAG compliance — an automated scan
covers a fraction of the criteria.

axe-core is loaded from QA_AXE_PATH (a local axe.min.js) or downloaded once
from the CDN into qa/.cache/.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

AXE_VERSION = "4.10.2"
AXE_URL = f"https://cdnjs.cloudflare.com/ajax/libs/axe-core/{AXE_VERSION}/axe.min.js"
_SOURCE: Optional[str] = None


def axe_source(cache_dir: Path) -> Optional[str]:
    global _SOURCE
    if _SOURCE:
        return _SOURCE
    explicit = os.environ.get("QA_AXE_PATH")
    candidates = [Path(explicit)] if explicit else []
    candidates.append(cache_dir / f"axe-{AXE_VERSION}.min.js")
    for path in candidates:
        if path.is_file():
            _SOURCE = path.read_text(encoding="utf-8")
            return _SOURCE
    try:
        import requests

        response = requests.get(AXE_URL, timeout=30)
        response.raise_for_status()
    except Exception:  # noqa: BLE001 - offline: the scan is skipped, not failed
        return None
    cache_dir.mkdir(parents=True, exist_ok=True)
    candidates[-1].write_text(response.text, encoding="utf-8")
    _SOURCE = response.text
    return _SOURCE


def run_axe(driver, cache_dir: Path, context: Optional[str] = None) -> dict:
    source = axe_source(cache_dir)
    if source is None:
        return {"available": False, "reason": "axe-core not available (offline and no QA_AXE_PATH)"}
    try:
        driver.execute_script(source)
        driver.set_script_timeout(60)
        raw = driver.execute_async_script(
            "const done = arguments[arguments.length - 1];"
            "axe.run(arguments[0] || document, {resultTypes: ['violations']}).then(r => done(r)).catch(e => done({error: String(e)}));",
            context,
        )
    except Exception as error:  # noqa: BLE001
        return {"available": True, "error": repr(error)}
    if not isinstance(raw, dict) or raw.get("error"):
        return {"available": True, "error": (raw or {}).get("error") if isinstance(raw, dict) else repr(raw)}
    violations = [
        {
            "id": v.get("id"),
            "impact": v.get("impact"),
            "help": v.get("help"),
            "help_url": v.get("helpUrl"),
            "nodes": len(v.get("nodes", [])),
            "targets": [", ".join(n.get("target", [])) for n in v.get("nodes", [])[:3]],
        }
        for v in raw.get("violations", [])
    ]
    by_impact: dict[str, int] = {}
    for v in violations:
        by_impact[v["impact"] or "unknown"] = by_impact.get(v["impact"] or "unknown", 0) + 1
    return {
        "available": True,
        "url": raw.get("url"),
        "axe_version": raw.get("testEngine", {}).get("version"),
        "violations": violations,
        "summary": by_impact,
    }
