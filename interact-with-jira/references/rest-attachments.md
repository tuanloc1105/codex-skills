# Jira attachment REST workflows

Common capability contracts, Basic authentication, risk tiers, and error handling are in [REST API workflow](rest-api-workflows.md). Use these REST workflows only after live MCP discovery lacks the exact capability or MCP is unavailable. Jira comment endpoints are not binary-upload endpoints; an inline comment can reference only media that was uploaded first.

## Upload an attachment

The Jira Platform create-attachments endpoint is a dynamic Tier B capability unless it is later added to the verified registry. Derive its exact current method, path, success status, multipart shape, scopes, permissions, and verification from the official attachment endpoint page before use.

1. Verify the API-token account/site, explicit issue key/ID, issue access, and authorization for the exact file. Re-read current attachments to identify an unintended duplicate filename.
2. Require an explicit regular-file path. Resolve a safe basename, byte count, and MIME type; enforce a task-appropriate size bound before sending.
3. Use `JIRA_ACCESS_TOKEN` only with the configured account email through HTTP Basic, constructed inside the protected HTTP helper. Never use it as a Bearer token. Keep authorization, multipart bytes, and response bodies out of logs; disable verbose HTTP and automatic cross-host redirects.
4. Send the file once to the exact official Jira Platform attachment endpoint and require its documented success status and response shape. Do not use the comment REST API for the binary upload.
5. Re-read the issue attachments and match returned attachment ID, filename, byte count, and MIME type. Report success only after the read-back matches.

If the upload returns `503` or any uncertain result, perform only the attachment-list read-back, report whether a matching attachment exists, and stop. Do not retry, change routes, or change credentials automatically. A further attempt requires fresh authorization even when read-back proves no attachment was created.

REST comment/description APIs may reference already-uploaded media only when the current official contract documents that representation. They do not replace the upload step. Do not create a standalone attachment and then repeat an inline path that would create a duplicate.

## Download an attachment

1. Resolve the attachment ID from explicit context and re-read issue association when needed.
2. Fetch metadata first; validate ID, association, size, media type, and filename.
3. Require an explicit destination. Sanitize to a basename, discard directory/control characters, reject empty/`.`/`..`, resolve inside destination, reject symlink/path escape, and refuse existing targets.
4. Apply the task size limit before download; stop if absent/unexpectedly large without a policy.
5. Stream to a new temporary file on the destination filesystem; never buffer the body.
6. Handle redirects manually. Permit only HTTPS documented Atlassian delivery hosts or verified `*.atlassian.net`/`api.atlassian.com`. Never forward authorization cross-host; stop on downgrade, untrusted host, loop, or ambiguity.
7. Require success and compare bytes with metadata size and trustworthy `Content-Length`. Partial/range responses are incomplete unless explicitly implemented and verified.
8. Atomically rename to the unused final path. On failure remove only this attempt's temporary file. Report final path/bytes without content or signed URLs.
