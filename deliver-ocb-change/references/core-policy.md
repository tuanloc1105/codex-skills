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

- Epic base branch: `feature/{epic_id}_{epic-slug}`. Never include the Developer username in an Epic branch name; Epic branches are shared delivery bases.
- `feature/{jira_id}_{username}_{task-slug}`
- `hotfix/{jira_id}_{username}_{task-slug}`

Use `{jira_id} {task-title}` as the default MR title. The MR description must contain only the canonical absolute URL of the working Jira issue, with no label, heading, surrounding Markdown, implementation summary, verification text, or AI-review placeholder. An external AI reviewer may append content later; do not anticipate, reproduce, edit, or validate that reviewer-owned content as part of MR creation.

An explicit request to create the MR also authorizes one bounded Jira comment on the uniquely resolved working issue after the MR is successfully created and re-read. This comment is the only permitted Jira backlink mechanism for the MR: never create or update a Jira Web Link, remote link, development link, issue link, or another Jira field to record the MR URL, and never treat one as satisfying this requirement. The rendered comment must contain exactly one clickable hyperlink and no other visible content; its displayed text and link destination must both equal the canonical absolute MR URL. Do not rely on Jira auto-linking plain text. When the route accepts Atlassian Document Format, use one paragraph containing one text node whose text is the MR URL and whose single `link` mark has `attrs.href` equal to the same URL. Before commenting, read enough existing comments to determine whether one already has exactly that visible text and hyperlink destination; skip only when that exact clickable comment exists. Otherwise add exactly one comment, then re-read the created comment by ID and verify both its displayed text and hyperlink destination. If MR creation or its URL remains uncertain, do not comment. If the comment result is uncertain, re-read existing comments before any retry and never duplicate a possibly created comment.

Resolve `username` from the current request, approved/current plan, or authoritative repository profile evidence, in that order. Never infer it from Git identity or email. Require a branch-safe, unambiguous value. Every working branch contains `{jira_id}` and `{username}`; every commit begins `{jira_id}_{username}_{task_name}` followed by descriptive commit content. Missing or mismatched naming evidence is a user-overridable **Hard** gate for each affected action.

Verify issue ancestry and Epic topology before planning or mutation:

- Story, Task, and Bug are peer issue types that belong directly to an Epic.
- A Subtask belongs to a direct-parent Story, Task, or Bug, and that parent belongs to the delivery Epic.
- A prose key mention is not relationship evidence.
- The Epic base is the exact existing remote Epic branch and is always the MR target. If the user explicitly authorizes creating a missing Epic branch, use `feature/{epic_id}_{epic-slug}` without a Developer username unless a higher-precedence repository profile provides another exact pattern. Missing existence, mapping, or SHA evidence is a **Hard** gate before `$plan`; after warning, the user may explicitly authorize an exact fallback Epic base or exact branch action and accept the recorded topology risk. Do not require branch-owner role or confirmation evidence for the Epic base.
- Resolve a separate development base for branch creation. Use the Epic base for an independent ticket. When the user explicitly chooses to begin a dependent ticket before its predecessor is merged, the development base may be the exact remote working branch of the immediately preceding ticket in the same Epic.
- For a stacked development base, verify the predecessor Jira key and dependency, working branch and current SHA, its ancestry from the same Epic base, its MR source and Epic target when an MR exists, and the complete ordered dependency chain. Never infer the relationship from a branch name or prose key mention alone. Branch the new ticket from that verified predecessor SHA and record that SHA so later drift is observable.
- Use each ticket's working branch as its MR source and the Epic base as its MR target. Never retarget a stacked MR to its predecessor branch or substitute a global integration branch.
- The Developer owns submitting stacked MRs for review in dependency order. An MR for a later ticket may exist while predecessors are open, but the workflow contract and handoff must identify the immediate predecessor branch/MR, explain that the Epic-target diff is temporarily cumulative, and state the required review and merge order. Keep this disclosure out of the Jira-only MR body.
- A stacked ticket must not merge before every predecessor in its recorded chain has merged into the Epic branch. After predecessor merge or predecessor-branch drift, revalidate ancestry and scope, update or rebase as repository policy requires, remeasure the Epic-target diff, and rerun affected verification. Predecessor merge order is a non-overridable merge-readiness requirement; changing the dependency topology requires an explicit newly verified development base and updated contract rather than an override.

For a correction discovered after Story, Task, or Bug completion, verify the original issue, its Story, Task, or Bug type, completed state, and Epic. By default, use `$interact-with-jira` to create exactly one specifically authorized bug-fix Subtask under it, re-read all required fields and ancestry, and use the new key for a new Epic-based working branch and MR. Missing Subtask evidence or reuse of an old branch, commits, or MR is a **Hard** gate: pause and warn, then continue only under an explicit scoped override that identifies the exact issue and Git path and accepts the traceability risk.

## LinearB work-activity integrity

Treat LinearB evidence as traceability, not as a productivity target. Jira estimates and worklogs do not substitute for observable issue or Git activity. Never create fake Jira items, commits, branches, or MRs; keep an issue open after truthful completion; delay a reviewable MR; or alter real workflow timing merely to increase FTE or another metric.

### Automatic Jira work start

An explicit request to deliver a uniquely resolved Jira issue with this skill authorizes only the following bounded work-start mutations on that issue: transition it to the exact available `In Progress`-type state when needed, fill an empty Start Date with today, and fill an empty Due Date with tomorrow. It does not authorize assignment, sprint, estimate, description, hierarchy, or any other Jira change. Before source mutation:

1. Run exactly `date "+%Y-%m-%d"` and use its stdout as today. Derive tomorrow as the next calendar date from that value in the same local timezone; do not infer either date from model context or a Jira timestamp.
2. Through `$interact-with-jira`, read the exact issue status and current Start Date and Due Date values, list the available transitions, and inspect field schema/edit metadata. Resolve Start Date by exact field metadata because it may be a project-specific custom field; use Jira's exact Due Date field. Never guess a custom-field ID from its display name alone.
3. If the issue is already in an `In Progress`-type state, skip the status transition. Otherwise perform the exact available transition once. If Start Date is already non-empty, leave it unchanged; otherwise set it to today. If Due Date is already non-empty, leave it unchanged; otherwise set it to tomorrow. Combine fields with the transition only when its metadata declares them writable there; otherwise make one minimal issue edit containing only the still-empty date fields.
4. Re-read and verify the resulting status and both date fields. For an ambiguous or failed mutation result, re-read before any retry and never repeat a write whose effect may already have occurred.

Missing transitions, ambiguous field identity, non-writable fields, permission failures, or unverifiable results are warning-first gates before implementation. Pause dependent source mutation, report the observed state and recommended correction, and continue only after the user explicitly accepts the exact residual risk and authorizes the exact issue and implementation scope. An override does not permit guessing a field or retrying an uncertain mutation.

Before source mutation, verify and record:

- The currently authenticated Jira account and the working issue's current assignee match the Developer. Do not infer historical or current assignment from Git identity.
- The issue is in an `In Progress`-type state at the truthful start of implementation, and its Start Date and Due Date satisfy the automatic Jira work-start procedure above. The bounded delivery request supplies authorization only for those exact work-start operations; every operation still follows `$interact-with-jira` preflight, execute-once, and verifying re-read rules.
- When the team uses sprints for this delivery, the issue belongs to the exact intended sprint and the sprint dates cover the truthful work period. Historical sprint membership, a similarly named sprint, or completion during a date range does not prove intended membership. When sprint delivery is not applicable, record why.

Assignee, work-start status and dates, and applicable sprint alignment are separate user-overridable **Hard** gates before implementation. On failure, pause only source mutation, state the observed value, missing or conflicting evidence, reporting risk, and exact recommended Jira correction. Continue without making the correction when the user explicitly accepts that risk and authorizes the exact issue, repository, path scope, and implementation action; record each failed gate as `Overridden`, never `Passed`. Risk acceptance does not authorize a Jira mutation beyond the bounded automatic work-start operations above.

After the LinearB init commit, publish the exact working branch and push that commit to the verified remote under exact current-session authorization. Verify that the remote branch resolves to the init commit SHA and record the observation. This is a non-overridable **Hard** gate before implementation because local-only commits are not current LinearB evidence. A push failure pauses source mutation until the branch and init commit are remotely observable. Do not create a draft MR merely for observability or manufacture activity.

Before `CODE_READY`, perform a traceability audit across the Jira key, assignee, work status, applicable sprint, working branch, ticket-owned commits, remote source, and MR when one exists. Record legitimate non-code work or local-only periods that are outside remote Git evidence rather than inventing an MR for them. A mismatch or unobservable period is a user-overridable **Hard** gate for dependent delivery: pause, recommend the smallest truthful correction, and continue under an exact scoped override when the user accepts the residual reporting risk. Post-merge LinearB measurement remains outside this skill.

## PR-size boundary and indivisible-change exception

Keep every PR at or below 155 changed code lines by default. Use the LinearB PR-size value as authoritative when it represents the ticket-owned diff. While a stacked predecessor remains unmerged, record LinearB's cumulative value but use the verified incremental development-base diff for the later ticket's gate; after predecessors merge, LinearB and the final Epic-target measurement must be reconciled before merge. Before a PR exists or when LinearB is unavailable, use the conservative sum of added and deleted non-binary lines across the applicable intended Git diff, including source, tests, configuration, migrations, and generated text that will be committed. A valid repository profile may set a stricter positive maximum but never a value above 155.

Enforce two **Hard** gates:

- **Pre-code PR size:** before `PLAN_APPROVED`, source mutation, or `IMPLEMENTING`, inspect the expected touchpoints for every intended single-PR slice and record a supported estimate. When an estimate exceeds the effective maximum, recommend the smallest Jira Subtasks that remain independently buildable, testable, reviewable, and traceable. Prefer slices by behavior, endpoint, domain contract, migration step, or other functional boundary; never split mechanically by file, function, class, DTO, or line count. Refine reducible work until each intended PR is compliant. If further reduction is demonstrably impossible, verify the indivisible-change exception below instead. An unresolved estimate, split assessment, or exception fails the gate. Do not treat commit-sized units or plan phases alone as compliant PR slices.
- **Actual PR size:** before `CODE_READY`, any post-implementation push, or MR creation, measure the ticket-owned incremental diff against its resolved development base. The required pre-implementation init-commit push contains no implementation diff and is governed by the LinearB publication gate instead. For an independent ticket the comparison base is the Epic base. For a stacked ticket it is the verified predecessor branch SHA; also measure and disclose the temporary cumulative diff against the Epic MR target, but do not count predecessor-owned changes toward the later ticket's size gate. Recheck LinearB when it becomes observable and reconcile it with the recorded incremental boundary. After every predecessor merges, remeasure against the updated Epic target before merging; the final Epic-target diff must represent the ticket-owned scope and pass the size gate or a verified indivisible-change exception. If unrelated or predecessor-owned changes remain, stop the merge and repair or reverify the topology rather than treating them as the later ticket's authorized scope.

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

After implementation reaches `CODE_READY` and the working MR exists with the expected repository, source, and target, transition the uniquely resolved working Jira issue to `Done`. The explicit delivery request authorizes only this bounded completion transition and the conditional atomic worklog below. Pipeline results, MR approval, mergeability, and MR merge are not prerequisites.

Before the first `Done` transition attempt, use `$interact-with-jira` to read the current status, raw Original Estimate (`timeoriginalestimate`), current Time Spent, the complete paginated worklog list and count, the exact available `Done` transition ID, and its transition metadata:

- If the issue is already `Done`, do not transition it and do not add a worklog. Proceed directly to final verification.
- If the issue is not `Done` and the verified worklog count is zero, require a positive Original Estimate. In the **first and only initial transition request**, send exactly one `update.worklog` entry shaped as `[{"add":{"timeSpentSeconds":<timeoriginalestimate>}}]` together with the exact `Done` transition. Never try the transition without that worklog first, and never create the worklog through a standalone worklog command or endpoint.
- If at least one worklog already exists, transition to `Done` without adding another worklog. Existing Time Spent alone is not a substitute for reading the complete worklog count.
- If Original Estimate is absent or non-positive when the zero-worklog branch requires it, or the available transition/tool metadata cannot support the atomic worklog update, pause this Jira completion action and warn the user. Do not invent an estimate or fall back to a separate worklog call.
- If any transition response is unclear, times out, or otherwise leaves the result uncertain, re-read status, Time Spent, and the complete worklog list before any further write. If status changed or the worklog count increased, do not retry. Never automatically retry an uncertain mutation through another tool or route.

Finally, re-read and record the status, Time Spent, and complete worklog count. Require `Done`; when this workflow added the worklog, also require an exact count increase of one and verify the resulting Time Spent reflects the added Original Estimate. Any mismatch is a warning-first verification failure: pause dependent claims of Jira completion, report the evidence, and continue only under an explicit scoped override without adding or duplicating a worklog.

Jira `Done` and GitLab merge are independent lifecycle facts. Conversely, Jira `Done` never proves pipeline success, MR approval, merge readiness, or `MERGED`. If permissions, transition metadata, Original Estimate when required, or an applicable Jira transition is unavailable, pause only the Jira transition and continue the MR review-and-merge workflow when its own gates permit.

## Bug handoff to Ready to test

When the user explicitly requests moving a uniquely resolved Bug to `Ready to test`, that request authorizes only the exact transition, its required Resolution selection, and reassignment to the issue's verified Reporter. It does not authorize changing any other field.

1. Re-read the issue and verify its issue type is exactly Bug, its current status, Reporter account, current assignee, and current Resolution. List available transitions with expanded field metadata and resolve the exact transition whose destination is `Ready to test`; do not match only by an assumed transition name.
2. Inspect the transition metadata for the Resolution field and its allowed values. Select the value corresponding to the verified fix outcome and workflow context; never guess from display-name resemblance. If more than one allowed Resolution remains plausible and the user has not identified the intended outcome, pause and ask the user to choose the exact value.
3. Prefer one transition request that sets the selected Resolution and assigns the issue to the exact Reporter account when the transition metadata permits both fields. If assignment is not supported on the transition screen, perform the transition with Resolution once, verify it, then use one minimal assignment operation targeting the previously verified Reporter.
4. Re-read and verify issue type Bug, status `Ready to test`, the exact selected Resolution, and assignee equal to Reporter. If any mutation result is uncertain, re-read before another write and never retry a possibly applied transition or assignment blindly.

Missing Reporter, inactive or unassignable Reporter, unavailable transition, absent or ambiguous Resolution choices, permissions, or unverifiable results are warning-first gates for this handoff. Pause the dependent Jira action, state the evidence and recommended correction, and continue only after the user explicitly accepts the scoped risk and supplies any still-missing exact value. An override never permits inventing a Reporter or Resolution.

## Developer and Git boundary

Prepare a complete, reviewable MR with relevant evidence. Require exact, current authorization for working-branch creation, the LinearB init commit, its initial push, implementation commits, later pushes, and MR creation. An explicit post-implementation request that enumerates the exact implementation commits, later pushes, and MRs may authorize those actions together and also authorizes the required pre-MR empty commit described below. Generic approval, plan approval, or authorization for one action does not authorize the others.

Resolve working-branch creation, LinearB init-commit, and exact initial-push authorization before the first source mutation in every affected repository. This authorization does not cover implementation commits, later pushes, or MR creation. Keep the implementation diff uncommitted while coding and running checks; do not stage unrelated or pre-existing work.

Immediately after the working branch is created and before any source edit, create one LinearB init commit as its first ticket-owned commit. When the working branch already exists, verify that the init commit is already the first ticket-owned commit; never create one retroactively after implementation commits and treat it as valid start evidence. Prefer `git commit --allow-empty` with the required `{jira_id}_{username}_{task_name} chore: initialize LinearB work tracking` message so the timestamp is established without changing delivery files. Verify the index is clean first: never commit, unstage, rewrite, or otherwise incorporate pre-existing or unrelated staged changes. If the index is not clean or an existing branch already contains ticket-owned implementation commits without the init commit, pause before implementation and require the user to resolve the boundary. Record the init commit SHA and timestamp, publish the branch to the exact verified remote, push the init commit, and verify the remote branch SHA matches. The remotely visible init commit is mandatory before `IMPLEMENTING`; it does not authorize or replace the later implementation commit set and does not waive verification.

### Required empty commit before MR creation

When the user authorizes MR creation at the post-implementation checkpoint, first create only the reviewed implementation commits covered by that authorization. Then, before pushing the final source SHA and creating the MR, create one additional empty commit on the exact working source branch using `git commit --allow-empty` with `{jira_id}_{username}_{task_name} chore: prepare merge request`. This post-implementation marker is separate from the LinearB init commit and must also be created when implementation already has no remaining diff. Verify the index is clean first; if it is not, pause this step without staging, unstaging, or incorporating unrelated work. Verify that the new commit tree equals its parent's tree, and record its SHA, parent SHA, and timestamp. Push that SHA under the existing push authorization, verify the remote source matches, then create and re-read the MR.

Before creating the marker, check whether the exact MR already exists. Reuse an existing matching MR without adding a marker retroactively. On a retry after marker creation, reuse the recorded marker only when it remains HEAD with the expected parent, message, and unchanged tree; never create duplicate markers for the same attempt. Stop on conflicting state and revalidate before continuing.

### Post-implementation delivery confirmation

After implementation and required checks are complete, stop at `CODE_READY` with the implementation diff uncommitted. Present the exact diff boundary, verification evidence, proposed commit set and messages, remote, source and target branches, and MR title/body. Continue only after the user explicitly authorizes the enumerated implementation commits, required post-implementation empty commit, push, and MR creation. Revalidate the diff and targets if anything changes after the preview.

Never self-approve or modify GitLab administration. Once the exact MR satisfies the platform-enforced approval rules, required checks, and GitLab mergeability, the Developer may proactively merge under explicit merge authorization. Do not require a separate approver-role confirmation. Never bypass applicable approval, protected-branch, pipeline, or mergeability controls. Deployment, release, Mobile delivery, and post-merge metrics remain out of scope.

Before `glab`, verify installed version, leaf help, authentication, repository, and identity. Use explicit source and target. Never use interactive defaults or auto-merge. Before a merge command, also verify the current platform-required approval state, current source and target, pipeline/check state, mergeability, and current MR SHA.

## Repository-aware AI attribution

Use only attribution explicitly permitted by higher-priority policy, repository instructions, or the profile. Never invent a trailer or hardcode a model identity. When no sanctioned mechanism exists, record `AI_ATTRIBUTION_UNAVAILABLE` as an **Advisory** limitation unless higher-priority policy makes it mandatory.

## Evidence rules

- Label assumptions and never promote them to verified facts.
- Record sources for mode, path classification, Jira identity and ancestry, repository profile, Git baseline, branch/remote/target, authorization, MR fields, and checks.
- Revalidate evidence after relevant changes.
- Treat profile conflicts as configuration drift requiring warning and an allowed scoped override before dependent mutation.
- Preserve unrelated changes; never stage, rewrite, discard, or include them in the delivery boundary.

## Out-of-scope ownership

Developer ownership continues through verified `MERGED`: reviewers provide any platform-required approval, and the Developer owns the explicitly authorized merge after approval and readiness gates pass. GitLab administration, deployment, release, DevSecOps, Service Operations, Mobile delivery, and post-merge reporting belong to other roles or workflows.
