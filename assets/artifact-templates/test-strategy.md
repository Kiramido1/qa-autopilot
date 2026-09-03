# Test strategy

> Gate 3 deliverable. Risk-based: P0 catastrophic → P1 business-critical → P2 important → P3 secondary.

## Scope and priorities
- In scope / out of scope:
- Order of execution (Phase A env smoke → B P0 → C P1 → D regression → E cross-feature → F integration/API):

## Coverage areas
| Area | Approach (UI / API / both) | Why |
|---|---|---|
| Functional (happy, negative, boundary, invalid/missing/null/duplicate, state, multi-step, cross-feature) | | |
| Authentication (login, logout, invalid creds, expiry, refresh, direct URL, persistence) | | |
| Authorization (each role × permission, UI + API, object-level, escalation) | | |
| Validation (min/max/just outside, required, formats, unicode, special chars, long, duplicates) | | |
| State (initial, loading, empty, success, failure, partial, expired, deleted, disabled, completed) | | |
| Integration (browser → frontend → API → backend → DB → external) | | |
| Security-aware (IDOR, escalation, session invalidation, upload limits, data exposure) | | |
| Accessibility-aware (labels, keyboard, focus, error messages) | | |

## Environment and browsers
- Environments: local / staging — data strategy (disposable, isolated, cleanup):
- Browser matrix (default Chrome; Firefox/Edge for critical regression when justified):

## What is deliberately not automated (and why)
-
