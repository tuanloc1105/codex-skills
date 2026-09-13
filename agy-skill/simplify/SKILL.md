---
name: simplify
description: Simplify recently changed code while preserving behavior. Use when the user asks to simplify, clean up, refactor, deduplicate, reduce state or indirection, improve reuse, or make frontend, backend, shared, infrastructure, or test code clearer and smaller in conceptual surface.
metadata:
  short-description: Simplify changed code without behavior drift
---

# Simplify Changed Code (Antigravity Edition)

Improve the quality of changed code through reuse, simplification, efficiency, and correct architectural placement. Preserve externally observable behavior unless the user explicitly requests a behavior change. This is a transformation workflow, not a general bug hunt: report an incidental correctness or security defect, but do not silently broaden cleanup into a code review or security audit.

When the user asks to simplify, clean up, refactor, or deduplicate, apply verified in-scope improvements. When the user asks only for an audit, analysis, or recommendations, return findings without editing.

## Load References

Read all runtime references before reviewing or editing:

- [target-and-scope.md](references/target-and-scope.md) for target resolution, ownership, and baselines.
- [review-angles.md](references/review-angles.md) for the four cleanup angles and domain overlays.
- [behavior-preservation.md](references/behavior-preservation.md) for proposal verification and equivalence evidence.
- [application-and-verification.md](references/application-and-verification.md) when edits are authorized.

For maintenance comparisons with extracted Claude Code prompts, use [upstream-crosswalk.md](references/upstream-crosswalk.md). It is provenance documentation; do not load it during ordinary simplification work.

## Resolve Scope

Resolve the exact target and create the scope manifest and working-tree baseline described in `target-and-scope.md`. Explicit historical targets do not include unrelated working-tree changes unless the user requests both. Treat user paths, exclusions, behavior changes, and public-contract constraints as hard boundaries.

Only propose or apply improvements introduced by the resolved change or directly necessary to simplify it. Do not refactor unrelated code, remove pre-existing dead code, or rewrite surrounding modules merely because a broader design looks preferable.

## Review Independently

Classify each changed file or hunk as frontend/UI, backend/service, shared/library, infrastructure/configuration, or test-only, with mixed classifications when boundaries cross. Run all four angles from `review-angles.md` independently so one pass does not suppress another:

1. **reuse**
2. **simplification**
3. **efficiency**
4. **altitude**

### Antigravity Subagent Passes

Use independent reviewer-only subagent passes via Antigravity's `invoke_subagent` when available:

- Dispatch 4 subagents in a single `invoke_subagent` call with `TypeName: 'research'`, each assigned one specific angle (`Role: 'Reuse Reviewer'`, `Role: 'Simplification Reviewer'`, `Role: 'Efficiency Reviewer'`, `Role: 'Altitude Reviewer'`).
- Give each reviewer the same compact scope manifest, changed-file classifications, diffstat, and touched symbols.
- If subagents cannot be invoked, perform separate sequential passes locally and disclose that provenance.

Each pass returns candidate records containing:

- `file` and the smallest relevant changed `line`;
- `summary` and angle `category`;
- `concrete_cost`: duplication, state, indirection, boundary leakage, wasted work, or maintenance divergence;
- `recommended_change`;
- `behavior_invariants` that the change must preserve;
- `evidence_needed` for unresolved assumptions;
- `origin_reviewer` when delegated.

Do not force every cleanup into a bug-shaped failure scenario. Include `failure_scenario` only when an observable runtime failure is part of the evidence.

## Reconcile and Verify Proposals

Pool all candidates after every angle finishes. Merge only candidates with the same opportunity, location, and mechanism; preserve complementary rationale and reviewer provenance. Resolve conflicting recommendations by this priority:

1. requested behavior and public contracts;
2. security, authorization, resource ownership, cancellation, and ordering;
3. runtime and domain boundaries;
4. fewer sources of truth, states, and execution paths;
5. reuse and deduplication;
6. readability and conceptual surface;
7. demonstrated hot-path or resource cost;
8. line-count reduction.

Verify each proposed transformation with `behavior-preservation.md` and classify it as `VERIFIED`, `NEEDS_DECISION`, or `REJECTED`. Apply only `VERIFIED` proposals. Resolve missing repository evidence when cheap; ask the user (using `ask_question`) before applying a `NEEDS_DECISION` proposal whose intended behavior or tradeoff cannot be inferred. Drop `REJECTED` proposals without editing.

## Apply and Finish

When edits are authorized, follow `application-and-verification.md`: keep an edit ledger, apply focused coherent units using Antigravity editing tools (`replace_file_content`, `write_to_file`), run narrow checks via `run_command`, compare against the baseline, and remove only dead code created by the simplification. A change is successful when it reduces conceptual or operational cost without violating an invariant; fewer lines alone is not evidence of improvement.

Report applied improvements, skipped decisions, checks run, and meaningful residual risk. If no verified improvement exists, say the scoped code is already sufficiently simple rather than manufacturing cleanup.
