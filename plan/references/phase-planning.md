# Dependency-Aware Phase Planning Reference

Read this reference completely only when phases, dependencies, execution waves, or subagent eligibility materially improve the plan.

While this structure is active, list both plan references in the Active Snapshot. Remove `references/phase-planning.md` when returning to a simple linear plan, acknowledge the write, and complete `rules-sync` before continuing.

## Dependency-Aware Phase Planning

Divide work into phases only when the boundaries improve execution, ownership, or verification. Do not turn a small linear task into artificial phases, and do not treat phase numbering or list order as an implicit dependency.

When phases are useful, assign zero-padded stable IDs such as `P01`, `P02`, and create exactly one self-contained `phases/P<NN>-<slug>.md` file for each phase. Declare every phase file in the `index.md` manifest and link it from the authoritative table in `plan.md`. Record for each phase:

- `Depends on`: prerequisite phase IDs or `None`
- `Wave`: the earliest execution wave allowed by those dependencies
- `Subagent`: `Eligible` or `Not eligible — <reason>`
- `Owned scope`: files, modules, services, external systems, or other mutable resources the phase may change
- `Produces`: the concrete result or contract returned for downstream work
- Phase-local verification and any cross-phase integration gate
- Intended logic, touchpoints, acceptance gate, rollback or recovery, and an executable task checklist

Treat `Depends on` as the source of truth and `Wave` as a derived scheduling aid:

- Put phases with no unmet implementation dependencies in Wave 1, even when they appear later in the document.
- Put phases in the same later wave only when all of their dependencies finish in earlier waves.
- Mark `Subagent: Eligible` only when the phase is bounded, does not consume another same-wave phase's output, has non-overlapping ownership, can be verified independently, and has a clear handoff result.
- Mark a phase not eligible when it may overlap another phase's files or mutable state, or when it owns shared contracts, migrations, lockfiles, generated artifacts, external side effects, or stateful processes without an explicit safe coordination strategy.
- Default to `Not eligible` when independence cannot be established confidently.

Before closing a record write, verify that the phase ID, filename, dependency list, wave, eligibility, owned scope, and output agree between `plan.md` and the phase file. A declared phase without a file, an unlisted phase file, duplicate phase ID, missing dependency, or dependency cycle blocks approval.

Eligibility means the executing agent may delegate the phase to a separate subagent; it is not a requirement to do so. Runtime capacity, current repository state, newly discovered coupling, or delegation overhead may justify serial execution. The main executing agent remains responsible for plan progress, shared resources, integration, conflict resolution, and cross-phase verification.

While using `$plan`, document this execution structure but do not spawn subagents to implement production work.
