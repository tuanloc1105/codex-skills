---
name: interact-with-jira
description: Work with Jira Cloud through Atlassian Rovo MCP first, registered or dynamically verified official Jira REST fallbacks when MCP lacks a capability or is unavailable, and official Atlassian CLI `acli` only when explicitly requested or approved. Use for Jira reads, writes, attachments, boards, sprints, releases, configuration, authentication, and safety gates.
---

# Interact with Jira

## Boundary

- Jira Cloud only. Exclude Data Center, Forge CLI, TWG CLI `twg`, browser automation, unofficial clients, and arbitrary REST execution.
- MCP is primary. Prefer the exact machine-readable [capability registry](references/rest-capability-registry.md). When it has no match, REST requires a task-scoped dynamic capability contract derived from current official Atlassian documentation as defined in [REST API workflow](references/rest-api-workflows.md); never infer an endpoint by resemblance.
- ACLI requires a task-scoped user request or approval. Do not inspect or invoke it merely because another route fails.
- Automatic MCP-to-REST selection authorizes only the route. It never authorizes a write, selects a target/payload, configures credentials, or retries an uncertain result.

## Resolve a route

1. Name the capability, product family, read/write class, and target provenance.
2. Inspect live official Rovo MCP tools and schemas. Use MCP when it exposes the exact capability; documentation snapshots do not prove runtime presence or absence.
3. If connected/authenticated MCP lacks it, use one exact registry capability when available. Otherwise build and disclose a dynamic capability contract from the exact official Jira Cloud REST endpoint page.
4. If MCP is unavailable, REST may proceed when existing credentials independently identify the site and the target/selector and authorization required by the operation's risk tier are satisfied. Otherwise ask whether to use ACLI.
5. If no exact official endpoint, required scope, target provenance, risk classification, bounds, or verification can be established, stop and ask about ACLI when useful.
6. If ACLI was requested initially, use its workflow directly; verify executable, version/help, authentication, site/account, and target.

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
- Do not assume MCP, REST, and ACLI credentials authenticate one another. Correlate REST OAuth resource/cloud ID or API-token site/account with the MCP target; stop on ambiguity.
- REST discovers existing credentials only: OAuth bearer, then existing API token. Never bootstrap consent/apps, replace/persist credentials, or expose tokens, headers, cookies, signed URLs, or secret paths.
- For ACLI, run root-to-leaf help and use installed syntax. Preserve prompts; use `--yes` only after exact confirmation. Never default to `--ignore-errors`.
- Do not install, upgrade, log out, switch identities, or modify configuration unless requested when a suitable route remains operational.

## Execute and report

- Match the live MCP schema, registry entry, dynamic capability contract, or current ACLI help exactly. Bound arguments/payloads and keep credentials out of commands/logs.
- Check native exit code, MCP result, or HTTP status before parsing. Respect `Retry-After` for reads; never automatically retry uncertain mutations.
- Report route/capability family, verified site, target, result, post-operation verification, and limitations. For attachments include final path and byte count. Do not repeat private content or secrets.

Stop when identity/site/target/payload/visibility is ambiguous, credentials cannot be correlated, permissions/scopes are absent, the exact official endpoint contract cannot be established, required Tier C confirmation is absent, or a mutation result is uncertain. Never silently switch to ACLI or browser automation.
