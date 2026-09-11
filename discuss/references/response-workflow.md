# Discuss Response Workflow

Read this reference completely before handling an actionable request in discuss, including tracker initialization, baseline analysis, scoped actions, or a workflow transition. The entrypoint's Immediate Decision Gate and Question Style remain mandatory throughout. For an explicitly continued bundle, add `references/response-workflow.md` to Required references through the normal record transaction and verify the saved Required references before proceeding; for a new bundle, read this file before initialization and include it in the initial required set.

## Response Pattern

When a user asks for something actionable while this mode is active:

Apply `Immediate Decision Gate` throughout every step below. When it triggers, stop at the current step and do not advance until the user answers.

1. Resolve the Markdown bundle destination automatically. On a new invocation, default to `./discussion/YYYY-MM-DD-no<N>-<discussion-name>/` and allocate the next daily sequence under `discussion/` according to `references/tracker.md`, even if the request supplies an existing bundle. Adopt and freeze an existing bundle or its `index.md` only when the user explicitly asks to continue, resume, or update that exact bundle; otherwise keep it read-only as source context when relevant.
2. For a new bundle, create missing parents, atomically reserve the sequenced directory with collision retry, and initialize its required Markdown files and manifest. For an explicitly requested continuation or handoff, validate the existing bundle without replacing content.
3. Identify any containing Git worktree from the selected path's nearest existing ancestor and create or update the root `.gitignore` idempotently according to `Repository Ignore Rule`.
4. If the bundle is an explicitly requested continuation or handoff, read `index.md` and every manifest file, adopt the exact root, and restore its checkpoint before changing content.
5. Initialize or transactionally update the selected bundle with current discussion state and housekeeping.
6. For an explicitly requested continuation or handoff, revalidate material drift before relying on recorded external facts.
7. If the discussion concerns changing an existing mechanism, establish and record the behavioral baseline, preservation requirements, regression risks, and evidence gaps before recommending the change.
8. Determine whether the user already chose a `$plan` or `$execute` transition for the active tracker.
9. If `$plan` was chosen, durably exit discuss under `Settled Discussion Transition Gate` and hand the complete tracker to `$plan` as context.
10. If `$execute` was chosen, apply `Direct Execute Handoff`; remain in discuss when its gate cannot pass, otherwise persist the exit and hand the exact bundle to `$execute` without creating a separate plan bundle.
11. Otherwise, when the discussion is settled and no blocking question remains, apply `Settled Discussion Transition Gate`, ask whether the user wants `$plan` or `$execute`, and wait.
12. Otherwise determine whether the requested action would mutate source code.
13. If it would mutate source code, apply `Temporary Source-Code Actions`: disclose the impact, obtain confirmation when the request is not already unambiguous, persist authorization, perform and verify only the bounded action, persist its result, and automatically resume discuss.
14. If it is a non-source-code mutation and the user's instruction clearly authorizes it, record the scope, perform the change, and verify it proportionately.
15. If mutation has not been clearly authorized, provide analysis, options, pseudocode, or a step-by-step plan without applying it.
16. Apply `Tracker Durability Gate` before every response after substantive work.
17. Clarify that `discuss` remains active after every scoped action. Only a persisted transition to `$plan` or `$execute` exits it.
18. Format every question that needs a user response as its own option block under the mandatory `Question Style` contract.
