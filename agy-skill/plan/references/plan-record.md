# Plan Record Bundle Reference (Antigravity Edition)

Read this reference completely before creating, updating, approving, or handing off a plan bundle.

## Saving Rules

Use a version 4 Markdown bundle. Never create a single plan file and never ask about storage.

- With no destination, create `./plans/YYYY-MM-DD-no<N>-<slug>/` relative to the working directory captured at entry.
- Treat an explicit directory or its `index.md` as a bundle destination. Reject other file destinations.
- Use lowercase ASCII slugs. Number new bundles independently within `./plans/` for each calendar date: inspect sibling directory names matching that date's `YYYY-MM-DD-no<N>-*` form, take the greatest positive integer `N`, and use `N + 1`; start at `no1` when none match. Ignore legacy names and malformed or non-positive sequence values, and never reuse a missing lower number.
- Reserve the selected directory with an atomic create. If it already exists because another writer won the race, recompute from the current siblings and retry with the next sequence number. The sequence belongs only to the containing `plans/` directory and is independent of the sequence under `discussion/`.
- Create missing ancestors automatically, reject Git metadata locations and escaping symlinks, then freeze the canonical bundle root.
- When entered from `discuss`, create a separate plan bundle and record the source discussion bundle in `context.md` and `evidence.md`.
- Tell the user `Use plan and continue the draft bundle at <root>`; after approval use `Use execute and read the plan bundle at <root>`.

Create this base layout:

```text
<bundle>/
├── index.md
├── context.md
├── decisions.md
├── plan.md
├── verification.md
├── evidence.md
└── phases/
    └── P<NN>-<slug>.md
```

`phases/` may be empty only for a genuinely small linear plan. Every phase declared in `plan.md` must have exactly one self-contained phase file, and every phase file must be declared in both the plan table and manifest.

## Index Template

```markdown
# Plan Record: <name>

<!-- workflow-record version:4 kind:plan tracker-id:<stable ID> -->

Tracker ID: <stable non-secret ID>
Created: <timestamp and timezone>
Last updated: <timestamp and timezone>
Status: <Draft planning discussion | Approved plan, not yet implemented | In progress | Implemented | Blocked | Paused>
Plan mode: <Active | Exited>
Execution readiness: <Not ready | Ready>
Execute mode: <Inactive | Ready | Active | Exited>
Resume instruction: <mode-appropriate instruction containing the canonical bundle root and tracker ID>
Workspace: <working directory>
Repository: <root, branch, commit>
Active action: <ID and status, or None>

<!-- workflow-active-snapshot:start version:2 -->
## Active Snapshot

Profile: <Lightweight | Durable | Audited>
Required references: <references/plan-record.md[, references/planning-workflow.md][, references/phase-planning.md]>
Goal: <current goal>
Current state: <current state>
Accepted decisions: <IDs or None>
Open items: <IDs or None>
Next safe action: <one exact action>
<!-- workflow-active-snapshot:end -->

## Resume Checkpoint

- Last completed:
- Current work:
- Blocking decision or dependency:
- Next safe action:
- Deferred work:
- Revalidation required:

<!-- workflow-manifest:start -->
index.md
context.md
decisions.md
plan.md
verification.md
evidence.md
<one phases/P<NN>-<slug>.md entry per phase>
<!-- workflow-manifest:end -->
```

The manifest begins with `index.md`; every entry is a unique relative `.md` path inside the bundle. `index.md` is the sole location for identity, lifecycle markers, Active Snapshot, manifest, and resume checkpoint.

## Content Ownership

- `context.md`: goal, background, current-state inspection, behavioral baseline, preservation requirements, scope, constraints, touchpoints, desired behavior, risks, and rollback.
- `decisions.md`: accepted/rejected decisions, assumptions, unknowns, and option-bearing open questions.
- `plan.md`: overall strategy, authoritative phase dependency table, derived waves, integration gates, and links to phase files. For a simple non-phased plan, it may also contain the one linear checklist.
- `phases/P<NN>-<slug>.md`: one self-contained phase each.
- `verification.md`: phase-local, wave integration, regression, final end-to-end checks, expected results, skipped checks, and residual risks.
- `evidence.md`: discussion source link, planning evidence, approval, amendments, action markers, commit records, execution decisions, handoff notes, re-entry, and exit.
