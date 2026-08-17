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
| Delivery mode and path classification | Required | Hard boundary | <evidence> | User/Developer | Pending |
| Jira identity and hierarchy | Required | Hard | <evidence> | Developer | Pending |
| New Subtask for post-completion bug | <Required/Not applicable> | Hard boundary | <evidence or reason> | User/Developer | Pending |
| Domain acceptance source | <Required/Not applicable/Deferred> | <Hard/Advisory> | <evidence> | Product/Developer | Pending |
| Epic base branch before plan | Required | Hard boundary | <evidence> | Tech Lead | Pending |
| Working branch naming and MR traceability | Required | Hard | <evidence> | Developer | Pending |
| Commit message prefix | Required for commit | Hard | <evidence> | Developer | Pending |
| Reviewable work slice | Required | Advisory | <evidence> | Developer | Pending |
| Common repository checks | Required | Hard | <evidence> | Developer | Pending |
| Backend verification | <Required/Not applicable> | <Hard/Advisory> | <evidence> | Backend Developer | Pending |
| Frontend/UI verification | <Required/Not applicable> | <Hard/Advisory> | <evidence> | Frontend Developer | Pending |
| AI attribution | <Required/Not applicable/Deferred> | <Hard/Advisory> | <evidence> | Developer | Pending |
| Git delivery authorization | Required for listed actions | Hard | <bundle> | User | Pending |
| Approval and merge | Not applicable: Reviewer/Lead owned | Hard boundary | <handoff> | Reviewer/Lead | Not started |

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

Classify gates from higher-priority instructions, core policy, applicable domain policies, Jira acceptance, and repository rules. Hard failures pause only dependent mutation until passed or validly overridden. Hard boundaries cannot be overridden. An override records failed gate, missing evidence, affected action, warning, explicit authorization, repository/state scope, reason, and residual risk, and expires when relevant state changes.

Mode and path classification must be exact before `$plan` or mutation. In `mixed` mode, both domain policies apply to their classified paths and the union of applicable gates must pass. Never downgrade `mixed` to one domain merely because one side has fewer changed lines.

The post-completion bug Subtask and Epic-base prerequisites retain the hard boundaries in [core-policy.md](core-policy.md). Git authorization is valid only when every field is exact and `Authorized: yes` is explicitly approved in the current plan context; plan approval alone is insufficient.

## State updates

Use and evidence these transitions:

`MODE_UNRESOLVED` -> `JIRA_UNVERIFIED` -> `JIRA_VERIFIED` -> `EPIC_BASE_VERIFIED` -> `PLAN_APPROVED` -> `IMPLEMENTING` -> `CODE_READY` -> `MR_PREPARED` -> `MR_READY`

- Enter `JIRA_UNVERIFIED` only after mode and path classification resolve.
- Stay there until Jira identity, ancestry, and applicable acceptance-source status are verified, including any required new bug-fix Subtask.
- Enter `EPIC_BASE_VERIFIED` only after exact remote existence, Epic mapping, SHA, and Tech Lead ownership are verified.
- Enter `PLAN_APPROVED` only with an approved plan and complete contract.
- Enter `IMPLEMENTING` after source-mutation gates pass or receive allowed scoped overrides.
- Enter `CODE_READY` after applicable acceptance criteria and the common plus domain checks pass, or allowed overrides record residual risk.
- Use `WAITING_EXTERNAL` when external credentials, permissions, approval, required evidence, tools, or systems prevent the next step. Record prior state, operation, owner, resume condition, and next check.
- Resume only after revalidating stale evidence, mode/path classification, and authorization.

When `$execute` owns execution, use its technical `Status: Blocked` only when the same condition meets that skill's blocker definition. Otherwise retain the truthful delivery state and resume checkpoint.

## Readiness definitions

`MR_PREPARED` requires verified mode and path boundaries, Jira context and ancestry, any required new Subtask, applicable acceptance evidence or override, verified Epic base, intended working source and Epic target, completed implementation, common and domain verification or recorded overrides, reviewed session diff, and an English proposed handoff. Use it when an external condition prevents authorized branch creation, push, or MR creation.

`MR_READY` additionally requires verified Epic-base ancestry, authorized push, and an existing MR in the correct GitLab repository targeting the Epic base. Source/target, title, description, and observable checks must pass or have allowed recorded overrides. Missing evidence is never verified by override; an unauthorized, uncreated, incorrectly targeted, non-Epic-based, or repository-ambiguous MR is never `MR_READY`.

## Handoff format

Report in English:

1. Final workflow state and truthful reason
2. Delivery mode, per-domain paths, and classification evidence
3. Jira, acceptance/design, profile, Git baseline, authorization, and MR evidence
4. Implementation summary and exact session diff boundary
5. Common, backend, and frontend checks with results, exceptions, and residual risks
6. Preserved unrelated changes
7. Next owner and actions, stopping before approval, merge, deployment, or release
