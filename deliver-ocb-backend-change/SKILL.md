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

Apply the precedence and hard-gate rules in the backend policy exactly.

## Run the Workflow

1. Begin intake at `JIRA_UNVERIFIED`. Record the repository, initial Git status, staged and unstaged diff boundaries, Jira key if supplied, requested outcome, and all existing user changes. Apply the authoritative transitions and readiness definitions in the workflow contract.
2. Resolve `.ocb/deliver-backend-change.yaml` as specified in the repository profile. Stop before mutation when it conflicts with observed repository evidence.
3. Enter `JIRA_UNVERIFIED`. Resolve the Jira key from the request, approved or current plan, current branch, and repository evidence, in that order. If it remains missing or ambiguous, ask the user and prohibit dependent mutation. When a unique key is available, use `$interact-with-jira` for minimal read-only identity, issue, type, parent, and Epic verification. Never guess among keys or multiple valid site/account identities.
4. While Jira is unverified, permit discussion, read-only repository inspection, and planning only. Prohibit source edits, branch creation, Git mutation, push, and MR creation.
5. After Jira verification, use `$plan-mode` and require an approved plan containing the complete `Backend Workflow Contract` before implementation. Do not create a separate lifecycle tracker.
6. Implement only the approved Backend Developer scope. Apply repository coding instructions, preserve unrelated changes, keep the change reviewable, and record verification evidence. Revalidate when the repository, branch, remote, target, or diff boundary drifts.
7. Perform commit, push, or MR creation only when the plan contains an exact authorized Git delivery bundle that remains valid under the workflow contract. Before invoking `glab`, verify its installed version, leaf-command help, authentication, repository target, and identity. Use explicit arguments; never use interactive defaults, auto-merge, or merge flags.
8. Assign `CODE_READY`, `MR_PREPARED`, `MR_READY`, or `WAITING_EXTERNAL` only from the evidence and criteria in the workflow contract.

## Enforce Waiting and Ownership

- Use workflow state `WAITING_EXTERNAL` when credentials, permission, approval, tooling, or an external system prevents the next required step after safe in-scope recovery is exhausted. When executing through `$execute-plan`, use its technical `Status: Blocked` only when the same condition satisfies that skill's genuine-blocker definition; otherwise remain `MR_PREPARED` and document the exact resume checkpoint.
- Treat a failed check as work to diagnose, not automatically as `WAITING_EXTERNAL`.
- Never self-approve, merge, change GitLab approval/protected-branch/merge settings, deploy, call LinearB deployment APIs, tag a release, perform Mobile delivery, or claim post-merge DORA results.
- Hand off `MR_READY` to Reviewer/Lead ownership. Report observed evidence without claiming an action or state that was not verified.

## Compose with Other Skills

- With `$discussion-only`, honor its mutation overlay and update its sole discussion tracker. Do not create the workflow contract as a third tracker.
- With `$plan-mode`, place the complete `Backend Workflow Contract` in the plan and preserve unresolved hard gates as explicit blocking questions.
- With `$execute-plan`, treat the approved plan as execution truth, revalidate its gates before mutation, update the same contract, and stop at `MR_READY`, `MR_PREPARED`, or documented `WAITING_EXTERNAL`.
- With `$interact-with-jira`, delegate all real Jira CLI behavior and safety rules to that skill. Keep reads minimal and never infer Jira mutation authority from this workflow.

## Report the Handoff

Use the handoff format in [workflow-contract.md](references/workflow-contract.md). State the final workflow state, evidence, checks, advisory exceptions, preserved unrelated changes, and the next owner. Never describe `MR_PREPARED` as `MR_READY`.
