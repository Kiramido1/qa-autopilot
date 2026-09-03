# Test strategy

> Gate 3 deliverable — coverage checklist in `references/gates.md#gate-3`. Risk-based: P0 catastrophic → P1
> business-critical → P2 important → P3 secondary. Exit criterion: every Critical/High feature has an approach
> and priority. Delete EXAMPLE text after use; full example in
> `assets/examples/demo-app-engagement/qa-artifacts/test-strategy.md`.

## Scope and priorities
- Sizing (S / M / L, see SKILL.md) and depth mode (quick / standard / deep): <!-- EXAMPLE: S, standard -->
- In scope / out of scope:
- Order of execution (Phase A env smoke → B P0 → C P1 → D regression → E cross-feature → F integration/API):
- Vertical slice first (the one P0 journey implemented and executed before breadth): <!-- EXAMPLE: AUTH-001 login → dashboard → /api/me -->

## Coverage areas
| Area | Approach (UI / API / both) | Why |
|---|---|---|
| Functional (happy, negative, boundary, invalid/missing/null/duplicate, state, multi-step, cross-feature) | | <!-- EXAMPLE: UI for journeys (ITEM-001), API for boundaries (API-002): 5 boundary cases in 20 ms instead of 5 browser round-trips --> |
| Authentication (login, logout, invalid creds, expiry, refresh, direct URL, persistence) | | |
| Authorization (each role × permission, UI + API, object-level, escalation) | | <!-- EXAMPLE: API only — a hidden button is not authorization; API-003 checks ownership directly --> |
| Validation (min/max/just outside, required, formats, unicode, special chars, long, duplicates) | | |
| State (initial, loading, empty, success, failure, partial, expired, deleted, disabled, completed) | | |
| Integration (browser → frontend → API → backend → DB → external) | | |
| Security-aware (IDOR, escalation, session invalidation, upload limits, data exposure) | | |
| Accessibility-aware (labels, keyboard, focus, error messages) | | |

## Environment and browsers
- Environments: local / staging — data strategy (disposable, isolated, cleanup):
- Browser matrix (default Chrome; Firefox/Edge for critical regression when justified):

## What is deliberately not automated (and why)
- <!-- EXAMPLE: session expiry — the application implements none; recorded as "assumed expected — needs product confirmation" -->
