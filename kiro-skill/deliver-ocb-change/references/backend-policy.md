# OCB Backend Delivery Policy

Apply this policy only to backend paths in `backend` or `mixed` mode, together with [core-policy.md](core-policy.md).

## Scope and implementation

Implement only approved Backend Developer scope. Before editing, locate repository instructions, application/service roots, API and data contracts, shared libraries, generated files, nearby tests, and build conventions. Preserve existing architecture and do not introduce speculative abstractions.

Verify applicable behavior including:

- Input validation, authorization, and error/response mapping
- API, event, external-integration, and backward-compatibility contracts
- Database queries, stored procedures, transactions, concurrency, and update-count behavior
- Security, secret handling, sensitive logging, and data exposure
- Focused unit, integration, contract, build, lint, and static-analysis checks owned by the repository

Repository-mandated checks are **Hard** gates. Other checks are classified by higher-priority instructions, Jira acceptance criteria, repository rules, and risk. Record applicability, commands, evidence, skipped checks, and residual risk; never claim an unperformed check.

For a backend-only change, do not apply frontend UI evidence gates. In `mixed` mode, classify affected paths and keep backend evidence separate from frontend evidence in the workflow contract.

## Readiness additions

`CODE_READY` requires backend acceptance criteria and required checks to pass, or an explicit allowed override with residual risk. `MR_PREPARED` additionally requires reviewed backend evidence and exact backend diff boundaries.

Backend scope excludes Frontend and Mobile delivery unless the resolved mode is `mixed`, in which case the frontend portion follows [frontend-policy.md](frontend-policy.md).
