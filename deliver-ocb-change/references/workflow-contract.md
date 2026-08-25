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

- Working Jira key: <Story/Task/Bug/Subtask key or unresolved>
- Username: <value and source or unresolved>
- Site/account status: <verified, ambiguous, unavailable, or unresolved>
- Working issue type and direct parent: <evidence or unresolved>
- Epic evidence: <key/source or unresolved>
- Delivery mode: <new work, post-completion bug fix, or unresolved>
- Completed Story, Task, or Bug and bug-fix Subtask: <evidence, not applicable with reason, or unresolved>
- Jira Done transition: <authorized action, resulting status and evidence, deferred with owner, or not applicable with reason>
- Epic base branch: <remote branch, SHA, existence and ownership evidence, or unresolved>
- Development base: <Epic base for an independent ticket, or predecessor Jira key, remote branch, recorded SHA, dependency evidence, and ancestry for a stacked ticket>
- Stack order: <ordered predecessor Jira keys/branches/MRs, user-owned review order, merge prerequisites, or not applicable>
- Acceptance/design source: <source, not applicable with reason, or unresolved>

### Repository Profile

- Profile: <path/version or bundled defaults>
- Domain roots and generated paths: <paths or unresolved>
- Evidence source: <paths or commands>
- Drift status: <clear or details>

### PR Size and Jira Work Split

- Effective maximum: <400 or stricter repository value and source>
- Measurement method: <LinearB value or additions plus deletions fallback>
- Expected touchpoints: <paths and change types>
- Pre-code estimate: <changed lines, supporting evidence, and confidence>
- Size classification: <handwritten/non-generated lines; qualifying spec/documentation lines; deterministic generated lines; exact paths>
- Artifact exception: <not required, pending, or evidence of provenance, regeneration, indivisibility, warning, and exact user authorization>
- Split required: <yes or no with reason>
- Current Jira slice: <key, acceptance boundary, branch, and intended PR>
- Additional Jira slices: <keys when verified; otherwise recommended types, parent/Epic, scope, dependencies, acceptance, verification, and per-PR estimates>
- Actual incremental PR size: <ticket-owned changed lines and exact development-base ref/SHA, or pending before CODE_READY>
- Cumulative Epic-target diff: <changed lines including unmerged predecessors, exact Epic ref/SHA, and disclosure state, or same as incremental for an independent ticket>
- Post-predecessor-merge size: <final Epic-target measurement, pending until predecessors merge, or not applicable>
- Drift action: <clear, stopped before excess scope, or details>

### Gate Matrix

| Gate | Applicability | Type | Evidence | Owner | State |
| --- | --- | --- | --- | --- | --- |
| Delivery mode and path classification | Required | Hard | <evidence or exact accepted assumption> | User/Developer | Pending |
| Jira identity and hierarchy | Required | Hard | <evidence> | Developer | Pending |
| New Subtask for post-completion bug | <Required/Not applicable> | Hard | <evidence or reason> | User/Developer | Pending |
| Domain acceptance source | <Required/Not applicable/Deferred> | <Hard/Advisory> | <evidence> | Product/Developer | Pending |
| Epic base branch before plan | Required | Hard | <evidence or exact accepted fallback> | Tech Lead/User | Pending |
| Development base and stacked ancestry | Required | Hard | <Epic base, or verified predecessor dependency, branch, SHA, ancestry, and ordered chain> | User/Developer | Pending |
| Working branch naming and MR traceability | Required | Hard | <evidence> | Developer | Pending |
| Commit message prefix | Required for commit | Hard | <evidence> | Developer | Pending |
| LinearB init commit before source mutation | Required | Hard | <working branch, first-ticket-owned-commit position, clean-index check, init commit SHA, and timestamp> | Developer | Pending |
| Pre-code PR size at or below effective maximum | Required before plan approval or source mutation | Hard; scoped artifact exception only | <estimate, classification, and exception evidence> | Developer/User | Pending |
| Actual PR size at or below effective maximum | Required before CODE_READY, push, or MR creation | Hard; scoped artifact exception only | <measurement, base, classification, and regeneration evidence> | Developer/User | Pending |
| Common repository checks | Required | Hard | <evidence> | Developer | Pending |
| Backend verification | <Required/Not applicable> | <Hard/Advisory> | <evidence> | Backend Developer | Pending |
| Frontend/UI verification | <Required/Not applicable> | <Hard/Advisory> | <evidence> | Frontend Developer | Pending |
| AI attribution | <Required/Not applicable/Deferred> | <Hard/Advisory> | <evidence> | Developer | Pending |
| Git delivery authorization | Required for listed actions before MR creation | Hard | <bundle> | User | Pending |
| Jira Done transition after MR creation | <Required when authorized/Deferred/Not applicable> | Hard for the transition only | <CODE_READY, MR repository/source/target, authorization, and re-read status> | User/Developer | Pending |
| Tech Lead approval | Required before merge | Hard; not overridable | <approver identity and current approval evidence> | Tech Lead | Pending |
| Merge readiness | Required before merge | Hard; not overridable | <source, target, SHA, checks, and GitLab mergeability> | Developer | Pending |
| Stacked predecessor merge order | <Required for stacked/Not applicable> | Hard; not overridable | <ordered predecessor merge evidence, refreshed ancestry, final diff, and rerun checks> | Developer | Pending |
| Developer merge | Required after Tech Lead approval | Hard | <merge commit/result evidence> | Developer | Pending |

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
- Development base: <Epic base, or predecessor Jira key, remote branch, SHA, dependency evidence, and source>
- Working issue and source branch: <key and resolved branch>
- Branch ancestry: <Epic base -> ordered predecessor branches -> working issue evidence>
- Stacked review and merge order: <ordered Jira keys/MRs, user-owned review sequence, and merge prerequisites, or not applicable>
- Remote and GitLab project: <identity>
- MR target, title, and description requirements: <values>
- Naming username and commit prefix: <source and value>
- AI attribution state: <mechanism, AI_ATTRIBUTION_UNAVAILABLE, or unresolved>

### Git Delivery Authorization

- Repository: <absolute path and GitLab project>
- Exact actions: <create branch, commit, push, create MR; list only user-authorized actions; merge is governed separately by verified Tech Lead approval>
- Pre-implementation branch/commit authorization: <current-session evidence or unresolved; required before source mutation>
- LinearB init commit: <working branch, first-ticket-owned-commit position, clean-index evidence, commit SHA and timestamp, or pending before IMPLEMENTING>
- Epic base branch: <remote ref and SHA>
- Development base: <exact remote ref and recorded SHA>
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
- Jira Done evidence: <issue key, transition authorization, resulting status, and observation time; deferred owner; or not applicable>
- Observable pipeline/check state: <state and observation time>
- Tech Lead approval: <approver identity, approval state, and observation time>
- Merge evidence: <merge result, resulting SHA, and observation time, or pending>
- Risks and remaining owner: <details>
```

## Gate rules

Use `Required`, `Not applicable`, or `Deferred` for applicability; every non-required entry needs its reason or resume checkpoint and owner. Use only `Pending`, `Passed`, `Failed`, `Overridden`, `Deferred`, or `Not applicable` for state.

Classify skill-defined gates from higher-priority instructions, core policy, applicable domain policies, Jira acceptance, and repository rules. The pre-code and actual PR-size gates may be overridden only by the complete scoped artifact exception in [core-policy.md](core-policy.md); ordinary handwritten excess remains blocked. Every other `Hard` failure pauses only the dependent action until it passes or the user validly overrides it after warning. An override records the failed gate, missing evidence, affected action, warning, explicit risk acceptance and authorization, exact repository/state/target/scope, reason, and residual risk, and expires when relevant state changes. Mark the gate `Overridden`, never `Passed`, and never describe missing evidence as verified.

If a failed gate leaves no executable value, the user must supply or explicitly select an exact value as part of the override. Risk acceptance alone does not authorize an unspecified Git mutation or let the agent guess a repository, issue, mode, path boundary, branch, remote, or MR target. Higher-priority instructions and safety constraints remain controlling and are not workflow gates.

Mode and path classification should be evidence-backed before `$plan` or mutation. If evidence is incomplete, pause and recommend the classification; continue only when the user explicitly authorizes an exact mode and path scope under a recorded override. In `mixed` mode, both domain policies apply to their classified paths and the union of applicable gates must pass or be individually overridden. Never downgrade `mixed` merely because one side has fewer changed lines.

The post-completion bug Subtask and Epic-base prerequisites use the warning-and-override procedure in [core-policy.md](core-policy.md). Resolve the development base independently: default to the Epic base, or use a verified predecessor working branch only when the user explicitly elects stacked execution before predecessor merge. A stacked contract must record the complete ordered dependency chain, fixed predecessor SHA used for branch creation, user-owned review order, and non-overridable predecessor-merge prerequisites. Before plan approval or source mutation, require the PR-size section to identify expected touchpoints, measurement method, effective maximum, a supported estimate, and separated line classifications when an artifact exception may apply. For a stacked ticket, apply the size gate to its incremental diff from the development base, disclose the cumulative Epic-target diff, and require a final Epic-target measurement after predecessors merge. If the estimate is unresolved or too large and no complete artifact exception applies, recommend Jira slices according to the current issue type, keep the workflow before `PLAN_APPROVED`, and do not mutate source. Plan phases and incremental commits do not replace the requirement for a separately traceable Jira slice, branch, and PR. Jira creation, editing, or status transition requires exact authorization through `$interact-with-jira`, followed by relationship or resulting-status verification as applicable. Git authorization is valid only when every operational field is exact and `Authorized: yes` is explicitly approved in the current plan context; plan approval or generic risk acceptance alone is insufficient. When implementation will create local commits, working-branch creation and commit authorization must be resolved before entering `IMPLEMENTING`. After creating or verifying the working branch, require a clean index and create the LinearB init commit before any source mutation; record its SHA and timestamp. Push and MR authorization may remain pending until code is ready. Do not use a pending commit or init-commit gate as permission to accumulate uncommitted implementation.

## State updates

Use and evidence these transitions:

`MODE_UNRESOLVED` -> `MODE_RESOLVED` -> `JIRA_RESOLVED` -> `EPIC_BASE_RESOLVED` -> `PLAN_APPROVED` -> `IMPLEMENTING` -> `CODE_READY` -> `MR_PREPARED` -> `MR_READY` -> `MERGED`

- Enter `MODE_RESOLVED` after mode and path classification pass or receive an exact scoped override.
- Enter `JIRA_RESOLVED` after Jira identity, ancestry, applicable acceptance status, and any post-completion Subtask gate each pass or receive a scoped override.
- Enter `EPIC_BASE_RESOLVED` after the Epic-base gate passes or the user authorizes an exact fallback under a scoped override, and the separate development base plus any stacked ancestry are resolved.
- Enter `PLAN_APPROVED` only with an approved plan, complete contract, and a pre-code PR-size gate that is `Passed` or validly `Overridden` through the scoped artifact exception for every planned Jira slice. An unresolved size gate cannot proceed.
- Enter `IMPLEMENTING` after the current Jira slice's pre-code PR-size gate passes or receives a valid artifact exception, other source-mutation gates pass or receive scoped overrides, and, for Git-backed implementation, exact working-branch creation and local incremental-commit authorization are recorded and the required LinearB init commit exists on each affected working branch with its SHA and timestamp captured.
- Enter `CODE_READY` after the actual ticket-owned incremental diff from the resolved development base is measured and the size gate is `Passed` or validly `Overridden` through the scoped artifact exception, the cumulative Epic-target diff is recorded for a stacked ticket, and applicable acceptance criteria and common plus domain checks pass or receive allowed scoped overrides.
- After `CODE_READY`, once the MR exists with the expected repository, source, and target, transition the working Jira issue to `Done` immediately when the exact transition is authorized, then re-read and record the resulting status. This transition does not require pipeline results, Tech Lead approval, mergeability, `MR_READY`, or merge evidence. If it is unauthorized or unavailable, defer only the Jira transition with an owner and resume condition; do not block the independent review-and-merge path.
- Enter `MERGED` only after verifying current Tech Lead approval on the exact MR, unchanged expected source and Epic target, current MR SHA, required pipeline/check results, GitLab mergeability, and successful Developer-performed merge. For a stacked ticket, first verify every predecessor merged into the Epic branch in order, refresh ancestry, update or rebase when repository policy requires, confirm the final Epic-target diff contains only the ticket-owned scope and passes the size gate, and rerun affected checks. Tech Lead approval is sufficient authorization under this workflow for the Developer to perform the merge; the Tech Lead does not need to perform it.
- Use `WAITING_EXTERNAL` when external credentials, permissions, approval, required evidence, tools, or systems prevent the next step. Record prior state, operation, owner, resume condition, and next check.
- Resume only after revalidating stale evidence, mode/path classification, overrides, and authorization.

When `$execute` owns execution, use its technical `Status: Blocked` only when the same condition meets that skill's blocker definition. Otherwise retain the truthful delivery state and resume checkpoint.

## Readiness definitions

`MR_PREPARED` requires every applicable gate to be `Passed`, `Overridden`, or truthfully `Not applicable`; an overridden actual PR-size gate must contain the complete artifact-exception evidence and separated measurements; exact intended working source and MR target; completed implementation; reviewed session diff; and an English proposed handoff. Every override must remain visible with its missing evidence and residual risk. Use this state when an external condition prevents authorized branch creation, push, or MR creation.

`MR_READY` additionally requires an authorized push and an existing MR in the exact GitLab repository with an exact source and Epic target. Ancestry, title, description, and observable checks must pass or have recorded overrides. A stacked MR may be `MR_READY` while predecessors remain open when its dependency chain, incremental and cumulative diffs, disclosure, and review order are recorded; it is not merge-ready until the non-overridable predecessor merge-order gate passes. Missing evidence is never verified by override; an unauthorized, uncreated, or repository/target-ambiguous MR is never `MR_READY` because the required action itself is not exactly defined or authorized. An exactly authorized Jira `Done` transition may already have occurred after `CODE_READY` and verified MR creation; its outcome is recorded separately and does not depend on this readiness state or merge.

`MERGED` additionally requires verified approval from a Tech Lead on that exact MR, current required checks, a mergeable GitLab state, an unchanged expected source and Epic target, and evidence that the Developer's merge completed successfully. A stacked ticket additionally requires ordered predecessor merge evidence, refreshed ancestry, a clean ticket-owned final Epic-target diff and size result, and rerun affected checks. Tech Lead approval, predecessor merge order, and merge-readiness gates are not overridable. Never self-approve, enable auto-merge, bypass controls, merge ahead of a predecessor, or treat an approval from an unverified role as Tech Lead approval.

## Handoff format

Report in English:

1. Final workflow state and truthful reason
2. Delivery mode, per-domain paths, and classification evidence
3. Jira, acceptance/design, profile, Git baseline, authorization, and MR evidence
4. Implementation summary and exact session diff boundary
5. Common, backend, and frontend checks with results, exceptions, and residual risks
6. Preserved unrelated changes
7. Tech Lead approval and Developer merge evidence, or the exact owner and resume condition when waiting
8. Next owner and actions, stopping before deployment or release
