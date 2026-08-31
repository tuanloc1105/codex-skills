---
name: workflow-plan
description: Plan-first collaboration workflow for Kiro. Creates one version 4 Markdown plan bundle under ./plans/, keeps it active through approval and execute handoff, and stores every declared phase in its own self-contained, stable-ID Markdown file under phases/. Use for reviewed implementation planning and durable cross-session handoff.
---

# Plan

## Workflow Modes Hook

Kiro IDE 1.x and CLI 3.x load this distribution's standalone v1 command hooks from the active Kiro scope. Resolve `workflow_modes_control.py` from `<project>/.kiro/workflow-modes/scripts/` when the project-owned marker is present; otherwise resolve it from `${KIRO_HOME:-<user-home>/.kiro}/workflow-modes/scripts/`. Run it with the configured Python interpreter and exact absolute path. Every lifecycle call must end with `--marker workflow-modes-v1`; confirm successful calls yield model-visible `WORKFLOW_*` context.
- On fresh `/workflow-plan` entry, reserve and initialize the draft bundle before substantive inspection, then run `activate plan --record <bundle-root>`. Keep this exact bundle through approval and execute handoff.
- After activation, recovery-anchor reconciliation, or any Required references change, read this complete entrypoint and every named reference, sync the required record scope, then run `rules-sync --record <plan-path> --reference <path>...` before substantive work or a final response.
- On entry from `/workflow-discuss`, require its persisted `transition plan --record <discussion-tracker>` result instead of reactivating a different mode.
- On entry from `/workflow-discuss`, resolve the separate target root, run `plan-init --record <discussion-root> --target <plan-root>`, initialize the complete bundle only beneath that declared target, then run `activate plan --record <plan-root>`. `plan-init` is a narrow bootstrap guard, not general plan-mode mutation permission.
- At activation and after every active `UserPromptSubmit` or `PreToolUse` recovery anchor, read `index.md` and every manifest file completely and run record-scope sync.
- After `UserPromptSubmit`, follow `sync_status`: `current` requires no reread; `snapshot` requires reading only the delimited Active Snapshot and running snapshot-scope sync; `record` requires a complete read and record-scope sync.
- Before bundle edits, run `write-open` with the acknowledged revision and declare new phase paths with `--path`; run `write-close` only after manifest, phase links, dependencies, and lifecycle state agree.
- Persist material planning deltas throughout the conversation. Before every user-facing response, run `checkpoint --record <plan-path>`; use `--no-change` only after confirming that the turn produced no material record change.
- After approval and after the plan's execute-ready metadata is durable, run `transition execute --record <plan-path>` before handing control to `/workflow-execute`.
- During that approval handoff, set the Active Snapshot profile to `Durable` unless it is already `Audited`; never downgrade `Audited`.

Kiro `Stop` is warning-only. The hook persists pending reconciliation for an uncheckpointed turn, and later prompt/tool boundaries deny mutation until synchronization and checkpoint repair succeed.

Confirm every control call returns model-visible `WORKFLOW_*` context. If the Kiro hook is unavailable, planning may continue because it is read-only apart from plan housekeeping, but state that lifecycle enforcement is unavailable. Never mutate source in plan or bypass a denied hook decision.

New plans use a version 4 bundle and the `Lightweight` profile. Profiles affect reread and persistence cadence only. Single-file and pre-v4 records are unsupported.

Use this skill to turn an ambiguous or important request into an approved execution plan while keeping one durable Markdown bundle from the beginning of planning.

## Reference Routing

Load only the reference needed for the current stage, and read it completely before applying it.

- Read [references/plan-record.md](references/plan-record.md) before creating, updating, approving, or handing off the Markdown plan.
- Read [references/phase-planning.md](references/phase-planning.md) only when phases, dependencies, waves, or subagent eligibility materially improve the plan.
- Keep `Required references` minimal: always `references/plan-record.md`; add `references/phase-planning.md` while phases, dependencies, waves, or subagent eligibility are in use. Persist and acknowledge each set change before reading the new reference and running `rules-sync`.

## Plan-First Boundary

Follow the `/workflow-plan` workflow directly without attempting to switch or discuss the runtime's collaboration mode.

- Do not make production code edits, run destructive commands, commit, push, deploy, or implement the planned work while using this skill.
- After saving the approved plan, begin implementation only when the user explicitly requests execution; hand the saved plan to `/workflow-execute` for that work.
- Read and respect repository instructions, user rules, AGENTS.md, active developer instructions, and higher-priority safety constraints.

## Relationship to Direct Discuss Handoffs

`/workflow-plan` remains the full plan-first workflow when the user wants a separate reviewed handoff. It is not mandatory between `/workflow-discuss` and `/workflow-execute`: an execution-ready discussion bundle may be adopted directly. Do not create a duplicate plan bundle for that route.

## Discuss Fallback

Follow the conversational restrictions and question style of `/workflow-discuss` before planning when the current session has no reliable clue about what the user wants, or when the agent is confused about the right direction. Do not activate a separate discuss tracker lifecycle during this fallback; the already-created `/workflow-plan` draft remains the only Markdown planning artifact.

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
- Summarize the agreed direction before returning to the `/workflow-plan` workflow.

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
8. After approval, finalize the same exact bundle as the approved handoff. Do not create a replacement bundle or implement it in the same `/workflow-plan` flow unless the user explicitly requests execution after saving.

## Question and Open-Issue Contract

Every question that requires a user response must include concrete options. Do not ask a bare open-ended question, including when requesting clarification, confirmation, or approval. Never ask a storage-choice question for the plan bundle.

- Present each distinct issue as a separate question block. Do not combine unrelated decisions under one option list.
- Provide 2-4 practical, mutually distinguishable options that answer that question.
- Mark one option as `Recommended` or `Default` when there is a reasonable choice.
- Include `Other — specify` when the listed choices may not cover the user's intent.
- When the user must supply a free-form value unrelated to plan-file storage, such as a URL or external resource name, offer useful defaults or actions first and include an option to provide a different value. Never invent the free-form value.
- If a question is non-blocking, state which default the agent will use if the user does not answer.
- Apply these rules to questions in chat and to every item in the proposed or saved plan's `Open Questions` section.
- For each open question in a plan, record its options, recommendation/default when applicable, and whether it blocks execution.
- Before sending a response or saving a plan, check that no user-facing question or open issue lacks its own option list.
