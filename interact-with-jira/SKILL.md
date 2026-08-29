---
name: interact-with-jira
description: Work with Jira Cloud through Atlassian Rovo MCP first, a closed risk-tiered registry of official Jira REST fallbacks when the live MCP schema lacks an exact capability, and official Atlassian CLI `acli` only when explicitly requested or approved. Use for Jira reads, bounded single-target writes, attachments, boards, sprints, releases, configuration, authentication, and safety gates.
---

# Interact with Jira

## Boundary

- Jira Cloud only. Exclude Data Center, Forge CLI, TWG CLI `twg`, browser automation, unofficial clients, and arbitrary REST execution.
- MCP is primary. REST is permitted only through the exact machine-readable [capability registry](references/rest-capability-registry.md), which defaults to deny.
- ACLI requires a task-scoped user request or approval. Do not inspect or invoke it merely because another route fails.
- Automatic MCP-to-REST selection authorizes only the route. It never authorizes a write, selects a target/payload, configures credentials, or retries an uncertain result.

## Resolve a route

1. Name the capability, product family, read/write class, and target provenance.
2. Inspect live official Rovo MCP tools and schemas. Use MCP when it exposes the exact capability; documentation snapshots do not prove runtime presence or absence.
3. If connected/authenticated MCP lacks it, resolve one exact registry capability ID. Apply method/path, scopes, tier, bounds, retry, and verification together. Never infer a neighboring endpoint.
4. If MCP is unavailable, registry REST may proceed only when an explicit target is known and existing REST credentials independently identify the site. Otherwise ask whether to use ACLI.
5. If no registry entry matches, report the limitation and ask about ACLI when useful. Unlisted REST remains prohibited.
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

### Tier C and prohibited REST

The registry has no Tier C entries. Delete, unlink/removal, bulk, destructive, administrative, broad-selector/JQL-selected writes, Agile mutation, and every unlisted pair are prohibited over REST. For ACLI or MCP bulk/destructive work, perform read-only preflight and request exact confirmation immediately before execution, including site/account, selector, count/IDs, payload, impact, and reversibility.

## Identity, credentials, and configuration

- Verify MCP identity/resources or `acli jira auth status`; redact unnecessary identity, site, and private content.
- Do not assume MCP, REST, and ACLI credentials authenticate one another. Correlate REST OAuth resource/cloud ID or API-token site/account with the MCP target; stop on ambiguity.
- REST discovers existing credentials only: OAuth bearer, then existing API token. Never bootstrap consent/apps, replace/persist credentials, or expose tokens, headers, cookies, signed URLs, or secret paths.
- For ACLI, run root-to-leaf help and use installed syntax. Preserve prompts; use `--yes` only after exact confirmation. Never default to `--ignore-errors`.
- Do not install, upgrade, log out, switch identities, or modify configuration unless requested when a suitable route remains operational.

## Execute and report

- Match the live MCP schema, registry entry, or current ACLI help exactly. Bound arguments/payloads and keep credentials out of commands/logs.
- Check native exit code, MCP result, or HTTP status before parsing. Respect `Retry-After` for reads; never automatically retry uncertain mutations.
- Report route/capability family, verified site, target, result, post-operation verification, and limitations. For attachments include final path and byte count. Do not repeat private content or secrets.

Stop when identity/site/target/payload/visibility is ambiguous, credentials cannot be correlated, permissions/scopes are absent, no exact registry entry exists, or a mutation result is uncertain. Never silently switch to ACLI or browser automation.
