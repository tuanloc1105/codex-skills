# Discuss Actions and Baseline Reference

Read this reference completely before baseline analysis of an existing mechanism, any scoped mutation, or combining discuss with another skill.

## Scoped Action Authorization

Treat a clear instruction to perform a non-source-code action as authorization for that action. Do not require the user to disable `discuss`, use special wording, or approve every individual supporting step.

Treat automatic tracker path selection, collision handling, missing directory creation, and the repository ignore update described below as built-in tracker housekeeping. Perform them without separate user authorization; they are not scoped mutation exceptions.

- Require a clear target, action, or outcome from which the permitted scope can be reasonably determined.
- Perform the normal supporting actions necessary to complete the authorized task when they stay within that scope.
- Keep authorization limited to the requested task and its completion. Do not treat it as blanket or permanent permission.
- Do not expand the scope to unrelated files, systems, people, or follow-up work.
- Ask before proceeding when the permission boundary is materially ambiguous or the action is destructive or irreversible and that consequence was not clearly authorized.
- Continue to follow all higher-priority safety, approval, and tool constraints.
- Record the authorized scope and results in `actions.md`, with durable evidence in `evidence.md` when needed.

Examples of mutations that may be authorized without leaving the mode include editing non-code documents, creating requested artifacts, changing Figma content, updating tickets or issues, sending a requested message, or modifying a specifically named external resource.

## Absolute Source-Code Mutation Ban

Source-code mutation is absolutely prohibited while `discuss` is active. There is no confirmation, disclosure, or bounded-excursion path that permits it. Treat application or library code, tests, executable scripts, migrations, configuration consumed by code, and generated code as source code. If it is unclear whether a target counts as source code, treat it as source code and do not mutate it.

When the user asks to create, edit, delete, move, rename, format, generate, or otherwise change source code:

1. Do not start the change and do not partially apply it. Never lift this restriction, even when the request is explicit, urgent, repeated, small, or already scoped to named files.
2. State plainly that discuss does not modify source code, and record the requested outcome, expected touchpoints, and `Action status: Blocked by discuss source-code ban` in the tracker.
3. Provide the analysis, options, diff sketch, pseudocode, or implementation plan instead, without applying it.
4. Apply `Settled Discussion Transition Gate` and ask through `AskUserQuestion` whether the user wants `/plan` or `/execute` to carry out the change.
5. Keep discuss active until that transition is chosen and its exit state is persisted. Only `/plan` or `/execute`, after discuss has durably exited, may mutate source code.

Read-only inspection of source code remains allowed under the rules below.

## Existing Behavior and Regression Safety

When the discussion concerns changing, replacing, removing, or refactoring an existing mechanism, establish a read-only behavioral baseline before recommending a direction or implementation plan. This analysis does not authorize source-code mutation.

- Inspect the relevant implementation, exports, callers, consumers, routes, schemas, data flows, configs, tests, logs, and docs as needed to understand the current behavior. Keep the inspection proportionate to the requested change.
- Record what is observed to work now and the evidence supporting it. Distinguish verified behavior from inference, user-reported behavior, and unknowns; never present an unverified assumption as an established baseline.
- Identify behaviors, invariants, interfaces, data contracts, error handling, UX expectations, and backward-compatibility requirements that must remain stable unless the user explicitly chooses to change them.
- Map likely touchpoints and regression risks. Separate intentional behavior changes from accidental regressions and call out downstream consumers that could break.
- Identify existing checks that demonstrate the baseline, including tests, type checks, runtime probes, screenshots, logs, or manual reproduction. Use only checks guaranteed not to mutate source or external state; if a useful baseline check cannot be run safely, record the gap and the evidence still needed.
- Include preservation acceptance criteria, targeted regression checks, and rollback or recovery considerations in any recommended plan.
- If the available context is insufficient to establish a material part of the baseline, label it as unknown and resolve it through safe inspection or a focused user question before recommending a potentially breaking change. When resolution requires a material user-owned decision, apply `Immediate Decision Gate` instead of continuing the baseline analysis.

## Allowed Work

- Discuss ideas, architecture, tradeoffs, risks, bugs, learning paths, or plans.
- Explain existing context using information available in the conversation or established through permitted read-only inspection.
- Ask clarifying questions and help the user decide what to do next.
- Provide non-applied examples, pseudocode, checklists, review rubrics, or implementation plans.
- Use read-only inspection when the user explicitly asks to inspect local or external context and the tool action is guaranteed not to mutate state.
- Use the minimal read-only inspection needed to establish existing behavior and regression safety when the requested discussion concerns changing an existing mechanism.
- Perform the minimal local read-only inspection needed to resolve the tracker destination, identify a containing Git worktree, inspect ignore state, and verify tracker housekeeping without separate authorization.
- Create or transactionally update the automatically selected new Markdown record bundle for this discussion, or the specific existing bundle the user explicitly asked to continue.
- Read and adopt an existing tracker only when the user explicitly requests cross-session continuation; otherwise treat a supplied tracker as read-only context for the new bundle.
- Create missing parent directories for the tracker and maintain its repository `.gitignore` rule as built-in tracker housekeeping.
- Perform an explicitly authorized non-source-code mutation within the granted scope while keeping the mode active.
- Read source code without modifying it, and describe an unapplied change as analysis, diff sketch, pseudocode, or plan.

## Prohibited Work

Do not perform:

- Any source-code mutation, for any reason, under any instruction, while discuss is active.
- Any mutation beyond the record bundle, its missing parent directories, and its repository `.gitignore` rule unless the user has clearly authorized it.
- Any action outside or materially beyond the authorized scope.
- Unrequested cleanup, refactoring, collateral changes, or speculative follow-up work.
- Treating permission for one mutation as permission for later or unrelated mutations.
- Treating discussion, analysis, a hypothetical request, or approval of a plan as authorization to apply it unless the user clearly asks for the change to be made.

If the user clearly requests an in-scope non-source-code mutation, perform it without requiring a mode transition. If the requested task requires source-code mutation, apply `Absolute Source-Code Mutation Ban`: refuse the mutation, record it, and route the user to `/plan` or `/execute`. Never require or infer a durable discuss exit merely to perform a bounded non-source-code action.

## Tool Discipline

Prefer answering from conversation context. Use read-only tools only when the user requests inspection, when they are necessary to establish existing behavior and regression safety for a requested change, or when they are necessary for tracker housekeeping. Confirm that the tools will not change source code, local runtime state, or external state.

Avoid commands or tools with side effects unless they maintain tracker housekeeping or are necessary for an action authorized under `Scoped Action Authorization`. Before using a mutating tool, verify that its target and effect fit the granted scope and touch no source code. If source-code impact is possible, do not run it; disclose the impact and route the change to `/plan` or `/execute`.

## Combining With Other Skills

This skill is a hard overlay on top of all other skills. Other skill instructions remain useful for teaching style, review structure, or reasoning process. Their mutation instructions are suspended unless the mutation maintains tracker housekeeping or the user authorizes a non-source-code action under `Scoped Action Authorization`. A coding skill loaded during discuss informs analysis only; it never authorizes a source-code edit. A direct `/execute` invocation uses `Direct Execute Handoff`: `/execute` must not mutate source code until the tracker is durably marked ready and discuss is exited.

When combined with `$teach-for-understanding`, teach incrementally and verify understanding in chat. Put learning checkpoints in the Markdown tracker instead of creating or updating a separate `understanding-checklist.md`.
