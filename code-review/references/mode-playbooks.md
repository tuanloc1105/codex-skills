# Mode Playbooks

Use the playbook selected by the user's requested effort. Default to `medium`. Preserve the user's target, base, focus files, exclusions, and extra instructions in every delegated task and verification pass.

## Low

Use this mode for a fast, hunk-only review.

1. Read the changed-file summary and unified diff once.
2. Cover the explicit target first. Otherwise cover committed and uncommitted branch changes.
3. Skip test and fixture hunks under `test/`, `spec/`, `__tests__/`, `fixtures/`, and `testdata/`, plus `*_test.*` and `*.test.*` files.
4. Do not read full files, inspect callers, spawn reviewers, or run verification.
5. Flag only hunk-visible runtime defects, duplicated helpers visible in the diff context, and dead code left by the diff.
6. Return at most four findings, most severe first, one line each:

   ```text
   path/to/file.ext:123 — what's wrong and the concrete failure
   ```

7. Return exactly `(none)` when nothing qualifies.

Do not infer behavior from code outside the hunk. Do not report style, naming, generic performance advice, missing tests by itself, or speculative contract drift.

## Low Minimum

Use this mode only when the user explicitly requests a minimum number of findings or exhaustive low-effort coverage.

1. Perform the `low` playbook.
2. Target `min(files_changed, 4)` findings without lowering the evidence bar.
3. When short of the target, make one additional hunk-only pass over the largest changed file and every removed code block.
4. Return `(none)` when no qualifying finding remains after the extra pass.

Treat the target as a search obligation, never as permission to invent findings.

## Medium

Use this mode for precision-biased review.

1. Gather the diff and inspect enclosing functions, callers, callees, tests, schemas, migrations, flags, config, and contracts only as needed.
2. Run correctness angles A-C and all five supporting angles from `finder-angles.md` independently.
3. Let each angle produce up to six candidates with a nameable failure scenario.
4. Deduplicate candidates after all finder passes.
5. Verify every remaining candidate with the precision-biased rules in `verification.md`.
6. Keep at most eight verified findings, most severe first.

Every reported issue should be something a maintainer would act on. Do not let finders silently drop half-believed candidates; verification owns the final decision.

## High

Use this mode for recall-biased review within the same finder scope as `medium`.

1. Run correctness angles A-C and all five supporting angles independently.
2. Let each angle produce up to six candidates.
3. Pass every candidate with a nameable scenario into recall-biased verification.
4. Default realistic uncertainty to `PLAUSIBLE` unless code refutes it.
5. Keep at most ten verified findings, most severe first.

Favor catching real defects over suppressing uncertain but reachable failure mechanisms.

## Extra High

Use this mode for broad recall with specialist angles and a fresh gap sweep.

1. Run correctness angles A-E and all five supporting angles independently.
2. Let each angle produce up to eight candidates.
3. Deduplicate only after all finder passes complete.
4. Run recall-biased three-state verification for every candidate.
5. Run the complete fresh-review sweep in `deep-sweep.md` against the deduplicated surviving list.
6. Verify every new sweep candidate before reporting it.
7. Keep at most fifteen verified findings, most severe first.

## Maximum

Use the `extra-high` playbook with the same fifteen-finding cap. Spend the additional effort on broader repository evidence, more complete caller and contract tracing, and stronger verification rather than inventing more categories or lowering the evidence bar.

## Reviewer Orchestration

When parallel reviewers are available and permitted:

1. Assign each selected finder angle to an independent reviewer.
2. Give each reviewer the raw diff, target, and user constraints.
3. Do not give a finder another finder's conclusions.
4. Run independent finder tasks concurrently within the available concurrency limit.
5. Assign each deduplicated candidate to a verifier that did not originate it when practical.
6. Give a gap-sweep reviewer the diff and deduplicated findings so it searches only for missing classes.

When independent reviewers are unavailable:

1. Run the same angles sequentially in one context.
2. Reset the question and evidence for each angle; do not let an earlier conclusion suppress later candidate generation.
3. Deduplicate and re-check each candidate in a separate self-contained pass.
4. Do not claim independent verification when only a same-context self-check ran.
