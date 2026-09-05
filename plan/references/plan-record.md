# Plan Record Bundle Reference

Read this reference completely before creating, updating, approving, or handing off a plan bundle.

## Saving Rules

Use a version 4 Markdown bundle. Never create a single plan file and never ask about storage.

- With no destination, create `./plans/YYYY-MM-DD-<slug>/` relative to the working directory captured at entry.
- Treat an explicit directory or its `index.md` as a bundle destination. Reject other file destinations.
- Use lowercase ASCII slugs and reserve the lowest collision-free sibling (`-2`, `-3`, and so on).
- Create missing ancestors automatically, reject Git metadata locations and escaping symlinks, then freeze the canonical bundle root.
- When entered from `$discuss`, create a separate plan bundle and record the source discussion bundle in `context.md` and `evidence.md`.
- Tell the user `Use $plan and continue the draft bundle at <root>`; after approval use `Use $execute and read the plan bundle at <root>`.

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
Plan mode: <Active | Paused | Exited>
Execution readiness: <Not ready | Ready>
Execution authorization: <Not granted | Granted>
Execute mode: <Inactive | Ready | Active | Paused | Exited>
Resume instruction: <mode-appropriate bundle instruction>
Workspace: <working directory>
Repository: <root, branch, commit>
Active action: <ID and status, or None>

<!-- workflow-active-snapshot:start version:2 -->
## Active Snapshot

Profile: <Lightweight | Durable | Audited>
Required references: <references/plan-record.md[, references/phase-planning.md]>
Goal: <current goal>
Current state: <current state>
Accepted decisions: <IDs or None>
Open items: <IDs or None>
Next safe action: <one exact action>
Supporting skills: <skill name or locator — purpose for the next action; or None>
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

Keep `Supporting skills` in the Active Snapshot limited to skills needed for the next safe action, with each skill name or locator and its purpose; use `None` when none apply. This is resume context, not the mode reference allowlist: do not add these names to `Required references` or `rules-sync`. On adoption or after compaction, reassess their relevance and the user’s exclusions before loading them; a recorded mention grants no authority and does not require automatic activation. Refresh this field when the next action changes, and remove skills whose work is finished. Existing bundles without it remain valid; add it during the next material record update when useful.

## Content Ownership

- `context.md`: goal, background, current-state inspection, behavioral baseline, preservation requirements, scope, constraints, touchpoints, desired behavior, risks, and rollback.
- `decisions.md`: accepted/rejected decisions, assumptions, unknowns, and open questions with their blocking scope. Before sending a choice question, persist its text, displayed number-to-option mapping, evidence/impact, and dependent planning, approval, or execution work. Record the answer and its constraints without expanding it into implementation permission; restore pending mappings on resume.
- `plan.md`: overall strategy, phase links, and integration gates; phase files own dependency and scheduling metadata. For a simple non-phased plan, it may also contain the one linear checklist.
- `phases/P<NN>-<slug>.md`: one self-contained phase each.
- `verification.md`: phase-local, wave integration, regression, final end-to-end checks, expected results, skipped checks, and residual risks.
- `evidence.md`: discussion source link, planning evidence, approval, amendments, action markers, commit records, execution decisions, handoff notes, re-entry, and exit.

## Phase File Contract

Use stable IDs and filenames such as `phases/P01-add-bundle-model.md`. A phase file contains:

```markdown
# P01: <name>

Status: <Pending | In progress | Completed | Blocked | Superseded>
Depends on: <IDs or None>
Wave: <positive integer>
Subagent: <Eligible | Not eligible — reason>
Owned scope: <exclusive paths/resources>
Produces: <downstream contract>

## Goal
## Context
## Tasks
- [ ] <specific action>
## Intended Logic
## Touchpoints
## Verification
## Acceptance Gate
## Rollback or Recovery
## Execution Notes
```

`Depends on` in each phase file is authoritative; `Wave` is the earliest wave derived from it. Keep scheduling, ownership, output, and status only in the phase file. In `plan.md`, use a lightweight index:

```markdown
| ID | Phase file |
| --- | --- |
| P01 | [P01](phases/P01-add-bundle-model.md) |
```

Do not duplicate phase metadata in new plan tables. Existing version 4 tables may retain duplicated columns only while their values exactly match the corresponding phase files. Every link and declared phase must resolve to a manifest file. The hook validates IDs, links in both directions, nonempty metadata, dependency cycles, and earliest waves; meaningful tasks and acceptance criteria still require review.

## Persistence Contract

- Snapshot sync reads only the Active Snapshot in `index.md`; record sync reads the complete manifest.
- Before post-activation edits, run `write-open --record <root> --previous-revision <revision>`, declaring each new phase or optional file with `--path`.
- Update all affected files and cross-links, then run `write-close --record <root>`. A failed close leaves the transaction open for repair.
- Do not transition, checkpoint, stop, or mutate outside the bundle while the transaction is open.
- After close, checkpoint the turn. A no-change checkpoint is valid only when the bundle remains accurate.

## Approval and Execute Handoff

Approval requires a decision-complete bundle: concrete goal and scope, verified baseline, preservation criteria, accepted decisions, no blocking questions, complete phase dependencies and ownership, implementation logic, verification, integration gates, and rollback.

After explicit approval, record the source and accepted scope in `evidence.md` and keep planning active:

```markdown
Status: Approved plan, not yet implemented
Plan mode: Active
Execution readiness: Ready
Execution authorization: Not granted
Execute mode: Inactive
```

Approval alone is a valid stopping point. Revisions stay in the same bundle; a material change to the approved outcome makes the affected approval stale until the user accepts it.

An answer to a requirements question approves only that choice, not the entire plan or its implementation. Keep requirement acceptance, plan approval, and execution authorization distinct; report each with its actual status. Do not complete dependent plan sections using a pending choice as an implicit default.

Only when the user explicitly requests implementation (including “approve and implement”), persist:

```markdown
Plan mode: Exited
Execution authorization: Granted
Execute mode: Ready
Resume instruction: Invoke $execute, read index.md and every manifest file, keep this exact bundle as the execution source of truth, and continue updating it until explicit exit or pause.
```

Record the execution request and scope in evidence. Checkpoint planning deltas with the planning reference set first. In the handoff write, set the profile to `Durable` unless already `Audited`, change Required references to `None` for execute adoption, update the checkpoint, and close the transaction. Then run `transition execute --record <root>`; execute acknowledges its own rules. Do not transition on approval alone.

For exit, pause, or cancellation, preserve the actual approval and checklist state, set `Plan mode: Exited` or `Paused`, record the instruction, close writes, checkpoint, and deactivate. Do not manufacture execution readiness. Follow the entrypoint recovery path if persistence fails.

## Quality Bar

- Make the plan operational and decision-complete without preserving a raw transcript. For Lightweight records, keep sections short, link evidence by ID, batch related updates, and use no-change checkpoints without timestamp-only edits. Summarize superseded history before the bundle approaches the hook’s 2 MiB limit; preserve decisions, authority, unresolved work, and evidence locators.
- Record current behavior and evidence before changing an existing mechanism.
- Give each material risk a targeted check and each intentional behavior change explicit acceptance criteria.
- Keep phase IDs, filenames, dependencies, waves, ownership, outputs, verification, and manifest internally consistent.
- Mark subagent eligibility only for bounded, independently verifiable, non-overlapping ownership.
- Label unknowns and state how execution will resolve them; unresolved outcome-changing choices block approval.

## Repository Ignore Rule

When inside a Git worktree, idempotently ignore this exact bundle with one root-anchored trailing-slash rule, such as `/plans/2026-09-05-topic/`. Reuse an existing matching rule; do not add a broad rule hiding unrelated files. Preserve existing `.gitignore` content and index state. If ignore maintenance fails, retain the bundle and report the limitation.
