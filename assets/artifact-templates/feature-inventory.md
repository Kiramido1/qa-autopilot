# Feature inventory

> Gate 2 deliverable — checklist in `references/gates.md#gate-2`. Rank by business impact, security impact,
> data integrity, frequency of use, failure probability, complexity and dependency count — not by size.
> Exit criterion: every reachable feature has a row and the Critical/High set has a stated rationale.
> Delete the EXAMPLE row after use; full example in `assets/examples/demo-app-engagement/qa-artifacts/feature-inventory.md`.

| ID | Feature | Pages | Roles | Endpoints | Entities | Preconditions | Happy path | Negative paths | State transitions | Side effects | Risk (Critical/High/Medium/Low) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| EXAMPLE F-003 | Delete item with confirmation | /dashboard | user (own), admin (all) | POST /items/<id>/delete, DELETE /api/items/<id> | Item | logged in, item exists | confirm → row gone, toast | cancel keeps item; other owner → 403; unknown id → 404 | present → deleted (hard) | none | High |
| F-001 | | | | | | | | | | | |

## Risk rationale
- F-001 → why this risk level: <!-- EXAMPLE: F-003 High — destructive, irreversible, and the ownership check is the only barrier against IDOR -->
