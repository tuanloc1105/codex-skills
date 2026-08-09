# Frontend Workflow Contract

## Contents

- [Plan template](#plan-template)
- [Gate rules](#gate-rules)
- [State updates](#state-updates)
- [Readiness definitions](#readiness-definitions)
- [Handoff format](#handoff-format)

## Plan template

Add this English section to the approved implementation plan. Keep it as the single execution record.

```markdown
## Frontend Workflow Contract

Workflow State: JIRA_UNVERIFIED

### Jira and UI Acceptance Evidence

- Jira key: <key or unresolved>
- Site/account status: <verified, ambiguous, unavailable, or unresolved>
- Issue type: <type or unresolved>
- Parent evidence: <key/type/source or unresolved>
- Epic evidence: <key/source or unresolved>
- Acceptance criteria: <source and verified summary, or unresolved>
- Design source: <URL/path/version, not applicable with reason, or unresolved>

### Repository Profile

- Profile: <path and version, or bundled defaults>
- Application/design-system roots: <paths or unresolved>
- Evidence source: <paths or commands>
- Drift status: <clear or details>

### Gate Matrix

| Gate | Applicability | Type | Evidence | Owner | State |
| --- | --- | --- | --- | --- | --- |
| Jira identity and hierarchy | Required | Hard | <evidence> | Frontend Developer | Pending |
| UI acceptance and design source | <Required/Not applicable/Deferred> | <Hard/Advisory> | <evidence> | Product/Design/Frontend | Pending |
| Branch and MR traceability | Required | Hard | <evidence> | Frontend Developer | Pending |
| Reviewable work slice | Required | Advisory | <evidence> | Frontend Developer | Pending |
| Repository-mandated checks | Required | Hard | <evidence> | Frontend Developer | Pending |
| Responsive/browser/accessibility evidence | <Required/Not applicable/Deferred> | <Hard/Advisory> | <evidence> | Frontend Developer | Pending |
| AI attribution | <Required/Not applicable/Deferred> | <Hard/Advisory> | <evidence> | Frontend Developer | Pending |
| Git delivery authorization | Required for listed actions | Hard | <bundle> | User | Pending |
| Approval and merge | Not applicable: Reviewer/Lead owned | Hard boundary | <handoff> | Reviewer/Lead | Not started |

### Existing Git Baseline and Diff Boundary

- Repository: <absolute path>
- Initial branch and HEAD: <branch and SHA>
- Initial status: <status>
- Pre-existing staged/unstaged/untracked paths: <paths>
- Session-owned paths or hunks: <scope>

### Delivery Contract

- Source branch: <branch or unresolved>
- Remote: <remote and repository identity or unresolved>
- Target branch: <branch or unresolved>
- MR title: <resolved title or pattern>
- MR description requirements: context, Jira link, implementation, UI impact, verification, risks, handoff
- AI attribution state: <mechanism, AI_ATTRIBUTION_UNAVAILABLE, or unresolved>

### Git Delivery Authorization

- Repository: <exact absolute path and GitLab project identity>
- Exact actions: <commit, push, create MR; list only authorized actions>
- Source branch: <exact branch>
- Remote: <exact remote>
- Target branch: <exact target>
- Diff boundary: <exact paths or reviewed diff identity>
- Authorized: no

### Verification

- Repository checks: <planned commands and expected results>
- UI states: <loading, empty, error, permission, validation, success, or applicability>
- Viewports and browsers: <matrix or applicability>
- Accessibility: <keyboard, focus, semantics, contrast, assistive technology, or applicability>
- Visual evidence: <screenshots, comparison source, storage location, or applicability>
- Security/privacy checks: <planned checks or applicability>
- Actual results: <update during execution>

### MR Evidence and Final Handoff

- MR URL/IID: <verified value or unavailable>
- Verified source/target/title/description: <evidence>
- Observable pipeline/check state: <state and observation time>
- Risks and remaining owner: <details>
```

## Gate rules

Use `Required`, `Not applicable`, or `Deferred` for applicability. Every `Not applicable` entry requires a reason. Every `Deferred` entry requires a checkpoint, resume condition, and owner.

Classify gates as `Hard` or `Advisory` from [frontend-policy.md](frontend-policy.md), higher-priority instructions, Jira acceptance criteria, and repository rules. A hard failure prohibits only the dependent mutation; it does not prohibit safe discussion, read-only inspection, planning, or unrelated verification. An advisory failure records impact and mitigation without falsely blocking delivery.

Use only `Pending`, `Passed`, `Failed`, `Deferred`, or `Not applicable` in the matrix `State` column. A required hard gate permits dependent mutation only when `Passed`. `Failed` prohibits that mutation; `Deferred` requires its recorded checkpoint before proceeding; and `Not applicable` requires a reason and may be used only when applicability is not `Required`.

The Git delivery authorization is valid only when every field is exact and `Authorized: yes` is explicitly approved in the current plan context. Validate both the absolute checkout and GitLab project identity. Invalidate it if the repository, action set, source branch, remote, target branch, or diff boundary changes. Plan approval alone is not Git delivery authorization.

## State updates

Use these transitions and record evidence at each transition:

`JIRA_UNVERIFIED` -> `JIRA_VERIFIED` -> `PLAN_APPROVED` -> `IMPLEMENTING` -> `CODE_READY` -> `MR_PREPARED` -> `MR_READY`

- Stay at `JIRA_UNVERIFIED` until site/account, issue identity, required ancestry, and acceptance-source status are verified.
- Enter `JIRA_VERIFIED` only after those Jira checks pass.
- Enter `PLAN_APPROVED` only with an approved implementation plan and complete contract.
- Enter `IMPLEMENTING` only after all source-mutation hard gates pass.
- Enter `CODE_READY` only after acceptance criteria are met and planned checks run, or unavailable advisory checks and residual risk are recorded.
- Use `WAITING_EXTERNAL` from any state when an external credential, permission, approval, required design source, tool, or system is required. Record the prior state, blocked operation, owner, resume condition, and next command/check.
- Resume from the recorded checkpoint after revalidating stale evidence and authorization.

When `$execute` owns execution, map `WAITING_EXTERNAL` to technical plan `Status: Blocked` only after its recovery paths are exhausted and the condition meets its genuine-blocker definition. Otherwise remain `MR_PREPARED` and record the unavailable path. Never change a cooperating skill's completion semantics.

## Readiness definitions

`MR_PREPARED` requires verified Jira context, acceptance-source status, intended source and target branches, completed implementation, repository-mandated checks, reviewed UI evidence or recorded advisory exceptions, reviewed session diff boundary, and an English proposed MR handoff. Use it when authorization, credentials, permissions, tooling, or another external condition prevents push or MR creation.

`MR_READY` additionally requires evidence that the source branch was pushed under a matching, still-valid Git delivery authorization; the MR exists in the correct GitLab repository; source and target match; the title contains the Jira key and resolved pattern; the description contains all required sections; and the observable pipeline/check state was inspected. An unauthorized, uncreated, or unverified MR is never `MR_READY`.

## Handoff format

Report in English:

1. Final workflow state and truthful reason
2. Jira, acceptance/design, repository-profile, Git-baseline, authorization, and MR evidence
3. Implementation summary and exact session diff boundary
4. Checks run, UI evidence, results, skipped checks, and residual risks
5. Advisory exceptions, including work-slice, browser/accessibility, or attribution limitations
6. Preserved unrelated changes
7. Next owner and actions, stopping before approval, merge, deployment, or release
