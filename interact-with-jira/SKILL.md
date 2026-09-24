---
name: interact-with-jira
description: Work with Jira Cloud through official Atlassian Rovo MCP, including MCP-issued Media upload and download transfers. Use for Jira reads, writes, attachments, boards, sprints, releases, configuration, authentication, and safety gates. No Jira REST API or ACLI fallback.
---

# Interact with Jira

## OCB Jira metadata

For `https://wowocb.atlassian.net`, use the checked-in [metadata snapshot](references/wowocb-metadata.json) to resolve project keys/IDs, issue types, statuses by work type, board IDs, and issue link types. Read [snapshot usage and recovery](references/wowocb-metadata.md) before using those values. The snapshot was retrieved through authenticated Atlassian Rovo MCP on 2026-09-23 and reflects that account's visibility. Do not refresh the site-wide catalog routinely; follow the recovery procedure only when a concrete mismatch, missing value, or Jira validation error makes it necessary.

The snapshot is not a substitute for issue-specific current state, transitions, required create/edit fields, permissions, or assignee/sprint eligibility. Fetch only the necessary live metadata for the exact target when an operation needs it, as required by the risk-tier rules below.

For a new Sub-task on `wowocb.atlassian.net` that also needs an Original Estimate, read [the OCB Sub-task estimate workflow](references/wowocb-metadata.md#sub-task-original-estimate) before writing. Its two-step MCP route is an observed option when the create metadata omits Time tracking; it does not authorize either write by itself.

## Boundary

- Jira Cloud operations use official Atlassian Rovo MCP only. Do not use or offer Jira REST API, ACLI, browser automation, unofficial clients, Forge CLI, or TWG CLI as fallbacks. Data Center is outside this skill.
- Local HTTP file transfers are allowed only for the exact Atlassian Media upload or download delegated by the live MCP response. Bind the URL, temporary authorization, file, and destination to that operation as described in [MCP file transfers](references/mcp-workflows.md#media-transfer-authorization). Do not construct independent Jira API requests or inspect local REST credentials.
- Capability discovery and transport access do not authorize mutations. Preserve the user's exact target, payload, outcome, and any limits on attempts or secret visibility.

## Resolve an MCP capability

1. Name the capability, product family, read/write class, and target provenance.
2. Inspect live official Rovo MCP tools and schemas. On v2, use `discover` when the exact capability is deferred, then invoke it through the matching `executeRead`, `executeWrite`, or `executeDestructive` route. Use MCP when it exposes the exact capability; documentation snapshots do not prove runtime presence or absence.
   For file transfers, discover `uploadAttachmentToJiraIssue` or `downloadJiraIssueAttachment` as needed; absence from the initial tool list is not evidence that MCP lacks the capability.
3. If the exact capability is unavailable, perform bounded read-only diagnosis of the current connection, schema, permissions, and execution constraints. Consider a supported sequence of MCP operations only within the already authorized outcome.
4. If no permitted MCP sequence can complete the task, report the observed blocker, completed steps, unresolved state, and the specific capability, permission, or user constraint that prevents progress. Do not enter a fallback or repeated approval loop.

On a definite Jira validation rejection, inspect the rejected field, exact issue-type metadata, available MCP create/edit capabilities, and a comparable same-project issue where useful. A definitive rejection that establishes no write permits a corrected attempt within the existing authorization. A timeout or ambiguous result requires reconciliation first; absence from one read alone does not establish non-write. Do not repeat an unchanged failing request or a request whose outcome remains uncertain.

For attachments, reconcile the Media upload and Jira attach/embed steps separately using the [upload workflow](references/mcp-workflows.md#upload-and-attach-files). Keep a verified `fileId` when only completion failed. Continue a corrected attempt only when the prior outcome is established, the live contract supports it, and the user's attempt limit allows it. Stop when diagnosis supplies no supported correction, the result remains uncertain, or a required permission or execution facility is unavailable.

Read [MCP workflow](references/mcp-workflows.md) before operating on Jira. For attachment content or checksum verification, also follow its [download workflow](references/mcp-workflows.md#download-and-verify-attachments). Consult [official sources](references/official-sources.md) when a schema or capability needs clarification.

## Risk tiers

### Tier A — bounded reads

Tier A covers bounded MCP reads, including issue details, metadata, comments, worklogs, links, watchers, attachment downloads, boards, sprints, and versions/releases. Verify identity/site and target provenance, request minimum fields, narrow JQL/filter/state, set finite page ceilings, and respect visibility permissions. Report incomplete pagination when a ceiling is reached.

### Tier B — one authorized target

Tier B covers bounded MCP writes that do not fall under Tier C: create one issue, add/edit a comment or worklog, create an issue link, add a watcher, assign an issue, transition its status, edit selected fields, or upload/attach one file. The current request or authoritative workflow must authorize the exact target and bounded payload. For a new issue, bind the project, issue type, parent when applicable, and approved content before creation; verify the returned key afterward. For links, bind both issues. Never infer mutation authority from a branch, recent activity, search results, or conversational proximity.

Before writing:

1. Verify identity/site, live MCP schema, relevant permissions, and target provenance; classify the actual effect even when one tool supports several risk tiers.
2. Re-read current state and required metadata; show target/payload when not already explicit.
3. Execute the validated attempt once and inspect the tool's success or error result.
4. Re-read the affected state. Resolve an uncertain result before another mutation; use the phase-specific reconciliation rules for attachments.

### Tier C — sensitive, broad, or destructive

Tier C covers delete, unlink/removal, bulk, destructive, administrative, broad-selector/JQL-selected writes, permission/configuration changes, and Agile mutations. Perform a read-only preflight, enumerate or count affected targets, explain impact and reversibility, then request exact confirmation immediately before execution. Confirmation must include site/account, MCP capability, selector, count/IDs, and payload; it is invalid if any of those change. Execute once, stop on partial or uncertain results, and verify with an available MCP read. A tool labeled `executeWrite` does not lower a Tier C action's confirmation requirements.

## Identity, credentials, and configuration

- Verify identity and accessible resources through MCP; do not infer the Jira account from Git identity or another client's credentials.
- MCP authentication belongs to the configured client. Never extract or repurpose its login credentials, expose tokens/cookies/headers, or configure independent Jira API credentials for this workflow.
- MCP-issued Media authorization is scoped to the current file transfer. Authorization for that transfer covers its required execution step without a separate token-transport approval, unless the user explicitly restricted tool-input visibility. Do not copy transfer secrets into chat, diagnostic logs, files, or task records; follow [Media transfer authorization](references/mcp-workflows.md#media-transfer-authorization) for the execution boundary and any existing user restriction.
- Do not install, upgrade, log out, switch identities, or modify configuration unless requested when a suitable route remains operational.

## Execute and report

- Match the live MCP schema and bound arguments/payloads. Only the scoped Media execution step may carry MCP-issued transfer authorization; do not copy it into chat, diagnostic logs, or local records.
- Check native exit code, MCP result, or HTTP status before parsing. Respect `Retry-After` for reads; never automatically retry uncertain mutations.
- Report MCP capability, verified site, target, result, post-operation verification, and limitations. For attachments distinguish Media uploaded, Jira attached, and downloaded content verified; include filename, byte count, media type, attachment ID, and any verification gap. Attachment IDs needed for follow-up are not credentials. Do not repeat private file content, tokens, or signed URLs.

Stop dependent writes when identity/site/target/payload is ambiguous, required permissions or Tier C confirmation are absent, no supported MCP capability can complete the operation, user visibility constraints cannot be met, or a mutation remains uncertain after bounded reconciliation. Report the exact blocker and preserve completed work.
