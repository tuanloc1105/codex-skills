# Atlassian Rovo MCP workflow for Jira Cloud

## Contents

- Discover and select an MCP client
- Configure the server in Kiro Crew
- Migrate an existing v1 connection to v2
- Authenticate and identify the target
- Read data
- Mutate data
- Route an unsupported capability
- Troubleshoot

## Discover and select an MCP client

Atlassian Rovo MCP is a remote Streamable HTTP server. Before configuration, confirm how
this Kiro Crew instance registers MCP servers and inspect the current tool list/help; do
not copy another client's syntax.

Current official endpoint (v2):

```text
https://mcp.atlassian.com/v2/mcp
```

v2 exposes a `discover` + `execute` tool pair by default. When this Kiro Crew instance (or
an MCP gateway in front of it) needs every tool in a flat `tools/list` response instead of
the discover/execute indirection, use the variant that expands all tools directly:

```text
https://mcp.atlassian.com/v2/mcp?tools=all
```

Do not configure the retired `/v1/sse` endpoint, and do not configure the older
`/v1/mcp` or `/v1/mcp/authv2` endpoints for a new setup — use v2. If an existing
configuration still points at a v1 endpoint, follow "Migrate an existing v1 connection to
v2" below. Do not replace official Atlassian Rovo MCP with a third-party Jira MCP package
unless the user requests it and the risks have been assessed.

## Configure the server in Kiro Crew

The Atlassian Rovo MCP server is registered in this Kiro Crew instance's agent/MCP
configuration (through the dashboard's MCP settings or the agent config that lists MCP
servers), not through a `codex mcp` CLI. When the user asks to set it up:

- Add an MCP server entry pointing at the Streamable HTTP endpoint
  `https://mcp.atlassian.com/v2/mcp` with OAuth authorization, using this instance's
  own MCP-server configuration mechanism (add `?tools=all` when a flat tool list is
  required). Describe the action in prose to the user rather
  than inventing exact CLI syntax; direct them to the Kiro Crew MCP settings when a manual
  step is required.
- OAuth opens a browser for the user to sign in and consent. Do not choose an account/site
  automatically when multiple options exist. Do not put an access token in a command,
  configuration file, or chat.
- Prefer a safe default where write tools still require approval rather than auto-approving
  every mutation. Read the current configuration, preserve unrelated fields, and add or
  change only values the user requested.

`enabled` and a successful OAuth flow only confirm that the configuration was recognized.
Open a new session when needed, confirm the Atlassian tools appear in this session's tool
list, and call exactly one minimal read-only tool to verify that the server connected and
OAuth actually works.

## Migrate an existing v1 connection to v2

Atlassian released v2 of Rovo MCP with more tools and products. On **1 Mar 2027** any v1
connection automatically begins exposing and using v2 tools; before then a v1 connection
keeps its v1 tools, so migrate deliberately rather than waiting for the cutover. This
applies whenever the current Kiro Crew configuration still targets `https://mcp.atlassian.com/v1/mcp`
or `https://mcp.atlassian.com/v1/mcp/authv2`.

Migrate only when the user asks. A working v1 connection is not by itself a reason to
change configuration mid-task. Read the current configuration first, preserve unrelated
fields, and change only the endpoint (and, if requested, the `?tools=all` variant).

Steps for Kiro Crew's own MCP-server configuration:

1. **Identify the v1 entry.** In the dashboard's MCP settings or the agent config that
   lists MCP servers, find the Atlassian entry whose `url`/`serverUrl` is
   `https://mcp.atlassian.com/v1/mcp` or `.../v1/mcp/authv2`. If none exists, there is
   nothing to migrate — a fresh setup should just use v2 directly.
2. **Repoint the URL to v2.** Change that single value to
   `https://mcp.atlassian.com/v2/mcp` (append `?tools=all` only when a flat `tools/list`
   without the `discover`/`execute` pair is required). Leave OAuth mode, approval policy,
   and every other field unchanged. Describe the edit in prose; direct the user to the
   Kiro Crew MCP settings for any manual step rather than inventing CLI syntax.
3. **Re-authenticate.** v2 is a **separate OAuth resource**, so v1 credentials do **not**
   carry over. Trigger the server's OAuth flow again (it opens a browser for sign-in and
   consent). Do not attempt to reuse or copy a v1 token, and never place a token in a
   command, config file, or chat.
4. **Clear stale client credentials if the client refuses to connect.** An incompatible
   client cached from v1 may need its cached `clientId` / `.well-known` OAuth registration
   cleared before v2 will connect. Do this only when a connection actually fails after the
   repoint, and confirm the observed error first.
5. **Verify.** Open a new session when needed, confirm the Atlassian tools appear in this
   session's tool list, then call exactly one minimal read-only tool (for example an
   identity/resources lookup) to confirm the v2 server connected and OAuth works. Only
   report success after that live check passes.

Notes:

- Bearer-token / API-token connections were documented for `v1/mcp` only. If the existing
  entry authenticates with a static token rather than OAuth, do not silently repoint it;
  surface that to the user and confirm the intended v2 authentication before changing it.
- Do not migrate a client you were not asked about, and do not touch a v1 entry that
  belongs to a different tool or another user's configuration.

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

- Server is absent: check the MCP-server configuration scope, that the Atlassian tools appear in this session's tool list, and try a client restart or a new session.
- `enabled` but tools cannot be called: run a live read-only check; inspect OAuth, token expiration, organization permissions, domain/IP allowlists, and network access.
- OAuth does not open or the callback fails: retry login after checking browser/callback behavior and the domain allowlist; do not automatically switch to a token.
- `Access denied`: verify the user's Jira permissions and Read/Write/Search groups in Atlassian Administration.
- Expected tool is absent: recheck the live tool list/schema, then use a registered capability or derive an exact dynamic REST contract from current official documentation.
- Multiple sites or incorrect `cloudId`: repeat resource discovery and ask the user to select the target.
