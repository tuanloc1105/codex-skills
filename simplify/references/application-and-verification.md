# Application and Verification

Use this workflow only when the user authorized edits through a simplify, refactor, cleanup, or equivalent implementation request.

## Edit Ledger

Before editing, create an internal ledger for every `VERIFIED` proposal:

```json
{
  "proposal": "reuse-config-parser",
  "files": ["src/config.ts"],
  "reason": "remove divergent parser",
  "invariants": ["same error type", "same empty-value handling"],
  "planned_check": "focused config parser tests",
  "baseline": "starting file hash or exact hunk"
}
```

Every edit must trace to a ledger entry. Add an adjacent file only when needed to compile, update a directly affected caller, preserve the contract, or remove dead code created by the same proposal; record why.

## Apply Coherent Units

1. Re-read the current file and baseline immediately before editing so concurrent or user changes are not overwritten.
2. Apply the smallest coherent transformation that realizes one or a tightly coupled set of proposals.
3. Preserve public behavior and formatting conventions unless the request explicitly changes them.
4. Do not mix incidental bug fixes, broad formatting, dependency upgrades, or unrelated cleanup into the unit.
5. Remove imports, variables, helpers, comments, fixtures, or tests only when the applied transformation made them unused.
6. Run the planned narrow check before continuing to a dependent unit.

If repository evidence changes or a check refutes the proposal, stop applying that proposal and record it as rejected. Do not force the cleanup through by weakening a test or contract.

## Quality Gates

After all units:

1. **Behavior:** re-run the applicable equivalence cases and confirm public API, data shape, side effects, errors, ordering, user-visible output, and safety boundaries remain unchanged.
2. **Focused checks:** run relevant tests, type checks, lint, build, or a targeted reproduction for the touched paths. Use broader checks only when the change crosses shared boundaries and they add material confidence.
3. **Tests:** confirm assertions, snapshots, fixtures, and cleanup still test the same behavior with useful diagnostics. Add or adjust focused coverage when a new shared path or removed branch carries meaningful risk.
4. **Final diff:** compare against the captured baseline, not merely `HEAD`, and confirm every edit maps to the ledger.
5. **Ownership:** preserve all pre-existing changes outside the ledger and any overlapping user state.
6. **Dead code:** remove only artifacts made unused by the applied units.
7. **Net result:** confirm the change reduced a named conceptual or operational cost without adding a larger abstraction, dependency, or migration burden.

Do not claim verification for checks that did not run. Report the exact skipped check or unresolved contract and its consequence.

## Output

Summarize:

- verified improvements applied;
- concrete cost removed and important invariants preserved;
- decisions or proposals skipped;
- checks run and their results;
- meaningful residual risk.

Do not create commits, push, publish, or open a pull or merge request unless the user separately requested that action.
