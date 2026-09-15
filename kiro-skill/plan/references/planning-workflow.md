# Plan Conversation Workflow

Read this reference completely before creating or revising a plan, establishing its baseline, or requesting approval. The entrypoint's Plan-First Boundary and Question and Open-Issue Contract remain mandatory. For an existing bundle, add `references/planning-workflow.md` through the normal record transaction and verify the saved Required references before proceeding; for a new bundle, read this file before initialization and include it in the initial required set.

## Conversation Workflow

1. Resolve, reserve, initialize, read, and validate the exact draft plan bundle under `Saving Rules`.
2. Restate the user's goal in concrete terms and persist it to the draft.
3. Gather only the missing information that materially changes the plan. Keep questions concise and follow the mandatory `Question and Open-Issue Contract`; do not ask for details that can be discovered safely from the workspace.
4. Inspect enough context to remove guesswork:
   - Relevant project steering (`.kiro/steering/*.md`) and local conventions
   - Existing files, exports, callers, routes, schemas, tests, configs, logs, or docs — use the `code` tool for symbol/document lookups and `grep`/`glob` for pattern discovery rather than broad `find`/recursive `grep` from the home directory
   - Current constraints from the user and active environment
5. Establish an existing-behavior and regression-safety baseline before proposing changes to an existing mechanism:
   - Record the current behavior and the evidence supporting it; distinguish verified facts, user-reported behavior, inferences, and unknowns
   - Identify stable behaviors, invariants, interfaces, data contracts, UX expectations, error handling, and backward-compatibility requirements that must be preserved unless the user explicitly changes them
   - Trace affected callers, consumers, integrations, data flows, and other downstream touchpoints
   - Identify the existing tests, checks, logs, screenshots, or manual reproduction that demonstrate the baseline; run only safe read-only checks and record any checks that could not be run
   - Separate intentional behavior changes from regressions and make material evidence gaps explicit before planning potentially breaking work
   - For a genuinely wide sweep that would flood this session's context, delegate to `spawn_run` and fold the distilled result back into `context.md`
6. Propose a plan with clear scope:
   - What will change
   - What will not change
   - Main files, modules, services, UI surfaces, data flows, or external systems touched
   - Phase dependencies, execution waves, and bounded `spawn_run` subagent candidates when the work benefits from phases
   - Risks, assumptions, and open questions
   - Preservation acceptance criteria, regression checks, and verification strategy
   - Rollback or recovery for material behavior changes
7. Ask the user to approve or revise the plan, including its dependency and delegation structure when present. Present approval, targeted revision, broader rework, and pause/cancel as applicable options — via `ask_question` on a dashboard session (ending the turn) or the numbered fallback plus trailing `[OPTIONS: ...]` otherwise. Approval is required before changing the existing draft record to its final execute-ready status.
8. After approval, finalize the same exact bundle as the approved handoff. Do not create a replacement bundle or implement it in the same `$plan` flow unless the user explicitly requests execution after saving.
