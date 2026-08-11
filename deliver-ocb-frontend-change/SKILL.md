---
name: deliver-ocb-frontend-change
description: Deliver OCB Frontend Developer work from Jira verification through approved planning, implementation, UI-focused verification, bounded Git delivery, and a verified GitLab merge request handoff. Use for explicit `$deliver-ocb-frontend-change` requests, OCB web frontend Jira implementation or plan execution, and OCB-traceable GitLab MR preparation. Do not use for generic frontend advice, backend or Mobile delivery, unrelated Jira administration, deployment, release, merge, approval, or generic LinearB reporting.
---

# Deliver OCB Frontend Change

Guide an OCB Frontend Developer to an evidence-backed `MR_READY` handoff. End before approval, merge, deployment, release, or post-merge measurement.

## Load the Contract

Read all three references before changing source or Git state:

- [Frontend policy](references/frontend-policy.md): R1, the Developer boundary of R2, repository-aware R4, UI evidence, and role limits.
- [Repository profile](references/repository-profile.md): optional local overrides, precedence, and drift handling.
- [Workflow contract](references/workflow-contract.md): required plan section, gates, evidence, authorization, and handoff format.

Apply the precedence, warning-first gate, and override rules in the frontend policy exactly.

## Run the Workflow

1. Begin intake at `JIRA_UNVERIFIED`. Record the repository, initial Git status, staged and unstaged diff boundaries, Jira key if supplied, requested outcome, UI acceptance source, and all existing user changes. Apply the authoritative transitions and readiness definitions in the workflow contract.
2. Resolve `.ocb/deliver-frontend-change.yaml` as specified in the repository profile. Warn when it conflicts with observed repository evidence and apply the gate-override procedure before dependent mutation.
3. Enter `JIRA_UNVERIFIED`. Resolve the working Jira key from the request, approved or current plan, current branch, and repository evidence, in that order. If it remains missing or ambiguous, warn the user, ask for the missing value or an explicit override, and do not guess among keys or multiple valid site/account identities. When a unique key is available, use `$interact-with-jira` for minimal read-only identity, issue, type, parent/relationship, Epic, and acceptance-criteria verification. A Story or Task must belong directly to an Epic. A Subtask must have a direct-parent Task, and that Task must belong to the same Epic used for delivery. Do not treat prose mentioning a key as relationship evidence or guess among multiple candidate Epics. When the requested change fixes a bug discovered after a Task is complete, verify the completed Task and invoke `$interact-with-jira` to create exactly one new bug-fix Subtask under it using the user's exact authorized summary and fields. Re-read the created Subtask, adopt its key as the working Jira key, and never reuse the completed Task's old branch, commits, or MR for the fix.
4. Resolve the Epic base branch from explicit request evidence or authoritative repository evidence and verify that the exact remote branch already exists in the target repository. The Epic base branch is created and owned by the Tech Lead; never create it, infer it from an unrelated integration branch, or substitute another branch. Permit discussion and read-only repository or design-source inspection while Jira or the Epic base branch is unverified, but do not begin `$plan`, create a plan artifact, mutate source, or mutate Git. Missing or ambiguous Epic base branch evidence is a non-overridable ownership prerequisite; wait for the Tech Lead or user to supply and create the exact branch.
5. After Jira and the Epic base branch are verified, prefer `$plan` and an approved plan containing the complete `Frontend Workflow Contract` before implementation. If the user explicitly directs execution without a plan after receiving the warning, record the override in the contract or handoff and continue within the authorized scope. The Epic-base prerequisite itself cannot be overridden. Do not create a separate lifecycle tracker.
6. Before implementation, create or verify the working branch directly from the verified Epic base branch, whether the working issue is a Story, Task, or Subtask. Treat the working branch as the MR source and the Epic base branch as the MR target. Require exact authorization for working-branch creation and revalidate the exact `Epic base -> working issue` ancestry before dependent mutation.
7. Implement only the approved Frontend Developer scope on the working branch. Follow the repository's design system, component, state, data-fetching, accessibility, localization, security, and testing conventions. Preserve unrelated changes, keep the change reviewable, and record applicable viewport/browser and UI evidence. Revalidate when the repository, Epic base or working branch, remote, target, diff boundary, Jira acceptance criteria, or design source drifts.
8. Perform commit, push, or working-MR creation only with exact authorization for those Git delivery actions. Resolve `username` from an explicit value in the current request, the approved or current plan, or authoritative repository policy/profile evidence, in that order. Do not infer it from `git config user.name`. If it remains missing, ambiguous, or conflicting, warn and ask for the value or an explicit commit-prefix override. Start every commit message with `{jira_id}_{username}_{task_name}` followed by the descriptive commit content unless the user explicitly overrides that gate after the warning. Before invoking `glab`, verify its installed version, leaf-command help, authentication, repository target, and identity. Use explicit source and target arguments. Every Story, Task, or Subtask working MR targets the verified Epic base branch. Never use interactive defaults, auto-merge, or merge flags.
9. Assign `CODE_READY`, `MR_PREPARED`, `MR_READY`, or `WAITING_EXTERNAL` only from the evidence and criteria in the workflow contract.

## Enforce Waiting and Ownership

- Treat workflow gates as warning-first and user-overridable. For each unmet gate, state the missing evidence, affected action, risk, and recommended fix. Continue when the user explicitly accepts that risk and authorizes the exact affected action; record who overrode what, why, and the remaining risk. An override is scoped to the current repository, state, and action and expires when any of them changes.
- Never use a gate override to violate higher-priority instructions, guess an ambiguous repository/diff target, expose secrets, perform destructive recovery, or cross the ownership boundaries below. Git mutations still require explicit authorization for the exact action and scope.

- Use workflow state `WAITING_EXTERNAL` when credentials, permission, approval, tooling, a required design source, or an external system prevents the next required step after safe in-scope recovery is exhausted. When executing through `$execute`, use its technical `Status: Blocked` only when the same condition satisfies that skill's genuine-blocker definition; otherwise remain `MR_PREPARED` and document the exact resume checkpoint.
- Treat a failed check or visual discrepancy as work to diagnose, not automatically as `WAITING_EXTERNAL`.
- Never self-approve, merge, change GitLab approval/protected-branch/merge settings, deploy, call LinearB deployment APIs, tag a release, perform Backend or Mobile delivery, or claim post-merge DORA results.
- Hand off `MR_READY` to Reviewer/Lead ownership. Report observed evidence without claiming an action or state that was not verified.

## Compose with Other Skills

- With `$discuss`, honor its mutation overlay and update its sole discussion tracker. Do not create the workflow contract as a third tracker.
- With `$plan`, place the complete `Frontend Workflow Contract` in the plan and preserve unresolved gates as warnings or explicit override decisions.
- With `$execute`, treat the approved plan as execution truth, revalidate its gates before mutation, update the same contract, and stop at `MR_READY`, `MR_PREPARED`, or documented `WAITING_EXTERNAL`.
- With `$interact-with-jira`, delegate all real Jira CLI behavior and safety rules to that skill. Keep reads minimal and never infer Jira mutation authority from this workflow.
- With a UI design or design-to-code skill, use it only for the approved visual scope. This workflow remains authoritative for Jira, Git delivery, evidence, and ownership gates.

## Report the Handoff

Use the handoff format in [workflow-contract.md](references/workflow-contract.md). State the final workflow state, evidence, checks, UI verification, advisory exceptions, preserved unrelated changes, and the next owner. Never describe `MR_PREPARED` as `MR_READY`.
