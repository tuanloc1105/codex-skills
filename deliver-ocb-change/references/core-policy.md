# OCB Delivery Core Policy

## Scope and precedence

Apply requirements in this order:

1. Higher-priority instructions and repository rules
2. A valid `.ocb/deliver-change.yaml` repository profile
3. This core policy and the applicable domain policy

Treat every skill-defined gate as warning-first and user-overridable under the applicable policy. The pre-code and actual PR-size gates use the narrower indivisible-change exception defined below; they are not generally overridable. When a gate fails, pause only its dependent action and present the missing evidence, affected action, risk, and recommended fix. If the user explicitly accepts the residual risk and authorizes the exact action under the applicable policy, record the gate as `Overridden` and continue. Never treat an override as proof that missing evidence was verified.

An override is valid only for the recorded repository, state, target, scope, and action and expires when any changes. It cannot violate higher-priority instructions, choose among still-ambiguous targets, expose secrets, authorize unspecified Git mutations, or permit destructive recovery outside the user's exact authorization. When a gate lacks an executable value, such as a base branch or delivery mode, require the user to select or authorize an exact value as part of the override; never guess it.

## Jira traceability and branch topology

### New-ticket content, estimate, and assignee

For every newly created Jira Story, Task, Bug, or Subtask:

- Write the title and body in concise Vietnamese. Keep identifiers, API names, code symbols, and unavoidable product terms unchanged when translating them would reduce precision.
- Use exactly these body headings in this order, with short scope-specific content under every heading and no additional top-level section:

  ```markdown
  ## Hiện trạng

  ## Mục tiêu

  ## Phạm vi

  ## Tiêu chi hoàn thành
  ```

- Derive the estimate from the verified scope, expected touchpoints, complexity, dependencies, testing, and delivery work. Record the rationale in the workflow contract, but keep the Jira body concise. The estimate must be positive and no greater than 3 hours even though the wider company ceiling is 6 hours. Refine work above 3 hours into independently deliverable child or sibling Subtasks before creation. If a genuinely indivisible ticket still exceeds 3 hours, stop and ask the user for an exact scoped exception; never silently enter 4–6 hours or falsify the estimate.
- Before creation, inspect Jira create metadata to resolve the exact estimate field and its unit. Convert the chosen hour estimate only through verified Jira semantics. Treat omission from create metadata as an evidence gap, not conclusive proof that estimates are unsupported: when the current official Jira tool accepts additional system fields, corroborate the exact field shape and unit from a recent same-project issue returned with both `timetracking` and `timeoriginalestimate`, then supply `timetracking.originalEstimate` and verify both representations after creation. Never infer the field from a neighboring project, prose, or name resemblance. If neither create metadata nor this same-project corroboration establishes a writable compatible estimate field, stop and report the limitation instead of omitting or guessing it.
- Resolve the currently authenticated Jira account through `$interact-with-jira` identity evidence and assign the new work item to that exact account. Do not infer the assignee from Git identity, email, display-name text, or the requested branch username. If the account cannot be assigned in the target project, stop and report the permission or assignability failure.
- Jira creation remains mutation-gated. Present the proposed project, issue type, parent/Epic, Vietnamese title/body, estimate value and unit, and current-account assignee before requesting exact authorization. After creation, re-read and verify the key, type, hierarchy, title, body headings and content, estimate, and assignee; an incomplete or normalized-away field is not verified success.

Use these default branch patterns:

- Epic base branch: `feature/{epic_id}_{epic-slug}`. Never include the Developer username in an Epic branch name; Epic branches are shared, Tech-Lead-owned delivery bases.
- `feature/{jira_id}_{username}_{task-slug}`
- `hotfix/{jira_id}_{username}_{task-slug}`

Use `{jira_id} {task-title}` as the default MR title. Put the Jira link, implementation context, verification, risks, and handoff in the description.

Resolve `username` from the current request, approved/current plan, or authoritative repository profile evidence, in that order. Never infer it from Git identity or email. Require a branch-safe, unambiguous value. Every working branch contains `{jira_id}` and `{username}`; every commit begins `{jira_id}_{username}_{task_name}` followed by descriptive commit content. Missing or mismatched naming evidence is a user-overridable **Hard** gate for each affected action.

Verify issue ancestry and Epic topology before planning or mutation:

- Story, Task, and Bug are peer issue types that belong directly to an Epic.
- A Subtask belongs to a direct-parent Story, Task, or Bug, and that parent belongs to the delivery Epic.
- A prose key mention is not relationship evidence.
- The Epic base is the exact existing Tech-Lead-owned Epic branch and is always the MR target. If the user explicitly authorizes creating a missing Epic branch, use `feature/{epic_id}_{epic-slug}` without a Developer username unless a higher-precedence repository profile provides another exact pattern. Missing existence, mapping, SHA, or ownership evidence is a **Hard** gate before `$plan`; after warning, the user may explicitly authorize an exact fallback Epic base or exact branch action and accept the recorded topology risk.
- Resolve a separate development base for branch creation. Use the Epic base for an independent ticket. When the user explicitly chooses to begin a dependent ticket before its predecessor is merged, the development base may be the exact remote working branch of the immediately preceding ticket in the same Epic.
- For a stacked development base, verify the predecessor Jira key and dependency, working branch and current SHA, its ancestry from the same Epic base, its MR source and Epic target when an MR exists, and the complete ordered dependency chain. Never infer the relationship from a branch name or prose key mention alone. Branch the new ticket from that verified predecessor SHA and record that SHA so later drift is observable.
- Use each ticket's working branch as its MR source and the Epic base as its MR target. Never retarget a stacked MR to its predecessor branch or substitute a global integration branch.
- The Developer owns submitting stacked MRs for review in dependency order. An MR for a later ticket may exist while predecessors are open, but its description must identify the immediate predecessor branch/MR, explain that the Epic-target diff is temporarily cumulative, and state the required review and merge order.
- A stacked ticket must not merge before every predecessor in its recorded chain has merged into the Epic branch. After predecessor merge or predecessor-branch drift, revalidate ancestry and scope, update or rebase as repository policy requires, remeasure the Epic-target diff, and rerun affected verification. Predecessor merge order is a non-overridable merge-readiness requirement; changing the dependency topology requires an explicit newly verified development base and updated contract rather than an override.

For a correction discovered after Story, Task, or Bug completion, verify the original issue, its Story, Task, or Bug type, completed state, and Epic. By default, use `$interact-with-jira` to create exactly one specifically authorized bug-fix Subtask under it, re-read all required fields and ancestry, and use the new key for a new Epic-based working branch and MR. Missing Subtask evidence or reuse of an old branch, commits, or MR is a **Hard** gate: pause and warn, then continue only under an explicit scoped override that identifies the exact issue and Git path and accepts the traceability risk.

## PR-size boundary and indivisible-change exception

Keep every PR at or below 155 changed code lines by default. Use the LinearB PR-size value as authoritative when it represents the ticket-owned diff. While a stacked predecessor remains unmerged, record LinearB's cumulative value but use the verified incremental development-base diff for the later ticket's gate; after predecessors merge, LinearB and the final Epic-target measurement must be reconciled before merge. Before a PR exists or when LinearB is unavailable, use the conservative sum of added and deleted non-binary lines across the applicable intended Git diff, including source, tests, configuration, migrations, and generated text that will be committed. A valid repository profile may set a stricter positive maximum but never a value above 155.

Enforce two **Hard** gates:

- **Pre-code PR size:** before `PLAN_APPROVED`, source mutation, or `IMPLEMENTING`, inspect the expected touchpoints for every intended single-PR slice and record a supported estimate. When an estimate exceeds the effective maximum, recommend the smallest Jira Subtasks that remain independently buildable, testable, reviewable, and traceable. Prefer slices by behavior, endpoint, domain contract, migration step, or other functional boundary; never split mechanically by file, function, class, DTO, or line count. Refine reducible work until each intended PR is compliant. If further reduction is demonstrably impossible, verify the indivisible-change exception below instead. An unresolved estimate, split assessment, or exception fails the gate. Do not treat commit-sized units or plan phases alone as compliant PR slices.
- **Actual PR size:** before `CODE_READY`, push, or MR creation, measure the ticket-owned incremental diff against its resolved development base. For an independent ticket this is the Epic base. For a stacked ticket this is the verified predecessor branch SHA; also measure and disclose the temporary cumulative diff against the Epic MR target, but do not count predecessor-owned changes toward the later ticket's size gate. Recheck LinearB when it becomes observable and reconcile it with the recorded incremental boundary. After every predecessor merges, remeasure against the updated Epic target before merging; the final Epic-target diff must represent the ticket-owned scope and pass the size gate or a verified indivisible-change exception. If unrelated or predecessor-owned changes remain, stop the merge and repair or reverify the topology rather than treating them as the later ticket's authorized scope.

The PR-size hard gate does not apply to the exact unavoidable excess of an oversized PR when all of these conditions are recorded and verified. Classify the size gate as `Not applicable — verified indivisible change`, not `Passed` or `Overridden`; the exception-evidence requirement remains a **Hard** gate:

1. The workflow records the total changed lines and separates handwritten/non-generated, authoritative specification or documentation, and deterministic generated lines with exact paths. Generated output is not hand-edited.
2. The Developer documents at least the credible split alternatives considered and why each would break an atomic API/data contract, leave the build or committed output inconsistent, make a migration unsafe or non-reversible under repository policy, duplicate tightly coupled work, or create an intermediate state that cannot be independently built, tested, reviewed, or delivered. Convenience, deadline pressure, broad function grouping, or avoiding Jira work is not indivisibility.
3. The retained diff is the smallest coherent implementation. Handwritten DTOs or contracts over the limit qualify only when their fields and validation form one atomic external or persistence contract and decomposition would change compatibility or semantics. DTOs that contain independent domain groups must be composed or split when repository conventions permit it.
4. For deterministic generated artifacts, identify the repository-owned generator, exact command or script, source inputs, and relevant version/configuration. A clean regeneration or equivalent focused comparison must demonstrate reproducibility, with expected metadata exclusions recorded.
5. All applicable acceptance, contract, migration, build, test, security, and domain checks remain required. The MR handoff warns reviewers about the oversized indivisible scope and provides a review order or path grouping when useful.
6. Revalidate the exception after any source, generator, configuration, base-ref, target, or diff-boundary change. Reducible handwritten excess, unrelated scope, or unverified generated drift invalidates the exception and restores the size hard gate.

The exception changes only the size-gate applicability for the exact indivisible excess. It does not waive the supported split assessment, Jira traceability, Git authorization, verification, security, generated-file ownership rules, or higher-priority instructions. Report total PR size, separated measurements, indivisibility evidence, and residual review risk in the MR handoff.

Split Jira work without violating the verified hierarchy:

- For a Story, Task, or Bug, recommend child Subtasks.
- For a Subtask, narrow it to the first compliant slice and recommend sibling Subtasks under the same parent Story, Task, or Bug. If it cannot be narrowed, recommend new sibling Subtasks and ask the user how to disposition the original.

Give each slice its own Jira key, acceptance boundary, estimate, working branch, and PR. Record dependencies and verification per slice. Never create or edit Jira work items without exact user authorization; after mutation, re-read their keys, types, parents, and Epic ancestry. Do not begin code for a slice until its Jira evidence, approved scope, and pre-code estimate pass.

## Jira completion timing

After implementation reaches `CODE_READY` and the working MR exists with the expected repository, source, and target, the working Jira issue may transition to `Done`. Pipeline results, Tech Lead approval, mergeability, and MR merge are not prerequisites. Perform the transition only with exact authorization for that issue and transition through `$interact-with-jira`, then re-read the issue and record the resulting status and evidence.

Jira `Done` and GitLab merge are independent lifecycle facts. Conversely, Jira `Done` never proves pipeline success, Tech Lead approval, merge readiness, or `MERGED`. If authorization, permissions, or an applicable Jira transition is unavailable, pause only the Jira transition and continue the MR review-and-merge workflow when its own gates permit.

## Developer and Git boundary

Prepare a complete, reviewable MR with relevant evidence. Require exact, current authorization for working-branch creation, commit, push, and MR creation. Scheduler artifact creation, scheduler installation, and scheduler activation are separate actions and require exact authorization. Plan approval, selecting a delivery time, or selecting `schedule final commit + MR` alone is not Git or scheduler authorization.

Resolve working-branch creation and local-commit authorization before the first source mutation in every affected repository. A single current-session authorization may cover the required LinearB init commit and all planned local incremental commits for the exact repository, branch, Jira scope, and authorized path/diff scope; it does not authorize push or MR creation. If local commits are not authorized, pause implementation before editing source.

Immediately after the working branch is created and before any source edit, create one LinearB init commit as its first ticket-owned commit. When the working branch already exists, verify that the init commit is already the first ticket-owned commit; never create one retroactively after implementation commits and treat it as valid start evidence. Prefer `git commit --allow-empty` with the required `{jira_id}_{username}_{task_name} chore: initialize LinearB work tracking` message so the timestamp is established without changing delivery files. Verify the index is clean first: never commit, unstage, rewrite, or otherwise incorporate pre-existing or unrelated staged changes. If the index is not clean or an existing branch already contains ticket-owned implementation commits without the init commit, pause before implementation and require the user to resolve the boundary. Record the init commit SHA and timestamp. The init commit is mandatory before `IMPLEMENTING`; it does not replace any smallest-complete-unit implementation commit or waive verification. Never implement an entire phase into the working tree and ask for commit authorization only afterward. Once authorized and initialized, commit each smallest complete verified unit immediately under the active execution or coding workflow.

Before the first source mutation, ask the user to choose `commit now` or `schedule final commit + MR`, unless the current request already selects one exactly. This choice controls the final delivery checkpoint and does not postpone the mandatory LinearB init commit or smallest verified incremental commits. A scheduled worker may commit only an explicitly recorded, verified remainder that still matches its pinned diff identity; it must never collect unrelated or later working-tree changes.

Scheduled delivery must follow [scheduled-delivery.md](scheduled-delivery.md). Use a Python worker with a native persistent OS scheduler rather than an in-chat timer or an unsupervised Python loop. The worker must fail closed on authorization, repository, branch, HEAD, diff, checks, authentication, remote, target, MR, or idempotency drift. A chat session ending never cancels or authorizes the job. Record scheduler artifacts, native service identity, loaded state, next run, logs, result state, cancellation command, and cleanup owner in the workflow contract.

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
