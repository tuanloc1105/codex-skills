# Simplification Review Angles

Run every angle independently against the same resolved scope. Candidates need a concrete cost and a smaller safe direction, not a stylistic preference.

## Reuse

Search changed symbols and adjacent shared modules for existing helpers, validators, parsers, types, constants, policies, components, fixtures, and data-access primitives that could replace new duplication.

Keep a reuse candidate only when it:

- removes a second source of truth or realistic drift;
- consolidates behavior already intended to be identical;
- reduces repeated maintenance across named callers; or
- restores an established repository boundary.

Name the reusable source and compare contracts before recommending it. Reject reuse that pulls a heavy dependency, runtime side effect, browser/server-incompatible module, framework detail, or broader API into a narrower layer. Similar syntax alone does not prove shared intent.

## Simplification

Look for conceptual surface introduced or exposed by the change:

- redundant or derivable state;
- duplicate branches, conditions, or near-copy blocks;
- unnecessary wrappers, adapters, effects, observers, callbacks, or configuration;
- parameters that pass information already owned by the correct object or context;
- stringly-typed values when an established constant, enum, union, or branded type already governs the contract;
- comments narrating the patch or duplicating obvious code;
- abstractions with one use that hide rather than name behavior;
- helpers whose extraction separates logic from the invariant needed to understand it;
- tests or fixtures with repeated setup that obscures the asserted behavior.

Prefer fewer states, sources of truth, and execution paths over fewer lines. Flatten control flow only when it makes ordering and invariants clearer; nesting depth alone is not a defect. Preserve API documentation, protocol mappings, algorithm explanations, and comments that capture non-obvious constraints.

## Efficiency

Look for demonstrated operational cost introduced by the change:

- repeated computation, parsing, serialization, file access, queries, or remote calls;
- N+1 access patterns or unbounded reads;
- no-op updates that repeatedly notify downstream consumers;
- blocking work in startup, request, render, polling, or event hot paths;
- unbounded collections, retained closures, listeners, timers, tasks, or buffers;
- overly broad data loading where a bounded operation already exists;
- dependency or bundle growth, module side effects, or cross-runtime imports;
- retry, timeout, cancellation, cache-key, transaction, or connection-pool behavior that multiplies work.

Name the realistic frequency, scale, retention lifetime, contention, bundle boundary, or resource cost. Do not propose micro-optimization without such evidence.

Parallelize operations only when independence, result ordering, failure aggregation, cancellation, rate limits, and bounded concurrency are preserved. Remove an existence pre-check only when it creates a real check-then-act race or duplicate I/O and the direct operation preserves acceptable error semantics.

## Altitude

Check whether the change places an invariant at the correct architectural boundary:

- a special case below shared infrastructure while sibling paths still diverge;
- authorization, normalization, validation, caching, retry, or error policy duplicated beneath its source of truth;
- transport or persistence details leaking into domain logic;
- domain rules implemented separately in UI, API, worker, or repository adapters;
- a helper extracted too low or too high for the callers that own the behavior;
- a public abstraction added to solve one local call site;
- test-only seams leaking into production APIs.

Name at least one concrete sibling, caller, or boundary affected by the placement. Reject broad redesigns that require unrelated migration. Prefer the smallest shared boundary that removes actual divergence while preserving ownership.

## Domain Overlays

Apply only overlays relevant to the scope classification.

### Frontend and UI

Check derived versus stored UI state, controlled inputs, effects and cleanup, stale closures, hook dependencies, routing, loading/error/empty states, hydration boundaries, referential stability, semantic elements, focus and keyboard behavior, established localization patterns, avoidable renders, client waterfalls, eager assets, and browser bundle boundaries.

Do not trade accessibility, visible state transitions, stable server/client output, or user-facing formatting for shorter component code.

### Backend and Services

Check service/domain/repository boundaries, request and response shapes, authorization and tenant scope, transaction and rollback ownership, idempotency, background-job semantics, cache invalidation, error taxonomy, configuration ownership, query shape, pagination, streaming, timeout/cancellation propagation, and retry behavior.

Do not merge layers merely to reduce indirection when the boundary owns a transaction, policy, external contract, or replaceable dependency.

### Shared Libraries

Apply both caller-side overlays when shared code crosses frontend and backend runtimes. Check public types, tree-shaking and side effects, dependency direction, serialization, environment assumptions, and compatibility for every named consumer.

### Infrastructure and Configuration

Check duplicated configuration sources, generated versus hand-maintained state, ordering and dependency declarations, environment inheritance, secret boundaries, idempotency, rollback, and whether apparent repetition is required by the platform schema.

### Tests

Simplify setup, fixtures, helpers, and assertions only when failure diagnostics and behavioral coverage remain clear. Do not weaken assertions, broaden snapshots, hide important inputs in generic factories, or delete an apparently duplicated case that exercises a distinct boundary.
