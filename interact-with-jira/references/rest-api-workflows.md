# Jira Cloud REST API fallback workflow

Use this workflow only when the current Atlassian Rovo MCP schema lacks a capability in the closed allowlist in `../SKILL.md`, or MCP is unavailable but the explicit target and Jira site can be independently verified. REST selection is automatic for an allowlisted capability; mutation authorization and credential changes are not.

## Closed endpoint allowlist

- `GET /rest/api/3/attachment/{id}` for metadata required by an explicit download.
- `GET /rest/api/3/attachment/content/{id}` for that attachment's bytes.
- `POST /rest/api/3/issue/{issueIdOrKey}/comment` for one authorized comment on exactly one explicitly identified issue.

Path variables may contain only the resolved attachment ID or issue key/ID. Do not use unlisted methods or endpoints, derive bulk routes, or treat neighboring documentation as permission.

## Discover credentials and correlate the site

1. Discover only existing credentials without printing their paths, values, decoded claims, or headers.
2. Prefer an existing OAuth 2.0 bearer credential. Correlate its official accessible-resources Jira URL/cloud ID with the MCP target, and use `https://api.atlassian.com/ex/jira/{cloudId}`.
3. Otherwise use an existing API token only with its configured account and `https://<site>.atlassian.net`. Supply authorization from a secret source at request time, never a command argument or committed file.
4. Stop if credentials are absent, expired, require new consent, map to multiple sites, or cannot be correlated. Do not create an app, start consent, replace a token, switch accounts, or persist credentials automatically.
5. REST credential failure must not affect MCP or silently route to ACLI, browser automation, or another endpoint.

Use a client that accepts headers separately, disables automatic cross-host redirects, streams bodies, and exposes status and byte counts. Never log authorization headers, cookies, response bodies, signed URLs, or unnece ssary identity fields.

## Download one explicit attachment

1. Resolve the attachment ID from the explicit issue/context. Re-read the issue when needed to verify association and visibility.
2. Fetch metadata first with `GET /rest/api/3/attachment/{id}`. Require success; validate ID, issue association when observable, declared size, media type, and filename.
3. Require an explicit destination. Sanitize the server filename to a basename: discard directory components/control characters, reject `.`/`..` and empty names, resolve inside the destination, reject symlink/path escape, and refuse an existing target. Never overwrite implicitly.
4. Apply the task's size policy before download. If no limit exists and size is absent or unexpectedly large, stop for a decision.
5. Stream `GET /rest/api/3/attachment/content/{id}` to a new temporary file in the destination filesystem; do not buffer the body.
6. Handle redirects manually. Permit only HTTPS hosts documented for Atlassian attachment delivery or the verified `*.atlassian.net`/`api.atlassian.com` boundary. Never forward authorization cross-host. Stop on downgrade, untrusted host, loop, or ambiguity; never report the signed URL.
7. Require success and compare written bytes with metadata size and trustworthy `Content-Length`. Treat partial/range responses as incomplete unless explicitly implemented and verified.
8. Atomically move the completed temporary file to the new final path. On failure, remove only this attempt's temporary file. Report verified site, attachment, final path, byte count, and limitations without exposing content.

## Add one explicitly authorized comment

1. Require the request or authoritative workflow to identify exactly one issue key/ID and authorize the bounded comment/evidence. Never infer it from a branch, recent activity, JQL/search, another issue, or conversational proximity. Multiple targets and every other REST write are outside the allowlist.
2. Re-read that issue and verify its key/ID and site. Stop if target, site, payload, or visibility is ambiguous.
3. Build bounded Atlassian Document Format from only authorized content. Preserve explicit visibility; do not invent, remove, or broaden it.
4. Send `POST /rest/api/3/issue/{issueIdOrKey}/comment` exactly once. Require HTTP `201` and retain only minimal verification data.
5. Re-read and locate the created comment by returned ID or a bounded exact marker. Report success only after verification.
6. On timeout, disconnect, ambiguous response, or uncertain verification, never POST again or repeat through MCP/ACLI. Re-read state once safely, report uncertainty, and request a decision.

## Fail and report safely

- For `401`, `403`, missing scopes, or reauthorization, report the prerequisite and stop.
- For `404`, verify site and explicit target; do not search broadly for a replacement.
- For `409`, `429`, or `5xx`, follow retry guidance for reads only. Never automatically retry a comment POST.
- Report that REST fallback was used, the verified site/target, allowlisted capability, result, verification, and limitations. Redact tokens, unnecessary identity data, private URLs, attachment contents, and unnecessary comment content.
