# OCB Delivery Core Policy

## Scope and precedence

Apply requirements in this order:

1. Higher-priority instructions and repository rules
2. A valid `.ocb/deliver-change.yaml` repository profile
3. This core policy and the applicable domain policy

Treat every skill-defined gate as warning-first and user-overridable under the applicable policy. The pre-code and actual PR-size gates use the narrower artifact-exception policy defined below; they are not generally overridable. When a gate fails, pause only its dependent action and present the missing evidence, affected action, risk, and recommended fix. If the user explicitly accepts the residual risk and authorizes the exact action under the applicable policy, record the gate as `Overridden` and continue. Never treat an override as proof that missing evidence was verified.

An override is valid only for the recorded repository, state, target, scope, and action and expires when any changes. It cannot violate higher-priority instructions, choose among still-ambiguous targets, expose secrets, authorize unspecified Git mutations, or permit destructive recovery outside the user's exact authorization. When a gate lacks an executable value, such as a base branch or delivery mode, require the user to select or authorize an exact value as part of the override; never guess it.

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
- The default base is the exact existing Tech-Lead-owned Epic branch. Missing existence, mapping, SHA, or ownership evidence is a **Hard** gate before `$plan`; after warning, the user may explicitly authorize an exact fallback base or exact branch action and accept the recorded topology risk.
- Create every Story, Task, or Subtask working branch directly from the Epic base.
- Use the working branch as MR source and Epic base as target. Never substitute a parent issue branch or global integration branch.

For a bug discovered after Task completion, verify the original Task, completed state, and Epic. By default, use `$interact-with-jira` to create exactly one specifically authorized bug-fix Subtask under it, re-read all required fields and ancestry, and use the new key for a new Epic-based working branch and MR. Missing Subtask evidence or reuse of an old branch, commits, or MR is a **Hard** gate: pause and warn, then continue only under an explicit scoped override that identifies the exact issue and Git path and accepts the traceability risk.

## PR-size boundary and scoped artifact exception

Keep every PR at or below 400 changed code lines by default. A PR may exceed that boundary only through the scoped artifact exception below. Use the LinearB PR-size value as authoritative when it is observable. Before a PR exists or when LinearB is unavailable, use the conservative sum of added and deleted non-binary lines across the intended Git diff, including source, tests, configuration, migrations, and generated text that will be committed. A valid repository profile may set a stricter positive maximum but never a value above 400.

Enforce two **Hard** gates:

- **Pre-code PR size:** before `PLAN_APPROVED`, source mutation, or `IMPLEMENTING`, inspect the expected touchpoints for every intended single-PR slice and record a supported per-slice estimate at or below the effective maximum. An unresolved or oversized slice fails the gate unless the exact excess paths qualify for the artifact exception below. When the original issue cannot fit one compliant PR, stop before code, recommend a Jira split, and refine independently deliverable slices in the plan until every slice has a supported compliant estimate or valid artifact exception. Do not treat commit-sized units or plan phases alone as compliant PR slices.
- **Actual PR size:** before `CODE_READY`, push, or MR creation, measure the complete intended PR diff against its exact Epic base. Recheck LinearB when it becomes observable. A value above the effective maximum fails the gate unless the exact excess paths remain covered by a valid artifact exception; otherwise stop before adding the excess scope when drift is detected, amend the execution record, and move the remaining work to another approved Jira slice and PR.

An oversized PR may proceed without splitting only when all of these conditions are recorded and verified:

1. Every line above the effective maximum is confined to authoritative specification or documentation source and deterministic artifacts generated from that source. Generated output is not hand-edited.
2. The workflow records exact qualifying paths, generated paths, total changed lines, qualifying-artifact changed lines, and the remaining handwritten/non-generated changed lines. The handwritten/non-generated portion is independently reviewable and at or below the effective maximum.
3. The repository-owned generator, exact command or script, source inputs, and relevant version/configuration are identified. A clean regeneration or equivalent focused comparison demonstrates reproducibility, with any expected metadata exclusions recorded.
4. Splitting the qualifying source from its generated artifacts would leave the contract, build, or committed generated client inconsistent; the workflow records why the oversized artifact set is indivisible for this PR.
5. After receiving the measurements and warning, the user explicitly accepts the review risk and authorizes the exact repository, Jira slice, source branch, target branch, qualifying paths, generated paths, and intended action. Record both size gates as `Overridden`, never `Passed`.
6. Revalidate the exception after any source, generator, configuration, base-ref, target, or diff-boundary change. Any unrelated handwritten excess or unverified generated drift invalidates the exception and restores the block.

The exception changes only the size-gate outcome. It does not waive Jira traceability, Git authorization, verification, security, generated-file ownership rules, or higher-priority instructions. Report total PR size and the separated handwritten and qualifying-artifact measurements in the MR handoff so the reviewer can plan review effort.

Split Jira work without violating the verified hierarchy:

- For a Task, recommend child Subtasks.
- For a Story, recommend sibling delivery Tasks directly under the same Epic.
- For a Subtask, narrow it to the first compliant slice and recommend sibling Subtasks under the same parent Task. If it cannot be narrowed, recommend new sibling Subtasks and ask the user how to disposition the original.

Give each slice its own Jira key, acceptance boundary, estimate, working branch, and PR. Record dependencies and verification per slice. Never create or edit Jira work items without exact user authorization; after mutation, re-read their keys, types, parents, and Epic ancestry. Do not begin code for a slice until its Jira evidence, approved scope, and pre-code estimate pass.

## Developer and Git boundary

Prepare a complete, reviewable MR with relevant evidence. Require exact, current authorization for working-branch creation, commit, push, and MR creation. Plan approval alone is not Git authorization.

Resolve working-branch creation and local-commit authorization before the first source mutation in every affected repository. A single current-session authorization may cover all planned local incremental commits for the exact repository, branch, Jira scope, and authorized path/diff scope; it does not authorize push or MR creation. If local commits are not authorized, pause implementation before editing source. Never implement an entire phase into the working tree and ask for commit authorization only afterward. Once authorized, commit each smallest complete verified unit immediately under the active execution or coding workflow.

Never self-approve or modify GitLab administration. Once a Tech Lead approval is verified on the exact MR and required checks and GitLab mergeability pass, the Developer may proactively merge without requiring the Tech Lead to perform the merge. Never bypass approval, protected-branch, pipeline, or mergeability controls. Deployment, release, Mobile delivery, and post-merge metrics remain out of scope.

Before `glab`, verify installed version, leaf help, authentication, repository, and identity. Use explicit source and target. Never use interactive defaults or auto-merge. Before a merge command, also verify the Tech Lead approver identity and approval state, current source and target, pipeline/check state, mergeability, and current MR SHA.

## Repository-aware AI attribution

Use only attribution explicitly permitted by higher-priority policy, repository instructions, or the profile. Never invent a trailer or hardcode a model identity. When no sanctioned mechanism exists, record `AI_ATTRIBUTION_UNAVAILABLE` as an **Advisory** limitation unless higher-priority policy makes it mandatory.

## Evidence rules

- Label assumptions and never promote them to verified facts.
- Record sources for mode, path classification, Jira identity and ancestry, repository profile, Git baseline, branch/remote/target, authorization, MR fields, and checks.
- Revalidate evidence after relevant changes.
- Treat profile conflicts as configuration drift requiring warning and an allowed scoped override before dependent mutation.
- Preserve unrelated changes; never stage, rewrite, discard, or include them in the delivery boundary.

## Out-of-scope ownership

Developer ownership continues through verified `MERGED`: the Tech Lead owns review and approval, and the Developer owns the merge after that approval. GitLab administration, deployment, release, DevSecOps, Service Operations, Mobile delivery, and post-merge reporting belong to other roles or workflows.
