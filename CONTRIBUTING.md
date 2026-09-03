# Contributing

Issues and pull requests are welcome — field reports from real engagements most of all
(`.github/ISSUE_TEMPLATE/field_report.md`).

## Ground rules

1. The non-negotiable rules in `SKILL.md` are the product. A change that lets the suite report
   green without evidence, hide a failure, or weaken an assertion is not accepted, however
   convenient.
2. Every runner change ships with a `--selftest` check (`assets/framework-skeleton/core/selftest.py`).
3. Every framework change runs green against the demo app: `python scripts/run_demo.py`.
4. Reference docs stay short and prescriptive. If a paragraph does not change what the agent
   does, delete it.

## Local checks

```bash
pip install -r assets/framework-skeleton/requirements-dev.txt -r assets/demo-app/requirements.txt
python assets/framework-skeleton/run_tests.py --selftest
python scripts/run_demo.py --retries 1
python scripts/run_demo.py --bugs stale-dashboard --test ITEM-001      # must exit 1
cd assets/framework-skeleton && ruff check . && ruff format --check . && mypy . && cd ../..
python evals/check_engagement.py assets/examples/demo-app-engagement \
  --qa assets/framework-skeleton --reports assets/examples/demo-app-engagement/runs --run 20260903-132200
```

If you change the report format, regenerate the example runs with `scripts/run_demo.py --run-id <id>` and copy
the new `execution-report.md` files into `assets/examples/demo-app-engagement/runs/`; then regenerate the matrix
(`run_tests.py --traceability --artifacts-dir ... --from-run 20260903-132200`). If you change `SKILL.md`'s
description, re-judge `evals/trigger-queries.json` and update `benchmark.md`.

## Layout

- `SKILL.md` — entry point; keep it under ~500 lines, move detail to `references/`.
- `references/` — one file per phase group; each section ends with an exit criterion.
- `assets/artifact-templates/` — one template per deliverable, each with an EXAMPLE row.
- `assets/framework-skeleton/` — the runner and framework; `core/engine.py` is the runner.
- `assets/demo-app/` — the app CI runs against; keep it small and deterministic.
- `assets/examples/` — a full worked engagement; regenerate its run reports when the runner's
  report format changes.
- `evals/` — task and trigger evals and `check_engagement.py`; update `benchmark.md` when you run them.
- `scripts/qa_status.py` — the resume helper; keep its artifact list in gate order.

## Releases

Update `CHANGELOG.md`, bump `metadata.version` in `SKILL.md`, tag `vX.Y.Z`.
