---
name: interact-with-jira
description: Work with Jira Cloud through Atlassian Rovo MCP first, registered or dynamically verified official Jira REST fallbacks when MCP lacks a capability or is unavailable, and official Atlassian CLI `acli` only when explicitly requested or approved. Use for Jira reads, writes, attachments, boards, sprints, releases, configuration, authentication, and safety gates.
---

# Interact with Jira

## OCB Jira metadata

For `https://wowocb.atlassian.net`, use the checked-in [metadata snapshot](references/wowocb-metadata.json) to resolve project keys/IDs, issue types, statuses by work type, board IDs, and issue link types. Read [snapshot usage and recovery](references/wowocb-metadata.md) before using those values. The snapshot was retrieved through authenticated Atlassian Rovo MCP on 2026-09-23 and reflects that account's visibility. Do not refresh the site-wide catalog routinely; follow the recovery procedure only when a concrete mismatch, missing value, or Jira validation error makes it necessary.

The snapshot is not a substitute for issue-specific current state, transitions, required create/edit fields, permissions, or assignee/sprint eligibility. Fetch only the necessary live metadata for the exact target when an operation needs it, as required by the risk-tier rules below.

For a new Sub-task on `wowocb.atlassian.net` that also needs an Original Estimate, read [the OCB Sub-task estimate workflow](references/wowocb-metadata.md#sub-task-original-estimate) before writing. Its two-step MCP route is an observed option when the create metadata omits Time tracking; it does not authorize either write by itself.

## Boundary

- Jira Cloud only. Exclude Data Center, Forge CLI, TWG CLI `twg`, browser automation, unofficial clients, and arbitrary REST execution.
- MCP is primary. Prefer the exact machine-readable [capability registry](references/rest-capability-registry.md). When it has no match, REST requires a task-scoped dynamic capability contract derived from current official Atlassian documentation as defined in [REST API workflow](references/rest-api-workflows.md); never infer an endpoint by resemblance.
- ACLI requires a task-scoped user request or approval. Do not inspect or invoke it merely because another route fails.
- Automatic MCP-to-REST selection authorizes only the route. It never authorizes a new target/payload, configures credentials, or overrides an explicit user limit on routes or attempts. An already authorized attachment upload may continue through another documented route after an unusable route or a verified non-write, as described in the MCP and REST attachment workflows.

## Resolve a route

1. Name the capability, product family, read/write class, and target provenance.
2. Inspect live official Rovo MCP tools and schemas. On v2, use `discover` when the exact capability is deferred, then invoke it through the matching `executeRead`, `executeWrite`, or `executeDestructive` route. Use MCP when it exposes the exact capability; documentation snapshots do not prove runtime presence or absence.
   For uploads, live-discover `uploadAttachmentToJiraIssue`; its absence from the initial tool list is not evidence that MCP lacks attachment support.
3. If connected/authenticated MCP lacks the capability or its upload route cannot satisfy the current execution and secret-handling constraints, use one exact registry capability when available. Otherwise build and disclose a dynamic capability contract from the exact official Jira Cloud REST endpoint page. Respect any route the user prohibited.
4. If MCP is unavailable, REST may proceed when existing credentials independently identify the site and the target/selector and authorization required by the operation's risk tier are satisfied. Otherwise ask whether to use ACLI.
5. If no exact official endpoint, required scope, target provenance, risk classification, bounds, or verification can be established, stop and ask about ACLI when useful.
6. If ACLI was requested initially, use its workflow directly; verify executable, version/help, authentication, site/account, and target.

On a definite Jira validation rejection, continue bounded read-only diagnosis before declaring the task blocked: inspect the rejected field, exact issue-type metadata, available MCP create/edit capabilities, and a comparable same-project issue where useful. Consider a supported sequence of separate authorized writes, then the registered or documented REST route under its credential rules. A rejected create is not an uncertain create; verify absence before a revised attempt. Never retry an uncertain write, bypass a missing permission, assume another credential's identity, or inspect ACLI without its required authorization.

For an authorized attachment upload, keep working toward the verified attachment when an attempt fails. Read the exact current Atlassian endpoint documentation, diagnose the status and response without exposing secrets, check the issue attachment list, and try another permitted, documented route or a corrected request when the prior attempt is confirmed not to have created the attachment. The original authorization covers the same issue, file bytes, filename, and intended outcome unless the user limited attempts or routes; a different target, file, or outcome needs fresh authorization. Never repeat an unresolved write or create a duplicate. Stop only when every permitted route is unavailable, the result remains uncertain after read-back, a required credential/permission is missing, or the user-imposed boundary prevents further work; report the precise blocker and what was tried.

Read [MCP workflow](references/mcp-workflows.md) before MCP, [REST API workflow](references/rest-api-workflows.md) plus the registry/domain reference before REST, and [ACLI workflow](references/command-workflows.md) before ACLI. Consult [official sources](references/official-sources.md) for current interfaces.

## Risk tiers

### Tier A — bounded reads

After verifying identity/site and explicit target provenance, apply only registry bounds: minimum fields, narrow JQL/filter/state, finite page ceilings, and permission-respecting output. Tier A covers registered issue detail/changelog/comments/worklogs/links/watchers, attachments, boards/backlogs/sprints, and versions/releases.

### Tier B — one authorized target

Tier B covers only registered comment, create-link, add-watcher, assignment, transition, and selected-field edit operations. The current request or authoritative workflow must independently authorize the exact target and bounded payload. Never infer a write target from a branch, recent activity, search results, or conversational proximity.

Before writing:

1. Verify identity/site, exact registry entry, scopes/permissions, and target provenance.
2. Re-read current state and required metadata; show target/payload when not already explicit.
3. Execute once and require the documented success status.
4. Re-read the entry's verification state. If the result is uncertain, do not retry through MCP, REST, or ACLI.

### Tier C — sensitive, broad, or destructive

Tier C covers delete, unlink/removal, bulk, destructive, administrative, broad-selector/JQL-selected writes, permission/configuration changes, and Agile mutations. Perform a read-only preflight, enumerate or count affected targets, explain impact and reversibility, then request exact confirmation immediately before execution. Confirmation must include site/account, endpoint, selector, count/IDs, and payload; it is invalid if any of those change. Execute once, stop on partial or uncertain results, and verify with a safe read when the official API provides one.

## Identity, credentials, and configuration

- Verify MCP identity/resources or `acli jira auth status`; redact unnecessary identity, site, and private content.
- Do not assume MCP, REST, and ACLI credentials authenticate one another. Correlate the REST API-token site/account with the MCP target; stop on ambiguity.
- REST uses an existing Jira Cloud API token only through HTTP Basic authentication with its configured account email and `https://<site>.atlassian.net`. Never send `JIRA_ACCESS_TOKEN` or any Jira API token with `Authorization: Bearer`, and do not use an OAuth access token for REST in this skill. The approved local REST token source is `~/.codex/.vault/.env.vault`, key `JIRA_ACCESS_TOKEN`; create the empty protected scaffold when it is missing, then have the user populate it. Load the configured value only into a child process environment as defined in the REST workflow, never into agent context. Never bootstrap consent/apps, replace/persist credential values, or expose tokens, headers, cookies, signed URLs, or other secret paths.
- An Atlassian Media upload Bearer token is a separate, short-lived credential minted by MCP. Use it only for the exact Media URL, collection, and file it authorizes; never substitute or reuse `JIRA_ACCESS_TOKEN`, copy Media authorization across tasks/sessions, or expose the token or signed upload command in chat or records. A shell tool receives the token-bearing command in its input even when its history is redacted. If the user forbids that exposure, treat MCP Media as unusable unless a protected executor exists; a task-specific explicit exception permits the bounded command-execution path in [MCP upload workflow](references/mcp-workflows.md). Do not repeatedly rediscover an unusable route.
- For ACLI, run root-to-leaf help and use installed syntax. Preserve prompts; use `--yes` only after exact confirmation. Never default to `--ignore-errors`.
- Do not install, upgrade, log out, switch identities, or modify configuration unless requested when a suitable route remains operational.

## Execute and report

- Match the live MCP schema, registry entry, dynamic capability contract, or current ACLI help exactly. Bound arguments/payloads and keep credentials out of commands/logs.
- Check native exit code, MCP result, or HTTP status before parsing. Respect `Retry-After` for reads; never automatically retry uncertain mutations.
- Report route/capability family, verified site, target, result, post-operation verification, and limitations. For attachments include only sanitized filename/path metadata, byte count, media type, status, and a redacted or shortened ID when appropriate. Do not repeat private content or secrets.

Stop when identity/site/target/payload/visibility is ambiguous, credentials cannot be correlated, permissions/scopes are absent, the exact official endpoint contract cannot be established, required Tier C confirmation is absent, or a mutation result is uncertain. Never silently switch to ACLI or browser automation.
