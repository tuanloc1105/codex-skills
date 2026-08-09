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

Apply the precedence and hard-gate rules in the frontend policy exactly.

## Run the Workflow

1. Begin intake at `JIRA_UNVERIFIED`. Record the repository, initial Git status, staged and unstaged diff boundaries, Jira key if supplied, requested outcome, UI acceptance source, and all existing user changes. Apply the authoritative transitions and readiness definitions in the workflow contract.
2. Resolve `.ocb/deliver-frontend-change.yaml` as specified in the repository profile. Stop before mutation when it conflicts with observed repository evidence.
3. Enter `JIRA_UNVERIFIED`. Resolve the Jira key from the request, approved or current plan, current branch, and repository evidence, in that order. If it remains missing or ambiguous, ask the user and prohibit dependent mutation. When a unique key is available, use `$interact-with-jira` for minimal read-only identity, issue, type, parent, Epic, and acceptance-criteria verification. Never guess among keys or multiple valid site/account identities.
4. While Jira is unverified, permit discussion, read-only repository and design-source inspection, and planning only. Prohibit source edits, branch creation, Git mutation, push, and MR creation.
5. After Jira verification, use `$plan` and require an approved plan containing the complete `Frontend Workflow Contract` before implementation. Do not create a separate lifecycle tracker.
6. Implement only the approved Frontend Developer scope. Follow the repository's design system, component, state, data-fetching, accessibility, localization, security, and testing conventions. Preserve unrelated changes, keep the change reviewable, and record applicable viewport/browser and UI evidence. Revalidate when the repository, branch, remote, target, diff boundary, Jira acceptance criteria, or design source drifts.
7. Perform commit, push, or MR creation only when the plan contains an exact authorized Git delivery bundle that remains valid under the workflow contract. Before invoking `glab`, verify its installed version, leaf-command help, authentication, repository target, and identity. Use explicit arguments; never use interactive defaults, auto-merge, or merge flags.
8. Assign `CODE_READY`, `MR_PREPARED`, `MR_READY`, or `WAITING_EXTERNAL` only from the evidence and criteria in the workflow contract.

## Enforce Waiting and Ownership

- Use workflow state `WAITING_EXTERNAL` when credentials, permission, approval, tooling, a required design source, or an external system prevents the next required step after safe in-scope recovery is exhausted. When executing through `$execute`, use its technical `Status: Blocked` only when the same condition satisfies that skill's genuine-blocker definition; otherwise remain `MR_PREPARED` and document the exact resume checkpoint.
- Treat a failed check or visual discrepancy as work to diagnose, not automatically as `WAITING_EXTERNAL`.
- Never self-approve, merge, change GitLab approval/protected-branch/merge settings, deploy, call LinearB deployment APIs, tag a release, perform Backend or Mobile delivery, or claim post-merge DORA results.
- Hand off `MR_READY` to Reviewer/Lead ownership. Report observed evidence without claiming an action or state that was not verified.

## Compose with Other Skills

- With `$discuss`, honor its mutation overlay and update its sole discussion tracker. Do not create the workflow contract as a third tracker.
- With `$plan`, place the complete `Frontend Workflow Contract` in the plan and preserve unresolved hard gates as explicit blocking questions.
- With `$execute`, treat the approved plan as execution truth, revalidate its gates before mutation, update the same contract, and stop at `MR_READY`, `MR_PREPARED`, or documented `WAITING_EXTERNAL`.
- With `$interact-with-jira`, delegate all real Jira CLI behavior and safety rules to that skill. Keep reads minimal and never infer Jira mutation authority from this workflow.
- With a UI design or design-to-code skill, use it only for the approved visual scope. This workflow remains authoritative for Jira, Git delivery, evidence, and ownership gates.

## Report the Handoff

Use the handoff format in [workflow-contract.md](references/workflow-contract.md). State the final workflow state, evidence, checks, UI verification, advisory exceptions, preserved unrelated changes, and the next owner. Never describe `MR_PREPARED` as `MR_READY`.
