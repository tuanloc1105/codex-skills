---
name: code-review
description: Claude-Code-inspired code review workflow for diffs, pull requests, branches, commits, or working-tree changes. Use for low, medium, high, extra-high, or maximum-effort reviews; minimum-findings low mode; precision- or recall-biased bug finding; three-state verification; structured ReportFindings output; GitHub inline comments; or applying verified fixes with --fix.
---

# Claude Code Review

Review changed code for actionable defects a maintainer would fix. Prioritize crashes, wrong outputs, lost invariants, data loss, security-sensitive bypasses, broken async or control flow, compatibility regressions, and concrete reuse, simplification, efficiency, architectural-altitude, or repository-convention problems. Do not report style, naming, generic performance advice, missing tests by itself, or cleanup without an observable maintenance or runtime consequence.

## Select the Mode

Infer the mode from the user's wording. Default to `medium`.

| Mode | Candidate Search | Verification | Finding Cap |
| --- | --- | --- | --- |
| `low` | one hunk-only diff pass | none | 4 |
| `low-minimum` | one hunk-only pass, then one focused extra pass if short | none | target `min(files_changed, 4)` |
| `medium` | 3 correctness + 5 supporting angles, up to 6 candidates each | three-state, precision-biased | 8 |
| `high` | 3 correctness + 5 supporting angles, up to 6 candidates each | three-state, recall-biased | 10 |
| `extra-high` | 5 correctness + 5 supporting angles, up to 8 candidates each | three-state + gap sweep | 15 |
| `max` / `maximum` | 5 correctness + 5 supporting angles, up to 8 candidates each | three-state + gap sweep | 15 |

Use `low-minimum` only when the user explicitly requests a minimum number of findings or exhaustive low-effort coverage. Never invent findings to meet its target.

At `medium`, favor precision: every reported issue should be something a maintainer would act on. At `high`, `extra-high`, and `max`, favor recall: pass every candidate with a nameable failure scenario into verification instead of silently dropping uncertain candidates.

## Gather the Diff

Read the requested target before judging it. Honor an explicit base or target first. Otherwise, for a local branch, cover both committed and uncommitted changes with the equivalent of:

```text
git diff @{upstream}...HEAD
git diff HEAD
```

Fall back to the repository's main branch or the working tree when no upstream exists. Gather the changed-file summary and unified diff, then inspect enclosing functions, callers, callees, tests, fixtures, schemas, generated types, migrations, feature flags, config, and documented contracts only as needed to establish behavior. Keep large raw outputs out of the conversation; index or summarize them and retrieve focused sections.

For `low` and `low-minimum`, make one diff-reading call, skip test and fixture hunks (`test/`, `spec/`, `__tests__/`, `*_test.*`, `*.test.*`, `fixtures/`, `testdata/`), do not read full files, and judge only what is visible in the hunk.

## Generate Candidates Independently

Run each selected angle independently. Do not let one angle suppress another. Preserve two candidates on the same line when their failure mechanisms differ; deduplicate only after generation. Record `file`, `line`, one-line `summary`, concrete `failure_scenario`, and a short kebab-case `category` for every candidate.

### Correctness A: Line-by-Line Diff Scan

Read every hunk line by line, then inspect the enclosing function. Treat bugs in unchanged lines of a touched function as in scope when the change re-exposes them or fails to fix them. Ask what input, state, timing, or platform makes each line wrong. Look for inverted conditions, off-by-one errors, null or undefined dereferences, missing `await`, falsy-zero checks, wrong-variable copy-paste, swallowed errors, and unescaped regex metacharacters.

### Correctness B: Removed-Behavior Auditor

For every deleted or replaced line, identify the invariant or behavior it enforced and locate where the new code re-establishes it. Keep candidates for removed guards, dropped error paths, narrowed validation, lost cleanup, or deleted behavior whose replacement is incomplete.

### Correctness C: Cross-File and Contract Tracer

Trace changed public or cross-file symbols through callers and callees. Check new preconditions, return shapes, exceptions, timing, ordering, serialization, schemas, migrations, flags, and tests that encode behavior. Flag concrete compatibility or contract drift, including tests changed merely to accept a regression.

### Correctness D: Edge-Case Matrix

For `extra-high` and `max`, stress empty and singleton inputs, zero and negative values, missing optional fields, duplicates, cold caches, retries, partial failures, concurrency, cancellation, timezone or locale shifts, and platform-specific paths. Keep a candidate only when the code does not exclude the triggering state.

### Correctness E: Lifecycle and Persistence Sweep

For `extra-high` and `max`, inspect authorization, initialization and teardown ordering, rollback, persistence, cache invalidation, resource ownership, and error recovery. Require a concrete wrong effect, not a general concern.

### Supporting Angles

Run all five supporting angles at `medium` and above:

- `reuse`: find new code that duplicates an existing helper, abstraction, validation rule, or source of truth and can diverge observably.
- `simplification`: find dead code or unnecessary branching, state, or indirection introduced or left behind by the diff when it creates a concrete correctness or maintenance hazard.
- `efficiency`: find repeated I/O, queries, parsing, allocation, or unbounded work with a realistic hot-path, scale, timeout, or resource-exhaustion scenario.
- `altitude`: check whether the fix lives at the wrong layer, handles a symptom instead of the shared invariant, or leaves sibling paths broken. Name an affected path.
- `conventions`: compare with established repository patterns when deviating changes behavior, error handling, compatibility, or operational expectations. Do not report cosmetic inconsistency.

## Low-Effort Output

Flag only hunk-visible runtime bugs, duplicated helpers visible in diff context, and dead code left by the diff. Do not infer from code outside the hunk.

Return at most four findings, most severe first, one line each:

```text
path/to/file.ext:123 — what's wrong and the concrete failure
```

Return exactly `(none)` when nothing qualifies. In `low-minimum`, target `min(files_changed, 4)` findings; if short, make one more pass over the largest changed file and removed code blocks, then return `(none)` only when the diff is trivially correct. The target is a search obligation, not permission to lower the evidence bar.

## Verify Candidates

Deduplicate candidates with the same defect, location, and reason. Give each remaining candidate one focused verification pass, independent from its finder. When the execution environment and applicable instructions permit parallel reviewers, one verifier per candidate is preferred; otherwise perform a separate self-contained pass.

Classify each candidate:

- `CONFIRMED`: name the triggering input or state and the wrong output, crash, or broken effect; cite the supporting line.
- `PLAUSIBLE`: the mechanism is real, but trigger certainty depends on timing, environment, config, data shape, or runtime state; state what would confirm it.
- `REFUTED`: the claim is factually wrong, guarded elsewhere, provably impossible by a type, constant, or invariant, already handled in the diff, or has no observable effect; cite the refuting line.

Keep `CONFIRMED` and `PLAUSIBLE`; discard `REFUTED`. A single non-refuted verification carries a finding.

In recall-biased modes, default realistic uncertainty to `PLAUSIBLE`, not `REFUTED`: races, rare-but-reachable nullish values, error-handler paths, cold caches, missing optional fields, falsy-zero bugs, boundary off-by-one cases, retry storms, partial failures, and regex or allowlist anchor loss. Refute only with evidence constructible from the code.

## Run the Gap Sweep

For `extra-high` and `max`, sweep all changed hunks and touched symbols after verification. Search for any class not yet covered: data shape, authorization, lifecycle ordering, cancellation, persistence, migration, cache invalidation, rollback, observability-impacting error handling, or compatibility. Add only candidates with a concrete scenario and verify them before reporting.

## Report Findings

Rank findings most severe first and respect the mode cap. For human-readable output, put findings before the summary. Include the file and line, severity when useful, concise title, concrete failure scenario, why the change causes it, category, and verification verdict when a verify pass ran. If none survive, say so clearly and mention only meaningful residual risk or skipped checks.

When a ReportFindings-style tool is available or the caller requests structured output, call it exactly once with:

```json
{
  "level": "medium",
  "findings": [
    {
      "file": "path/to/file.ext",
      "line": 123,
      "summary": "Concise defect title",
      "failure_scenario": "Trigger and observable wrong behavior",
      "category": "correctness",
      "verdict": "CONFIRMED"
    }
  ]
}
```

Use an empty `findings` array when nothing survives. Do not print a duplicate textual findings list after using the reporting tool.

## Post GitHub Comments

When the user passes `--comment` or explicitly requests comments and the target is a GitHub PR, first produce the findings list, then post one inline PR comment per finding with the available GitHub inline-comment capability. Include a suggestion block only when it fully fixes the issue. If unavailable, fall back to an appropriate configured GitHub API or CLI; otherwise print the findings and state that posting was skipped. If the target is not a PR, print the findings and state that commenting was ignored.

## Apply Fixes

When the user passes `--fix` or explicitly requests fixes, produce and verify the findings first, then apply each valid correctness, reuse, simplification, efficiency, altitude, and conventions fix to the working tree. Skip and briefly explain any finding whose fix would change intended behavior, require changes well outside the reviewed diff, or is a false positive. Run the narrowest meaningful verification, then report what was fixed, what was skipped, and any checks not run. If a ReportFindings-style tool is required, call it after applying fixes and do not duplicate its findings in prose.
