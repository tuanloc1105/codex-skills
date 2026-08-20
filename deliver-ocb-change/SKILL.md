---
name: deliver-ocb-change
description: Deliver OCB Backend or web Frontend Developer work from Jira verification through approved planning, implementation, domain-specific verification, bounded Git delivery, Tech Lead approval, and developer-performed GitLab merge. Use for explicit `$deliver-ocb-change` requests, OCB backend, frontend, or mixed Jira implementation or plan execution, OCB-traceable GitLab MR preparation, and merge after verified Tech Lead approval. Do not use for generic coding advice, Mobile delivery, unrelated Jira administration, deployment, release, self-approval, or generic LinearB reporting.
---

# Deliver OCB Change

Guide an OCB Backend or Frontend Developer through an evidence-backed `MERGED` outcome. The Developer may proactively merge after verified Tech Lead approval; end before deployment, release, or post-merge measurement.

## Load the Contract

Before changing source or Git state, read:

- [Core policy](references/core-policy.md): shared Jira, Git, authorization, evidence, and ownership rules.
- [Repository profile](references/repository-profile.md): optional local overrides, mode routing, precedence, and drift handling.
- [Workflow contract](references/workflow-contract.md): required plan section, gates, states, authorization, and handoff format.

After resolving the delivery mode, read the complete applicable domain policy:

- `backend`: [Backend policy](references/backend-policy.md).
- `frontend`: [Frontend policy](references/frontend-policy.md).
- `mixed`: both policies; apply each rule to its affected scope and satisfy the union of applicable gates.

Apply precedence, warning-first gates, and override rules from the core and applicable domain policies exactly.

## Resolve Delivery Mode

Resolve exactly one mode before `$plan`, source mutation, or Git mutation: `backend`, `frontend`, or `mixed`.

Use evidence in this order:

1. Explicit value in the current user request.
2. Approved or current plan.
3. Valid `.ocb/deliver-change.yaml` profile.
4. Authoritative repository instructions.
5. Unambiguous target paths and requested implementation scope.

Do not silently classify from a repository name, framework guess, a single ambiguous file, or unrelated paths in a monorepo. Use `mixed` when the authorized implementation crosses backend and frontend boundaries. If evidence remains missing, ambiguous, or conflicting, pause dependent work, report the conflict, and recommend a mode and exact path scope. Continue when the user explicitly selects or accepts that exact classification under a recorded override.

Record the resolved mode, evidence source, affected roots, and per-path classification in the workflow contract. Re-resolve it when scope or diff boundaries drift. A missing or ambiguous mode is a **Hard** gate before `$plan` or mutation. Pause, warn, and recommend a mode; continue only when the user explicitly accepts the stated classification risk and authorizes that exact mode and scope.

## Run the Workflow

1. Begin at `MODE_UNRESOLVED`. Record the repository, initial Git status, staged and unstaged diff boundaries, Jira key if supplied, requested outcome, acceptance source when applicable, and all existing user changes.
2. Resolve delivery mode, then resolve `.ocb/deliver-change.yaml` as specified in the repository profile. Warn on configuration drift before dependent mutation.
3. Enter `MODE_RESOLVED`. Resolve the working Jira key from the request, approved or current plan, current branch, and repository evidence, in that order. If missing or ambiguous, pause, warn, and recommend an exact Jira context rather than silently guessing. With a unique key, use `$interact-with-jira` for minimal identity, issue, type, parent, relationship, and Epic verification, plus acceptance-criteria verification when required by the applicable domain policy. A Story or Task should belong directly to an Epic. A Subtask should have a direct-parent Task belonging to the same delivery Epic. Never treat prose mentioning a key as verified relationship evidence. For a bug found after Task completion, default to creating and re-reading exactly one authorized bug-fix Subtask. If any Jira gate remains unmet or the user requests reuse of an old delivery path, warn and continue only under an explicit scoped override that identifies the exact issue and Git path.
4. Resolve and verify the exact existing remote Epic base branch. The default expects a Tech-Lead-owned Epic branch and never silently infers or substitutes an integration branch. If evidence is missing or conflicts, pause, warn, and recommend the exact verification or branch fix. Continue only after the user explicitly accepts the risk and identifies or authorizes the exact fallback base and affected action. Read-only repository or design-source inspection may continue while unresolved.
5. After mode, Jira, and Epic-base gates pass or receive valid scoped overrides, assess every intended single-PR slice against the pre-code PR-size gate in the workflow contract. Prefer `$plan` with a complete `OCB Delivery Workflow Contract`. Do not approve the plan or mutate source while any slice estimate is unresolved or exceeds the effective maximum unless the excess consists only of qualifying spec/documentation source and deterministic generated artifacts and the scoped size-exception procedure in the core policy is complete. Otherwise, recommend a Jira work split and refine it until every independently deliverable slice has a supported compliant estimate, record the slices in the plan, and obtain explicit authorization before creating or editing Jira work items through `$interact-with-jira`. If the user explicitly directs execution without a plan after warning, record the scoped override for skipping the plan only; PR-size evidence and either compliance or a valid artifact exception remain mandatory. Do not create a separate lifecycle tracker.
6. Resolve branch username from the current request, approved/current plan, or authoritative repository evidence, in that order; never infer it from `git config user.name`. Before the first source mutation, obtain exact current-session authorization for working-branch creation and local incremental commits in every affected repository. Create or verify the working branch directly from the Epic base using `{jira_id}_{username}_{task-slug}`. The working branch is the MR source and Epic base is the target. Keep push and MR creation separately gated unless they were also explicitly authorized.
7. Implement only the approved scope on the working branch. Follow repository instructions and applicable domain policies, preserve unrelated changes, keep the change reviewable, and record verification evidence. Re-estimate after material scope drift and stop before writing the portion expected to exceed the effective maximum unless the scoped artifact exception remains valid for the exact excess paths and regenerated output; otherwise amend the execution record and recommend the next Jira slice. Commit each smallest complete verified unit at the cadence required by `$execute` or the active coding workflow; never accumulate a phase-sized working-tree diff and defer commit authorization until implementation is complete. For `mixed`, maintain a per-domain path boundary and run the union of applicable checks.
8. Push or create a working MR only with exact authorization for those actions. Reuse the verified username for the required `{jira_id}_{username}_{task_name}` commit prefix unless the user explicitly overrides that naming gate after warning. Before `glab`, verify its version, leaf-command help, authentication, repository target, and identity. Always provide explicit source and the exact resolved MR target; never use interactive defaults or auto-merge.
9. After `MR_READY`, verify that the approval is from a Tech Lead, the MR still has the exact expected source and target, required checks and GitLab mergeability pass, and no relevant evidence has gone stale. The Developer may then proactively perform the merge; Tech Lead approval is sufficient and the Tech Lead does not need to perform the merge. Never self-approve or bypass GitLab approval, protected-branch, pipeline, or mergeability controls.
10. Assign `CODE_READY`, `MR_PREPARED`, `MR_READY`, `MERGED`, or `WAITING_EXTERNAL` only from evidence and criteria in the workflow contract.

## Enforce Waiting and Ownership

- Treat every skill-defined gate as warning-first and user-overridable only under its applicable policy. Ordinary oversized handwritten changes remain blocked and must be split. The pre-code and actual PR-size gates may be `Overridden` only through the narrowly scoped spec/documentation and deterministic-generated-artifact exception in the core policy. On a gate failure, pause only the dependent action; state missing evidence, affected action, risk, and recommended fix. If the user explicitly accepts the risk and authorizes the exact action under the applicable policy, record the scoped override and continue. Revalidate it after state drift.
- An override never supplies missing operational details or mutation authorization: require an exact repository, target, scope, and action before acting. Never use an override to violate higher-priority instructions, guess among ambiguous targets, expose secrets, perform destructive recovery outside authorization, or claim missing evidence was verified.
- Use `WAITING_EXTERNAL` when credentials, permission, Tech Lead approval, tooling, required design evidence, or another external system prevents the next step after safe recovery is exhausted. A failed check or visual discrepancy is work to diagnose, not automatically an external wait.
- Never self-approve, bypass or change GitLab approval/protected-branch/merge settings, deploy, call LinearB deployment APIs, tag releases, perform Mobile delivery, or claim post-merge DORA results.
- At `MR_READY`, Tech Lead owns review and approval while the Developer owns the merge after that approval is verified. Distinguish verified evidence, accepted assumptions, overrides, and residual risks explicitly.

## Compose with Other Skills

- With `$discuss`, honor its mutation overlay and update its sole tracker.
- With `$plan`, place the complete `OCB Delivery Workflow Contract` in the plan.
- With `$execute`, keep the approved plan as execution truth, revalidate gates before mutation, obtain OCB branch and local-commit authorization before source mutation, follow `$execute`'s smallest-verified-unit commit cadence, and continue through `MERGED` after verified Tech Lead approval unless the workflow truthfully ends at `MR_PREPARED`, `MR_READY`, or documented `WAITING_EXTERNAL`.
- With `$interact-with-jira`, delegate all real Jira behavior and safety rules to that skill.
- With a UI design or design-to-code skill, use it only for approved frontend scope; this workflow remains authoritative for Jira, Git, evidence, and ownership.

## Report the Handoff

Use the format in [workflow-contract.md](references/workflow-contract.md). State the final workflow state, mode and path classification, evidence, checks, domain verification, exceptions, preserved unrelated changes, and next owner. Never describe `MR_PREPARED` as `MR_READY`.
