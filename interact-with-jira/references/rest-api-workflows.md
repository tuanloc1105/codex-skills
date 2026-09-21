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

1. Discover only existing credentials without printing values, decoded claims, or headers. The one approved local token path may be named when reporting presence or a permission problem: `~/.codex/.vault/.env.vault`.
2. Use only an existing Jira Cloud API token with its configured account email and `https://<site>.atlassian.net`. Authenticate with HTTP Basic using `email:token`, constructed only inside the HTTP helper.
3. Never send `JIRA_ACCESS_TOKEN` or any Jira API token with `Authorization: Bearer`. Do not use OAuth access tokens, `https://api.atlassian.com/ex/jira/{cloudId}`, or token-shape guessing for REST in this skill.
4. Stop when the API token, account email, or site is absent, expired, ambiguous, or lacks the registered or documented permissions. Do not create an app, replace tokens, switch accounts, or persist credentials.

### Load the approved local token

- Use only `JIRA_ACCESS_TOKEN` from `~/.codex/.vault/.env.vault`. Do not search for alternate vaults, token files, or similarly named keys.
- Resolve the current user's home directory without printing it. If `~/.codex/.vault/` is absent, create only those missing directories with mode `0700`. If `.env.vault` is absent, create it without overwriting any path, write exactly `JIRA_ACCESS_TOKEN=` followed by one newline, and set mode `0600`. Do not add example values, comments, quotes, or another credential key.
- After creating the file, stop before any Jira request. Tell the user to open `~/.codex/.vault/.env.vault`, paste the token after `JIRA_ACCESS_TOKEN=`, save it, and ask the agent to continue. Never ask the user to paste the token into chat and never open or display the file through a tool.
- For an existing path, check only that it is a regular file owned by the current user and is not accessible by group or others (equivalent to mode `0600`). Metadata checks must not print its contents. Stop and report the path and permission problem when these checks fail; do not repair permissions unless the user asks.
- Test key presence only inside a non-verbose child process that sources the file and returns status, never the value. If `JIRA_ACCESS_TOKEN` is unset and the dotenv file loaded successfully, append exactly `JIRA_ACCESS_TOKEN=` once without rendering existing content, then stop and give the same populate-and-resume instruction. If the key exists but is empty, do not append a duplicate; stop and ask the user to populate it. If the dotenv file has invalid shell syntax, stop without modifying it and report only the parse failure and path.
- Start a child process that sources the dotenv file with automatic export enabled, then immediately `exec`s the HTTP helper. The agent must not use `cat`, `grep`, `sed`, `awk`, command substitution, shell tracing, environment dumps, or any tool output that reads or renders the assignment. Do not return the loaded environment to the parent process.
- The HTTP helper must read `JIRA_ACCESS_TOKEN` from its process environment and construct the authorization header inside process memory. Never interpolate the token into a shell command, command argument, URL, temporary file, request body, exception, debug trace, or log. Disable verbose HTTP and shell tracing.
- Treat `JIRA_ACCESS_TOKEN` only as a Jira Cloud API token for Basic authentication in this workflow. Independently verify the account email and site; combine `email:token` and encode the Basic credential only inside the helper. Never materialize or print the combined credential, and never fall back to Bearer authentication based on the variable name, token shape, or an authentication error.
- Do not decode, compare, validate by display, rotate, rewrite, or persist the token. For `401` or `403`, report the status and correlated site/account without retrying with another credential.

Use a client with separate headers, disabled automatic cross-host redirects, streaming, and exposed status/headers. Never log authorization, cookies, bodies, signed URLs, or unnecessary identity.

## Request and response policy

- Allow requests only to the verified `https://<site>.atlassian.net` origin associated with the API-token account. Use the exact path and API version from the endpoint contract; do not rewrite it into a familiar Jira Platform or Software family. Encode path/query values independently and enforce contract field/filter/page/byte ceilings before sending.
- Accept only documented success statuses/shapes. Treat pagination tokens as opaque and stop at entry ceilings.
- For `401`/`403`, report authentication/scope/permission. For `404`, verify explicit site/target without broad replacement search.
- For `409`, `429`, or `5xx`, retry only idempotent Tier A reads, honoring `Retry-After` with bounded attempts. Never retry Tier B/Tier C or cross tools after uncertainty.
- For an attachment-upload `503`, re-read the issue attachment list to determine whether the mutation succeeded, then stop. Do not retry or switch routes automatically, even when read-back shows no new attachment.
- Perform the contract's exact verification before reporting a write successful.

Report registered capability ID or `dynamic`, official source, REST family, risk tier, verified site/target, bounds, result, verification, and limitations without private content.
