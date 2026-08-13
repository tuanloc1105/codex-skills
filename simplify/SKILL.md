---
name: 'simplify'
description: Simplify recently changed code with a parallel, domain-aware subagent review workflow for reuse, behavior preservation, quality, and efficiency, then apply focused fixes. Use when the user asks to simplify, clean up, refactor, deduplicate, or make a change smaller/clearer, including frontend, backend, shared, or mixed changes.
metadata:
  short-description: Simplify changed code with parallel review
---

# Simplify: Code Review and Cleanup

Review changed files for reuse, behavior preservation, quality, and efficiency. If the user asked for edits, fix confirmed in-scope issues; otherwise return findings only.

## Phase 1: Identify Changes

Honor an explicit commit, branch, or commit-range scope from the caller. For a range such as `<session-start>..HEAD`, inspect that complete range with `git diff <session-start>..HEAD` and `git log --reverse --format=fuller <session-start>..HEAD`; do not reduce it to the latest commit or current working-tree diff. Also run `git status --short`, `git diff`, and `git diff --cached` to include unstaged, staged, and untracked changes in scope. Use `git diff HEAD` only when a single combined working-tree diff is useful. Include untracked files added for the current change. If the caller supplied no range and there are no git changes, review the most recently modified files that the user mentioned or that you edited earlier in this conversation.

## Scope Guardrails

Only fix issues introduced by the current diff or directly blocking the requested simplification. Do not refactor unrelated code, delete pre-existing dead code, or broaden the change into a general cleanup.

## Phase 2: Review Changed Code

Use parallel subagent review when available. Invoking `$simplify` / the simplify skill is the user's explicit request to use four concurrent reviewer-only subagents, one for each pass below. Give each a compact review packet: changed file list, diffstat, relevant hunks or file excerpts, touched symbols, and the pass-specific assignment. When no diff exists, include the relevant file contents and why those files are in scope. Tell reviewers to return only candidate findings with `file`, `line`, one-line `summary`, concrete `failure_scenario`, `recommended_fix`, and any "no findings" result.

If subagents are unavailable, rejected by tooling, or explicitly disabled, perform the same four passes yourself. Say why delegation was not used, and batch reads/searches so you do not run four redundant full scans.

Before launching or performing the review passes, classify each changed file or hunk as **frontend/UI**, **backend/service**, **shared/library**, **infra/config**, or **test-only**. Include that classification and any uncertainty in the review packet. Apply the common checklist items to every change. Apply frontend-only checks only to frontend/UI changes, backend-only checks only to backend/service changes, and both overlays to shared or mixed changes when callers cross the frontend/backend boundary. If uncertain, mark the scope as mixed and state the assumption in the final risk note.

### Agent 1: Code Reuse Review

Batch reuse discovery by changed file, symbol, or category:

1. **Search for existing utilities and helpers** that could replace newly written code. Look for similar patterns elsewhere in the codebase — common locations are utility directories, shared modules, and files adjacent to the changed ones.
2. **Flag any new function that duplicates existing functionality.** Suggest the existing function to use instead.
3. **Flag any inline logic that could use an existing utility** — hand-rolled string manipulation, manual path handling, custom environment checks, ad-hoc type guards, and similar patterns are common candidates.

### Agent 2: Behavior Preservation Review

Review the diff for accidental behavior changes introduced by the simplification:

1. **Line-by-line hunk scan**: read every changed hunk and the enclosing function. Look for wrong or inverted conditions, off-by-one boundaries, null/undefined dereferences, missing `await`, falsy-zero checks, wrong-variable copy-paste, swallowed errors, and unescaped regex metacharacters.
2. **Removed behavior audit**: for deleted or replaced lines that affect guards, validation, error handling, control flow, data shape, async behavior, public API behavior, or test coverage, name the behavior they provided. Search the new code for where that behavior is re-established. If it is missing, flag it.
3. **Cross-file tracing**: inspect callers and important callees for exported/shared functions, changed signatures, changed return shapes, changed side effects, or functions with non-local callers. Flag new preconditions, new exceptions, timing/ordering changes, or parallel changes in the same diff that make a call unsafe.
4. **Type and API contract preservation**: check exported types/interfaces, optional or nullable fields, return shapes, overloads, event names, CLI/API arguments, and env/config keys for accidental contract changes.
5. **Safety regression smoke check**: flag simplifications that remove or weaken validation, authorization checks, sanitization/escaping, path constraints, secret redaction, or safe error handling.
6. **Frontend behavior overlay**: for frontend/UI changes, check routing/navigation, form state, controlled vs uncontrolled inputs, loading/error/empty states, hydration/client-server boundaries, persisted UI state, and user-visible text or formatting.
7. **Backend behavior overlay**: for backend/service changes, check HTTP/API status and error shapes, request/response serialization, authz and tenant scoping, transaction boundaries, rollback behavior, idempotency, retry behavior, background job/queue semantics, cache invalidation, and database schema compatibility.

### Agent 3: Code Quality Review

Review the same changes for hacky patterns:

1. **Redundant state**: state that duplicates existing state, cached values that could be derived, observers/effects that could be direct calls
2. **Parameter sprawl**: adding new parameters to a function instead of generalizing or restructuring existing ones
3. **Copy-paste with slight variation**: near-duplicate code blocks that should be unified within the changed code and are not already covered by existing helper reuse
4. **Leaky abstractions**: exposing internal details that should be encapsulated, or breaking existing abstraction boundaries
5. **Stringly-typed code**: using raw strings where constants, enums (string unions), or branded types already exist in the codebase
6. **Nested conditionals**: ternary chains (`a ? x : b ? y : ...`), nested if/else, or nested switch 3+ levels deep — flatten with early returns, guard clauses, a lookup table, or an if/else-if cascade
7. **Unnecessary comments**: comments explaining WHAT the code does (well-named identifiers already do that), narrating the change, or referencing the task/caller — delete; keep only non-obvious WHY (hidden constraints, subtle invariants, workarounds)
8. **Frontend quality overlay**: for frontend/UI changes, check hooks and component lifecycle, stale closures, dependency arrays, cleanup/cancellation, mutation vs immutability, referential stability, unnecessary wrapper elements/components, semantic elements, labels, keyboard/focus behavior, necessary ARIA, and hardcoded user-facing strings when the repo has an i18n pattern.
9. **Backend quality overlay**: for backend/service changes, check service/domain boundaries, repository/data-access boundaries, business invariant placement, error taxonomy, structured logging context, configuration ownership, and whether shared helpers leak transport, persistence, or framework details into domain logic.

### Agent 4: Efficiency Review

Review the same changes for efficiency:

1. **Unnecessary work**: redundant computations, repeated file reads, duplicate network/API calls, N+1 patterns
2. **Missed concurrency**: independent operations run sequentially when they could run in parallel
3. **Hot-path bloat**: new blocking work added to startup or per-request/per-render hot paths
4. **Dependency and bundle surface**: new imports or helper reuse that pull heavy dependencies, module side effects, or browser/server-only code into the wrong runtime or hot path.
5. **Recurring no-op updates**: state/store updates inside polling loops, intervals, or event handlers that fire unconditionally — add a change-detection guard so downstream consumers aren't notified when nothing changed
6. **Unnecessary existence checks**: pre-checking file/resource existence before operating (TOCTOU anti-pattern) — operate directly and handle the error
7. **Memory**: unbounded data structures, missing cleanup, event listener leaks
8. **Overly broad operations**: reading entire files when only a portion is needed, loading all items when filtering for one
9. **Frontend efficiency overlay**: for frontend/UI changes, check avoidable re-renders, unstable props/callbacks, expensive render-time work, hydration or bundle bloat, eager asset loading, layout thrash, and client-side waterfalls.
10. **Backend efficiency overlay**: for backend/service changes, check database query shape, N+1 queries, missing pagination or limits, index-sensitive filters, connection pooling, transaction scope, streaming vs buffering, timeout/cancellation propagation, retry storms, and cache key scoping.

## Phase 3: Fix Issues

Wait for all four review passes to complete, whether they were delegated or done locally. Aggregate their candidate findings before editing:

1. **Deduplicate** candidates that point to the same defect, location, and reason. Keep the clearest failure scenario.
2. **Verify** each remaining candidate as:
   - **CONFIRMED**: the triggering input/state and wrong output, crash, or regression can be named from the code.
   - **PLAUSIBLE**: the mechanism is real but the exact trigger depends on realistic runtime state, configuration, timing, or data shape.
   - **REFUTED**: the candidate is factually wrong, impossible due to a visible invariant, already guarded in the diff, or pure style with no observable effect.
3. **Fix** CONFIRMED findings and PLAUSIBLE findings that are directly in scope for the simplification. If fixing a PLAUSIBLE finding would broaden the task, note the risk instead. Skip REFUTED findings without debate.

## Phase 4: Verify Quality Gates

After applying fixes, run the narrowest relevant checks available:

1. **Behavior preserved**: confirm the simplified code keeps the same external behavior, public API, data shape, and user-visible output unless the user asked otherwise.
2. **Tests/types/lint**: run focused tests, typecheck, lint, or build commands that match the touched files. If no suitable command exists, say so.
3. **Test adequacy**: confirm tests still assert the preserved behavior, important assertions or snapshots were not weakened, and any new shared helper or deduplicated branch has focused coverage when risk warrants it.
4. **Diff audit**: review the final diff and remove any changes that are unrelated to simplification.
5. **Dead code from this change**: remove imports, variables, helpers, or tests made unused by the simplification.
6. **Risk note**: mention any behavior that could not be verified.

When done, briefly summarize what was fixed (or confirm the code was already clean).
