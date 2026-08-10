---
name: deliver-ocb-backend-change
description: Deliver OCB Backend Developer work from Jira verification through approved planning, implementation, verification, bounded Git delivery, and a verified GitLab merge request handoff. Use for explicit `$deliver-ocb-backend-change` requests, OCB backend Jira implementation or plan execution, and OCB-traceable GitLab MR preparation. Do not use for generic backend advice, unrelated Jira administration, Mobile delivery, deployment, release, merge, approval, or generic LinearB reporting.
---

# Deliver OCB Backend Change

Guide an OCB Backend Developer to an evidence-backed `MR_READY` handoff. End before approval, merge, deployment, release, or post-merge measurement.

## Load the Contract

Read all three references before changing source or Git state:

- [Backend policy](references/backend-policy.md): R1, the Developer boundary of R2, repository-aware R4, and role limits.
- [Repository profile](references/repository-profile.md): optional local overrides, precedence, and drift handling.
- [Workflow contract](references/workflow-contract.md): required plan section, gates, evidence, authorization, and handoff format.

Apply the precedence, warning-first gate, and override rules in the backend policy exactly.

## Run the Workflow

1. Begin intake at `JIRA_UNVERIFIED`. Record the repository, initial Git status, staged and unstaged diff boundaries, Jira key if supplied, requested outcome, and all existing user changes. Apply the authoritative transitions and readiness definitions in the workflow contract.
2. Resolve `.ocb/deliver-backend-change.yaml` as specified in the repository profile. Warn when it conflicts with observed repository evidence and apply the gate-override procedure before dependent mutation.
3. Enter `JIRA_UNVERIFIED`. Resolve the working Jira key from the request, approved or current plan, current branch, and repository evidence, in that order. If it remains missing or ambiguous, warn the user, ask for the missing value or an explicit override, and do not guess among keys or multiple valid site/account identities. When a unique key is available, use `$interact-with-jira` for minimal read-only identity, issue, type, parent/relationship, and Epic verification. For a Task, resolve exactly one representative Story through a supported direct-parent relationship or an explicit Jira relationship whose verified semantics establish that the Task develops or implements that Story; require the Task and Story to belong to the same Epic. For a Subtask, require a direct-parent Task and resolve that Task's representative Story by the same rule. Do not treat prose mentioning a key as relationship evidence or guess among multiple candidate Stories.
4. While Jira is unverified, permit discussion, read-only repository inspection, and planning. Before source or Git mutation, warn about every unmet gate and request an explicit override for the exact affected actions.
5. Prefer `$plan` and an approved plan containing the complete `Backend Workflow Contract` before implementation. If the user explicitly directs execution without it after receiving the warning, record the override in the contract or handoff and continue within the authorized scope. Do not create a separate lifecycle tracker.
6. Before implementation, create or verify the representative issue branch, then create or verify the working branch from it. Create the representative Story branch from `Pilot`. Create a Task branch from its verified representative Story branch, whether that Jira relationship is a supported parent or an explicit development/implementation relationship. For a Subtask, reuse its direct-parent Task branch as the representative branch; if absent, first create that Task branch from its verified representative Story branch. A working branch may later be reused as the representative branch for direct children. Treat the working branch as the MR source and its representative issue branch as the MR target. Require exact authorization for every needed branch creation, and revalidate the complete applicable `Pilot -> Story -> Task -> Subtask` branch ancestry before dependent mutation.
7. Implement only the approved Backend Developer scope on the working branch. Apply repository coding instructions, preserve unrelated changes, keep the change reviewable, and record verification evidence. Revalidate when the repository, base, representative or working branch, remote, target, or diff boundary drifts.
8. Perform commit, push, working-MR creation, or Story-roll-up-MR creation only with exact authorization for those Git delivery actions. Resolve `username` from an explicit value in the current request, the approved or current plan, or authoritative repository policy/profile evidence, in that order. Do not infer it from `git config user.name`. If it remains missing, ambiguous, or conflicting, warn and ask for the value or an explicit commit-prefix override. Start every commit message with `{jira_id}_{username}_{task_name}` followed by the descriptive commit content unless the user explicitly overrides that gate after the warning. Before invoking `glab`, verify its installed version, leaf-command help, authentication, repository target, and identity. Use explicit source and target arguments. A Task/Subtask working MR targets its representative issue branch and never targets `Pilot`. After all required Task changes are externally approved and verified as merged into the Story branch, a separately authorized Story roll-up MR may use that Story branch as source and `Pilot` as target. Never use interactive defaults, auto-merge, or merge flags.
9. Assign `CODE_READY`, `MR_PREPARED`, `MR_READY`, or `WAITING_EXTERNAL` only from the evidence and criteria in the workflow contract.

## Enforce Waiting and Ownership

- Treat workflow gates as warning-first and user-overridable. For each unmet gate, state the missing evidence, affected action, risk, and recommended fix. Continue when the user explicitly accepts that risk and authorizes the exact affected action; record who overrode what, why, and the remaining risk. An override is scoped to the current repository, state, and action and expires when any of them changes.
- Never use a gate override to violate higher-priority instructions, guess an ambiguous repository/diff target, expose secrets, perform destructive recovery, or cross the ownership boundaries below. Git mutations still require explicit authorization for the exact action and scope.

- Use workflow state `WAITING_EXTERNAL` when credentials, permission, approval, tooling, or an external system prevents the next required step after safe in-scope recovery is exhausted. When executing through `$execute`, use its technical `Status: Blocked` only when the same condition satisfies that skill's genuine-blocker definition; otherwise remain `MR_PREPARED` and document the exact resume checkpoint.
- Treat a failed check as work to diagnose, not automatically as `WAITING_EXTERNAL`.
- Never self-approve, merge, change GitLab approval/protected-branch/merge settings, deploy, call LinearB deployment APIs, tag a release, perform Mobile delivery, or claim post-merge DORA results.
- Hand off `MR_READY` to Reviewer/Lead ownership. Report observed evidence without claiming an action or state that was not verified.

## Compose with Other Skills

- With `$discuss`, honor its mutation overlay and update its sole discussion tracker. Do not create the workflow contract as a third tracker.
- With `$plan`, place the complete `Backend Workflow Contract` in the plan and preserve unresolved gates as warnings or explicit override decisions.
- With `$execute`, treat the approved plan as execution truth, revalidate its gates before mutation, update the same contract, and stop at `MR_READY`, `MR_PREPARED`, or documented `WAITING_EXTERNAL`.
- With `$interact-with-jira`, delegate all real Jira CLI behavior and safety rules to that skill. Keep reads minimal and never infer Jira mutation authority from this workflow.

## Report the Handoff

Use the handoff format in [workflow-contract.md](references/workflow-contract.md). State the final workflow state, evidence, checks, advisory exceptions, preserved unrelated changes, and the next owner. Never describe `MR_PREPARED` as `MR_READY`.
