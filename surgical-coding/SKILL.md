---
name: surgical-coding
description: Use for non-trivial code edits, bug fixes, refactors, tests, reviews, and repo-grounded implementation. Emphasizes reading before writing, surgical scope, local conventions, and narrow verification.
---

# Surgical Coding

Use this skill for non-trivial code edits, bug fixes, refactors, tests, reviews, and repo-grounded implementation.

## Workflow

1. State assumptions when the request is ambiguous. If ambiguity changes the implementation materially, ask before editing.
2. Read before writing: inspect relevant exports, immediate callers, tests, shared utilities, and nearby conventions.
3. Make the smallest change that solves the requested problem.
4. Avoid speculative abstraction, configurability, or unrelated cleanup.
5. Match the codebase's conventions, even when another style seems preferable.
6. Verify with tests, typecheck, lint, runtime checks, screenshots, or targeted reproduction according to task risk.
7. Report skipped checks, uncertainty, and residual risk clearly.

## Guardrails

- Every changed line should trace to the user's request.
- Remove only unused code introduced by your change.
- Do not delete or rewrite unrelated existing hooks, config, code, comments, or formatting.
- If two local patterns conflict, choose the more recent or better-tested pattern and name the conflict.
