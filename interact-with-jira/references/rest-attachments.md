# Jira attachment REST workflow

This preserves file safety for `attachment.metadata` and `attachment.content`; common mechanics are in [REST API workflow](rest-api-workflows.md).

1. Resolve the attachment ID from explicit context and re-read issue association when needed.
2. Fetch metadata first; validate ID, association, size, media type, and filename.
3. Require an explicit destination. Sanitize to a basename, discard directory/control characters, reject empty/`.`/`..`, resolve inside destination, reject symlink/path escape, and refuse existing targets.
4. Apply the task size limit before download; stop if absent/unexpectedly large without a policy.
5. Stream to a new temporary file on the destination filesystem; never buffer the body.
6. Handle redirects manually. Permit only HTTPS documented Atlassian delivery hosts or verified `*.atlassian.net`/`api.atlassian.com`. Never forward authorization cross-host; stop on downgrade, untrusted host, loop, or ambiguity.
7. Require success and compare bytes with metadata size and trustworthy `Content-Length`. Partial/range responses are incomplete unless explicitly implemented and verified.
8. Atomically rename to the unused final path. On failure remove only this attempt's temporary file. Report final path/bytes without content or signed URLs.
