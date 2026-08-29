---
name: plan
description: Plan-first collaboration workflow for Codex. Use when the user explicitly invokes $plan, says "len plan", "lap ke hoach", "thao luan truoc", "how to do it", wants to discuss and approve an implementation plan before code changes, or wants a detailed handoff plan saved to a file for a future Codex session. This skill creates one draft Markdown record at entry, keeps it active throughout planning, requires explicit user approval before implementation, and finalizes that same file with context, dependency-aware phases, execution waves, subagent eligibility notes, touchpoints, intended logic, verification steps, and a persistent $execute resume marker. Without an explicit destination, automatically save the draft under ./plans/ in the current working directory without asking about the path, filename, or collisions.
---

# Plan

## Workflow Modes Hook

When the `workflow-modes` plugin is installed and its hooks are trusted, resolve `workflow_modes_control.py` from the installed plugin bundle, normally `<user-home>/plugins/workflow-modes/scripts/`. Invoke it with the configured Python interpreter because the installed script may not have executable permissions, and pass `--marker workflow-modes-v1` after the lifecycle action's other required arguments, as advertised by that action's local `--help` output.

- On fresh `$plan` entry, resolve and exclusively reserve the draft plan path before substantive inspection, initialize its draft metadata, and run `activate plan --record <plan-path>`. Keep this exact file from planning discussion through approval and execute handoff.
- After activation, compaction, or any Required references change, read this complete entrypoint and every named reference, sync the required record scope, then run `rules-sync --record <plan-path> --reference <path>...` before substantive work or a final response.
- On entry from `$discuss`, require its persisted `transition plan --record <discussion-tracker>` result instead of reactivating a different mode.
- On entry from `$discuss`, resolve and initialize the separate draft plan immediately, then run `activate plan --record <plan-path>` to rebind plan mode from the discussion context to its exact record.
- At activation and after every `PostCompact` reminder, read the exact draft plan completely and run `sync --record <plan-path> --scope record` before substantive work.
- After `UserPromptSubmit`, follow `sync_status`: `current` requires no reread; `snapshot` requires reading only the delimited Active Snapshot and running snapshot-scope sync; `record` requires a complete read and record-scope sync.
- After writing the plan from an acknowledged revision, run `ack-write --record <plan-path> --previous-revision <last acknowledged record revision>`. On denial, read and reconcile the complete plan and use record-scope sync.
- Persist material planning deltas throughout the conversation. Before every user-facing response, run `checkpoint --record <plan-path>`; use `--no-change` only after confirming that the turn produced no material record change.
- After approval and after the plan's execute-ready metadata is durable, run `transition execute --record <plan-path>` before handing control to `$execute`.
- During that approval handoff, set the Active Snapshot profile to `Durable` unless it is already `Audited`; never downgrade `Audited`.

Confirm every control call returns model-visible `WORKFLOW_*` context. If the plugin is unavailable, planning may continue because it is read-only apart from plan housekeeping, but state that lifecycle enforcement is unavailable. Never mutate source in plan or bypass a denied hook decision.

New plans use the `Lightweight` profile. Profiles affect reread and persistence cadence only, not the plan boundary or transition gates. Respect `Durable` or `Audited` when already required. Treat a version 2 plan without an Active Snapshot as `Audited` until its next valid update adds the workflow-record version 3 header and Active Snapshot version 2.

Use this skill to turn an ambiguous or important request into an approved execution plan while keeping one durable Markdown record from the beginning of planning.

## Reference Routing

Load only the reference needed for the current stage, and read it completely before applying it.

- Read [references/plan-record.md](references/plan-record.md) before creating, updating, approving, or handing off the Markdown plan.
- Read [references/phase-planning.md](references/phase-planning.md) only when phases, dependencies, waves, or subagent eligibility materially improve the plan.
- Keep `Required references` minimal: always `references/plan-record.md`; add `references/phase-planning.md` while phases, dependencies, waves, or subagent eligibility are in use. Persist and acknowledge each set change before reading the new reference and running `rules-sync`.

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
