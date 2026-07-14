# Security Review Checklist

Use this checklist as attack-oriented prompts. Do not mark a category safe only because a keyword is absent; inspect call paths, framework defaults, middleware order, and reachable sinks.

## OWASP Top 10 Scan

### Authentication Bypass

- Check login, registration, password reset, magic link, SSO/OAuth/OIDC, MFA, session refresh, logout, API keys, service tokens, and webhook authentication.
- Look for missing authentication middleware, route groups that bypass guards, insecure fallback auth, trust in client-provided user IDs/roles, unsigned or weakly signed tokens, JWT `alg=none`/key confusion, stale sessions, and weak reset-token lifecycle.
- Validate session fixation, remember-me cookies, token rotation, revocation, expiration, device/session invalidation, and MFA bypass through alternate flows.
- Attack question: Can a user become another user, create a valid session, reuse an expired token, bypass MFA, or call a protected endpoint without the intended guard?

### Broken Access Control

- Check object-level authorization, function-level authorization, tenant isolation, admin-only actions, direct object references, file access, exports, background jobs, and GraphQL/resolver permissions.
- Look for authorization checks only in the UI, predictable IDs, missing ownership checks, confused deputy flows, mass assignment of role/owner fields, overbroad service permissions, and middleware gaps on nested routes.
- Verify authorization is enforced server-side at the data/action boundary, not only at route entry.
- Attack question: Can a low-privilege or cross-tenant user read, modify, delete, approve, export, or trigger work for data they do not own?

### Injection: SQL, NoSQL, Command

- Check query builders, raw SQL, ORM escape hatches, dynamic filters/sorts, search endpoints, aggregation pipelines, shell/process execution, template engines, LDAP/XML/XPath queries, and deserialization.
- Look for string concatenation in queries/commands, unvalidated operators, JSON query injection, `$where`/regex abuse, shell metacharacters, unsafe path interpolation, and dynamic code execution.
- Prefer allowlists, parameterized queries, structured query APIs, argument arrays for process calls, and strict schema validation.
- Attack question: Can attacker-controlled input alter the query, command, interpreter, or template semantics?

### XSS

- Check server-rendered HTML, client rendering, markdown/HTML sanitization, rich-text editors, error messages, URLs, templates, localization strings, file previews, SVG uploads, and DOM sinks.
- Look for `innerHTML`, unsafe template interpolation, bypassable sanitizers, untrusted HTML attributes/URLs, weak CSP, stored user content rendered to privileged users, and framework escape hatches.
- Validate context-aware output encoding for HTML, attributes, JavaScript, CSS, and URLs.
- Attack question: Can attacker-controlled content execute script in another user's browser or steal tokens/actions?

### CSRF

- Check cookie-authenticated state-changing routes, admin actions, payment/account changes, logout, password/email changes, and legacy form endpoints.
- Look for missing CSRF tokens, unsafe `GET` state changes, lax SameSite assumptions, CORS misconfigurations with credentials, and JSON endpoints reachable by simple requests.
- Validate token binding, SameSite cookie settings, origin/referer checks where appropriate, and idempotency for dangerous actions.
- Attack question: Can another site force a victim's browser to perform a meaningful authenticated action?

### SSRF

- Check URL fetchers, webhooks, importers, link previews, PDF/image processors, proxy endpoints, metadata fetchers, integrations, and cloud storage callbacks.
- Look for user-controlled URLs, redirects, DNS rebinding, internal IP/range access, cloud metadata access, custom protocols, IPv6/decimal/octal IP bypasses, and weak allowlists.
- Validate egress controls, protocol allowlists, DNS/IP pinning, redirect handling, response size/time limits, and network segmentation.
- Attack question: Can input make the server reach internal services, cloud metadata, privileged APIs, or attacker-controlled endpoints with sensitive credentials?

### Security Misconfiguration

- Check environment config, debug flags, error pages, CORS, security headers, cookie flags, TLS settings, default credentials, admin consoles, bucket/storage ACLs, container/Kubernetes/IAM config, and CI/CD secrets exposure.
- Look for permissive CORS, verbose stack traces, public debug endpoints, missing `HttpOnly`/`Secure`/`SameSite`, disabled certificate validation, public storage buckets, overly permissive IAM, and unsafe default deployments.
- Attack question: Does configuration expose internals, weaken browser protections, broaden network access, or grant more privilege than the code expects?

### Sensitive Data Exposure

- Check logs, errors, analytics, caches, URLs, query strings, API responses, exports, backups, local storage, cookies, telemetry, traces, and test fixtures.
- Look for secrets, tokens, passwords, PII, financial data, session IDs, encryption keys, internal URLs, and excessive object serialization.
- Validate minimization, masking, redaction, retention, encryption in transit/at rest, secure cookie storage, and safe debug/test data handling.
- Attack question: Can an attacker obtain sensitive data through responses, logs, artifacts, storage, or accidental overexposure?

### Dependency Vulnerabilities

- Check package manifests, lockfiles, vendored code, container base images, GitHub Actions, plugins, transitive dependencies, and runtime versions.
- Look for known vulnerable packages, typosquatting, unpinned versions, deprecated libraries, unsafe postinstall scripts, vulnerable base images, and abandoned auth/crypto/security middleware.
- Validate with the ecosystem's audit tools when possible, but manually assess reachability and exploitability.
- Attack question: Is a vulnerable dependency reachable in the deployed path with attacker-controlled input or privileged context?

## Additional Attacker-Focused Reviews

### Business Logic Abuse and Insecure Design

- Check workflows with money, credits, coupons, refunds, subscriptions, approvals, invitations, role changes, quotas, inventory, order state, and account recovery.
- Look for state-machine bypass, valid actions used in invalid order, missing state transition checks, client-trusted prices/roles/limits/entitlements, replayable actions, duplicate actions, one-time operations that are not atomic, and approval flows with confused actors.
- Validate server-side invariants for every state transition and side effect.
- Attack question: Can an attacker use legitimate endpoints to get an outcome the business rules should forbid?

### IDOR and BOLA

- Treat IDOR/BOLA as a first-class finding even when it also fits broken access control.
- Check route params, GraphQL IDs, object IDs in JSON bodies, tenant IDs, organization IDs, filenames, export IDs, invitation IDs, and background job IDs.
- Look for predictable identifiers, missing object ownership checks, scoped UI queries paired with unscoped mutation handlers, and authorization performed before object resolution.
- Attack question: Can changing an identifier read, modify, export, delete, or trigger work for another user or tenant?

### File Handling and Path Traversal

- Check uploads, downloads, file previews, archives, image/PDF processing, import/export, temporary files, storage keys, and public object URLs.
- Look for MIME sniffing/spoofing, polyglot files, dangerous extensions, SVG/HTML execution, zip slip, decompression bombs, path traversal, symlink following/races, overwrite risks, public bucket ACLs, weak signed URL scope/lifetime, temp-file permission issues, and parser vulnerabilities.
- Validate canonical paths, extension/MIME allowlists, content scanning, size limits, random storage names, private-by-default storage, scoped short-lived signed URLs, safe temp directories, and safe preview rendering.
- Attack question: Can an attacker read/write arbitrary files, execute active content, poison stored files, or exhaust parsers/storage?

### Deserialization and Unsafe Parsing

- Check JSON/XML/YAML parsers, pickle/Marshal/Java serialization, JWT/custom token parsing, template parsing, webhook payloads, and message queues.
- Look for unsafe object deserialization, XXE, entity expansion, polymorphic type loading, dynamic class resolution, unsafe YAML loaders, and template injection.
- Validate safe parser modes, schema validation, disabled external entities, and signed/encrypted message formats where trust crosses boundaries.
- Attack question: Can attacker-controlled serialized data create objects, fetch files/network resources, execute code, or bypass validation?

### Race Conditions and TOCTOU

- Check double-submit paths, payment/refund, coupon redemption, balance transfer, inventory reservation, password reset, MFA, invitation acceptance, quota checks, and privilege changes.
- Look for check-then-act sequences outside transactions, non-idempotent retries, missing unique constraints, reused one-time tokens, stale authorization decisions, cache invalidation mistakes, eventual consistency gaps, and async job/webhook races.
- Validate transactional boundaries, idempotency keys, locking, unique constraints, compare-and-set updates, retry safety, cache consistency, and replay protection.
- Attack question: Can concurrent or replayed requests bypass a limit, spend twice, reuse a token, or create an impossible state?

### DoS and Resource Exhaustion

- Check upload sizes, request body limits, regex use, search/filter endpoints, pagination, exports, report generation, webhooks, queues, decompression, image/PDF parsing, and nested JSON/XML.
- Look for unbounded queries, N+1 amplification, catastrophic regex, infinite recursion, large fan-out jobs, decompression bombs, and expensive unauthenticated endpoints.
- Validate rate limits, timeouts, memory limits, pagination caps, async job quotas, circuit breakers, and cancellation.
- Attack question: Can cheap attacker input force expensive CPU, memory, database, network, storage, or queue work?

### Supply Chain and CI/CD

- Go beyond dependency CVEs: inspect package scripts, lockfile integrity, GitHub Actions, CI permissions, build artifacts, release workflows, package publishing, and third-party plugins.
- Look for dependency confusion, unpinned actions/images, broad `GITHUB_TOKEN` permissions, secrets exposed to pull requests, unsafe `pull_request_target`, mutable tags, postinstall script abuse, poisoned build steps, registry misconfiguration, maintainer/plugin compromise, and untrusted code in release jobs.
- Validate least-privilege CI tokens, pinned SHAs for high-risk actions, protected environments, lockfile integrity, package provenance/signing, SBOMs where expected, artifact integrity, and separated build/release credentials.
- Attack question: Can an attacker modify the build, steal CI secrets, publish a malicious artifact, or compromise consumers through the pipeline?

### Cloud, Container, and IaC

- Check Terraform/CloudFormation/Pulumi, Kubernetes manifests, Dockerfiles, compose files, Helm charts, cloud IAM, storage, databases, queues, security groups, and metadata access.
- Look for public buckets, open security groups, privileged containers, root containers, writable host mounts, `hostPath`/Docker socket exposure, overbroad IAM/trust policies, risky OIDC federation, exposed admin ports, default credentials, unsigned/unscanned images, and missing network policies.
- Validate private-by-default resources, minimal IAM actions/resources, non-root containers, read-only filesystems where feasible, safe secret mounts, image signing/scanning, egress restrictions, and metadata service protections.
- Attack question: Can a compromised app, container, or CI job laterally move, reach private services, or obtain cloud credentials?

### Session, Token, and Cookie Hardening

- Check access/refresh tokens, JWT claims, `kid`/JWKS cache behavior, cookie flags, cookie prefix/domain/path settings, session storage, logout, API keys, token rotation, audience/issuer validation, clock skew, and cross-device sessions.
- Look for long-lived bearer tokens, missing revocation, refresh token reuse, weak signing keys, missing `aud`/`iss` checks, `kid` confusion, client-side token storage, unhashed API keys, repeatedly visible API secrets, overbroad API key scopes, and cookies missing `HttpOnly`, `Secure`, or appropriate `SameSite`.
- Validate rotation, replay detection, device/session invalidation, scoped claims, short lifetimes, API key hashing/one-time display/scopes, and server-side revocation for high-risk actions.
- Attack question: Can a stolen, stale, replayed, or confused token remain useful longer or wider than intended?

### API-Specific Security

- Check REST, GraphQL, RPC, webhooks, mobile APIs, internal APIs exposed externally, versioned endpoints, batch endpoints, and admin APIs.
- Look for BOLA, broken function-level authorization, mass assignment, excessive data exposure, unrestricted resource consumption, unsafe filters/sorts/includes, pagination scraping, GraphQL depth/complexity abuse, introspection leaks, batch endpoint bypasses, webhook replay/freshness gaps, cost/compute abuse, and inconsistent auth across API versions.
- Validate schema-level allowlists, per-field authorization, response shaping, mutation authorization, GraphQL depth/complexity limits, webhook signatures, replay windows, pagination/export caps, and consistent middleware across versions.
- Attack question: Can API flexibility expose fields, functions, objects, or resource usage the UI would never allow?

### Security Monitoring and Incident Readiness

- Check whether security events are logged, alertable, retained, correlated, and usable for investigation.
- Look for missing audit trails for admin actions, exports, auth failures, access denials, key/token lifecycle, permission changes, and suspicious high-volume actions.
- Validate actor, target, tenant, request ID, source IP/device, outcome, and before/after values where appropriate.
- Attack question: If this exploit happened today, would the team detect it and reconstruct what happened?

### AI and LLM Security

- Apply this section when the codebase uses prompts, agents, tools/function calling, retrieval, embeddings, model gateways, AI-generated code/actions, or user-provided documents.
- Look for direct/indirect prompt injection, RAG poisoning, vector-store tenant isolation failures, tool permission abuse, retrieval data exfiltration, cross-tenant context leakage, unsafe tool arguments, hidden instruction trust, model output used as authorization/code/SQL/commands, prompt/secret leakage, AI cost DoS, and unreviewed autonomous actions.
- Validate strict tool allowlists, tool-call authorization, human approval for high-risk actions, tenant-scoped retrieval, output validation, prompt/data separation, secret redaction, budget/rate controls, and audit logs for model/tool actions.
- Attack question: Can untrusted content steer the model or its tools to leak data, change state, bypass policy, or execute unintended actions?

## Hardening Review

### Input Validation

- Validate at trust boundaries using schemas or typed validators.
- Prefer allowlists over denylists for enums, IDs, filenames, URLs, MIME types, sort keys, and operators.
- Check canonicalization before validation for paths, URLs, encodings, Unicode, and IPs.
- Reject unexpected fields to reduce mass assignment and query/operator injection.

### Output Encoding

- Encode for the exact output context: HTML body, HTML attribute, JavaScript string, CSS, URL, shell, SQL, JSON, CSV, and logs.
- Avoid passing raw user content into framework escape hatches.
- Sanitize rich HTML with a maintained sanitizer and strict allowlist.

### Rate Limiting

- Check login, signup, password reset, OTP/MFA, token refresh, email/SMS sends, search, exports, expensive jobs, upload, webhook ingestion, and public APIs.
- Key limits by user, IP, tenant, credential, endpoint, and action where appropriate.
- Validate lockout/backoff behavior, abuse monitoring, and bypasses through alternate endpoints or distributed identifiers.

### Secret Management

- Ensure secrets are not committed, logged, exposed to clients, embedded in images, or printed in CI.
- Check rotation, scoping, environment separation, vault/KMS usage, and safe local defaults.
- Validate that build-time variables intended for servers are not bundled into frontend code.

### Encryption

- Use modern TLS and certificate validation for transport.
- Use authenticated encryption or well-reviewed libraries for stored secrets and sensitive fields.
- Avoid custom crypto, hardcoded keys, static IVs/nonces, weak hashing, and reversible storage of passwords.
- Store passwords with adaptive password hashing such as Argon2id, bcrypt, or scrypt.

### Logging and Audit Trail

- Log security-relevant events: auth success/failure, privilege changes, access denials, admin actions, token/key lifecycle, data exports, high-risk API calls, and abuse throttling.
- Redact secrets and sensitive data.
- Include actor, target, tenant, source, request ID, and outcome when useful.
- Ensure logs are tamper-resistant enough for incident response.

### Least Privilege

- Check database users, cloud IAM, service accounts, filesystem permissions, container capabilities, CI tokens, API scopes, and admin roles.
- Prefer narrowly scoped credentials and separate read/write/admin permissions.
- Validate that background jobs and internal services cannot perform user-facing privileged actions without explicit authorization context.

### Network Segmentation

- Check inbound exposure, egress rules, service-to-service access, metadata service access, admin panels, databases, caches, queues, and observability endpoints.
- Restrict SSRF blast radius with egress controls and metadata protections.
- Ensure private services are not reachable from public networks or untrusted workloads.

## Finding Validation Template

For every candidate finding, answer:

- Source: What attacker-controlled input or identity reaches the code?
- Boundary: Which auth, tenant, network, or validation boundary should stop it?
- Sink: What sensitive operation, interpreter, renderer, query, command, file, network call, or data exposure occurs?
- Reachability: What route, role, config, or dependency path makes it exploitable?
- Impact: What can the attacker read, change, execute, or disrupt?
- Evidence: What code lines, tests, traces, or commands support the finding?
- Fix: What minimal change removes the exploit path without relying on client-side controls?
