# OCB Backend Delivery Policy

## Scope and precedence

Apply this policy only to Backend Developer work. Resolve requirements in this order:

1. Higher-priority instructions and repository rules
2. A valid `.ocb/deliver-backend-change.yaml` repository profile
3. The defaults in this reference

Treat every gate labeled **Hard** as warning-first. By default, do not perform its dependent action until it passes. After presenting the missing evidence, affected action, risk, and recommended fix, accept an explicit user override for that exact action and record it. Do not allow an override to violate higher-priority instructions, rely on an ambiguous repository or diff target, expose secrets, perform destructive recovery, bypass exact Git-action authorization, or cross the ownership boundaries in this policy.

## R1: Jira traceability and work slicing

Use these default branch patterns:

- `feature/{jira_id}_{task-slug}`
- `hotfix/{jira_id}_{task-slug}`

Use `{jira_id} {task-title}` as the default MR title pattern. Put the Jira link and implementation context in the MR description.

Start every commit message with `{jira_id}_{username}_{task_name}` followed by the descriptive commit content. Resolve `username` from an explicit value in the current request, the approved or current plan, or authoritative repository policy/profile evidence, in that order. Do not infer it from `git config user.name`, an email address, or another unverified identity source. If it remains missing, ambiguous, or conflicting, warn the user and ask for the value or an explicit override. Resolve all three prefix values before committing by default; a missing, guessed, or mismatched value is a user-overridable **Hard** gate for the commit.

Verify the issue ancestry and Epic-based branch topology before planning, source mutation, or Git mutation:

- A Story belongs to an Epic.
- A Task belongs to an Epic at the same Jira hierarchy level as a Story; a Task does not require a representative Story.
- A Subtask belongs to a direct-parent Task, and that Task belongs to the delivery Epic. The Jira parent relationship does not make the Task branch a Git base or MR target.
- The working issue may be a Story, Task, or Subtask with verified ancestry to exactly one delivery Epic. Do not use a description-only key mention as relationship evidence.
- The Tech Lead creates the Epic base branch. Resolve and verify that exact remote branch before `$plan` begins. Its absence or ambiguity is a non-overridable ownership prerequisite: do not create it, substitute `Pilot` or another integration branch, or create a plan artifact while waiting.
- Create every Story, Task, or Subtask working branch directly from the verified Epic base branch.
- Implement and commit only on the current working branch. Create its MR with that branch as source and the Epic base branch as target. Do not target a Story, Task, Subtask, `Pilot`, or another integration branch.

When a bug is discovered after a Task is complete, treat the fix as new traceable work rather than a continuation of the completed delivery:

- Verify the original Task, its completed state, and its Epic before planning the fix.
- Invoke `$interact-with-jira` and follow its specific-target write rules to create exactly one new bug-fix Subtask whose direct parent is the completed Task. The bug-fix request may authorize that one creation, but do not invent an ambiguous summary, project, parent, issue type, or required field.
- Re-read the created Subtask and use its key, fields, parent, and Epic ancestry as the new working Jira evidence.
- Create a new working branch directly from the verified Epic base branch and target the Epic base branch with the new MR. Never check out, reopen, append commits to, force-update, or create another MR from the completed Task's old working branch.

Jira identity and Epic ancestry are **Hard** gates. For a post-completion bug fix, verified creation and re-read of the new Subtask are **Hard** gates before `$plan`. Verified existence of the Tech-Lead-owned Epic base branch is a **Hard boundary** before `$plan`. The exact `Epic base -> working issue` branch ancestry, branch naming, commit naming, Epic-base MR target, and Jira traceability are **Hard** gates for Git delivery.

Prefer a change that can be completed in one to two working days. Treat an MR above 400 changed lines as an **Advisory** exception: explain review and rollback risk and propose a smaller split when reasonable. Do not block an otherwise valid delivery solely because of line count.

## R2: Developer boundary

Prepare a complete, reviewable MR with relevant verification evidence. Do not:

- Self-approve or merge the MR
- Change approval rules, protected branches, merge methods, squash settings, or fast-forward settings
- Repair incompatible repository administration as part of Backend Developer delivery

If repository evidence shows an incompatible merge policy, report it for Reviewer/Lead ownership and keep the workflow at the truthful pre-merge state.

## R4: Repository-aware AI attribution

Resolve AI attribution from higher-priority policy, repository instructions, or the repository profile. Use only a mechanism explicitly permitted there.

Never add `Co-Authored-By`, `Co-Worker`, or a similar trailer when repository policy prohibits it. Never hardcode a model identity for work produced by another tool.

When no sanctioned mechanism exists, record `AI_ATTRIBUTION_UNAVAILABLE` as an **Advisory** measurement limitation. Do not block backend delivery unless a higher-priority policy explicitly makes attribution mandatory.

## Evidence rules

- Label assumptions as assumptions; do not promote them to verified facts.
- Record the source for Jira identity, ancestry, repository profile, Git baseline, branch/remote/target, MR fields, and pipeline/check state.
- Revalidate evidence after relevant state changes.
- Treat profile-versus-repository conflict as configuration drift; warn before dependent mutation and require an explicit scoped override unless higher-priority instructions prohibit proceeding.
- Preserve unrelated working-tree changes; never stage, rewrite, discard, or include them in the delivery boundary.

## Out-of-scope ownership

Backend Developer ownership ends at verified `MR_READY`. The following belong to other roles or workflows:

- Review approval and merge execution
- GitLab approval, branch protection, and merge-policy administration
- R3 deployment API integration and all deployment activity
- R5 release branches, release tags, and release notes
- DevSecOps, Service Operations, Mobile delivery, and post-merge DORA or LinearB reporting
