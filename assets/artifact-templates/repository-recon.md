# Repository reconnaissance

> Gate 1 deliverable — checklist in `references/gates.md#gate-1`. Verify behavior in the implementation, not in
> names, comments or docs; cite `file:line`. Exit criterion: you can explain the architecture and the major
> business flows. Sampling order for large repos: routes/entry points → high-risk paths → the rest; list what
> you did not read in `coverage-gaps.md`. Delete EXAMPLE rows after use; full example in
> `assets/examples/demo-app-engagement/qa-artifacts/repository-recon.md`.

## Architecture (text diagram)
```
Browser → Frontend (framework) → API (routes) → Services → DB / integrations
```

## Frontend map
| Page / route | Components | Forms & validation | States (loading/empty/error) | Roles |
|---|---|---|---|---|
| EXAMPLE `/dashboard` (app.py:120) | items table, confirm dialog, toast | new-item form, `maxlength=50` client-side | empty row `items-empty`, error banner `item-error` | user, admin |

- Routing / state management / API client:
- Toasts, modals, tables, filters, pagination, uploads, downloads:

## Backend map
| Route | Method | Auth | Roles | Request schema | Response schema | Errors |
|---|---|---|---|---|---|---|
| EXAMPLE `/api/items/<id>` (app.py:196) | DELETE | session cookie (`api_auth`) | owner or admin | — | 204 empty | 401 anon · 403 not owner · 404 unknown id |

- Middleware, background jobs, transactions:

## Database map
| Entity | Key fields / constraints | Relationships | State fields | Soft delete / audit |
|---|---|---|---|---|
| EXAMPLE Item | id (auto), name 1–50 chars (`validate_name`, app.py:66), owner email | owner → User | none | hard delete |

- Important invariants:

## Integrations
| Integration | Purpose | Failure impact | Testability (mock / sandbox / live) |
|---|---|---|---|
| EXAMPLE none | | | |

## Authentication & authorization model
- Login / session / refresh / expiry:
- Roles and permissions (UI vs API enforcement): <!-- EXAMPLE: UI hides nothing by role; API enforces ownership in `_delete` — both checked -->

## Business rules (verified in code)
- Rule → where enforced (file:line) → how verified: <!-- EXAMPLE: item name ≤ 50 → app.py:66 → API-002 boundary test -->

## High-risk areas
- Area → why (impact, complexity, dependencies, history):

## Existing coverage vs gaps
- Covered:
- Missing:
