# Plan Record Reference

Read this reference completely before creating, updating, approving, or handing off a Markdown plan.

## Saving Rules

Resolve, create, and freeze the draft plan file automatically at the start of `$plan`. Never ask the user about its save location, directory, filename, overwrite behavior, or collisions.

- Capture the current working directory when the skill starts and resolve every relative destination against it.
- Classify a user-provided destination without asking: an existing directory, a path ending in a separator, or explicit directory wording is a directory; otherwise treat it as a file path.
- If the user gives a directory, generate the plan filename inside it.
- If the user gives any explicit file path, including a bare filename, preserve that path exactly after resolving it against the captured current working directory.
- If the user gives no destination, use `./plans/` relative to the current working directory at the time the skill starts.
- For an agent-generated filename, derive `<plan-name>` from the current title or goal. Use `plan` only when no meaningful slug can be derived.
- Resolve the final candidate path before writing. If it or a symlink at that path already exists and the user did not explicitly request overwrite, preserve it and automatically choose the lowest available numbered sibling for that basename, such as `YYYY-MM-DD-<plan-name>-2.md`; do not ask. Overwrite only when the user explicitly instructed it and the resolved target passes the same path-safety checks.
- Resolve the directory that will contain the plan. If that directory or any parent directory does not exist, create the missing directories automatically before saving; do not ask for separate confirmation.
- For a new plan, reserve the selected file with exclusive creation and retry with the next numbered sibling if another writer wins the same path. Freeze the successfully reserved or explicitly overwritten path for the remainder of the `$plan` flow.
- After the destination directory exists, determine whether it is inside a Git worktree. If it is, ensure the worktree root's `.gitignore` ignores the directory containing the plans:
  - Create the root `.gitignore` if it does not exist, preserve its existing contents, and add a root-relative anchored directory rule with a trailing slash.
  - Do not add a duplicate rule or modify `.gitignore` when the destination directory is already ignored.
  - If the destination directory is the worktree root, ignore the plan file itself with a root-relative anchored file rule instead; never add a rule that ignores the entire worktree.
  - If the selected directory already contains non-plan files, warn that its folder-level rule also ignores untracked files there, but do not change the destination or ask for permission.
- For an agent-generated filename, use the format `YYYY-MM-DD-<plan-name>.md`.
- For an agent-generated filename, use the current local date unless the user requests another date.
- Slugify an agent-generated `<plan-name>` with lowercase ASCII words joined by hyphens.
- Initialize the reserved file with `Status: Draft planning discussion`, `Plan mode: Active`, `Execution readiness: Not ready`, a stable non-secret tracker ID, the machine-readable workflow-record header from the template, and an exact resume checkpoint. Update it after every material planning turn.
- Initialize the version 3 Active Snapshot with `Profile: Lightweight` and keep its goal, current state, accepted decisions, open items, and next safe action concise and current.
- Keep the saved file self-contained. A future session should not need the original chat to understand the work.
- Include the mode markers, last-updated timestamp, and status-appropriate resume instruction from the handoff template. A draft resumes with `$plan`; after approval the same line changes to the persistent `$execute` instruction, which remains authoritative even when implementation status later becomes `Implemented`.
- Tell the user the exact path when the draft is established and again when it is finalized.
- For a draft, tell the user: `Use $plan and continue the draft at <final-path>.` After approval, tell the user: `Use $execute and read the plan at <final-path>.`
- If the resolved plan directory or file cannot be created, report the exact blocker and stop without asking a storage-choice question or silently relocating an explicit destination. If only `.gitignore` maintenance fails, keep the resolved destination, save the plan there, and report that it could not be ignored; never relocate the plan solely because of an ignore failure.

## Handoff Plan Template

Write the plan in Markdown with these sections. Include only truthful, task-relevant details, but be specific enough that a new agent does not need to guess.

```markdown
# How to do it: <Plan Name>

<!-- workflow-record version:3 kind:plan tracker-id:<stable tracker ID> -->

Date: <YYYY-MM-DD>
Last updated: <timestamp and timezone>
Timezone: <local timezone if known>
Status: <Draft planning discussion | Approved plan, not yet implemented>
Plan mode: <Active | Exited>
Execution readiness: <Not ready | Ready>
Execute mode: <Inactive | Ready>
Resume instruction: <While draft: Invoke $plan, read this file completely, and continue this exact draft before substantive work. | After approval: Invoke $execute, read this file completely, keep this exact file as the execution source of truth, and continue updating it until the user explicitly exits execute.>

<!-- workflow-active-snapshot:start version:1 -->
## Active Snapshot

Profile: <Lightweight | Durable | Audited>
Goal: <current concrete goal>
Current state: <draft, awaiting decision, approved, or executing state>
Accepted decisions: <active decision IDs or concise values, or None>
Open items: <blocking or next open items, or None>
Next safe action: <one exact next action>
<!-- workflow-active-snapshot:end -->

## Goal
<Concrete outcome the user wants.>

## Background
<Why this work is needed, important user preferences, and relevant conversation context.>

## Current State
<What was inspected and what is true now: repo layout, files, behavior, configs, constraints, or missing pieces.>

## Existing Behavior Baseline
<Current working behavior and supporting evidence. Distinguish verified facts, user-reported behavior, inferences, unknowns, and checks that could not be run safely.>

## Preservation Requirements
<Behaviors, invariants, interfaces, contracts, compatibility guarantees, error handling, and UX expectations that must remain unchanged unless explicitly approved otherwise.>

## Scope
<In scope.>

## Out of Scope
<What the next session should not do unless separately requested.>

## Rules and Constraints
<User rules, AGENTS.md instructions, plan-first boundaries, tooling constraints, style conventions, safety constraints.>

## Touchpoints
<Files, modules, components, commands, data stores, APIs, screens, routes, tests, docs, or external systems likely involved.>

## Desired Logic and Behavior
<The intended behavior, state transitions, data flow, edge cases, error handling, UX expectations, or acceptance criteria.>

## Regression Risks and Safety Checks
<Affected callers and consumers, likely regressions, intentional behavior changes, baseline checks, preservation acceptance criteria, and targeted tests or manual checks that will detect breakage.>

## Execution Structure
<For small linear work, write "Sequential; no subagent candidates." For phased work, use the table below. `Depends on` is authoritative; `Wave` must agree with it.>

| Phase | Depends on | Wave | Subagent | Owned scope | Produces |
|---|---|---:|---|---|---|
| P1 | None | 1 | Eligible | <paths or mutable resources> | <handoff result> |
| P2 | None | 1 | Eligible | <disjoint paths or resources> | <handoff result> |
| P3 | P1, P2 | 2 | Not eligible — integration phase | <integration scope> | <integrated result> |

## Step-by-Step Plan
### Phase P1: <Name>

Phase verification: <narrow checks and expected result.>

1. [ ] <Specific action.>
2. [ ] <Specific action.>

### Phase P2: <Name>

Phase verification: <narrow checks and expected result.>

1. [ ] <Specific action.>

<Repeat for remaining phases. For small linear work, use one ordinary checklist instead.>

## Verification
<Compare post-change behavior with the recorded baseline and preservation requirements. Separate phase-local checks, integration checks after each parallel wave, targeted regression checks, and final end-to-end checks. Include expected results, screenshots/manual QA if relevant, and residual risk when checks cannot run.>

## Rollback or Recovery
<How to undo or safely recover if implementation fails.>

## Open Questions
<For each unresolved issue, include 2-4 options, a recommendation/default when applicable, and whether it blocks execution; otherwise write "None".>

## Amendments and Evidence
<Keep this section for `$execute`. Initially record "None at approval". While execute mode is active, append stable-ID entries for material corrections, added work, decisions, evidence, out-of-scope handoffs, re-entry, and exit without rewriting the approved baseline.>

| ID | Recorded at | Kind | Source | Change or evidence | Affected scope | Status |
|---|---|---|---|---|---|---|
| — | — | — | — | None at approval | — | — |

## Handoff Notes
<Anything the next session should know before starting, including assumptions and warnings.>
```

## Quality Bar

- Make the plan operational, not aspirational.
- Prefer concrete file paths, commands, function names, UI labels, schemas, routes, and test names when known.
- Do not plan a change to an existing mechanism without recording the behavioral baseline, preservation requirements, supporting evidence, affected consumers, and material unknowns.
- Treat preserved behavior as explicit acceptance criteria. Distinguish every approved behavior change from an accidental regression and pair material risks with targeted checks.
- Include enough context for a fresh session to proceed accurately without rereading the whole chat.
- Include the persistent execute marker and exact resume instruction. Reading or adopting the saved plan in any future session must activate `$execute` even when the plan is already implemented.
- Capture user-approved decisions, rejected alternatives, and tradeoffs that affect implementation.
- Keep the document organized for execution: clear steps, clear verification, clear boundaries.
- Use stable phase IDs for every dependency; never imply that phase number alone creates an ordering requirement.
- Give each subagent-eligible phase a non-overlapping ownership boundary, a concrete output contract, and an independent verification path.
- Keep dependency, wave, and eligibility metadata internally consistent; otherwise mark the phase sequential until the uncertainty is resolved.
- If information is unknown, label it as unknown and say how the next session should discover it.
