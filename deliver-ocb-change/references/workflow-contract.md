# OCB Delivery Workflow Contract

## Plan template

Add this English section to the approved implementation plan and keep it as the single execution record.

For an existing discuss/plan/execute bundle, use the file ownership and resume binding in [Composition and resume](composition-and-resume.md). Keep one authoritative OCB contract and link evidence instead of duplicating the record. Do not alter the generic workflow's reference allowlist or lifecycle format.

```markdown
## OCB Delivery Workflow Contract

Workflow State: MODE_UNRESOLVED

### OCB Policy Binding and Resume

- Policy owner: deliver-ocb-change
- Applicable skill and policy sources: <resolved skill root, relative policy paths, and source revisions or content fingerprints>
- Domain policy set: <backend, frontend, both for mixed, or unresolved before classification>
- Repository policy/profile sources: <instruction paths and revisions; .ocb/deliver-change.yaml or verified absence>
- Contract location: <exact record path and section>
- Agreed delivery endpoint: <MERGED by default, or an explicitly limited user-requested endpoint with evidence>
- Policy reload checkpoint: <session/context boundary, files read, and material drift or none>
- Authorization reconciliation: <action-specific evidence links, current-session requirements checked, unresolved actions, and applicable expiry/drift conditions>
- Resume instruction: Restore deliver-ocb-change and read its applicable policies before dependent work; retain this exact record, revalidate OCB gates, and apply company commit rules even when generic execution defaults differ.

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
- Jira work start: <`date "+%Y-%m-%d"` stdout, derived tomorrow, pre-read status/date values and metadata, transition/edit operations or skips, and verified status/Start Date/Due Date>
- Jira Done transition: <pre-read status, Original Estimate, Time Spent and complete worklog count; transition ID/metadata; atomic worklog operation or skip reason; resulting status, Time Spent, worklog count and count delta; deferred owner; or not applicable>
- Bug Ready-to-test handoff: <Bug type, pre-read status/Reporter/assignee/Resolution, destination transition and allowed Resolution metadata, selected Resolution, assignment operation, verified Ready to test/Resolution/Reporter-assignee match, or not applicable>
- Epic base branch: <remote branch, SHA, existence and Epic mapping evidence, or unresolved>
- Development base: <Epic base for an independent ticket, or predecessor Jira key, remote branch, recorded SHA, dependency evidence, and ancestry for a stacked ticket>
- Stack order: <ordered predecessor Jira keys/branches/MRs, user-owned review order, merge prerequisites, or not applicable>
- Acceptance/design source: <source, not applicable with reason, or unresolved>
- New-ticket language and structure: <Vietnamese title/body; exact four headings; concise-content evidence; or not applicable>
- New-ticket estimate: <agent estimate at or below 3 hours, rationale, Jira field/unit, split/exception status, or not applicable>
- New-ticket assignee: <verified current Jira account identity and post-create assignment evidence, or not applicable>

### Repository Profile

- Profile: <path/version or bundled defaults>
- Domain roots and generated paths: <paths or unresolved>
- Evidence source: <paths or commands>
- Drift status: <clear or details>

### PR Size and Jira Work Split

- Effective maximum: <155 or stricter repository value and source>
- Measurement method: <LinearB value or additions plus deletions fallback>
- Expected touchpoints: <paths and change types>
- Pre-code estimate: <changed lines, supporting evidence, and confidence>
- Size classification: <handwritten/non-generated lines; qualifying spec/documentation lines; deterministic generated lines; exact paths>
- Indivisible-change exception: <not required, pending, or exact paths, split alternatives, indivisibility reason, separated measurements, regeneration evidence when applicable, checks, and review warning>
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
| Jira assignee matches authenticated Developer | Required | Hard, user-overridable | <authenticated account, current assignee, observation time> | Developer/User | Pending |
| Truthful Jira work-start status and dates | Required before implementation | Hard, user-overridable | <today command/result, tomorrow, pre/post status, Start Date, Due Date, metadata, mutations/skips, timestamp> | Developer/User | Pending |
| Intended sprint alignment | <Required when sprint delivery applies/Not applicable> | Hard, user-overridable | <sprint ID/name, dates, membership, or reason not applicable> | Developer/User | Pending |
| New Jira ticket contract | <Required for creation/Not applicable> | Hard | <Vietnamese title/body, four headings, estimate <= 3 hours with field/unit, current-account assignee, authorization, and post-create re-read> | User/Developer | Pending |
| New Subtask for post-completion bug | <Required/Not applicable> | Hard | <evidence or reason> | User/Developer | Pending |
| Domain acceptance source | <Required/Not applicable/Deferred> | <Hard/Advisory> | <evidence> | Product/Developer | Pending |
| Epic base branch before plan | Required | Hard | <remote existence, SHA, Epic mapping, or exact accepted fallback> | User/Developer | Pending |
| Development base and stacked ancestry | Required | Hard | <Epic base, or verified predecessor dependency, branch, SHA, ancestry, and ordered chain> | User/Developer | Pending |
| Working branch naming and MR traceability | Required | Hard | <evidence> | Developer | Pending |
| Commit message prefix | Required for commit | Hard | <evidence> | Developer | Pending |
| LinearB init commit before source mutation | Required | Hard | <working branch, first-ticket-owned-commit position, clean-index check, init commit SHA, and timestamp> | Developer | Pending |
| Working branch and LinearB init commit published | Required before implementation | Hard; not overridable | <verified remote/project, published branch, remote SHA equal to init commit SHA, and observation time> | Developer | Pending |
| Pre-MR empty commit | Required for user-requested MR creation | Hard | <clean index, marker SHA, parent SHA, timestamp, identical trees, and pushed source SHA; existing-MR reuse evidence when applicable> | Developer | Pending |
| Pre-code PR size assessment | Required before plan approval or source mutation | Hard unless exact excess has a verified indivisible-change exception | <estimate, functional Subtask recommendation, or indivisibility evidence> | Developer/User | Pending |
| Actual PR size assessment | Required before CODE_READY, post-implementation push, or MR creation | Hard unless exact excess has a verified indivisible-change exception | <measurement, base, classification, split assessment, and exception evidence> | Developer/User | Pending |
| Final activity traceability audit | Required before CODE_READY | Hard, user-overridable | <Jira key, assignee, status, sprint, branch, intended commits, remote/MR visibility, and unobservable legitimate work> | Developer/User | Pending |
| Indivisible-change exception evidence | <Required for unavoidable excess/Not applicable> | Hard | <exact paths, alternatives considered, smallest coherent scope, separated measurements, checks, and regeneration evidence when applicable> | Developer | Pending |
| Common repository checks | Required | Hard | <evidence> | Developer | Pending |
| Backend verification | <Required/Not applicable> | <Hard/Advisory> | <evidence> | Backend Developer | Pending |
| Frontend/UI verification | <Required/Not applicable> | <Hard/Advisory> | <evidence> | Frontend Developer | Pending |
| AI attribution | <Required/Not applicable/Deferred> | <Hard/Advisory> | <evidence> | Developer | Pending |
| Git delivery authorization | Required for listed actions before MR creation | Hard | <bundle> | User | Pending |
| Post-implementation delivery confirmation | Required after CODE_READY | Hard | <reviewed diff, checks, commit set/messages, push, MR source/target/title/body, and exact authorization> | User | Pending |
| Jira-only MR body and Jira MR-link comment | Required for MR creation | Hard, warning-first | <canonical Jira URL as entire initial MR body; canonical MR URL as one deduplicated Jira comment; post-write re-reads> | Developer/User | Pending |
| Jira Done transition and atomic worklog after MR creation | Required | Hard for the transition only, warning-first | <CODE_READY, MR repository/source/target, pre-read status/Original Estimate/Time Spent/worklogs, exact transition payload, post-read Done/Time Spent/worklog count> | Developer/User | Pending |
| Bug Ready-to-test Resolution and Reporter assignment | <Required when requested for Bug/Not applicable> | Hard, warning-first | <Bug verification, exact destination, allowed Resolution choices, selected Resolution, Reporter identity, resulting status/Resolution/assignee> | Developer/User | Pending |
| Platform-required MR approval | Required before merge | Hard; not overridable | <current GitLab approval state satisfying repository rules> | Reviewer/Developer | Pending |
| Merge readiness | Required before merge | Hard; not overridable | <source, target, SHA, checks, and GitLab mergeability> | Developer | Pending |
| Stacked predecessor merge order | <Required for stacked/Not applicable> | Hard; not overridable | <ordered predecessor merge evidence, refreshed ancestry, final diff, and rerun checks> | Developer | Pending |
| Developer merge | Required after platform-required approval | Hard | <merge commit/result evidence> | Developer | Pending |

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

- Epic base branch: <remote ref, SHA, repository, and Epic mapping source>
- Development base: <Epic base, or predecessor Jira key, remote branch, SHA, dependency evidence, and source>
- Working issue and source branch: <key and resolved branch>
- Work-activity context: <authenticated Jira account, current assignee, `date "+%Y-%m-%d"` result, verified In Progress/Start Date/Due Date, intended sprint and dates, and observation time>
- Branch ancestry: <Epic base -> ordered predecessor branches -> working issue evidence>
- Stacked review and merge order: <ordered Jira keys/MRs, user-owned review sequence, and merge prerequisites, or not applicable>
- Remote and GitLab project: <identity>
- MR target and title: <values>
- Initial MR body: <canonical absolute working Jira URL only>
- Jira MR-link comment: <canonical absolute MR URL, duplicate preflight, comment ID/evidence, or pending>
- Naming username and commit prefix: <source and value>
- AI attribution state: <mechanism, AI_ATTRIBUTION_UNAVAILABLE, or unresolved>

### Git Delivery Authorization

- Repository: <absolute path and GitLab project>
- Exact actions: <create branch, init commit, initial push, implementation commit, pre-MR empty commit, later push, create MR, add Jira MR-link comment; list only user-authorized actions; merge authorization is governed separately>
- Pre-implementation branch/init-commit/initial-push authorization: <current-session evidence or unresolved; required before source mutation>
- LinearB init commit: <working branch, first-ticket-owned-commit position, clean-index evidence, commit SHA and timestamp, or pending before IMPLEMENTING>
- LinearB observability: <published remote branch, remote SHA equal to init commit SHA, and observation time, or unresolved before IMPLEMENTING>
- Post-implementation authorization: <reviewed diff, proposed implementation commit set/messages, post-implementation empty commit, push, MR actions/targets, Jira MR-link comment, exact user evidence, or unresolved at CODE_READY>
- Pre-MR empty commit: <exact MR request authorizing the marker, message, clean-index evidence, SHA, parent SHA, timestamp, identical-tree verification, and pushed source SHA; or existing-MR reuse evidence>
- Epic base branch: <remote ref and SHA>
- Development base: <exact remote ref and recorded SHA>
- Working source branch: <exact branch>
- Remote and MR target: <exact values>
- Diff boundary: <exact paths or reviewed diff identity>
- Authorized: no

### Post-implementation Delivery Checkpoint

- Reviewed uncommitted diff: <repositories, branches, paths/hunks, size, and identity>
- Verification evidence: <checks and results>
- Proposed implementation commits: <exact paths per commit and messages>
- Pre-MR empty commit: <exact message and expected parent, or pending>
- Push and MR proposal: <remote, source, target, title, Jira-only body, Jira MR-link comment, and secondary effects>
- User confirmation: <exact authorized actions and targets, or pending at CODE_READY>

### Verification

- Common checks: <commands and expected results>
- Backend checks: <commands, contracts, data/security evidence, or applicability>
- Frontend checks: <commands, UI states, viewports/browsers, accessibility, visual and privacy evidence, or applicability>
- Actual results: <update during execution>
- Activity traceability audit: <Jira/branch/intended-commit/MR correlation, sprint and status re-read, unobservable legitimate activity, corrections, or scoped overrides>

### MR Evidence and Final Handoff

- MR URL/IID: <verified value or unavailable>
- Verified source/target/title/description: <evidence>
- Jira MR-link comment: <exact MR URL, duplicate preflight, verified comment evidence, or deferred owner>
- Jira Done evidence: <issue key, pre-read status/Original Estimate/Time Spent/complete worklog count, exact transition and atomic worklog decision, resulting Done/Time Spent/worklog count and observation time; deferred owner; or not applicable>
- Bug Ready-to-test evidence: <issue key/type, transition, selected Resolution, Reporter, resulting status/Resolution/assignee, observation time, or not applicable>
- Observable pipeline/check state: <state and observation time>
- Platform-required approval: <current approval state, applicable repository rule, and observation time>
- Merge evidence: <merge result, resulting SHA, and observation time, or pending>
- Risks and remaining owner: <details>
```

## Gate rules

Use `Required`, `Not applicable`, or `Deferred` for applicability; every non-required entry needs its reason or resume checkpoint and owner. Use only `Pending`, `Passed`, `Failed`, `Overridden`, `Deferred`, or `Not applicable` for state.

Classify skill-defined gates from higher-priority instructions, core policy, applicable domain policies, Jira acceptance, and repository rules. Reducible excess above the effective maximum remains blocked until independently deliverable functional Jira slices are recommended and refined. When the complete indivisible-change exception in [core-policy.md](core-policy.md) is verified, mark the PR-size gate `Not applicable — verified indivisible change` and pass the separate exception-evidence gate; never label an exception as ordinary size compliance. Every other `Hard` failure pauses only the dependent action until it passes or the user validly overrides it after warning. An override records the failed gate, missing evidence, affected action, warning, explicit risk acceptance and authorization, exact repository/state/target/scope, reason, and residual risk, and expires when relevant state changes. Mark an overridden gate `Overridden`, never `Passed`, and never describe missing evidence as verified.

If a failed gate leaves no executable value, the user must supply or explicitly select an exact value as part of the override. Risk acceptance alone does not authorize an unspecified Git mutation or let the agent guess a repository, issue, mode, path boundary, branch, remote, or MR target. Higher-priority instructions and safety constraints remain controlling and are not workflow gates.

Mode and path classification should be evidence-backed before `$plan` or mutation. If evidence is incomplete, pause and recommend the classification; continue only when the user explicitly authorizes an exact mode and path scope under a recorded override. In `mixed` mode, both domain policies apply to their classified paths and the union of applicable gates must pass or be individually overridden. Never downgrade `mixed` merely because one side has fewer changed lines.

Before source mutation, execute the bounded automatic Jira work-start procedure from [core-policy.md](core-policy.md), then require current Jira evidence for authenticated-Developer assignment, a truthful `In Progress`-type state, verified Start Date and Due Date, and exact intended sprint membership when sprint delivery applies. Each is warning-first and user-overridable: pause dependent implementation, state the observed mismatch and reporting risk, recommend the exact Jira correction, and continue only under an exact scoped override. A gate override never authorizes assignment, sprint, or any Jira mutation beyond the bounded automatic operations. After the init commit, publish the working branch and push the init commit to the verified remote, then verify the remote SHA. Local-only evidence cannot satisfy or override this pre-implementation gate. Never delay truthful completion or create artificial delivery objects to improve a metric.

The post-completion bug Subtask and Epic-base prerequisites use the warning-and-override procedure in [core-policy.md](core-policy.md). Resolve the development base independently: default to the Epic base, or use a verified predecessor working branch only when the user explicitly elects stacked execution before predecessor merge. A stacked contract must record the complete ordered dependency chain, fixed predecessor SHA used for branch creation, user-owned review order, and non-overridable predecessor-merge prerequisites. Before plan approval or source mutation, require the PR-size section to identify expected touchpoints, measurement method, effective maximum, a supported estimate, separated line classifications, and either functional Jira Subtask recommendations or complete indivisibility evidence for every oversized slice. For a stacked ticket, apply the assessment to its incremental diff from the development base, disclose the cumulative Epic-target diff, and require a final Epic-target measurement after predecessors merge. If the estimate, split assessment, or required exception evidence is unresolved, keep the workflow before `PLAN_APPROVED` and do not mutate source. Plan phases do not replace the requirement for a separately traceable Jira slice, branch, and PR. Except for the exact bounded automatic start and completion operations authorized by a delivery request under [core-policy.md](core-policy.md), Jira creation, editing, or status transition requires exact authorization through `$interact-with-jira`, followed by relationship or resulting-status verification as applicable. Git authorization is valid only when every operational field is exact and `Authorized: yes` is explicitly approved in the current plan context; plan approval or generic risk acceptance alone is insufficient. Working-branch creation, init-commit, and initial-push authorization must be resolved before entering `IMPLEMENTING`. After creating or verifying the working branch, require a clean index, create the LinearB init commit, publish the branch, push the commit, and verify the remote SHA before any source mutation; record the SHA, timestamp, remote, and observation. Keep implementation changes uncommitted through verification. Implementation-commit, later-push, and MR authorization remains pending until the user reviews and approves the exact post-implementation delivery proposal at `CODE_READY`.

Before creating any Jira work item, require the complete new-ticket contract from [core-policy.md](core-policy.md). The agent must produce and justify an estimate no greater than 3 hours, verify the Jira field and unit, and propose further functional Subtasks for work above that limit. The current authenticated Jira identity must be verified and used as assignee. Creation authorization must cover the exact Vietnamese title/body, issue type and hierarchy, estimate, and assignee; after creation, re-read every field and keep the gate failed if Jira omitted, normalized, or rejected any required value.

At `CODE_READY`, stop with the reviewed implementation diff uncommitted and present the exact commit, push, and MR proposal. The MR proposal must use only the canonical Jira URL as its initial body and include the one-comment Jira backlink operation. Do not perform any of those actions until the user explicitly confirms the enumerated repositories, branches, diff boundary, commit messages, remote, source/target, Jira-only MR body, and Jira comment target. Revalidate the proposal after drift.

## State updates

Use and evidence these transitions:

`MODE_UNRESOLVED` -> `MODE_RESOLVED` -> `JIRA_RESOLVED` -> `EPIC_BASE_RESOLVED` -> `PLAN_APPROVED` -> `IMPLEMENTING` -> `CODE_READY` -> `MR_PREPARED` -> `MR_READY` -> `MERGED`

- Enter `MODE_RESOLVED` after mode and path classification pass or receive an exact scoped override.
- Enter `JIRA_RESOLVED` after Jira identity, ancestry, applicable acceptance status, and any post-completion Subtask gate each pass or receive a scoped override.
- Enter `EPIC_BASE_RESOLVED` after the Epic-base gate passes or the user authorizes an exact fallback under a scoped override, and the separate development base plus any stacked ancestry are resolved.
- Enter `PLAN_APPROVED` only with an approved plan, complete contract, and a resolved pre-code size assessment for every planned Jira slice: compliant size, refined functional split, or `Not applicable — verified indivisible change` with its exception-evidence gate passed.
- Enter `IMPLEMENTING` after the current Jira slice's pre-code size assessment is resolved through compliance or a verified indivisible-change exception, authenticated-Developer assignment, truthful work-start status, applicable sprint alignment, and other source-mutation gates pass or receive scoped overrides, and, for Git-backed implementation, exact working-branch creation, init-commit, and initial-push authorization are recorded; the required LinearB init commit exists on each affected working branch with its SHA and timestamp captured; and the published remote branch is verified at that exact SHA.
- Enter `CODE_READY` after the uncommitted ticket-owned implementation diff from the resolved development base is measured and its size assessment is compliant or covered by a revalidated indivisible-change exception, the cumulative Epic-target diff is recorded for a stacked ticket, the final activity traceability audit passes or receives an allowed scoped override, and applicable acceptance criteria and common plus domain checks pass or receive allowed scoped overrides. Pause here for post-implementation delivery confirmation.
- After `CODE_READY`, once the MR exists with the expected repository, source, and target, execute the bounded Jira completion procedure from [core-policy.md](core-policy.md). Pre-read status, raw Original Estimate, Time Spent, the complete worklog list/count, and transition metadata. When the issue is not `Done` and has no worklog, add exactly one worklog equal to Original Estimate within the first `Done` transition request; never use a standalone worklog call or first try without it. Re-read and record final `Done`, Time Spent, worklog count, and any count delta. This does not require pipeline results, approval, mergeability, `MR_READY`, or merge evidence. If unavailable or unverifiable, defer only the Jira completion action with an owner and resume condition; do not duplicate a possibly applied worklog or block the independent review-and-merge path.
- Enter `MERGED` only after verifying that the exact MR satisfies current platform-required approval rules; do not add an approver-role, branch-owner, or separate confirmation gate. In every case verify the unchanged expected source and target, current MR SHA, required pipeline/check results, GitLab mergeability, explicit merge authorization, and successful Developer-performed merge. For a stacked ticket, first verify every predecessor merged into the Epic branch in order, refresh ancestry, update or rebase when repository policy requires, confirm the final Epic-target diff contains only the ticket-owned scope and is size-compliant or covered by a revalidated indivisible-change exception, and rerun affected checks.
- Use `WAITING_EXTERNAL` when external credentials, permissions, approval, required evidence, tools, or systems prevent the next step. Record prior state, operation, owner, resume condition, and next check.
- Resume only after revalidating stale evidence, mode/path classification, overrides, and authorization.

When `$execute` owns execution, use its technical `Status: Blocked` only when the same condition meets that skill's blocker definition. Otherwise retain the truthful delivery state and resume checkpoint.

Apply the outcome mapping in [Composition and resume](composition-and-resume.md): technical implementation completion, Jira Done, or a workflow-mode exit is never evidence of OCB merge completion. Preserve the actual delivery state, remaining gate owner, and resume condition at a pause or external wait.

## Readiness definitions

`MR_PREPARED` requires every applicable gate to be `Passed`, `Overridden`, or truthfully `Not applicable`; a size gate marked `Not applicable — verified indivisible change` must have its separate exception-evidence gate passed with separated measurements and review warning; exact intended working source and MR target; completed implementation; reviewed session diff; and an English proposed handoff. Every override must remain visible with its missing evidence and residual risk. Use this state when an external condition prevents authorized branch creation, push, or MR creation.

`MR_READY` additionally requires an authorized push; an existing MR in the exact GitLab repository with the exact source and Epic target; an initial MR body consisting only of the canonical Jira URL; and exactly one verified Jira comment containing only the canonical MR URL, unless an identical pre-existing comment was reused. Ignore later AI-review additions when validating the initial body contract. Ancestry, title, and observable checks must pass or have recorded overrides. A stacked MR may be `MR_READY` while predecessors remain open when its dependency chain, incremental and cumulative diffs, disclosure, and review order are recorded outside the Jira-only MR body; it is not merge-ready until the non-overridable predecessor merge-order gate passes. Missing evidence is never verified by override; an unauthorized, uncreated, or repository/target-ambiguous MR is never `MR_READY` because the required action itself is not exactly defined or authorized. An exactly authorized Jira `Done` or `Ready to test` transition may already have occurred after `CODE_READY` and verified MR creation; its outcome is recorded separately and does not depend on this readiness state or merge.

`MERGED` additionally requires the exact MR to satisfy current platform-required approval rules. It does not require proving an approver role or target-branch ownership. It always requires current required checks, a mergeable GitLab state, an unchanged expected source and target, explicit merge authorization, and evidence that the Developer's merge completed successfully. A stacked ticket additionally requires ordered predecessor merge evidence, refreshed ancestry, a clean ticket-owned final Epic-target diff and size result, and rerun affected checks. Platform approval, predecessor merge order, and merge-readiness gates are not overridable. Never self-approve, enable auto-merge, bypass controls, or merge ahead of a predecessor.

## Handoff format

Report in English:

1. Final workflow state and truthful reason
2. Delivery mode, per-domain paths, and classification evidence
3. Jira, acceptance/design, profile, Git baseline, authorization, and MR evidence
4. Implementation summary and exact session diff boundary
5. Common, backend, and frontend checks with results, exceptions, and residual risks
6. Preserved unrelated changes
7. Platform-required approval and Developer merge evidence, or the exact owner and resume condition when waiting
8. Next owner and actions, stopping before deployment or release
