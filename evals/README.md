# Evals

Two kinds, both cheap to re-run after any change to `SKILL.md` or the references.

## Task evals — `evals.json`

Five realistic prompts (full engagement, triage of an injected defect, PR impact with resume,
extending an existing pytest-selenium suite, blocked environment) with objective assertions.
Run each prompt in Claude Code **with** the skill installed and **without** it (baseline), then:

```bash
python evals/check_engagement.py <workdir>        # the mechanical assertions
grep -rn "time.sleep" <workdir>/qa --include=*.py  # plus the grep assertions listed per eval
```

Record pass/fail per assertion in `benchmark.md`. The transcript assertions (status lines, no
artifact pasted, honest block) are read from the conversation.

## Trigger evals — `trigger-queries.json`

Ten queries that must load the skill and ten near-misses that must not. Judge each against the
`description` in `SKILL.md` (or run them in Claude Code and note which loaded the skill). Record
the rate in `benchmark.md`; a change to the description re-runs this set.

## `check_engagement.py`

Also the mechanical part of Gate 17. Works on a real repo (`qa-artifacts/`, `qa/`, `qa/reports/`)
and on the bundled example:

```bash
python evals/check_engagement.py assets/examples/demo-app-engagement \
  --qa assets/framework-skeleton --reports assets/examples/demo-app-engagement/runs --run 20260903-132200
```
