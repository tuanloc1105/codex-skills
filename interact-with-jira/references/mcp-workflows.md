# Atlassian Rovo MCP workflow for Jira Cloud

## Contents

- Discover and select an MCP client
- Choose native HTTP or an `mcp-remote` bridge
- Configure Codex
- Switch transports safely
- Migrate an existing v1 connection to v2
- Authenticate and identify the target
- Read data
- Mutate data
- Upload and attach files
- Route an unsupported capability
- Troubleshoot

## Discover and select an MCP client

Atlassian Rovo MCP is a remote Streamable HTTP server. Before configuration, identify the user's MCP client and inspect its current help/documentation; do not copy Codex syntax to another client.

Current official endpoint (v2):

```text
https://mcp.atlassian.com/v2/mcp
```

v2 exposes a small primary tool set and defers the rest behind `discover` and the risk-specific `executeRead`, `executeWrite`, and `executeDestructive` tools. When an MCP gateway requires every tool in a flat, paginated `tools/list` response, use:

```text
https://mcp.atlassian.com/v2/mcp?tools=all
```

Do not configure the retired `/v1/sse`, `/v1/mcp`, or `/v1/mcp/authv2` endpoints for a new setup. If an existing configuration still points at v1, follow the migration workflow below. Do not replace official Atlassian Rovo MCP with a third-party Jira MCP package unless the user requests it and the risks have been assessed.

## Choose native HTTP or an `mcp-remote` bridge

When configuration is requested and either transport is viable, present these choices and let the user select:

- **Native HTTP (recommended):** the MCP client connects directly to Atlassian's Streamable HTTP endpoint. This removes a local proxy and npm dependency.
- **`mcp-remote` bridge:** the MCP client launches a local stdio command through `npx`, and `mcp-remote` bridges it to Atlassian's remote endpoint. Use this for stdio-only clients or when the user explicitly prefers it.

`mcp-remote` is a third-party transport bridge, not the Atlassian MCP server. Before configuring it, verify `node`, `npm`, the package owner/repository, and the current package version. Show the exact package and version to the user; after they select this option, pin that version in the MCP command rather than executing an unversioned package or `@latest`. Do not install it globally. Treat the first `npx` execution as third-party code execution and preserve the client's normal command approval.

Use one active Atlassian entry per configuration scope. Do not leave native and bridged entries enabled together: they can expose duplicate tools, use different OAuth caches, and make the active identity or mutation result ambiguous.

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
codex mcp add atlassian --url https://mcp.atlassian.com/v2/mcp
codex mcp login atlassian
```

If the user selects the `mcp-remote` bridge instead, substitute the exact version verified for the task:

```text
node --version
npm --version
npm view mcp-remote version repository.url --json
codex mcp add atlassian -- npx -y mcp-remote@<verified-version> https://mcp.atlassian.com/v2/mcp
```

Do not run `codex mcp login` for the bridged entry. Start or reconnect the MCP server and let `mcp-remote` initiate its OAuth browser flow. Its OAuth state belongs to the bridge and must not be assumed to match Codex's native OAuth state.

OAuth opens a browser for the user to sign in and consent. Do not choose an account/site automatically when multiple options exist. Do not put an access token in a command, configuration, or chat.

Recommended safe configuration in `~/.codex/config.toml` or the project configuration selected by the user:

```toml
[mcp_servers.atlassian]
url = "https://mcp.atlassian.com/v2/mcp"
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

## Switch transports safely

Switch only when the user selects the destination transport. A working connection is not permission to rewrite its configuration.

1. Inspect `codex mcp get <server-name> --json` and confirm the entry is the intended Atlassian server and configuration scope. Record non-secret approval settings, environment-variable names, and custom timeouts; never print or copy secret values.
2. Resolve the destination configuration completely before removing the current entry. For `mcp-remote`, verify and pin the selected package version. For native HTTP, use the exact current Atlassian endpoint.
3. Remove and re-add the same server name with `codex mcp remove <server-name>` followed by exactly one destination form:

   ```text
   # bridge -> native
   codex mcp add <server-name> --url https://mcp.atlassian.com/v2/mcp
   codex mcp login <server-name>

   # native -> bridge
   codex mcp add <server-name> -- npx -y mcp-remote@<verified-version> https://mcp.atlassian.com/v2/mcp
   ```

4. Reapply only recorded non-secret settings supported by the destination transport. Do not migrate OAuth cache files or tokens between native Codex and `mcp-remote`; authenticate the destination independently.
5. Verify `codex mcp get <server-name> --json`, restart or reconnect the client when required, and make exactly one minimal read-only identity/resources call. Confirm the expected Atlassian account and site before declaring the switch complete.

If removal would discard settings that cannot be reconstructed, or the destination cannot be authenticated and verified, stop and provide the exact recovery step. Do not create a second enabled Atlassian entry as a fallback. An uncertain write made before or during a switch must be resolved by reading its target; never retry it through the other transport.

## Migrate an existing v1 connection to v2

Atlassian released v2 with more tools and supported products. On **1 Mar 2027**, existing v1 connections begin exposing and using v2 tools automatically; migrate deliberately before then when the user requests the upgrade. The v1 endpoints are `https://mcp.atlassian.com/v1/mcp` and `https://mcp.atlassian.com/v1/mcp/authv2` — the `authv2` suffix does not mean the connection uses Rovo MCP v2.

Before changing anything, inspect the current Codex CLI and server entry:

```text
codex --version
codex mcp --help
codex mcp list --json
codex mcp get atlassian
```

Use the actual server name if it is not `atlassian`. Preserve unrelated configuration and custom timeout values. Migrate only the entry whose URL exactly matches a v1 endpoint:

1. Record the server name, URL, authentication mode, approval settings, headers or token environment-variable references, and custom startup/tool timeouts. Do not print credential values.
2. For an OAuth entry, remove and re-add that exact server using the current CLI syntax and `https://mcp.atlassian.com/v2/mcp` (or `?tools=all` only when a flat tool list is required). Reapply settings that `codex mcp add` does not preserve.
3. Run `codex mcp login <server-name>` and complete browser sign-in. v2 is a separate OAuth resource, so v1 OAuth credentials do not carry over.
4. For a Basic API-token or service-account Bearer-token entry, v2 supports token authentication, but do not expose, copy, or rewrite the secret automatically. Preserve the existing secret reference and follow the current official API-token configuration when repointing the URL. Confirm the intended `cloudId`, because token credentials are not bound to one site and may expose fewer tools than OAuth.
5. If authentication fails because the client retained a v1 OAuth registration, log out that server and retry login. Clear cached `clientId` or `.well-known` registration state only after observing a compatible failure and identifying the client-owned cache precisely.
6. Verify with `codex mcp list`, `codex mcp get <server-name>`, a new session or `/mcp` when needed, then exactly one minimal read-only identity/resources call. Report success only after the live v2 check passes.

Do not silently migrate another client, another user's configuration, or an entry with a non-v1 URL. If removal and re-addition would discard settings that cannot be reconstructed safely, stop and present the exact manual edit required instead.

## Authenticate and identify the target

- Prefer OAuth 2.1 for interactive sessions. Personal API tokens and service-account API keys are for non-interactive/M2M use and may be used only when the organization permits them and the user requests them; their tool set may be smaller, and their credentials are not bound to one `cloudId`.
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

## Upload and attach files

Treat `uploadAttachmentToJiraIssue` as a deferred capability: call live `discover` for that exact name in the current authenticated session even when it is absent from the initial tool list. A documentation snapshot or result from another session proves neither presence nor absence. If the discovered MCP route cannot complete under the current execution or user-imposed secret constraints, treat it as unusable and evaluate a permitted documented REST route; do not keep repeating discovery.

### Preflight

1. Verify the MCP account, site, issue key/ID, issue access, and current attachment list.
2. Verify that the explicit path is a regular file. Resolve its basename, byte count, and MIME type without reading unnecessary content; identify an existing same-name attachment so the user does not create an accidental duplicate.
3. Bind the authorized outcome before uploading: either one standalone attachment or one inline media reference in a specific comment/description. These outcomes are mutually exclusive.
4. Confirm that the execution environment can consume the MCP-issued upload authorization within the user's visibility constraints. The MCP response itself contains the token-bearing command. Passing it to a shell tool also places it in that tool's input, even if the app later redacts the history. If the user forbids this and no protected executor exists, do not mint the token; inspect a permitted documented route, such as Jira Platform REST with independently verified Basic credentials. A task-specific upload request alone does not waive a tool-input visibility limit. If the user explicitly authorizes the tool-input exception for this upload, use the bounded procedure below. If every other route is forbidden or unavailable, explain the concrete blocker.

### Phase 1 — upload bytes to Atlassian Media

1. Invoke `uploadAttachmentToJiraIssue` once with only `issueIdOrKey` and `filePath`, matching the live schema. It returns a short-lived Atlassian Media upload command plus `collection`, `fileName`, and instructions for extracting `fileId`.
2. Treat the returned command and Bearer token as secrets. Do not print, echo, log, persist in a tracker/artifact/fixture, enable shell tracing or verbose HTTP, or write them to a temporary file. Prefer protected process memory. Do not copy authorization from another task/session; mint it for each upload.
3. When the user explicitly permits the command in tool input, keep the raw MCP result in session-local memory (for example, inside `functions.exec`); emit only sanitized fields. Before passing its `uploadCommand` to a shell tool, validate the exact HTTPS `api.media.atlassian.com` upload URL, collection, requested basename and local file path; reject unexpected commands or shell separators. Disable cross-host redirects (remove `--location` and set `--max-redirs 0` when using the returned `curl` command). Pass it directly to the execution tool without copying it into a chat message, record, file, or printed tool output. This exception exposes the command to the execution tool's input; never describe it as hidden from that tool. The Media Bearer token is not `JIRA_ACCESS_TOKEN` and must never be replaced by it.
4. Require a successful process/HTTP result and parse the documented Media JSON response. Match its `name` and `size` to the selected file before extracting the media `id` as `fileId`; a shell exit alone is insufficient. On failure or an ambiguous result, read back the issue attachments before any further write. If the Media upload alone failed, diagnose it against current Atlassian documentation and retry only with a newly minted authorization and a verified corrected request; never replay an old token-bearing command. If the attach outcome is uncertain, follow the reconciliation rule below.

### Phase 2 — choose exactly one completion path

**Standalone attachment:** invoke `uploadAttachmentToJiraIssue` once with `issueIdOrKey` and the returned `fileId`. Do not also embed that media inline. Re-read issue attachments and match attachment ID, filename, byte count, and MIME type before reporting success. When exact content verification is requested, use a separately permitted attachment-content read, compare downloaded byte count and SHA-256 with the source, and keep signed download URLs and authorization out of output. Preserve existing attachments unless their removal was separately authorized.

**Inline comment or description:** do not invoke standalone phase 2. Pass the returned `fileId`, `collection`, and `fileName` to the exact live comment/description capability fields, such as `inlineFileId`, `inlineFileCollection`, and `inlineFileName`. Inline embedding creates the Jira attachment. Re-read the comment/description for its media reference and the issue attachment list for the corresponding filename, byte count, and MIME type. Report success only when both match.

If an upload, attach, or embed result is uncertain, read back the exact issue attachment list and inline target where applicable. If the intended file is present, verify its ID, name, byte count, MIME type, and content when requested; do not upload again. If read-back cannot establish whether the write happened, stop further mutations and report the uncertainty. If read-back establishes that no matching attachment exists, diagnose the failure using the current official documentation, then continue with a corrected MCP attempt or a permitted official REST route under its credential workflow. The original task authorization covers further attempts only for the same issue, file bytes, filename, and standalone/inline outcome, subject to any explicit user attempt or route limit. Mint a fresh Media authorization for each new MCP attempt. Never use ACLI or browser automation without the authorization required by `SKILL.md`.

## Probe and route an unsupported capability

- If MCP is unconfigured, unavailable, disconnected, unauthenticated, or blocked by policy, tell the user which condition was observed. Continue to REST when existing credentials independently identify the intended site and the registered or dynamic capability contract's target and authorization requirements are satisfied; otherwise ask whether they want to use ACLI. Do not inspect or invoke ACLI before they approve.
- Resolve the exact requested capability first, then inspect the live server tool list and candidate schemas. A published supported-tools snapshot is discovery evidence only; it neither proves a runtime tool is loaded nor proves absence. For attachment uploads, always run live `discover` for `uploadAttachmentToJiraIssue` before selecting a fallback.
- If MCP is connected and authenticated but lacks the exact capability or cannot complete an upload under the current execution constraints, prefer one exact capability ID in `rest-capability-registry.json`. If none matches, route to `rest-api-workflows.md` and derive a dynamic capability contract from the exact current official endpoint page. Independently verify the REST API-token account/site and use only the Basic-auth workflow defined there; respect any user prohibition on REST.
- If no exact official Jira Cloud endpoint or complete dynamic contract can be established, explain the limitation and ask whether the user wants ACLI. Neighboring endpoints and undocumented method/path pairs are not alternatives.
- Treat approval as scoped to the current Jira task. Do not make ACLI the default for later tasks.
- After approval, follow `references/command-workflows.md`, verify the ACLI site/account/target, and repeat any mutation preview when the execution tool or impact changes.

## Troubleshoot

- Server is absent: check configuration scope, `codex mcp list`, client restart/new session, and `/mcp`; confirm the URL is the v2 endpoint rather than a retired v1 endpoint.
- `enabled` but tools cannot be called: run a live read-only check; inspect OAuth, token expiration, organization permissions, domain/IP allowlists, and network access.
- OAuth does not open or the callback fails: retry login after checking browser/callback behavior and the domain allowlist; do not automatically switch to a token.
- `mcp-remote` does not start or authenticate: verify Node/npm availability, the pinned package identity/version, local callback-port availability, client process logs with secrets redacted, and Atlassian's OAuth/domain policy. Do not silently fall back to an unpinned version or copy native OAuth state into the bridge.
- `Access denied`: verify the user's Jira permissions and Read/Write/Search groups in Atlassian Administration.
- Expected tool is absent: recheck the live tool list/schema, then use a registered capability or derive an exact dynamic REST contract from current official documentation.
- Multiple sites or incorrect `cloudId`: repeat resource discovery and ask the user to select the target.
