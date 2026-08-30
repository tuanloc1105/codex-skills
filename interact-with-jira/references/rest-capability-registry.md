# Verified Jira REST capability registry

[`rest-capability-registry.json`](rest-capability-registry.json) is the preferred set of pre-verified capabilities. Its `default: deny` means an absent method/path is not implicitly registered. An absent capability may still use the dynamic official-documentation workflow in [REST API workflow](rest-api-workflows.md); neighboring endpoints and caller-supplied method/path pairs remain prohibited.

## Entry contract

Every entry records product/API family, live MCP probe, exact REST pair, classic and granular OAuth scopes, tier, target provenance, authorization, bounds, retry/idempotency, and verification. Resolve all fields before requesting.

- Tier A: bounded read. Existing verified REST credentials may be selected automatically only after the live MCP schema lacks the exact capability.
- Tier B: authorized single-target write. Route selection never authorizes the mutation. Bind target and payload, pre-read, execute once, and re-read the documented outcome.
- Tier C: intentionally absent from the pre-verified registry. Such operations require a dynamic contract and immediate pre-execution confirmation under `SKILL.md`.

Classic scopes are the compact operator contract. With granular grants, require every granular scope in the entry and recheck the current official endpoint page. Jira permissions and issue security still apply.

## Resolution

1. Name the capability and bind target provenance independently of route selection.
2. Inspect live Rovo MCP tools and schemas; use an exact MCP capability when present.
3. Otherwise find one exact registry ID and verify its method/path template; never match by resemblance.
4. Apply family, scopes, tier, bounds, authorization, retry, and verification together.
5. If no entry matches, derive a dynamic contract through [REST API workflow](rest-api-workflows.md). Stop if the exact official contract cannot be established.

Use [Platform issue workflows](rest-platform-issues.md), [Agile workflows](rest-agile.md), or [Attachment workflow](rest-attachments.md) for domain semantics. Common credentials, requests, and errors are in [REST API workflow](rest-api-workflows.md).

## Registry boundary

There is no pre-verified entry for deleting/unlinking, removing watchers, deleting comments/worklogs/issues/boards/versions, bulk mutation, Agile mutation, administration, or JQL-selected writes. Official documentation can establish a task-scoped dynamic endpoint contract, but user intent, target provenance, risk-tier authorization, credentials, scopes, permissions, bounds, and verification remain independently required. Generic arbitrary REST execution is prohibited.
