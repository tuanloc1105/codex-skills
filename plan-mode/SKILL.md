---
name: plan-mode
description: Plan-first collaboration workflow for Codex. Use when the user asks to switch to Plan mode, says "len plan", "lap ke hoach", "thao luan truoc", "how to do it", wants to discuss and approve an implementation plan before code changes, or wants a detailed handoff plan saved to a file for a future Codex session. This skill requires Plan-mode behavior, explicit user approval before implementation, a discussion-only fallback when the session has no reliable clue or the agent is confused, and a final detailed "How to do it" plan file with context, dependency-aware phases, execution waves, subagent eligibility notes, touchpoints, intended logic, and verification steps.
---

# Plan Mode

Use this skill to turn an ambiguous or important request into an approved execution plan and a durable handoff document.

## Mode Requirement

Immediately enter Plan mode.

- If the runtime provides an actual mode-switch mechanism, use it before substantive work.
- If the collaboration mode is controlled externally and cannot be changed by a skill, state this limitation once, then strictly follow Plan-mode behavior in this skill.
- Do not make production code edits, run destructive commands, commit, push, deploy, or implement the planned work while using this skill unless the user explicitly exits Plan mode and asks for execution.
- Read and respect repository instructions, user rules, AGENTS.md, active developer instructions, and higher-priority safety constraints.

## Discussion-Only Fallback

Invoke or follow `$discussion-only` before planning when the current session has no reliable clue about what the user wants, or when the agent is confused about the right direction.

Use this fallback when:

- The user's goal is too vague to form an actionable plan.
- The workspace or task context is missing and cannot be inferred safely.
- Multiple materially different approaches are possible and choosing one would be guesswork.
- The agent feels uncertain, stuck, or confused about the user's intent.
- More conversation is needed before writing a useful "How to do it" handoff plan.

While in this fallback:

- Do not edit files, create artifacts, implement changes, or mutate local or external state.
- Ask concise clarifying questions and follow the mandatory `Question and Open-Issue Contract` below.
- Help the user choose the target outcome, constraints, and preferred approach.
- Summarize the agreed direction before returning to the Plan Mode workflow.

## Conversation Workflow

1. Restate the user's goal in concrete terms.
2. Gather only the missing information that materially changes the plan. Keep questions concise and follow the mandatory `Question and Open-Issue Contract`; do not ask for details that can be discovered safely from the workspace.
3. Inspect enough context to remove guesswork:
   - Relevant repository instructions and local conventions
   - Existing files, exports, callers, routes, schemas, tests, configs, logs, or docs
   - Current constraints from the user and active environment
4. Propose a plan with clear scope:
   - What will change
   - What will not change
   - Main files, modules, services, UI surfaces, data flows, or external systems touched
   - Phase dependencies, execution waves, and bounded subagent candidates when the work benefits from phases
   - Risks, assumptions, and open questions
   - Verification strategy
5. Ask the user to approve or revise the plan, including its dependency and delegation structure when present. Present approval, targeted revision, broader rework, and pause/cancel as applicable options. Treat approval as required before writing the final handoff plan.
6. After the plan is approved, ask where to save the plan file unless the user already gave an exact destination. Offer a recommended location when one can be inferred safely, plus an option to provide another path.
7. Save the approved "How to do it" plan as a Markdown file. Do not implement the plan in the same Plan-mode flow unless the user explicitly requests execution after saving.

## Question and Open-Issue Contract

Every question that requires a user response must include concrete options. Do not ask a bare open-ended question, including when requesting clarification, confirmation, approval, a save destination, overwrite behavior, or a change in mode.

- Present each distinct issue as a separate question block. Do not combine unrelated decisions under one option list.
- Provide 2-4 practical, mutually distinguishable options that answer that question.
- Mark one option as `Recommended` or `Default` when there is a reasonable choice.
- Include `Other — specify` when the listed choices may not cover the user's intent.
- When the user must supply a free-form value such as a path, URL, or name, offer useful defaults or actions first and include an option to provide a different value. Never invent the free-form value.
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

While using Plan Mode, document this execution structure but do not spawn subagents to implement production work.

## Saving Rules

Ask the user for the destination path before saving.

- If the user gives a directory, create the plan file inside it.
- If the user gives a full file path, use it, but ensure the filename starts with the date prefix.
- Filename format: `YYYY-MM-DD-<plan-name>.md`.
- Use the current local date unless the user requests another date.
- Slugify `<plan-name>` with lowercase ASCII words joined by hyphens.
- If a file already exists, ask with options: create a numbered variant (`Recommended`), overwrite, choose another name, or cancel.
- Keep the saved file self-contained. A future session should not need the original chat to understand the work.

## Handoff Plan Template

Write the plan in Markdown with these sections. Include only truthful, task-relevant details, but be specific enough that a new agent does not need to guess.

```markdown
# How to do it: <Plan Name>

Date: <YYYY-MM-DD>
Timezone: <local timezone if known>
Status: Approved plan, not yet implemented

## Goal
<Concrete outcome the user wants.>

## Background
<Why this work is needed, important user preferences, and relevant conversation context.>

## Current State
<What was inspected and what is true now: repo layout, files, behavior, configs, constraints, or missing pieces.>

## Scope
<In scope.>

## Out of Scope
<What the next session should not do unless separately requested.>

## Rules and Constraints
<User rules, AGENTS.md instructions, mode requirements, tooling constraints, style conventions, safety constraints.>

## Touchpoints
<Files, modules, components, commands, data stores, APIs, screens, routes, tests, docs, or external systems likely involved.>

## Desired Logic and Behavior
<The intended behavior, state transitions, data flow, edge cases, error handling, UX expectations, or acceptance criteria.>

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
<Separate phase-local checks, integration checks after each parallel wave, and final end-to-end checks. Include expected results, screenshots/manual QA if relevant, and residual risk when checks cannot run.>

## Rollback or Recovery
<How to undo or safely recover if implementation fails.>

## Open Questions
<For each unresolved issue, include 2-4 options, a recommendation/default when applicable, and whether it blocks execution; otherwise write "None".>

## Handoff Notes
<Anything the next session should know before starting, including assumptions and warnings.>
```

## Quality Bar

- Make the plan operational, not aspirational.
- Prefer concrete file paths, commands, function names, UI labels, schemas, routes, and test names when known.
- Include enough context for a fresh session to proceed accurately without rereading the whole chat.
- Capture user-approved decisions, rejected alternatives, and tradeoffs that affect implementation.
- Keep the document organized for execution: clear steps, clear verification, clear boundaries.
- Use stable phase IDs for every dependency; never imply that phase number alone creates an ordering requirement.
- Give each subagent-eligible phase a non-overlapping ownership boundary, a concrete output contract, and an independent verification path.
- Keep dependency, wave, and eligibility metadata internally consistent; otherwise mark the phase sequential until the uncertainty is resolved.
- If information is unknown, label it as unknown and say how the next session should discover it.
