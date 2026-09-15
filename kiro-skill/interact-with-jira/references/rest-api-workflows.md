# Jira Cloud REST fallback workflow

Use REST after live Rovo MCP lacks the exact capability, or MCP is unavailable while site and the operation's required target provenance can be independently verified. Route selection does not authorize mutation or credential changes.

## Resolve and validate

1. Prefer one exact capability ID from `rest-capability-registry.json`; apply its method/path, API family, scopes, tier, authorization, bounds, retry, and verification together.
2. If no entry matches, open the exact current endpoint page under `developer.atlassian.com/cloud/jira/`. Create a task-scoped dynamic capability contract before constructing a URL. Record the official source URL, product/API family and version, method, path template, documented success statuses, request and response shapes needed by the task, classic and granular scopes, Jira permissions, target provenance, risk tier, bounds, idempotency/retry rule, and post-operation verification.
3. Disclose a concise contract summary before any dynamic mutation. Do not persist it to the registry automatically. Never derive a method/path from naming conventions, a neighboring endpoint, search-result text, examples from third parties, or a caller-supplied generic pair.
4. Read the applicable domain reference: [attachments](rest-attachments.md), [Platform issues](rest-platform-issues.md), or [Agile workflows](rest-agile.md). When no local domain guide exists, the official endpoint page plus this workflow governs.

## Dynamic risk classification

- Tier A: bounded idempotent read. Require an explicit target or narrow filter, minimum fields, finite page/byte ceilings, and permission-respecting output. It may proceed without separate fallback approval after site and credentials are verified.
- Tier B: one non-destructive mutation against an explicitly authorized target and bounded payload. Pre-read current state and required metadata, execute once, accept only documented success, and re-read the documented outcome. Never retry automatically.
- Tier C: delete/removal, destructive or difficult-to-reverse action, bulk or selector-based mutation, administration, permission/configuration change, or Agile mutation. Perform a read-only preflight, resolve the final target set/count and impact, then request exact confirmation immediately before execution. Execute once; do not continue after partial or uncertain results.

When classification is ambiguous, use the higher tier. A user asking for an outcome authorizes a bounded Tier B mutation only when target and payload are explicit; it does not waive Tier C confirmation.

## Credentials and site correlation

1. Discover only existing credentials without printing paths, values, decoded claims, or headers.
2. Prefer OAuth bearer credentials. Correlate accessible-resource URL/cloud ID with MCP and use `https://api.atlassian.com/ex/jira/{cloudId}`.
3. Otherwise use an existing API token only with its configured account and `https://<site>.atlassian.net`; supply authorization from a secret source, never an argument or committed file.
4. Stop when credentials are absent/expired, need consent, map ambiguously, or lack the registered or documented dynamic scopes. Do not create an app, replace tokens, switch accounts, or persist credentials.

Use a client with separate headers, disabled automatic cross-host redirects, streaming, and exposed status/headers. Never log authorization, cookies, bodies, signed URLs, or unnecessary identity.

## Request and response policy

- Allow requests only to the verified Atlassian site or the official `api.atlassian.com` resource URL documented for the product and correlated cloud ID. Use the exact path and API version from the endpoint contract; do not rewrite it into a familiar Jira Platform or Software family. Encode path/query values independently and enforce contract field/filter/page/byte ceilings before sending.
- Accept only documented success statuses/shapes. Treat pagination tokens as opaque and stop at entry ceilings.
- For `401`/`403`, report authentication/scope/permission. For `404`, verify explicit site/target without broad replacement search.
- For `409`, `429`, or `5xx`, retry only idempotent Tier A reads, honoring `Retry-After` with bounded attempts. Never retry Tier B/Tier C or cross tools after uncertainty.
- Perform the contract's exact verification before reporting a write successful.

Report registered capability ID or `dynamic`, official source, REST family, risk tier, verified site/target, bounds, result, verification, and limitations without private content.
