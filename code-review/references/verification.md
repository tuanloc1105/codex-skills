# Candidate Verification

Verify after all finder angles complete and near-duplicates are merged. Give every remaining candidate one focused pass independent from its finder when possible.

## Contents

- Deduplication and verification case
- Three-state verdicts
- Precision and recall bias
- Verification record and guardrails

## Deduplicate

Merge candidates only when all three match:

1. the same defect;
2. the same location;
3. the same failure mechanism.

Keep candidates that share a line but fail for different inputs, states, or effects. Preserve the clearest summary, combine complementary evidence, and retain the union of origin angles and reviewer identifiers when merging.

## Build the Verification Case

For each candidate:

1. Restate the exact claim without the finder's speculation.
2. Locate the changed line and enclosing control flow.
3. Trace the minimum callers, callees, types, tests, config, or contracts needed to determine reachability.
4. Name the triggering input or state.
5. Name the observable wrong output, crash, data loss, security bypass, compatibility break, or broken side effect.
6. Search for guards or invariants that refute the trigger.
7. Classify the candidate as `CONFIRMED`, `PLAUSIBLE`, or `REFUTED`.

Base `CONFIRMED` and `REFUTED` on decisive, exact evidence rather than a
confidence impression. Cite or quote the changed line and the smallest caller, guard,
type, constant, test, configuration rule, or documented contract that proves the
verdict. If a required premise is still unknown, the evidence is not decisive.

## Verdicts

### CONFIRMED

Use `CONFIRMED` when code evidence establishes both the trigger and wrong effect.

State:

- the triggering input or state;
- the resulting wrong behavior;
- the supporting changed line and any essential contract line.

The evidence must show that the trigger is reachable and that the stated effect
follows. A likely-looking pattern without that link is not `CONFIRMED`.

### PLAUSIBLE

Use `PLAUSIBLE` when the failure mechanism is real but reachability depends on timing, environment, config, data shape, external contracts, or runtime state not provable from available code.

State:

- the realistic condition required;
- why current code does not exclude it;
- the evidence that would confirm or refute it.

Do not use `PLAUSIBLE` for a vague concern without a concrete wrong effect.

`PLAUSIBLE` may survive into the report, but it is not by itself a safe basis for
an automatic fix. Resolve the missing fact in `confirmation_needed` before
editing, or skip the fix with a concise reason; ask the user when resolution
depends on intended behavior rather than repository evidence.

### REFUTED

Use `REFUTED` only when code evidence shows that the claim is factually wrong, guarded elsewhere, impossible under a type or invariant, already handled by the diff, unreachable, or behaviorally harmless.

Cite the line, type, constant, guard, or contract that proves refutation. Do not refute merely because the trigger is rare or runtime-dependent.
If no exact evidence makes the trigger impossible, already handled, or harmless,
do not use `REFUTED` merely because the failure seems unlikely.

## Precision Bias

At `medium`, require a maintainer-actionable claim. Keep `PLAUSIBLE` only when both the mechanism and realistic trigger are specific. Resolve cheap uncertainty before reporting. Drop weak candidates that depend on multiple unsupported assumptions.

## Recall Bias

At `high`, `extra-high`, `xhigh`, `max`, and `maximum`, default realistic
uncertainty to `PLAUSIBLE` rather than `REFUTED` for:

- concurrency races and cancellation windows;
- rare but reachable nullish values;
- error handlers, cold caches, and missing optional fields;
- falsy-zero and empty-value mistakes;
- boundaries the code does not exclude;
- retries, partial failures, rollback, and recovery paths;
- regex or allowlist anchor loss;
- environment, platform, timezone, and compatibility differences.

A single non-refuted verification carries the finding. Still require a nameable trigger and observable wrong effect.

## Verification Record

Return this internal shape to the review coordinator:

```json
{
  "file": "path/to/file.ext",
  "line": 123,
  "summary": "Concise defect claim",
  "failure_scenario": "Trigger and observable wrong behavior",
  "category": "cross-file-contract",
  "origin_angles": ["line-scan", "cross-file-contract"],
  "origin_reviewers": ["finder-1", "finder-3"],
  "verdict": "PLAUSIBLE",
  "evidence": "Relevant code or contract",
  "confirmation_needed": "Specific missing fact"
}
```

Omit `confirmation_needed` for `CONFIRMED` and `REFUTED`. Discard `REFUTED` candidates before the final report. Keep provenance internal unless a caller-supplied schema explicitly requests it. Do not treat multiple origins as independent verification or use them to convert `PLAUSIBLE` into `CONFIRMED`.

## Verification Guardrails

- Do not convert a style preference into a correctness verdict. An exact applicable repository-instruction violation may remain a `conventions` finding when it meets the evidence contract in `finder-angles.md`.
- Do not rely only on a changed test when production code or a contract contradicts it.
- Do not assume an external API contract from memory when repository evidence is available.
- Do not run broad tests merely to verify one candidate when a focused trace or test is sufficient.
- Do not edit code during verification unless the user requested `--fix` and reporting has reached the fix phase.
