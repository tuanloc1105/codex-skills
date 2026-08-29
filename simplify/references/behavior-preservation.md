# Behavior Preservation

Behavior preservation verifies proposed transformations; it is not an independent search for unrelated bugs. For each candidate, compare the current scoped behavior with the proposed smaller form before editing.

## Proposal Verdicts

- `VERIFIED`: repository evidence establishes that the proposal reduces a concrete cost and preserves every applicable invariant.
- `NEEDS_DECISION`: the improvement is credible, but intended behavior, ownership, compatibility, or a tradeoff cannot be determined from available evidence.
- `REJECTED`: the proposal is not simpler in net terms, duplicates intentional behavior, violates an invariant, expands scope, or rests on a false premise.

Only `VERIFIED` proposals are safe to apply automatically. A small diff is not sufficient evidence. Resolve cheap uncertainty through focused callers, tests, types, configuration, history, or documentation; ask the user when the missing fact is an intent decision.

## Build the Equivalence Case

For each proposal:

1. State the concrete cost being removed.
2. Describe the exact transformation and touched symbols.
3. List input, output, state, side-effect, error, timing, ordering, cancellation, resource, and compatibility invariants that apply.
4. Trace the minimum callers, callees, types, tests, and boundaries needed to establish those invariants.
5. Check edge states already admitted by the code: empty, zero, nullish, boundary, partial failure, retry, cancellation, mixed-version, and platform-specific behavior where relevant.
6. Compare dependency direction, runtime environment, initialization, and module side effects when reusing or moving code.
7. Identify the narrow check that can validate the transformation after editing.
8. Assign a verdict with evidence and any decision still needed.

Use an internal record such as:

```json
{
  "file": "src/file.ext",
  "line": 123,
  "category": "reuse",
  "summary": "Reuse the canonical config parser",
  "concrete_cost": "Two parsers disagree on empty values",
  "recommended_change": "Route both callers through parseConfig",
  "behavior_invariants": ["Preserve ConfigError", "Preserve empty-value normalization"],
  "evidence": "Both callers already accept the canonical result type",
  "verdict": "VERIFIED"
}
```

## Contract Checklist

Inspect only applicable contracts:

- accepted inputs, defaults, nullability, and normalization;
- return type, value shape, ordering, pagination, and formatting;
- exceptions, status codes, retryability, logging, and error causes;
- sync or async completion, event order, cancellation, and cleanup;
- authorization, tenant scope, validation, escaping, and redaction;
- transactions, rollback, cache invalidation, idempotency, and durable data;
- public APIs, CLI arguments, configuration, environment variables, wire formats, schemas, and stored data;
- routes, form behavior, loading/error/empty states, hydration, focus, accessibility, and user-visible text;
- test intent, assertion strength, diagnostics, and fixture lifecycle.

Do not infer an external contract from memory when repository evidence exists. Do not use a changed test alone to justify behavior drift when production code, public types, or documentation contradict it.

## Net Simplification

Record meaningful before-and-after effects rather than treating line count as the goal:

- sources of truth removed;
- states or branches removed;
- duplicate implementations or policies removed;
- parameters, dependencies, or boundary crossings removed;
- indirection introduced or removed;
- hot-path work or retained resources reduced;
- callers migrated within the authorized scope.

Reject a proposal when its new abstraction, dependency, configuration, or migration burden outweighs the named cost. A few extra explicit lines may be simpler than a generic abstraction with hidden coupling.
