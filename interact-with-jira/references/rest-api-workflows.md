# Jira Cloud REST fallback workflow

Use REST only after live Rovo MCP lacks an exact [registry](rest-capability-registry.md) capability, or MCP is unavailable while target and site can be independently verified. Route selection does not authorize mutation or credential changes.

## Resolve and validate

1. Resolve one capability ID before constructing a URL.
2. Require an exact method/path-template match from `rest-capability-registry.json`; substitute only provenance-verified variables.
3. Apply API family, scopes, tier, authorization, bounds, retry, and verification together. Never accept a caller-supplied generic pair.
4. Read the matching domain reference: [attachments](rest-attachments.md), [Platform issues](rest-platform-issues.md), or [Agile reads](rest-agile.md).

## Credentials and site correlation

1. Discover only existing credentials without printing paths, values, decoded claims, or headers.
2. Prefer OAuth bearer credentials. Correlate accessible-resource URL/cloud ID with MCP and use `https://api.atlassian.com/ex/jira/{cloudId}`.
3. Otherwise use an existing API token only with its configured account and `https://<site>.atlassian.net`; supply authorization from a secret source, never an argument or committed file.
4. Stop when credentials are absent/expired, need consent, map ambiguously, or lack registry scopes. Do not create an app, replace tokens, switch accounts, or persist credentials.

Use a client with separate headers, disabled automatic cross-host redirects, streaming, and exposed status/headers. Never log authorization, cookies, bodies, signed URLs, or unnecessary identity.

## Request and response policy

- Encode path/query values independently and enforce field/filter/page ceilings before sending.
- Accept only documented success statuses/shapes. Treat pagination tokens as opaque and stop at entry ceilings.
- For `401`/`403`, report authentication/scope/permission. For `404`, verify explicit site/target without broad replacement search.
- For `409`, `429`, or `5xx`, retry only idempotent Tier A reads, honoring `Retry-After` with bounded attempts. Never retry Tier B or cross tools after uncertainty.
- Perform the exact registry verification before reporting a write successful.

Report capability ID, REST family, verified site/target, bounds, result, verification, and limitations without private content.
