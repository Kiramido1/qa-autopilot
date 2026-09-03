# Repository reconnaissance

> Gate 1 deliverable. Verify behavior in the implementation, not in names, comments or docs.
> Exit criterion: you can explain the architecture and the major business flows.

## Architecture (text diagram)
```
Browser → Frontend (framework) → API (routes) → Services → DB / integrations
```

## Frontend map
| Page / route | Components | Forms & validation | States (loading/empty/error) | Roles |
|---|---|---|---|---|

- Routing / state management / API client:
- Toasts, modals, tables, filters, pagination, uploads, downloads:

## Backend map
| Route | Method | Auth | Roles | Request schema | Response schema | Errors |
|---|---|---|---|---|---|---|

- Middleware, background jobs, transactions:

## Database map
| Entity | Key fields / constraints | Relationships | State fields | Soft delete / audit |
|---|---|---|---|---|

- Important invariants:

## Integrations
| Integration | Purpose | Failure impact | Testability (mock / sandbox / live) |
|---|---|---|---|

## Authentication & authorization model
- Login / session / refresh / expiry:
- Roles and permissions (UI vs API enforcement):

## Business rules (verified in code)
- Rule → where enforced (file:line) → how verified:

## High-risk areas
- Area → why (impact, complexity, dependencies, history):

## Existing coverage vs gaps
- Covered:
- Missing:
