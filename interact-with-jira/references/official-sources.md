# Official sources and freshness policy

ACLI sources were checked on 2026-08-03; Rovo MCP and Jira REST sources were checked on 2026-08-29. Recheck the relevant interface when using this skill.

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

1. [Issues](https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-issues/), [changelogs](https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-issues/#api-rest-api-3-issue-issueidorkey-changelog-get), and [transitions](https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-issues/#api-rest-api-3-issue-issueidorkey-transitions-get): issue detail/edit metadata/edit and transition routes, scopes, statuses, fields, and pagination.
2. [Comments](https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-issue-comments/), [worklogs](https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-issue-worklogs/), [watchers](https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-issue-watchers/), and [links](https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-issue-links/): bounded reads and selected Tier B writes.
3. [Issue attachments](https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-issue-attachments/): metadata, content, redirects, ranges, permissions, and scopes.
4. [Project versions](https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-project-versions/) and [versions](https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-project-versions/): release/version reads.
5. [Jira Software boards](https://developer.atlassian.com/cloud/jira/software/rest/api-group-board/) and [sprints](https://developer.atlassian.com/cloud/jira/software/rest/api-group-sprint/): board/backlog/sprint/version reads, pagination, and enhanced endpoint families.
6. [OAuth 2.0 (3LO)](https://developer.atlassian.com/cloud/jira/platform/oauth-2-3lo-apps/) and [API-token basic auth](https://developer.atlassian.com/cloud/jira/platform/basic-auth-for-rest-apis/): resource correlation, scopes, lifecycle, and account/site binding.

The runtime MCP schema decides whether MCP has a capability. Official REST pages decide endpoint behavior; `rest-capability-registry.json` is the closed authorization boundary.

## Freshness rules

- Read the changelog when the version differs from the previous use, authentication suddenly lacks a scope, or a command/flag conflicts with this skill.
- Prefer pages under `developer.atlassian.com/cloud/acli/`; do not use blogs, gists, forums, or third-party Jira CLI documentation as syntax sources.
- Some command-reference pages may show an older update date than the binary. When syntax conflicts, use the binary's `--help` and record the discrepancy.
- Do not hard-code “latest version” in automation. Atlassian requires frequent updates, and the changelog may introduce new OAuth requirements.
- For MCP, the tool schema/list exposed by the current server determines executable inputs. The Supported tools page verifies capability and scope but does not replace the runtime schema.
- Use the Streamable HTTP endpoint currently published by Getting started. Do not revert to the retired SSE endpoint.
- Recheck an exact REST endpoint when status, redirects, authentication, scopes, or schema differ. Never expand the registry because another official endpoint exists.
- Correlate OAuth accessible resources/cloud ID or the API-token account/site with the intended MCP target.

## Distinguish TWG CLI

Atlassian also publishes TWG CLI `twg`, which has its own command tree and agent skill. Do not mix `twg jira ...` with `acli jira ...`. If the user wants TWG CLI, use the [TWG CLI documentation](https://developer.atlassian.com/cloud/twg-cli/) and the official skill provided by the TWG installer instead of applying this skill.
