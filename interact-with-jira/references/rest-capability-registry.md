# Closed Jira REST capability registry

The machine-readable authority is [`rest-capability-registry.json`](rest-capability-registry.json). An operation is permitted only when one entry exactly matches its capability ID, method, and path template. `default: deny`; neighboring endpoints and caller-supplied method/path pairs are not permitted.

## Entry contract

Every entry records product/API family, live MCP probe, exact REST pair, classic and granular OAuth scopes, tier, target provenance, authorization, bounds, retry/idempotency, and verification. Resolve all fields before requesting.

- Tier A: bounded read. Existing verified REST credentials may be selected automatically only after the live MCP schema lacks the exact capability.
- Tier B: authorized single-target write. Route selection never authorizes the mutation. Bind target and payload, pre-read, execute once, and re-read the documented outcome.
- Tier C: intentionally absent. Bulk, destructive, administrative, broad-selector, removal/delete, Agile mutation, and all unlisted operations remain prohibited over REST.

Classic scopes are the compact operator contract. With granular grants, require every granular scope in the entry and recheck the current official endpoint page. Jira permissions and issue security still apply.

## Resolution

1. Name the capability and bind target provenance independently of route selection.
2. Inspect live Rovo MCP tools and schemas; use an exact MCP capability when present.
3. Otherwise find one exact registry ID and verify its method/path template; never match by resemblance.
4. Apply family, scopes, tier, bounds, authorization, retry, and verification together.
5. If no entry matches, stop. Offer ACLI only after reporting the limitation and obtaining task-scoped approval.

Use [Platform issue workflows](rest-platform-issues.md), [Agile workflows](rest-agile.md), or [Attachment workflow](rest-attachments.md) for domain semantics. Common credentials, requests, and errors are in [REST API workflow](rest-api-workflows.md).

## Default-deny boundary

There is no entry for deleting/unlinking, removing watchers, deleting comments/worklogs/issues/boards/versions, bulk mutation, Agile mutation, administration, JQL-selected writes, or generic REST execution. Official documentation proves behavior, not authorization.
