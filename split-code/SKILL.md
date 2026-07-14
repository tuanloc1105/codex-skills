---
name: split-code
description: Split oversized files, functions, methods, classes, modules, or packages into smaller readable units without changing behavior. Use when the user asks to split code, tách code, break up a long function/file, extract helpers, modularize code, move logic into modules/packages, or make code easier to read while preserving the exact existing logic, inputs, outputs, side effects, errors, ordering, and public API compatibility.
---

# Split Code

## Overview

Use this skill to perform structure-only refactors: make large code easier to scan by extracting cohesive helpers, modules, or packages while preserving the existing contract.

## Golden Rule

Preserve behavior exactly. Treat the task as code organization, not a rewrite.

Do not change algorithms, business rules, public APIs, input/output formats, side effects, mutation order, async sequencing, error types/messages, logging, metrics, permissions, validation behavior, or dependency semantics unless the user explicitly asks for that behavior change.

If a cleaner split requires a behavior change, stop and explain the tradeoff before editing.

## Workflow

1. Identify the requested scope: one function, one file, a class, a module, or a package boundary.
2. Inspect local context before editing: exports, imports, callers, tests, types, schemas, fixtures, snapshots, and nearby style conventions.
3. Characterize the current behavior before moving code. Prefer existing tests. If coverage is weak, note representative inputs, outputs, side effects, thrown errors, and externally visible state.
4. Choose split boundaries around cohesive stages such as parsing, validation, normalization, data access, computation, formatting, rendering, and orchestration.
5. Extract code mechanically first. Move logic with minimal edits, then repair imports, exports, names, and call sites.
6. Verify with the narrowest meaningful checks, then review the diff for accidental behavior changes.

## Split Strategy

Prefer small, named units that explain the existing intent:

- Extract pure calculations into helpers when inputs and outputs are clear.
- Extract side-effecting operations into helpers that make the side effect explicit in the name.
- Keep orchestration code readable by leaving high-level flow in the original function.
- Keep helper parameters concrete and minimal; avoid introducing broad context objects unless the code already uses that pattern.
- Keep helpers close to their only caller. Promote to shared modules only when there is real reuse or an established local pattern.
- Preserve existing public entry points. When moving exported behavior, leave wrappers or re-exports when callers depend on the old path.
- Avoid new packages, new dependency layers, or broad directory reshuffles unless the requested scope requires them.

## Behavior Preservation Checklist

Before and after each extraction, preserve:

- Function names and export names that callers use.
- Input coercion, defaults, null/undefined handling, and validation order.
- Return values, yielded values, streaming behavior, and object identity.
- Mutation targets, mutation timing, and iteration order.
- Async behavior, awaited boundaries, concurrency, retries, cancellation, and cleanup.
- Error classes, messages, wrapping, swallowing, and propagation.
- Logging, metrics, tracing, audit events, and feature flag checks.
- Date/time, randomness, floating-point behavior, locale formatting, and environment reads.

## Implementation Rules

Make the smallest structural change that improves readability.

- Match the repository's naming, formatting, module style, dependency injection style, and test style.
- Prefer extract-and-call over redesigning data flow.
- Do not optimize, deduplicate unrelated code, upgrade dependencies, change configuration, or modernize syntax as part of the split.
- Avoid changing tests to match new behavior. Update tests only for moved import paths, renamed private helpers, or added characterization coverage.
- Avoid circular imports when creating modules. If a split would create a cycle, choose a smaller helper extraction or a lower-level shared module.
- Keep comments only when they clarify a non-obvious boundary or invariant.

## Verification

Run the narrowest meaningful check available:

- The focused unit test for the function/module.
- The relevant integration test if behavior crosses module boundaries.
- Typecheck/lint only when the project normally relies on it or import/export changes make it useful.
- A small characterization script or sample command when no tests exist and it can be done safely.

If verification cannot be run, state exactly what was not run and why.

## Handoff

When finished, report:

- What code was split and where the new boundaries live.
- How public behavior was kept compatible.
- Which checks ran and their result.
- Any assumptions or residual risk from missing tests or unclear external contracts.
