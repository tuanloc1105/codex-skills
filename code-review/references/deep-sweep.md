# Deep Gap Sweep

Run this sweep after verification at `extra-high`, `xhigh`, `max`, and
`maximum`. Approach the diff as a fresh reviewer who can see the deduplicated
surviving findings. Search only for defects not already listed. An existing
category or mechanism does not suppress an uncovered defect at another location;
do not restate the same defect, location, and failure mechanism.

The fresh pass may run in a separate reviewer or as a deliberately reset
same-context reread when no reviewer is available. In either case, reread the
diff and enclosing functions rather than relying on the first pass's conclusions.

## Contents

- Input and data shape
- Extraction, defaults, and asymmetry
- Authorization and trust boundaries
- Lifecycle and resource ownership
- Persistence and transactions
- Concurrency and ordering
- Error recovery and observability
- Compatibility and platform behavior
- Sweep procedure

## Input and Data Shape

Stress:

- empty and singleton collections;
- zero, negative, maximum, and boundary values;
- missing, nullish, stale, duplicated, and out-of-order fields;
- malformed or partially valid payloads;
- changed serialization, normalization, defaults, and enum handling;
- pagination boundaries and mixed-version stored data.

Keep a candidate only when the code does not exclude the triggering state.

## Extraction, Defaults, and Asymmetry

Look specifically for mechanisms that broad first passes often miss:

- moved or extracted code that drops a guard, validation, cleanup step, regex or allowlist anchor, initialization, or ordering constraint;
- mutable function, field, or dataclass defaults evaluated once and then shared across calls or instances;
- process-random or otherwise nondeterministic `hash()` values used for persisted identifiers, cache keys, protocol values, or stable sharding;
- predicate, getter, or query-style methods that now have side effects, so repeated or reordered evaluation changes behavior;
- test or fixture setup that acquires or mutates state without symmetric teardown, or teardown that still targets the pre-change resource;
- lock-scope shrinkage that moves a dependent read, write, check, or cleanup outside the protected region;
- configuration defaults that flip behavior for callers or deployments that omit an explicit value.

For each candidate, name the triggering reuse, ordering, process boundary,
omitted configuration, or lifecycle path and its observable wrong effect.

## Authorization and Trust Boundaries

Check:

- authorization before every new read, write, export, or side effect;
- tenant, account, organization, and resource ownership boundaries;
- validation order relative to lookup and mutation;
- privilege changes introduced by fallback or error paths;
- escaping and injection boundaries for queries, templates, paths, shells, and URLs;
- secrets or sensitive fields newly logged, cached, serialized, or returned.

Require a concrete bypass, disclosure, or unauthorized effect.

## Lifecycle and Resource Ownership

Trace initialization, steady state, failure, cancellation, and teardown.

Check:

- partial initialization and cleanup ordering;
- double close, missing close, leaked handles, goroutines, tasks, subscriptions, listeners, and timers;
- cancellation propagation and work continuing after the caller stops;
- retries that duplicate non-idempotent effects;
- wrapper or pool ownership confusion;
- shutdown races and callbacks firing after disposal.

## Persistence and Transactions

Check:

- writes split across transaction boundaries;
- rollback that leaves derived state, files, messages, or caches behind;
- migration ordering, backward compatibility, defaults, and downgrade assumptions;
- stale reads after writes and missing cache invalidation;
- idempotency under retries and duplicate delivery;
- partial failure between database, queue, filesystem, and external API effects.

Name the durable inconsistent state or lost update.

## Concurrency and Ordering

Check:

- read-modify-write races;
- lock scope, deadlock order, and unlocked shared state;
- promises, futures, tasks, or callbacks completed in the wrong order;
- deduplication and cache stampede behavior;
- timeout and cancellation races;
- event ordering, replay, duplicate processing, and eventual consistency windows.

Do not report concurrency merely because shared state exists. Name the interleaving and wrong effect.

## Error Recovery and Observability

Check:

- errors converted into success, empty data, or stale data;
- lost error types, codes, causes, retryability, and context;
- fallback paths that violate the primary contract;
- cleanup or rollback errors masking the original failure;
- logging or metrics changes that make operational failure materially invisible;
- retries without limits, jitter, backoff, or idempotency when exhaustion is realistic.

## Compatibility and Platform Behavior

Check:

- public API, CLI, config, environment, wire-format, schema, and stored-data compatibility;
- timezone, locale, encoding, numeric precision, and daylight-saving transitions;
- path separators, case sensitivity, symlinks, permissions, and filesystem atomicity;
- dependency version ranges and feature availability established by project manifests;
- mixed old and new clients, workers, or database schemas during rollout.

## Sweep Procedure

1. List the exact defect, location, and failure mechanism covered by each surviving finding.
2. Walk every changed hunk and touched symbol once.
3. Apply the sections above only to defects not already listed; another finding with the same category or mechanism does not suppress an uncovered instance at a different location.
4. Record candidates with file, changed line, summary, failure scenario, category, and evidence needed.
5. Deduplicate new candidates against the existing list.
6. Keep at most eight new candidates, prioritizing severity and non-overlapping mechanisms.
7. Verify every new candidate with the active mode's recall-biased rules.
8. Add only `CONFIRMED` and `PLAUSIBLE` results to the final ranking.

If the fresh reread finds no genuinely new mechanism, return an empty sweep. Do
not pad the list or re-confirm an existing finding to fill the eight-candidate
allowance.
