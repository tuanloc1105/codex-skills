# Official sources and freshness policy

ACLI and Rovo MCP sources were checked on 2026-08-03; Jira REST sources were checked on 2026-08-29. Recheck the relevant interface when using this skill.

## Source precedence

1. `acli --version` and `acli ... --help` from the running binary: the authoritative source for executable syntax in the current environment.
2. [ACLI changelog](https://developer.atlassian.com/cloud/acli/changelog/): official source for releases, breaking changes, and reauthorization requirements.
3. [Jira command reference](https://developer.atlassian.com/cloud/acli/reference/commands/jira/): the Jira Cloud command tree and links to leaf commands.
4. [Install ACLI](https://developer.atlassian.com/cloud/acli/guides/install-acli/) and [update ACLI](https://developer.atlassian.com/cloud/acli/guides/update-install-guide/): supported platforms and update procedures.
5. [Jira auth login](https://developer.atlassian.com/cloud/acli/reference/commands/jira-auth-login/): OAuth and API tokens through standard input.
6. [Troubleshooting](https://developer.atlassian.com/cloud/acli/guides/troubleshooting-guide/): help paths and common errors.
7. [ACLI in CI](https://developer.atlassian.com/cloud/acli/guides/use-acli-on-ci/): bot accounts, secret variables, and tokens through stdin.
8. [Command chaining and output](https://developer.atlassian.com/cloud/acli/guides/manage-command-chaining-and-output-redirection/): JSON, pipes, and redirection.

## Atlassian Rovo MCP

1. [Getting started](https://support.atlassian.com/atlassian-rovo-mcp-server/docs/getting-started-with-the-atlassian-remote-mcp-server/): current endpoint, Codex setup, and OAuth.
2. [Supported tools](https://support.atlassian.com/atlassian-rovo-mcp-server/docs/supported-tools/): currently exposed tools, permission groups, and scopes.
3. [Authentication and authorization](https://support.atlassian.com/atlassian-rovo-mcp-server/docs/authentication-and-authorization/): choosing OAuth 2.1 or an API token.
4. [Configuring OAuth 2.1](https://support.atlassian.com/atlassian-rovo-mcp-server/docs/configuring-oauth-2-1/): Streamable HTTP endpoint, consent, cloud ID, and authentication errors.
5. [Setting up clients](https://support.atlassian.com/atlassian-rovo-mcp-server/docs/setting-up-clients/): environment and client requirements.
6. [Permissions](https://support.atlassian.com/security-and-access-policies/docs/Configure-Atlassian-Rovo-MCP-server-permission/): Read, Write, and Search access controlled by organization administrators.
7. [Domain, authentication, and IP controls](https://support.atlassian.com/security-and-access-policies/docs/control-atlassian-rovo-mcp-server-settings/): domain allowlist, API-token policy, and IP allowlist.

## Jira Cloud REST API v3

1. [Get attachment metadata](https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-issue-attachments/#api-rest-api-3-attachment-id-get): endpoint, permissions, scopes, and response.
2. [Get attachment content](https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-issue-attachments/#api-rest-api-3-attachment-content-id-get): content, redirects, ranges, permissions, and scopes.
3. [Add comment](https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-issue-comments/#api-rest-api-3-issue-issueidorkey-comment-post): ADF, visibility, permissions, scopes, and `201`.
4. [OAuth 2.0 (3LO)](https://developer.atlassian.com/cloud/jira/platform/oauth-2-3lo-apps/): accessible resources, cloud ID, gateway URL, scopes, and token lifecycle.
5. [Basic auth with API tokens](https://developer.atlassian.com/cloud/jira/platform/basic-auth-for-rest-apis/): account/site-bound token authentication.

The runtime MCP schema decides whether MCP has a capability. Current official REST pages decide endpoint behavior, but the closed allowlist in `SKILL.md` remains the authorization boundary.

## Freshness rules

- Read the changelog when the version differs from the previous use, authentication suddenly lacks a scope, or a command/flag conflicts with this skill.
- Prefer pages under `developer.atlassian.com/cloud/acli/`; do not use blogs, gists, forums, or third-party Jira CLI documentation as syntax sources.
- Some command-reference pages may show an older update date than the binary. When syntax conflicts, use the binary's `--help` and record the discrepancy.
- Do not hard-code “latest version” in automation. Atlassian requires frequent updates, and the changelog may introduce new OAuth requirements.
- For MCP, the tool schema/list exposed by the current server determines executable inputs. The Supported tools page verifies capability and scope but does not replace the runtime schema.
- Use the Streamable HTTP endpoint currently published by Getting started. Do not revert to the retired SSE endpoint.
- Recheck an exact REST endpoint when status, redirects, authentication, scopes, or schema differ. Never expand the allowlist because another official endpoint exists.
- Correlate OAuth accessible resources/cloud ID or the API-token account/site with the intended MCP target.

## Distinguish TWG CLI

Atlassian also publishes TWG CLI `twg`, which has its own command tree and agent skill. Do not mix `twg jira ...` with `acli jira ...`. If the user wants TWG CLI, use the [TWG CLI documentation](https://developer.atlassian.com/cloud/twg-cli/) and the official skill provided by the TWG installer instead of applying this skill.
