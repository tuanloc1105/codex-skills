---
name: plan
description: Plan-first collaboration workflow for Codex. Use when the user explicitly invokes $plan, says "len plan", "lap ke hoach", "thao luan truoc", "how to do it", wants to discuss and approve an implementation plan before code changes, or wants a detailed handoff plan saved to a file for a future Codex session. This skill creates one draft Markdown record at entry, keeps it active throughout planning, requires explicit user approval before implementation, and finalizes that same file with context, dependency-aware phases, execution waves, subagent eligibility notes, touchpoints, intended logic, verification steps, and a persistent $execute resume marker. Without an explicit destination, automatically save the draft under ./plans/ in the current working directory without asking about the path, filename, or collisions.
---

# Plan

## Workflow Modes Hook

When the `workflow-modes` plugin is installed and its hooks are trusted, resolve `workflow_modes_control.py` from the installed plugin bundle, normally `<user-home>/plugins/workflow-modes/scripts/`. Invoke it with the configured Python interpreter because the installed script may not have executable permissions, and pass `--marker workflow-modes-v1` after the lifecycle action's other required arguments, as advertised by that action's local `--help` output.

- On fresh `$plan` entry, resolve and exclusively reserve the draft plan path before substantive inspection, initialize its draft metadata, and run `activate plan --record <plan-path>`. Keep this exact file from planning discussion through approval and execute handoff.
- On entry from `$discuss`, require its persisted `transition plan --record <discussion-tracker>` result instead of reactivating a different mode.
- On entry from `$discuss`, resolve and initialize the separate draft plan immediately, then run `activate plan --record <plan-path>` to rebind plan mode from the discussion context to its exact record.
- At activation, after every `UserPromptSubmit` reminder, and after every `PostCompact` reminder, read the exact draft plan completely and run `sync --record <plan-path>` before substantive work.
- Persist material planning deltas throughout the conversation. Before every user-facing response, run `checkpoint --record <plan-path>`; use `--no-change` only after confirming that the turn produced no material record change.
- After approval and after the plan's execute-ready metadata is durable, run `transition execute --record <plan-path>` before handing control to `$execute`.

Confirm every control call returns model-visible `WORKFLOW_*` context. If the plugin is unavailable, planning may continue because it is read-only apart from plan housekeeping, but state that lifecycle enforcement is unavailable. Never mutate source in plan or bypass a denied hook decision.

Use this skill to turn an ambiguous or important request into an approved execution plan while keeping one durable Markdown record from the beginning of planning.

## Plan-First Boundary

Follow the `$plan` workflow directly without attempting to switch or discuss the runtime's collaboration mode.

- Do not make production code edits, run destructive commands, commit, push, deploy, or implement the planned work while using this skill.
- After saving the approved plan, begin implementation only when the user explicitly requests execution; hand the saved plan to `$execute` for that work.
- Read and respect repository instructions, user rules, AGENTS.md, active developer instructions, and higher-priority safety constraints.

## Relationship to Direct Discuss Handoffs

`$plan` remains the full plan-first workflow when the user invokes it or wants a separate reviewed handoff. It is not a mandatory formatting hop between `$discuss` and `$execute`: a `$discuss` tracker that passes that skill's `Direct Execute Handoff` may be adopted directly by `$execute` as the single execution record. Do not create a duplicate plan file when the user explicitly chose the direct tracker route; return to `$discuss` only when its execution-readiness gate still has blocking decisions or missing accepted state.

## Discuss Fallback

Follow the conversational restrictions and question style of `$discuss` before planning when the current session has no reliable clue about what the user wants, or when the agent is confused about the right direction. Do not activate a separate discuss tracker lifecycle during this fallback; the already-created `$plan` draft remains the only Markdown planning artifact.

Use this fallback when:

- The user's goal is too vague to form an actionable plan.
- The workspace or task context is missing and cannot be inferred safely.
- Multiple materially different approaches are possible and choosing one would be guesswork.
- The agent feels uncertain, stuck, or confused about the user's intent.
- More conversation is needed before writing a useful "How to do it" handoff plan.

While in this fallback, keep using the already established draft plan as the planning record:

- Do not edit source files, create unrelated artifacts, implement changes, or mutate external state. Draft-plan housekeeping and persistence remain required.
- Ask concise clarifying questions and follow the mandatory `Question and Open-Issue Contract` below.
- Help the user choose the target outcome, constraints, and preferred approach.
- Summarize the agreed direction before returning to the `$plan` workflow.

## Conversation Workflow

1. Resolve, reserve, initialize, activate, read, and sync the exact draft plan path under `Saving Rules`.
2. Restate the user's goal in concrete terms and persist it to the draft.
3. Gather only the missing information that materially changes the plan. Keep questions concise and follow the mandatory `Question and Open-Issue Contract`; do not ask for details that can be discovered safely from the workspace.
4. Inspect enough context to remove guesswork:
   - Relevant repository instructions and local conventions
   - Existing files, exports, callers, routes, schemas, tests, configs, logs, or docs
   - Current constraints from the user and active environment
5. Establish an existing-behavior and regression-safety baseline before proposing changes to an existing mechanism:
   - Record the current behavior and the evidence supporting it; distinguish verified facts, user-reported behavior, inferences, and unknowns
   - Identify stable behaviors, invariants, interfaces, data contracts, UX expectations, error handling, and backward-compatibility requirements that must be preserved unless the user explicitly changes them
   - Trace affected callers, consumers, integrations, data flows, and other downstream touchpoints
   - Identify the existing tests, checks, logs, screenshots, or manual reproduction that demonstrate the baseline; run only safe read-only checks and record any checks that could not be run
   - Separate intentional behavior changes from regressions and make material evidence gaps explicit before planning potentially breaking work
6. Propose a plan with clear scope:
   - What will change
   - What will not change
   - Main files, modules, services, UI surfaces, data flows, or external systems touched
   - Phase dependencies, execution waves, and bounded subagent candidates when the work benefits from phases
   - Risks, assumptions, and open questions
   - Preservation acceptance criteria, regression checks, and verification strategy
   - Rollback or recovery for material behavior changes
7. Ask the user to approve or revise the plan, including its dependency and delegation structure when present. Present approval, targeted revision, broader rework, and pause/cancel as applicable options. Approval is required before changing the existing draft record to its final execute-ready status.
8. After approval, finalize the same exact Markdown file as the approved "How to do it" handoff. Do not create a replacement plan or implement it in the same `$plan` flow unless the user explicitly requests execution after saving.

## Question and Open-Issue Contract

Every question that requires a user response must include concrete options. Do not ask a bare open-ended question, including when requesting clarification, confirmation, or approval. Never ask a storage-choice question for the plan file.

- Present each distinct issue as a separate question block. Do not combine unrelated decisions under one option list.
- Provide 2-4 practical, mutually distinguishable options that answer that question.
- Mark one option as `Recommended` or `Default` when there is a reasonable choice.
- Include `Other — specify` when the listed choices may not cover the user's intent.
- When the user must supply a free-form value unrelated to plan-file storage, such as a URL or external resource name, offer useful defaults or actions first and include an option to provide a different value. Never invent the free-form value.
- If a question is non-blocking, state which default the agent will use if the user does not answer.
- Apply these rules to questions in chat and to every item in the proposed or saved plan's `Open Questions` section.
- For each open question in a plan, record its options, recommendation/default when applicable, and whether it blocks execution.
- Before sending a response or saving a plan, check that no user-facing question or open issue lacks its own option list.

## Dependency-Aware Phase Planning

Divide work into phases only when the boundaries improve execution, ownership, or verification. Do not turn a small linear task into artificial phases, and do not treat phase numbering or list order as an implicit dependency.

When phases are useful, assign stable IDs such as `P1`, `P2`, and record for each phase:

- `Depends on`: prerequisite phase IDs or `None`
- `Wave`: the earliest execution wave allowed by those dependencies
- `Subagent`: `Eligible` or `Not eligible — <reason>`
- `Owned scope`: files, modules, services, external systems, or other mutable resources the phase may change
- `Produces`: the concrete result or contract returned for downstream work
- Phase-local verification and any cross-phase integration gate

Treat `Depends on` as the source of truth and `Wave` as a derived scheduling aid:

- Put phases with no unmet implementation dependencies in Wave 1, even when they appear later in the document.
- Put phases in the same later wave only when all of their dependencies finish in earlier waves.
- Mark `Subagent: Eligible` only when the phase is bounded, does not consume another same-wave phase's output, has non-overlapping ownership, can be verified independently, and has a clear handoff result.
- Mark a phase not eligible when it may overlap another phase's files or mutable state, or when it owns shared contracts, migrations, lockfiles, generated artifacts, external side effects, or stateful processes without an explicit safe coordination strategy.
- Default to `Not eligible` when independence cannot be established confidently.

Eligibility means the executing agent may delegate the phase to a separate subagent; it is not a requirement to do so. Runtime capacity, current repository state, newly discovered coupling, or delegation overhead may justify serial execution. The main executing agent remains responsible for plan progress, shared resources, integration, conflict resolution, and cross-phase verification.

While using `$plan`, document this execution structure but do not spawn subagents to implement production work.

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
- Keep the saved file self-contained. A future session should not need the original chat to understand the work.
- Include the mode markers, last-updated timestamp, and status-appropriate resume instruction from the handoff template. A draft resumes with `$plan`; after approval the same line changes to the persistent `$execute` instruction, which remains authoritative even when implementation status later becomes `Implemented`.
- Tell the user the exact path when the draft is established and again when it is finalized.
- For a draft, tell the user: `Use $plan and continue the draft at <final-path>.` After approval, tell the user: `Use $execute and read the plan at <final-path>.`
- If the resolved plan directory or file cannot be created, report the exact blocker and stop without asking a storage-choice question or silently relocating an explicit destination. If only `.gitignore` maintenance fails, keep the resolved destination, save the plan there, and report that it could not be ignored; never relocate the plan solely because of an ignore failure.

## Handoff Plan Template

Write the plan in Markdown with these sections. Include only truthful, task-relevant details, but be specific enough that a new agent does not need to guess.

```markdown
# How to do it: <Plan Name>

<!-- workflow-record version:2 kind:plan tracker-id:<stable tracker ID> -->

Date: <YYYY-MM-DD>
Last updated: <timestamp and timezone>
Timezone: <local timezone if known>
Status: <Draft planning discussion | Approved plan, not yet implemented>
Plan mode: <Active | Exited>
Execution readiness: <Not ready | Ready>
Execute mode: <Inactive | Ready>
Resume instruction: <While draft: Invoke $plan, read this file completely, and continue this exact draft before substantive work. | After approval: Invoke $execute, read this file completely, keep this exact file as the execution source of truth, and continue updating it until the user explicitly exits execute.>

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
