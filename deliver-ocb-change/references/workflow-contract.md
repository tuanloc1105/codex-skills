# OCB Delivery Workflow Contract

## Plan template

Add this English section to the approved implementation plan and keep it as the single execution record.

```markdown
## OCB Delivery Workflow Contract

Workflow State: MODE_UNRESOLVED

### Delivery Mode

- Mode: <backend, frontend, mixed, or unresolved>
- Evidence source: <current request, plan, profile, repository instructions, paths, or unresolved>
- Backend paths: <paths, not applicable with reason, or unresolved>
- Frontend paths: <paths, not applicable with reason, or unresolved>
- Classification drift: <clear or details>

### Jira and Acceptance Evidence

- Working Jira key: <Story/Task/Subtask key or unresolved>
- Username: <value and source or unresolved>
- Site/account status: <verified, ambiguous, unavailable, or unresolved>
- Working issue type and direct parent: <evidence or unresolved>
- Epic evidence: <key/source or unresolved>
- Delivery mode: <new work, post-completion bug fix, or unresolved>
- Completed Task and bug-fix Subtask: <evidence, not applicable with reason, or unresolved>
- Epic base branch: <remote branch, SHA, existence and ownership evidence, or unresolved>
- Acceptance/design source: <source, not applicable with reason, or unresolved>

### Repository Profile

- Profile: <path/version or bundled defaults>
- Domain roots and generated paths: <paths or unresolved>
- Evidence source: <paths or commands>
- Drift status: <clear or details>

### Gate Matrix

| Gate | Applicability | Type | Evidence | Owner | State |
| --- | --- | --- | --- | --- | --- |
| Delivery mode and path classification | Required | Hard | <evidence or exact accepted assumption> | User/Developer | Pending |
| Jira identity and hierarchy | Required | Hard | <evidence> | Developer | Pending |
| New Subtask for post-completion bug | <Required/Not applicable> | Hard | <evidence or reason> | User/Developer | Pending |
| Domain acceptance source | <Required/Not applicable/Deferred> | <Hard/Advisory> | <evidence> | Product/Developer | Pending |
| Epic base branch before plan | Required | Hard | <evidence or exact accepted fallback> | Tech Lead/User | Pending |
| Working branch naming and MR traceability | Required | Hard | <evidence> | Developer | Pending |
| Commit message prefix | Required for commit | Hard | <evidence> | Developer | Pending |
| Reviewable work slice | Required | Advisory | <evidence> | Developer | Pending |
| Common repository checks | Required | Hard | <evidence> | Developer | Pending |
| Backend verification | <Required/Not applicable> | <Hard/Advisory> | <evidence> | Backend Developer | Pending |
| Frontend/UI verification | <Required/Not applicable> | <Hard/Advisory> | <evidence> | Frontend Developer | Pending |
| AI attribution | <Required/Not applicable/Deferred> | <Hard/Advisory> | <evidence> | Developer | Pending |
| Git delivery authorization | Required for listed actions | Hard | <bundle> | User | Pending |
| Approval and merge | Not applicable: outside delivery scope | Ownership limit | <handoff> | Reviewer/Lead | Not started |

### Gate Overrides

- Override: <gate, warning, action, authorization evidence, scope, reason, residual risk, or none>

### Existing Git Baseline and Diff Boundary

- Repository: <absolute path>
- Initial branch and HEAD: <branch and SHA>
- Initial status: <status>
- Pre-existing paths: <staged, unstaged, and untracked paths>
- Session-owned backend paths/hunks: <scope>
- Session-owned frontend paths/hunks: <scope>

### Delivery Contract

- Epic base branch: <remote ref, SHA, repository, Epic mapping, and ownership source>
- Working issue and source branch: <key and resolved branch>
- Branch ancestry: <Epic base -> working issue evidence>
- Remote and GitLab project: <identity>
- MR target, title, and description requirements: <values>
- Naming username and commit prefix: <source and value>
- AI attribution state: <mechanism, AI_ATTRIBUTION_UNAVAILABLE, or unresolved>

### Git Delivery Authorization

- Repository: <absolute path and GitLab project>
- Exact actions: <create branch, commit, push, create MR; list only authorized actions>
- Epic base branch: <remote ref and SHA>
- Working source branch: <exact branch>
- Remote and MR target: <exact values>
- Diff boundary: <exact paths or reviewed diff identity>
- Authorized: no

### Verification

- Common checks: <commands and expected results>
- Backend checks: <commands, contracts, data/security evidence, or applicability>
- Frontend checks: <commands, UI states, viewports/browsers, accessibility, visual and privacy evidence, or applicability>
- Actual results: <update during execution>

### MR Evidence and Final Handoff

- MR URL/IID: <verified value or unavailable>
- Verified source/target/title/description: <evidence>
- Observable pipeline/check state: <state and observation time>
- Risks and remaining owner: <details>
```

## Gate rules

Use `Required`, `Not applicable`, or `Deferred` for applicability; every non-required entry needs its reason or resume checkpoint and owner. Use only `Pending`, `Passed`, `Failed`, `Overridden`, `Deferred`, or `Not applicable` for state.

Classify skill-defined gates from higher-priority instructions, core policy, applicable domain policies, Jira acceptance, and repository rules. Every `Hard` failure pauses only the dependent action until it passes or the user validly overrides it after warning. An override records the failed gate, missing evidence, affected action, warning, explicit risk acceptance and authorization, exact repository/state/target/scope, reason, and residual risk, and expires when relevant state changes. Mark the gate `Overridden`, never `Passed`, and never describe missing evidence as verified.

If a failed gate leaves no executable value, the user must supply or explicitly select an exact value as part of the override. Risk acceptance alone does not authorize an unspecified Git mutation or let the agent guess a repository, issue, mode, path boundary, branch, remote, or MR target. Higher-priority instructions and safety constraints remain controlling and are not workflow gates.

Mode and path classification should be evidence-backed before `$plan` or mutation. If evidence is incomplete, pause and recommend the classification; continue only when the user explicitly authorizes an exact mode and path scope under a recorded override. In `mixed` mode, both domain policies apply to their classified paths and the union of applicable gates must pass or be individually overridden. Never downgrade `mixed` merely because one side has fewer changed lines.

The post-completion bug Subtask and Epic-base prerequisites use the warning-and-override procedure in [core-policy.md](core-policy.md). Git authorization is valid only when every operational field is exact and `Authorized: yes` is explicitly approved in the current plan context; plan approval or generic risk acceptance alone is insufficient.

## State updates

Use and evidence these transitions:

`MODE_UNRESOLVED` -> `MODE_RESOLVED` -> `JIRA_RESOLVED` -> `EPIC_BASE_RESOLVED` -> `PLAN_APPROVED` -> `IMPLEMENTING` -> `CODE_READY` -> `MR_PREPARED` -> `MR_READY`

- Enter `MODE_RESOLVED` after mode and path classification pass or receive an exact scoped override.
- Enter `JIRA_RESOLVED` after Jira identity, ancestry, applicable acceptance status, and any post-completion Subtask gate each pass or receive a scoped override.
- Enter `EPIC_BASE_RESOLVED` after the Epic-base gate passes or the user authorizes an exact fallback under a scoped override.
- Enter `PLAN_APPROVED` only with an approved plan and complete contract.
- Enter `IMPLEMENTING` after source-mutation gates pass or receive scoped overrides.
- Enter `CODE_READY` after applicable acceptance criteria and common plus domain checks pass, or scoped overrides record residual risk.
- Use `WAITING_EXTERNAL` when external credentials, permissions, approval, required evidence, tools, or systems prevent the next step. Record prior state, operation, owner, resume condition, and next check.
- Resume only after revalidating stale evidence, mode/path classification, overrides, and authorization.

When `$execute` owns execution, use its technical `Status: Blocked` only when the same condition meets that skill's blocker definition. Otherwise retain the truthful delivery state and resume checkpoint.

## Readiness definitions

`MR_PREPARED` requires every applicable gate to be `Passed`, `Overridden`, or truthfully `Not applicable`; exact intended working source and MR target; completed implementation; reviewed session diff; and an English proposed handoff. Every override must remain visible with its missing evidence and residual risk. Use this state when an external condition prevents authorized branch creation, push, or MR creation.

`MR_READY` additionally requires an authorized push and an existing MR in the exact GitLab repository with an exact source and target. Ancestry, title, description, and observable checks must pass or have recorded overrides. Missing evidence is never verified by override; an unauthorized, uncreated, or repository/target-ambiguous MR is never `MR_READY` because the required action itself is not exactly defined or authorized.

## Handoff format

Report in English:

1. Final workflow state and truthful reason
2. Delivery mode, per-domain paths, and classification evidence
3. Jira, acceptance/design, profile, Git baseline, authorization, and MR evidence
4. Implementation summary and exact session diff boundary
5. Common, backend, and frontend checks with results, exceptions, and residual risks
6. Preserved unrelated changes
7. Next owner and actions, stopping before approval, merge, deployment, or release
