# OCB Backend Delivery Policy

## Scope and precedence

Apply this policy only to Backend Developer work. Resolve requirements in this order:

1. Higher-priority instructions and repository rules
2. A valid `.ocb/deliver-backend-change.yaml` repository profile
3. The defaults in this reference

Treat every gate labeled **Hard** as warning-first. By default, do not perform its dependent action until it passes. After presenting the missing evidence, affected action, risk, and recommended fix, accept an explicit user override for that exact action and record it. Do not allow an override to violate higher-priority instructions, rely on an ambiguous repository or diff target, expose secrets, perform destructive recovery, bypass exact Git-action authorization, or cross the ownership boundaries in this policy.

## R1: Jira traceability and work slicing

Use these default branch patterns:

- `feature/{jira_id}_{username}_{task-slug}`
- `hotfix/{jira_id}_{username}_{task-slug}`

Use `{jira_id} {task-title}` as the default MR title pattern. Put the Jira link and implementation context in the MR description.

Start every commit message with `{jira_id}_{username}_{task_name}` followed by the descriptive commit content. Resolve `username` from an explicit value in the current request, the approved or current plan, or authoritative repository policy/profile evidence, in that order. Do not infer it from `git config user.name`, an email address, or another unverified identity source. If it remains missing, ambiguous, or conflicting, warn the user and ask for the value or an explicit override. Resolve all three prefix values before committing by default; a missing, guessed, or mismatched value is a user-overridable **Hard** gate for the commit.

Verify the issue ancestry before source or Git mutation:

- A Story belongs to an Epic.
- A Task belongs to a Story that belongs to an Epic.
- A Subtask belongs to a Task whose ancestry reaches a Story and Epic.
- Create the branch from the smallest issue that has a verifiable output and fits the intended work slice.

Jira identity and hierarchy are **Hard** gates. Branch naming, commit naming, MR naming, and Jira traceability are **Hard** gates for Git delivery.

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
