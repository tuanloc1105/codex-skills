# Discuss Actions and Baseline Reference (Antigravity Edition)

Read this reference completely before baseline analysis of an existing mechanism, any scoped mutation, or combining discuss with another skill.

## Scoped Action Authorization

Treat a clear instruction to perform a non-source-code action as authorization for that action. Do not require the user to disable `discuss`, use special wording, or approve every individual supporting step.

Treat automatic tracker path selection, collision handling, missing directory creation, and the repository ignore update described below as built-in tracker housekeeping. Perform them without separate user authorization; they are not scoped mutation exceptions.

- Require a clear target, action, or outcome from which the permitted scope can be reasonably determined.
- Perform the normal supporting actions necessary to complete the authorized task when they stay within that scope.
- Keep authorization limited to the requested task and its completion. Do not treat it as blanket or permanent permission.
- Do not expand the scope to unrelated files, systems, people, or follow-up work.
- Ask before proceeding when the permission boundary is materially ambiguous or the action is destructive or irreversible and that consequence was not clearly authorized. Use `ask_question` when prompting.
- Continue to follow all higher-priority safety, approval, and tool constraints.
- Record the authorized scope and results in `actions.md`, with durable evidence in `evidence.md` when needed.

Examples of mutations that may be authorized without leaving the mode include editing non-code documents, creating requested artifacts, updating tickets or issues, or modifying a specifically named external resource.

## Temporary Source-Code Actions

The user may request a bounded action that creates, edits, deletes, moves, renames, formats, generates, or otherwise mutates source code while `discuss` remains the surrounding mode. Treat application or library code, tests, executable scripts, migrations, and generated code as source code.

Before starting such an action:

1. Identify the bounded requested outcome and disclose that completing it will mutate source code, naming the expected source-code scope when reasonably known.
2. Require the user to confirm that source-code impact. A request that already explicitly asks to edit, implement, fix, refactor, generate, or otherwise change named code is both the request and confirmation when its mutating effect is unambiguous; do not ask redundantly. A plan approval, hypothetical statement, or request to discuss a possible change is not confirmation.
3. Persist the action scope, confirmation, expected touchpoints, and `Action status: Authorized` in the tracker before mutation. If persistence fails, do not start the action.
4. Temporarily lift only the source-code mutation restriction needed for that action. Apply Antigravity editing tools (`replace_file_content`, `write_to_file`) or shell commands (`run_command`); do not broaden authorization or treat it as permission for unrelated follow-up work.
5. When the action succeeds, fails, or becomes blocked, persist its files or resources changed, checks and results, residual risks, and terminal action status. Then automatically resume full `discuss` behavior and the `Immediate Decision Gate` before responding. State that discuss remains active.

If it is unclear whether a target counts as source code, disclose that it will be treated as source code and obtain confirmation before mutating it. Read-only inspection remains allowed under the rules below.

An authorized source-code action is a temporary excursion within `discuss`, not a mode transition. Do not set `Mode status: Exited`, mark the tracker execution-ready, invoke `execute`, or create a `plan` merely because the action requires code changes.

## Existing Behavior and Regression Safety

When the discussion concerns changing, replacing, removing, or refactoring an existing mechanism, establish a read-only behavioral baseline before recommending a direction or implementation plan. This analysis does not authorize source-code mutation.

- Inspect the relevant implementation, exports, callers, consumers, routes, schemas, data flows, configs, tests, logs, and docs as needed to understand the current behavior. Use Antigravity read tools (`view_file`, `grep_search`, `find_by_name`, `list_dir`). Keep inspection proportionate to the requested change.
- Record what is observed to work now and the evidence supporting it. Distinguish verified behavior from inference, user-reported behavior, and unknowns; never present an unverified assumption as an established baseline.
- Identify behaviors, invariants, interfaces, data contracts, error handling, UX expectations, and backward-compatibility requirements that must remain stable unless the user explicitly chooses to change them.
- Map likely touchpoints and regression risks. Separate intentional behavior changes from accidental regressions and call out downstream consumers that could break.
- Identify existing checks that demonstrate the baseline, including tests, type checks, runtime probes, logs, or manual reproduction. Use only checks guaranteed not to mutate source or external state (`run_command` with non-destructive flags); if a useful baseline check cannot be run safely, record the gap and the evidence still needed.
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
