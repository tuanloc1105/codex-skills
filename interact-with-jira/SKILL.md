---
name: interact-with-jira
description: Work with Jira Cloud through the official Atlassian CLI (`acli`) and Atlassian Rovo MCP, including configuration, authentication, searching, viewing, creating, editing, transitioning work items, and other Jira capabilities supported by each tool. Use when Codex needs to select, coordinate, configure, or troubleshoot ACLI/MCP; automatically fall back to an available tool and apply safety gates to write, bulk, or destructive operations.
---

# Interact with Jira

## Stay within scope

- Apply this skill to Jira Cloud through Atlassian CLI `acli` and Atlassian Rovo MCP. Do not assume these workflows apply to Jira Data Center, Forge CLI, or TWG CLI `twg`.
- If the user says “Atlassian CLI” without naming the binary, check the executable or ask when both `acli` and `twg` are available. Do not use `twg` syntax with `acli`.
- Do not call the Jira REST API to work around ACLI or MCP limitations. If neither tool supports the task, report the limitation and ask for permission before expanding scope to another tool.

## Select and coordinate tools

1. Determine the required capability and target, and whether the operation is a read or write.
2. Perform lightweight checks for tools available in the current environment; do not require both:
   - ACLI: check the executable, version, help, and authentication according to the ACLI workflow.
   - MCP: check that the client loaded the Atlassian server/tools, the connection status, and the identity/site according to the MCP workflow.
3. Select an available tool that supports the task. When both are available:
   - Prefer MCP for natural-language interaction, cross-product context, and Jira tools exposed by the server.
   - Prefer ACLI for deterministic, scriptable operations or administrative groups that MCP does not expose.
   - You may use one tool for reads/preflight and the other for execution when that reduces risk; verify that both point to the same site/account/target.
4. If the selected tool is missing, disconnected, unauthenticated, or lacks the capability, try the other tool when it can finish safely. Briefly report the switch; do not require the user to install both.
5. Stop for missing tooling only when neither ACLI nor MCP is available or can be configured/authenticated within the permitted scope. If both are available but neither supports the required capability, report the limitation and ask for permission to expand scope.

Do not switch tools to automatically retry a mutation with an uncertain result. First read the target again with an available tool, determine what succeeded, and ask for a new decision.

## Verify before acting

1. For ACLI, run `acli --version`, `acli jira --help`, and the help for the group and leaf command you intend to use. Use syntax published by the current binary; do not guess flags from memory or from `twg`.
2. For MCP, use the tool schema published by the current server. Do not guess tool names, inputs, or capabilities from old examples; verify the server, authentication, site, and a read-only tool before a mutation.
3. When checking changes, installation, authentication, endpoints, or version errors, consult the [official Atlassian sources](references/official-sources.md).
4. Before first using ACLI, read the [ACLI workflow and safety guidance](references/command-workflows.md). Before using or configuring MCP, read the [Atlassian MCP workflow](references/mcp-workflows.md). Re-read the relevant section before bulk, destructive, or authentication operations.

## Configuration support

- When requested, you may guide or perform configuration for a missing tool. Verify the client, operating system, current binary/help, and official documentation before writing configuration.
- For MCP, prefer official Atlassian Rovo MCP over Streamable HTTP with OAuth 2.1 for interactive sessions. Do not use the retired SSE endpoint, place tokens directly in configuration/chat, or automatically enable an organization's API-token authentication.
- For ACLI, use official installation/authentication guidance and prefer web OAuth. Do not install, upgrade, log out, or replace credentials when the user only requested a Jira operation.
- Configuring one tool is not required to use the other. After configuration, verify with status and one minimal read-only operation; distinguish “declared/enabled” from “connected and successfully invoked.”

## Check identity and target

- With ACLI, run `acli jira auth status` before accessing real data. With MCP, use a read-only identity/resource tool published by the server to confirm the account, site, and `cloudId` when needed. Redact email, site, account ID, and cloud ID when they are unnecessary in chat.
- Use `acli jira auth switch --site <site> --email <email>` after the user selects another identity. Do not choose automatically among multiple potentially valid sites/accounts.
- Prefer the interactive OAuth flow of the tool in use. Do not assume an ACLI login also authenticates MCP or vice versa.
- For API tokens, provide the token through standard input from a secret store, environment variable, or uncommitted local file. Never place it in an argument, script, shell history, log, or chat.
- Do not log out, install, upgrade, or change credentials when the user only requested a Jira operation and a suitable tool remains operational.

## Classify actions

### Read-only

After verifying the target, these actions are allowed within the requested scope:

- Check ACLI or MCP client/server version, help, authentication, or status.
- Use ACLI `list`, `search`, `view`, `count`, and `get` commands supported by the current version.
- Use tools marked read-only by the current MCP server, including identity/resource discovery, work item, project, metadata, transition, and search reads when available.
- Look up work items, projects, boards, sprints, filters, and dashboards using a tool with the corresponding capability.

Keep JQL, fields, and result counts to the minimum needed. Prefer `--json` for machine processing; do not use `--paginate` unless the entire result set is truly required.

### Writes with a specific target

The user's initial request may authorize exactly one specific change, such as creating a work item, editing named fields, assigning an assignee, transitioning status, or adding a comment. Before executing:

1. Verify the site/account and command help or MCP tool schema.
2. Re-read the current work item/project when that can detect a wrong target or prevent overwriting.
3. Summarize the target and fields to change when the request does not make them explicit.
4. Preserve the ACLI/MCP client confirmation prompt; bypass or automatically approve it only after satisfying the gate below.
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

- For ACLI, pass native arguments as an argument vector/array; do not construct a shell string from Jira or user data. For MCP, send input matching the schema and include only required fields.
- Use JSON/ADF files for complex payloads; obtain a sample schema from `--generate-json` on the exact version and review the file before sending it.
- Check the native exit code or MCP tool result/error before parsing output. Do not treat partial output as complete success.
- Redact tokens, unnecessary email addresses, private content, and PII before presenting results in chat.
- Report the tool and command family/tool used, verified site, target, result, limitations, fallback if any, and post-write verification. Do not repeat secrets or sensitive payloads.

## Stop safely

Stop and ask when the site, account, project, work item, selector, or mutation is ambiguous; when help/schema conflicts with examples; when both tools lack permission or require reauthorization; when neither tool supports the capability; or when completion requires the REST API, browser automation, or an out-of-scope tool. Do not create silent workarounds, and do not stop merely because one of the two tools is absent.
