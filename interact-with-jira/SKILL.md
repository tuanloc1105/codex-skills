---
name: interact-with-jira
description: Work with Jira Cloud through Atlassian Rovo MCP first, a closed allowlist of official Jira REST API v3 fallbacks when MCP lacks the capability, and the official Atlassian CLI (`acli`) only when the user explicitly requests or approves it. Use for configuration, authentication, reads, writes, attachment downloads, one explicitly authorized issue comment, tool coordination, and safety gates for write, bulk, or destructive operations.
---

# Interact with Jira

## Stay within scope

- Apply this skill to Jira Cloud through Atlassian Rovo MCP, the closed official REST API allowlist below, and Atlassian CLI `acli`. Do not assume these workflows apply to Jira Data Center, Forge CLI, or TWG CLI `twg`.
- If the user says “Atlassian CLI” without naming the binary, check the executable or ask when both `acli` and `twg` are available. Do not use `twg` syntax with `acli`.
- REST access is limited to the exact method/path pairs below. Unlisted methods, paths, bulk writes, browser automation, and unofficial clients are prohibited; do not generalize this allowlist.

### Closed REST fallback allowlist

- `GET /rest/api/3/attachment/{id}` for metadata required by an explicit attachment download.
- `GET /rest/api/3/attachment/content/{id}` for that explicit attachment's content.
- `POST /rest/api/3/issue/{issueIdOrKey}/comment` for one comment on exactly one issue explicitly identified and authorized by the current request or authoritative workflow.

Automatic MCP-to-REST selection authorizes only the tool route. It does not authorize a mutation, select an issue, broaden a payload, configure credentials, or retry an uncertain result.

## Select and coordinate tools

1. Determine the required capability and target, and whether the operation is a read or write.
2. Use MCP by default. Check that the client loaded the official Atlassian server/tools, then verify the connection, authentication, identity, and site according to the MCP workflow before acting.
3. If MCP is connected and authenticated but its current schema lacks an allowlisted capability, route directly to the [REST API workflow](references/rest-api-workflows.md) without fallback approval or an ACLI check. Verify separate existing REST credentials and correlate their site/cloud resource with the MCP target.
4. If MCP is unavailable, disconnected, unauthenticated, or blocked, an allowlisted REST operation may proceed only when an explicit target is already known and existing REST credentials independently identify the intended Jira site. Otherwise ask whether the user wants ACLI; do not inspect or invoke it before approval.
5. For a capability outside the REST allowlist, report the MCP limitation and ask whether the user wants ACLI when it may support the task. Do not inspect or invoke ACLI until approved.
6. If the user explicitly requests ACLI at the outset, use its workflow directly without requiring an MCP check. Check the executable, version, help, and authentication before accessing Jira.
7. After the user requests or approves ACLI, verify its site/account/target. If it is unavailable, unauthenticated, or lacks the capability, report the limitation; do not silently switch tools or expand scope.

ACLI approval applies only to the current Jira task. Automatic REST routing applies only to the closed allowlist. Never switch tools to retry an uncertain mutation; re-read state safely, determine what may have succeeded, and ask for a new decision.

## Verify before acting

1. For ACLI, run `acli --version`, `acli jira --help`, and the help for the group and leaf command you intend to use. Use syntax published by the current binary; do not guess flags from memory or from `twg`.
2. For MCP, use the tool schema published by the current server. Do not guess tool names, inputs, or capabilities from old examples; verify the server, authentication, site, and a read-only tool before a mutation.
3. For REST, verify the exact method/path against the closed allowlist and current official documentation; do not infer neighboring endpoints.
4. When checking changes, installation, authentication, endpoints, or version errors, consult the [official Atlassian sources](references/official-sources.md).
5. Before first using ACLI, read the [ACLI workflow](references/command-workflows.md). Before MCP, read the [MCP workflow](references/mcp-workflows.md). Before REST credential discovery or a request, read the [REST API workflow](references/rest-api-workflows.md).

## Configuration support

- When requested, you may guide or perform configuration for a missing tool. Verify the client, operating system, current binary/help, and official documentation before writing configuration.
- For MCP, prefer official Atlassian Rovo MCP over Streamable HTTP with OAuth 2.1 for interactive sessions. Do not use the retired SSE endpoint, place tokens directly in configuration/chat, or automatically enable an organization's API-token authentication.
- For ACLI, use official installation/authentication guidance and prefer web OAuth. Do not install, upgrade, log out, or replace credentials when the user only requested a Jira operation.
- Configuring one tool is not required to use another. REST fallback may discover only existing credentials, preferring existing OAuth 2.0 bearer credentials and then an existing API token. Never bootstrap an app, start consent, replace, or persist credentials automatically. Do not inspect ACLI merely because MCP setup fails.

## Check identity and target

- With ACLI, run `acli jira auth status` before accessing real data. With MCP, use a read-only identity/resource tool published by the server to confirm the account, site, and `cloudId` when needed. Redact email, site, account ID, and cloud ID when they are unnecessary in chat.
- Use `acli jira auth switch --site <site> --email <email>` after the user selects another identity. Do not choose automatically among multiple potentially valid sites/accounts.
- Prefer the interactive OAuth flow of the tool in use. Do not assume MCP, REST, and ACLI credentials authenticate one another. Correlate REST OAuth accessible-resource/cloud ID or API-token site/account with the intended MCP target; stop on ambiguity.
- For API tokens, provide the token through standard input from a secret store, environment variable, or uncommitted local file. Never place it in an argument, script, shell history, log, or chat.
- Do not log out, install, upgrade, or change credentials when the user only requested a Jira operation and a suitable tool remains operational.

## Classify actions

### Read-only

After verifying the target, these actions are allowed within the requested scope:

- Check ACLI or MCP client/server version, help, authentication, or status.
- Use ACLI `list`, `search`, `view`, `count`, and `get` commands supported by the current version.
- Use tools marked read-only by the current MCP server, including identity/resource discovery, work item, project, metadata, transition, and search reads when available.
- Use the two allowlisted REST attachment `GET` operations only for an explicit download after metadata, target, destination, redirect, and file-safety checks.
- Look up work items, projects, boards, sprints, filters, and dashboards using a tool with the corresponding capability.

Keep JQL, fields, and result counts to the minimum needed. Prefer `--json` for machine processing; do not use `--paginate` unless the entire result set is truly required.

### Writes with a specific target

The user's initial request may authorize exactly one specific change. For REST comments, the current request or authoritative workflow must identify exactly one issue key/ID and authorize the bounded payload. Never infer the issue from a branch, recent activity, search results, or conversational proximity. Before executing:

1. Verify the site/account and command help or MCP tool schema.
2. Re-read the current work item/project when that can detect a wrong target or prevent overwriting.
3. Summarize the target and fields to change when the request does not make them explicit.
4. Preserve ACLI/MCP confirmation prompts; bypass them only after satisfying the gate below. REST fallback selection is not write approval.
5. After execution, check the exit code and re-read important objects to verify the result.

Do not treat a general request such as “clean up Jira” or “update these tickets” as authorization for every inferred change.

### Bulk or destructive operations

Always perform a read-only preflight and request explicit confirmation immediately before executing:

- Any mutation selecting targets by JQL, filter, file, or multiple keys.
- Delete, archive/unarchive, restore, change owner, remove/reset configuration, or remove a comment, attachment, watcher, or link.
- Delete/archive a project, board, sprint, or custom field.
- Any action that may affect workflows, access, reporting, or multiple users.

The preflight must identify the site/account, redacted command or MCP tool, selector, count and key/ID list when practical, fields/statuses to change, and reversibility. Stop after requesting confirmation; execute only when the user agrees in the current chat to that exact target and operation. Repeat the preview if the selector, data, identity, command, tool, or execution tool changes.

Do not use `--ignore-errors` by default. Do not automatically retry a mutation with an uncertain result; re-read state, report what succeeded or failed, and ask for a new decision.

## Execute and report

- For ACLI, pass native arguments as an argument vector. For MCP, match the schema. For REST, keep credentials out of arguments and logs, handle redirects within the trusted Atlassian boundary, and send only an allowlisted request.
- Use JSON/ADF files for complex payloads; obtain a sample schema from `--generate-json` on the exact version and review the file before sending it.
- Check the native exit code, HTTP status, or MCP result before parsing. A REST comment requires `201` plus a re-read locating it; a download requires a successful response and verified byte count.
- Redact tokens, unnecessary email addresses, private content, and PII before presenting results in chat.
- Report the tool or REST method family, verified site, target, result, limitations, fallback, final attachment path when relevant, and post-write verification. Do not repeat secrets, signed/private URLs, or sensitive payloads.

## Stop safely

Stop when the site, identity, issue, attachment, destination, payload, visibility, or mutation is ambiguous; credentials cannot be safely discovered or correlated; the selected tool lacks permission; a REST method/path is not allowlisted; or a result is uncertain. Ask before ACLI unless already requested or approved. Never silently fall back from MCP/REST to ACLI, use browser automation, or automatically retry a mutation.
