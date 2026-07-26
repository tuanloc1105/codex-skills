# Finder Angles

Run the angles selected by the active mode independently. Record every candidate before deduplication.

## Contents

- Candidate record
- Correctness angles A-E
- Supporting angles
- Non-findings

## Candidate Record

Capture:

- `file`: repository-relative path.
- `line`: the smallest changed line that demonstrates the defect.
- `summary`: one-line defect claim.
- `failure_scenario`: triggering input or state plus the observable wrong result.
- `category`: short kebab-case angle slug.
- `evidence_needed`: code, contract, runtime fact, or test needed to verify uncertainty.

Keep two candidates on the same line when their failure mechanisms differ. Drop a candidate during finding only when no concrete failure scenario can be named.

## Correctness A: Line-by-Line Diff Scan

Read every changed hunk line by line, then inspect the enclosing function.

Ask for each changed line:

- What input, state, timing, platform, or dependency response makes this wrong?
- Does the condition reverse or narrow previous behavior?
- Does zero, an empty value, `null`, `undefined`, or a missing optional field take the wrong branch?
- Is an index, range, count, timeout, page offset, or boundary off by one?
- Is an async result returned, awaited, cancelled, or propagated correctly?
- Is the wrong variable, receiver, identifier, or collection used?
- Is an error swallowed, replaced, double-wrapped, or converted into success?
- Is dynamic text inserted into a regex, query, shell expression, path, or serializer without required escaping?

Treat unchanged lines in a touched function as in scope only when the change re-exposes them, changes their preconditions, or fails to repair behavior the patch claims to fix.

## Correctness B: Removed-Behavior Auditor

For every deleted or replaced line, or coherent block when the lines enforce one
behavior together:

1. Name the guard, invariant, side effect, cleanup, error path, validation rule, or compatibility behavior it previously enforced.
2. Locate where the new code re-establishes that behavior.
3. Create a candidate when the replacement is absent, narrower, ordered incorrectly, or only covers one path.

Pay special attention to removed authorization checks, rollback, cleanup, retries, normalization, default handling, error propagation, feature-flag behavior, and tests deleted to accept changed behavior.

Do not report deletion by itself. Name the reachable wrong effect caused by losing the behavior.

## Correctness C: Cross-File and Contract Tracer

Trace every changed function, including private and local functions, through its
direct callers and callees. Do the same for other changed public or cross-file
symbols. Search for the symbol rather than assuming its scope from its name or
visibility.

Check for changes to:

- accepted inputs and new preconditions;
- return types, shapes, nullability, ordering, and pagination;
- exceptions, error codes, retry semantics, and transaction boundaries;
- sync versus async timing, cancellation, and callback ordering;
- serialization, schemas, generated types, migrations, and stored data;
- feature flags, configuration defaults, environment assumptions, and compatibility promises.

Evaluate the combined PR, not each file in isolation. A parallel change to a
callee in the same PR can make an otherwise unchanged call site unsafe through a
new precondition, result shape, exception, or ordering requirement.

Inspect tests and fixtures as evidence of the contract. Flag a test change when it merely makes an old behavior assertion accept a regression. Do not treat a missing test as a finding without an underlying behavior defect.

## Correctness D: Language and Framework Pitfalls

Use this angle at `extra-high`, `xhigh`, `max`, and `maximum`, and whenever the
diff clearly triggers it at a lower mode.

Check established traps for the active language and framework, including:

- JavaScript or TypeScript: falsy-zero checks, coercive equality, promise loss, closure capture, prototype or object-key hazards, regex state, and incomplete discriminated-union handling.
- Python: mutable defaults, late-bound closures, iterator exhaustion, broad exception capture, truthiness mistakes, and naive datetime handling.
- Go: nil-map writes, typed-nil interfaces, range-variable capture, ignored errors, slice aliasing, deferred cleanup ordering, and context loss.
- SQL and data access: injection, missing predicates, changed join cardinality, nullable comparisons, transaction gaps, and unbounded result sets.
- Cross-language: timezone or DST drift, float equality, integer overflow, path separator assumptions, locale-sensitive parsing, encoding, and resource ownership.

Flag only a concrete instance introduced or made reachable by the change. Do not emit a generic language checklist as findings.

## Correctness E: Wrapper and Proxy Correctness

Use this angle at `extra-high`, `xhigh`, `max`, and `maximum`, and whenever the
diff adds or changes a cache, proxy, decorator, adapter, client wrapper,
repository wrapper, or middleware layer.

Verify that every caller-used method:

- routes to the intended wrapped instance rather than a registry, session, global, or the wrapper itself;
- forwards all arguments, defaults, context, cancellation, and metadata;
- preserves result shape, errors, side effects, ordering, and async behavior;
- invalidates or updates wrapper-owned cache and state consistently;
- avoids re-entry, recursion, double instrumentation, double retry, and double transformation;
- remains exposed when the underlying interface grows.

Trace at least one real caller for any method whose correct receiver or forwarding contract is uncertain.

## Supporting: Reuse

Find new code that duplicates an existing helper, validator, parser, authorization rule, cache key, schema, or other source of truth. Keep the candidate only when duplication can produce observable divergence, inconsistent security, incompatible output, or repeated maintenance errors. Name the existing reusable source.

## Supporting: Simplification

Find dead code, redundant branching, unnecessary state, duplicated conditions, or indirection introduced or left behind by the diff. Keep the candidate only when the complexity creates a concrete correctness or maintenance hazard, such as two paths enforcing different invariants or stale state becoming reachable.

## Supporting: Efficiency

Find wasted work the diff introduces, including:

- repeated I/O, queries, parsing, allocation, serialization, locking, remote calls, or unbounded work;
- independent operations made unnecessarily sequential instead of safely concurrent;
- blocking work added to initialization, startup, or a realistic hot path;
- long-lived closures or callback objects that retain a much larger enclosing scope than they use.

For closure retention, identify the captured value and object lifetime that make
the retention material. Prefer a class, struct, or explicit callable that stores
only the required fields when that is the cheaper safe shape. Name the realistic
hot path, input scale, timeout, contention, retained memory, or
resource-exhaustion scenario and the cheaper alternative. Do not report
micro-optimizations or generic performance preferences.

## Supporting: Altitude

Check whether the change implements a shared invariant at the wrong layer, fixes
one symptom while sibling paths remain broken, or duplicates policy below its
source of truth. A special case layered onto shared infrastructure is a signal
that the underlying mechanism may need to enforce the invariant instead. Name at
least one sibling path, caller, or shared boundary that still fails or can
diverge; do not propose a broader abstraction without that concrete consequence.

## Supporting: Conventions

Find every applicable `AGENTS.md` and other repository instruction file that the
environment or user declares authoritative for a changed file. Respect the
documented directory scope and precedence, including nearer ancestor-directory
instructions when present.

Report an instruction violation only when the candidate can cite:

- the instruction file's repository-relative or absolute source path;
- the exact applicable rule; and
- the exact offending changed line.

An explicit applicable rule violation is actionable even when the rule is
procedural or stylistic. Do not infer the "spirit" of an instruction, turn a
general preference into a rule, or report anything for this sub-check when no
governing rule can be quoted.

Separately compare changed behavior with established repository patterns for
error handling, compatibility, config, logging, transactions, async control
flow, APIs, and tests. Report an undocumented-pattern deviation only when it
changes runtime behavior or operational expectations; ignore cosmetic
inconsistency.

## Non-Findings

Do not report:

- style, formatting, or naming preferences, unless an exact applicable repository instruction explicitly requires them;
- missing tests without a behavior defect;
- generic performance or architecture advice;
- cleanup with no observable consequence;
- pre-existing defects unrelated to the touched behavior;
- a theoretical risk whose triggering state the code excludes;
- duplicate descriptions of the same defect, location, and mechanism.
