# Atlassian Rovo MCP workflow for Jira Cloud

## Contents

- Discover and select an MCP client
- Configure Codex
- Authenticate and identify the target
- Read data
- Mutate data
- Route an unsupported capability
- Troubleshoot

## Discover and select an MCP client

Atlassian Rovo MCP is a remote Streamable HTTP server. Before configuration, identify the user's MCP client and inspect its current help/documentation; do not copy Codex syntax to another client.

Current official endpoint:

```text
https://mcp.atlassian.com/v1/mcp/authv2
```

Do not configure the `/v1/sse` endpoint. Do not replace official Atlassian Rovo MCP with a third-party Jira MCP package unless the user requests it and the risks have been assessed.

## Configure Codex

Verify the CLI first:

```text
codex --version
codex mcp --help
codex mcp add --help
codex mcp login --help
```

After the user requests configuration, add the server:

```text
codex mcp add atlassian --url https://mcp.atlassian.com/v1/mcp/authv2
codex mcp login atlassian
```

OAuth opens a browser for the user to sign in and consent. Do not choose an account/site automatically when multiple options exist. Do not put an access token in a command, configuration, or chat.

Recommended safe configuration in `~/.codex/config.toml` or the project configuration selected by the user:

```toml
[mcp_servers.atlassian]
url = "https://mcp.atlassian.com/v1/mcp/authv2"
auth = "oauth"
default_tools_approval_mode = "writes"
enabled = true
```

Do not overwrite an existing table. Read the current configuration, preserve unrelated fields, and add or change only values requested by the user. After the change, run:

```text
codex mcp list
codex mcp get atlassian
```

`enabled` and `OAuth` only confirm that the configuration was recognized. Open a new Codex session when needed, check `/mcp`, and call exactly one minimal read-only tool to verify that the server connected and OAuth actually works.

## Authenticate and identify the target

- Prefer OAuth 2.1 for interactive sessions. API tokens are for non-interactive/M2M use and may be used only when the organization permits them and the user requests them.
- Use `atlassianUserInfo` and `getAccessibleAtlassianResources`, or equivalent tools published by the current server, to verify the identity and site/cloud ID.
- When multiple sites exist, do not choose one solely by a similar name. Ask the user to select or correlate it with the specified target.
- MCP permissions do not exceed the user's Jira permissions. Organization administrators may also independently block Read, Write, or Search groups, OAuth domains, and IP addresses.

## Read data

Call only tools exposed by the current server and use their published schemas. Common Jira capabilities include reading work items, project/type metadata, transitions, remote links, account lookup, and JQL search.

Keep queries narrow:

- Request only required fields.
- Limit JQL and result counts.
- Do not retrieve descriptions, comments, attachments, or user data unless the task needs them.
- Redact email, account ID, cloud ID, site, and private content before reporting.

## Mutate data

Common write capabilities include creating/editing work items, comments, worklogs, and transitions. Before every mutation:

1. Verify identity/site and the tool schema.
2. Read the target or required metadata/transitions.
3. Preserve approval for write tools.
4. For bulk or destructive operations, perform a preflight and request confirmation as specified in `SKILL.md`.
5. After a successful tool result, re-read important targets.

If a tool times out or returns an uncertain result, do not invoke it again through MCP, REST, or ACLI. Read the target first to avoid a duplicate mutation.

## Probe and route an unsupported capability

- If MCP is unconfigured, unavailable, disconnected, unauthenticated, or blocked by policy, tell the user which condition was observed. Continue to REST when existing credentials independently identify the intended site and the registered or dynamic capability contract's target and authorization requirements are satisfied; otherwise ask whether they want to use ACLI. Do not inspect or invoke ACLI before they approve.
- Resolve the exact requested capability first, then inspect the live server tool list and candidate schemas. A published supported-tools snapshot is discovery evidence only; it neither proves a runtime tool is loaded nor proves absence.
- If MCP is connected and authenticated but lacks the exact capability, prefer one exact capability ID in `rest-capability-registry.json`. If none matches, route to `rest-api-workflows.md` and derive a dynamic capability contract from the exact current official endpoint page. Independently verify REST credentials/site; route selection never supplies mutation authorization.
- If no exact official Jira Cloud endpoint or complete dynamic contract can be established, explain the limitation and ask whether the user wants ACLI. Neighboring endpoints and undocumented method/path pairs are not alternatives.
- Treat approval as scoped to the current Jira task. Do not make ACLI the default for later tasks.
- After approval, follow `references/command-workflows.md`, verify the ACLI site/account/target, and repeat any mutation preview when the execution tool or impact changes.

## Troubleshoot

- Server is absent: check configuration scope, `codex mcp list`, client restart/new session, and `/mcp`.
- `enabled` but tools cannot be called: run a live read-only check; inspect OAuth, token expiration, organization permissions, domain/IP allowlists, and network access.
- OAuth does not open or the callback fails: retry login after checking browser/callback behavior and the domain allowlist; do not automatically switch to a token.
- `Access denied`: verify the user's Jira permissions and Read/Write/Search groups in Atlassian Administration.
- Expected tool is absent: recheck the live tool list/schema, then use a registered capability or derive an exact dynamic REST contract from current official documentation.
- Multiple sites or incorrect `cloudId`: repeat resource discovery and ask the user to select the target.
