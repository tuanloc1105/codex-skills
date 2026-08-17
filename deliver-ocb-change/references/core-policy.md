# OCB Delivery Core Policy

## Scope and precedence

Apply requirements in this order:

1. Higher-priority instructions and repository rules
2. A valid `.ocb/deliver-change.yaml` repository profile
3. This core policy and the applicable domain policy

Treat every **Hard** gate as warning-first unless labeled **Hard boundary**. After presenting missing evidence, affected action, risk, and recommended fix, accept an explicit user override only for the exact allowed action and record it. Never allow an override to violate higher-priority instructions, rely on an ambiguous repository or diff target, expose secrets, perform destructive recovery, bypass exact Git-action authorization, or cross an ownership boundary.

## Jira traceability and branch topology

Use these default branch patterns:

- `feature/{jira_id}_{username}_{task-slug}`
- `hotfix/{jira_id}_{username}_{task-slug}`

Use `{jira_id} {task-title}` as the default MR title. Put the Jira link, implementation context, verification, risks, and handoff in the description.

Resolve `username` from the current request, approved/current plan, or authoritative repository profile evidence, in that order. Never infer it from Git identity or email. Require a branch-safe, unambiguous value. Every working branch contains `{jira_id}` and `{username}`; every commit begins `{jira_id}_{username}_{task_name}` followed by descriptive commit content. Missing or mismatched naming evidence is a user-overridable **Hard** gate for each affected action.

Verify issue ancestry and Epic topology before planning or mutation:

- A Story or Task belongs directly to an Epic.
- A Subtask belongs to a direct-parent Task, and that Task belongs to the delivery Epic.
- A prose key mention is not relationship evidence.
- The Tech Lead creates the Epic base branch. Verify the exact existing remote branch before `$plan`; absence or ambiguity is a **Hard boundary**.
- Create every Story, Task, or Subtask working branch directly from the Epic base.
- Use the working branch as MR source and Epic base as target. Never substitute a parent issue branch or global integration branch.

For a bug discovered after Task completion, verify the original Task, completed state, and Epic. Through `$interact-with-jira`, create exactly one specifically authorized bug-fix Subtask under it, re-read all required fields and ancestry, and use the new key for a new Epic-based working branch and MR. Reusing the old branch, commits, or MR is outside this workflow.

Prefer a one-to-two-day change. More than 400 changed lines is an **Advisory** exception by default; explain review and rollback risk and propose a smaller slice when reasonable.

## Developer and Git boundary

Prepare a complete, reviewable MR with relevant evidence. Require exact, current authorization for working-branch creation, commit, push, and MR creation. Plan approval alone is not Git authorization. Never self-approve, merge, modify GitLab administration, deploy, release, perform Mobile delivery, or claim post-merge metrics.

Before `glab`, verify installed version, leaf help, authentication, repository, and identity. Use explicit source and target. Never use interactive defaults, auto-merge, or merge flags.

## Repository-aware AI attribution

Use only attribution explicitly permitted by higher-priority policy, repository instructions, or the profile. Never invent a trailer or hardcode a model identity. When no sanctioned mechanism exists, record `AI_ATTRIBUTION_UNAVAILABLE` as an **Advisory** limitation unless higher-priority policy makes it mandatory.

## Evidence rules

- Label assumptions and never promote them to verified facts.
- Record sources for mode, path classification, Jira identity and ancestry, repository profile, Git baseline, branch/remote/target, authorization, MR fields, and checks.
- Revalidate evidence after relevant changes.
- Treat profile conflicts as configuration drift requiring warning and an allowed scoped override before dependent mutation.
- Preserve unrelated changes; never stage, rewrite, discard, or include them in the delivery boundary.

## Out-of-scope ownership

Developer ownership ends at verified `MR_READY`. Review approval, merge, GitLab administration, deployment, release, DevSecOps, Service Operations, Mobile delivery, and post-merge reporting belong to other roles or workflows.
