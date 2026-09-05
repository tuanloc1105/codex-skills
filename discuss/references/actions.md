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

## Source-Code Boundary and Handoff

Do not create, edit, delete, move, rename, format, generate, or otherwise mutate source code while discuss is active. Treat application or library code, tests, executable scripts, migrations, and generated code as source code. A filename extension or a non-source tool label does not override the target's actual purpose.

Before any non-record mutation, verify its actual target and effect against the user's request and the current mode. Record the source and scope of authorization. Hook success, review PASS, a selected behavior option, and plan approval do not grant permission to implement.

A clear request to implement, fix, refactor, or otherwise change the agreed code supplies execution intent without special command wording or redundant confirmation. Satisfy Direct Execute Handoff in the tracker reference, resolve material blocking choices, persist the request's source and scope, and transition to execute before source mutation. Keep the same bundle; no separate plan is required. If the user explicitly requires remaining in discuss, explain that implementation requires execute and clarify the conflicting request before any source change.

If source impact is uncertain, inspect read-only first. Treat unresolved possible source impact as requiring execute. Never deactivate discuss merely to evade the handoff or ask a coding subagent to mutate source on its behalf.

On discovering unauthorized source edits or resuming an older source action, stop further source mutation, inspect the session-owned diff read-only, and record actual effects. Close the legacy action as paused, blocked, or failed as appropriate. Do not automatically revert, finish, commit, or call the work approved. Ask for the missing direction on the existing diff; any authorized source recovery also goes through execute. Preserve unrelated edits.

## Existing Behavior and Regression Safety

When the discussion concerns changing, replacing, removing, or refactoring an existing mechanism, establish a read-only behavioral baseline before recommending a direction or implementation plan. This analysis does not authorize source-code mutation.

- Inspect the relevant implementation, exports, callers, consumers, routes, schemas, data flows, configs, tests, logs, and docs as needed to understand the current behavior. Keep the inspection proportionate to the requested change.
- Record what is observed to work now and the evidence supporting it. Distinguish verified behavior from inference, user-reported behavior, and unknowns; never present an unverified assumption as an established baseline.
- Identify behaviors, invariants, interfaces, data contracts, error handling, UX expectations, and backward-compatibility requirements that must remain stable unless the user explicitly chooses to change them.
- Map likely touchpoints and regression risks. Separate intentional behavior changes from accidental regressions and call out downstream consumers that could break.
- Identify existing checks that demonstrate the baseline, including tests, type checks, runtime probes, screenshots, logs, or manual reproduction. Use checks with understood read-only behavior; if a useful baseline check cannot be run safely, record the gap and the evidence still needed.
- Include preservation acceptance criteria, targeted regression checks, and rollback or recovery considerations in any recommended plan.
- If the available context is insufficient to establish a material part of the baseline, label it as unknown and resolve it through safe inspection or a focused user question before recommending a potentially breaking change. When resolution requires a material user-owned decision, apply `Decision Gate` instead of continuing the baseline analysis.

## Allowed Work

- Discuss ideas, architecture, tradeoffs, risks, bugs, learning paths, or plans.
- Explain existing context using information available in the conversation or established through permitted read-only inspection.
- Ask clarifying questions and help the user decide what to do next.
- Provide non-applied examples, pseudocode, checklists, review rubrics, or implementation plans.
- Use read-only inspection when inspection is relevant to the requested discussion and the tool is reasonably established as read-only.
- Use the minimal read-only inspection needed to establish existing behavior and regression safety when the requested discussion concerns changing an existing mechanism.
- Perform the minimal local read-only inspection needed to resolve the tracker destination, identify a containing Git worktree, inspect ignore state, and verify tracker housekeeping without separate authorization.
- Create or transactionally update the automatically selected or user-specified Markdown record bundle for this discussion.
- Read and adopt an existing tracker supplied for cross-session continuation, and revalidate stale source references as required by `Cross-Session Handoff`.
- Create missing parent directories for the tracker and maintain its repository `.gitignore` rule as built-in tracker housekeeping.
- Perform an explicitly authorized non-source-code mutation within the granted scope while keeping the mode active.
- Prepare a direct execute handoff after an explicit implementation request; source changes begin only after the transition.

## Prohibited Work

Do not perform:

- Any source-code mutation while discuss remains active, including formatting, generators, tests that rewrite fixtures, or delegated implementation.
- Any mutation beyond the record bundle, its missing parent directories, and its repository `.gitignore` rule unless the user has clearly authorized it.
- Any action outside or materially beyond the authorized scope.
- Unrequested cleanup, refactoring, collateral changes, or speculative follow-up work.
- Treating permission for one mutation as permission for later or unrelated mutations.
- Treating discussion, analysis, a hypothetical request, or approval of a plan as authorization to apply it unless the user clearly asks for the change to be made.

If the user clearly requests an in-scope non-source-code mutation, perform it without requiring a mode transition. Source-code mutation follows `Source-Code Boundary and Handoff`; it never opens a temporary exception in discuss.

## Tool Discipline

Prefer answering from conversation context. Use read-only tools when relevant to the requested discussion, behavioral baseline, a factual unknown, or tracker housekeeping. Inspect likely side effects of unfamiliar commands; a script or build is not read-only merely because it is called a check. When the Immediate Decision Gate triggers, defer further inspection until the user answers.

Avoid commands or tools with side effects unless they maintain tracker housekeeping or are necessary for a non-source action authorized under `Scoped Action Authorization`. Use direct inspectable file tools or external tools within that scope. Potentially mutating shell/Git commands and opaque execution wrappers require execute; do not label them non-source to bypass the boundary. An allowed external class still requires checking actual effects, including possible source changes through remote APIs.

## Combining With Other Skills

This skill supplies the active discussion boundary, subject to higher-priority instructions and the user’s current scope. Other skill instructions remain useful for teaching style, review structure, or reasoning process. Their mutation instructions are suspended unless the mutation maintains tracker housekeeping or the user authorizes a non-source action under `Scoped Action Authorization`. Coding workflows and subagents may inspect or explain but cannot implement until Direct Execute Handoff is durable and discuss has transitioned to execute.

When combined with `$teach-for-understanding`, teach incrementally and verify understanding in chat. Put learning checkpoints in the Markdown tracker instead of creating or updating a separate `understanding-checklist.md`.
