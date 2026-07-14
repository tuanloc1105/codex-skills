---
name: security-review
description: Attacker-minded, multi-agent application security review for repositories, pull requests, diffs, APIs, backend/frontend code, infrastructure/config files, CI/CD, cloud/container/IaC, AI/LLM features, and dependency manifests. Use when Codex is asked to scan or review code for OWASP Top 10 risks, authentication bypass, broken access control, IDOR/BOLA, injection, XSS, CSRF, SSRF, security misconfiguration, sensitive data exposure, dependency vulnerabilities, business logic abuse, file handling/path traversal, deserialization, race conditions, DoS/resource exhaustion, supply chain issues, API security, session/token/cookie hardening, monitoring/incident readiness, or hardening topics such as input validation, output encoding, rate limiting, secret management, encryption, logging/audit trails, least privilege, and network segmentation.
---

# Security Review

## Operating Stance

Review like an attacker trying to prove a reachable exploit, then report like a defender who must fix it safely. Prefer evidence over pattern matching. Trace user-controlled input, identity, authorization context, secrets, network reachability, and data sinks from entry point to impact.

Always load `references/security-checklist.md` before performing a full security review. For a tiny targeted question, load only the relevant section.

## Workflow

1. Define scope.
   - Identify whether the target is a diff, pull request, commit, path, full repository, API, config set, dependency manifest, or specific finding.
   - Inspect routes, controllers, handlers, middleware, auth/session code, data access, external calls, config, and tests relevant to the scope.
   - Use semantic retrieval and narrow searches before broad file reads when working in a repository.

2. Build an attacker model.
   - List actors: unauthenticated user, authenticated low-privilege user, cross-tenant user, admin, service account, compromised dependency, internal network caller.
   - Map trust boundaries: browser to server, API gateway to service, service to database, service to cloud metadata/internal network, queue/webhook boundaries.
   - Identify assets: credentials, tokens, PII, tenant data, payment data, admin actions, internal endpoints, logs, backups, and signing/encryption keys.

3. Launch parallel reviewers for codebase reviews.
   - For any request to review a codebase, repository, full repository, pull request, branch diff, or multi-file security scope, do not perform the review as a single-agent pass.
   - Launch multiple sub-agents concurrently whenever sub-agent tools are available. This is mandatory for codebase/repository reviews, not an optional depth setting.
   - Launch at least four reviewers for a broad codebase review: `Access Control`, `Unsafe Sinks`, `Business Logic and API`, and `Platform and Supply Chain`. Add `Attack Surface`, `Abuse and Hardening`, and `AI/LLM` reviewers when the scope is large or those areas exist in the target.
   - Keep the main agent as coordinator. Sub-agents must not edit files and must not launch further sub-agents unless explicitly assigned as the coordinator.
   - Give every sub-agent the same target scope, attacker model, severity rubric, requirement to prove reachability, and path to this skill.
   - Assign distinct reviewer lenses:
     - Attack Surface Reviewer: routes, handlers, trust boundaries, exposed assets, auth/session flow.
     - Access Control Reviewer: authorization, tenant isolation, object ownership, IDOR/BOLA, privilege escalation.
     - Unsafe Sinks Reviewer: injection, XSS, SSRF, file handling/path traversal, deserialization, command execution, redirects, output encoding.
     - Business Logic and API Reviewer: workflow abuse, insecure design, mass assignment, API-specific risks, race conditions, replay, quota/payment/coupon/order abuse.
     - Platform and Supply Chain Reviewer: dependency vulnerabilities, CI/CD, secrets, cloud/container/IaC, least privilege, network segmentation, security misconfiguration.
     - Abuse and Hardening Reviewer: rate limits, CSRF/CORS, audit logs, error handling, sensitive data exposure, DoS/resource exhaustion.
     - AI/LLM Reviewer: add this reviewer when the target includes prompts, agents, retrieval, tool calling, model gateways, or AI-generated actions.
   - Require each sub-agent to return only candidate findings with severity, file/line, attacker preconditions, attack path, violated boundary or invariant, evidence, impact, recommended fix, verification status, and checks run.
   - Require each sub-agent to explicitly state when it found no issue in its assigned area.
   - If sub-agent tools are unavailable, state that limitation prominently and perform the same reviewer lenses as separate local passes before finalizing.

4. Scan by attack surface.
   - Apply the OWASP Top 10 and hardening checklist from `references/security-checklist.md`.
   - Prioritize risky flows: authentication, authorization, object ownership, tenant boundaries, file upload/download, search/query builders, templating/HTML rendering, redirects, SSRF-prone fetchers, command/process execution, deserialization, business workflows, API mutation endpoints, dependency manifests, CI/CD, cloud/container/IaC, and deployment config.

5. Validate candidates.
   - For each suspected issue, prove reachability from a realistic attacker-controlled source, valid action sequence, violated business invariant, race window, config trust path, or LLM/tool-call chain to meaningful impact.
   - Check preconditions, authorization state, tenant/object boundaries, sanitizers, framework protections, middleware order, and environment assumptions.
   - Prefer local tests, focused scripts, or existing test suites when safe and available.
   - Classify each candidate as `Verified`, `Likely`, or `Not verified`; do not present unverified pattern matches as confirmed vulnerabilities.

6. Synthesize sub-agent results.
   - Merge duplicates that share the same root cause, attacker path, affected asset, and fix; keep all affected locations as evidence.
   - Split findings when similar symptoms require different fixes, different attacker preconditions, or different trust boundaries.
   - Preserve dissent: if reviewers disagree, explain the conflict and choose the final status based on reachability evidence, not votes.
   - Re-check high and critical findings locally before finalizing when feasible.
   - Downgrade or remove findings that lack a plausible attacker source, reachable sink, violated boundary, violated invariant, exploitable config exposure, or risky LLM/tool-call chain.
   - Keep useful hardening observations separate from exploitable vulnerabilities.
   - If a conflict cannot be resolved, downgrade the status to `Likely` or `Not verified` and describe the uncertainty under residual risk.
   - Use the highest severity justified by demonstrated impact and realistic exploitability.

7. Report findings first.
   - Order by severity and exploitability.
   - For each finding include: severity, affected file/line, attacker preconditions, attack path, evidence, impact, recommended fix, and verification status.
   - Keep the summary brief and place it after findings.
   - Include sub-agent coverage, checks run, final synthesis decisions, and residual risk.

## Severity Rubric

- `Critical`: unauthenticated remote code execution, authentication bypass, admin takeover, mass sensitive data exfiltration, exposed production signing/encryption keys, cloud/CI takeover, malicious release pipeline compromise, container breakout to host/cloud credentials, or a trivial exploit with catastrophic impact.
- `High`: broken access control across tenants/users, exploitable SQL/NoSQL/command injection, stored XSS against privileged users, SSRF to sensitive internal services, credential exposure, practical dependency/supply-chain exploitation, financial fraud, race-condition double spend, or AI tool-call/data-exfiltration abuse with sensitive impact.
- `Medium`: CSRF on meaningful state changes, reflected/DOM XSS with realistic impact, missing rate limits on abuse-prone flows, weak cryptography, sensitive data overexposure, or logging/audit gaps that materially hinder detection.
- `Low`: defense-in-depth gaps, limited misconfigurations, missing security headers with no direct exploit path, or hardening opportunities with constrained impact.

## Output Format

Use this structure for review results:

```markdown
Findings
- [Severity] Title - file:line
  Status: Verified | Likely | Not verified
  Attack path: ...
  Evidence: ...
  Impact: ...
  Fix: ...

Sub-Agent Coverage
- Attack Surface Reviewer: ...
- Access Control Reviewer: ...
- Unsafe Sinks Reviewer: ...
- Business Logic and API Reviewer: ...
- Platform and Supply Chain Reviewer: ...
- Abuse and Hardening Reviewer: ...
- AI/LLM Reviewer: included | not applicable | unavailable

Synthesis Notes
- ...

Checks Run
- ...

Residual Risk
- ...

Summary
- ...

Final Conclusion
- ...
```

If no vulnerabilities are found, say so clearly, then list meaningful gaps in coverage such as unexecuted tests, unavailable deployment config, missing dependency lockfiles, or code paths not inspected.
