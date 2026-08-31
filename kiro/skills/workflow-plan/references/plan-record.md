# Plan Record Bundle Reference

Read this reference completely before creating, updating, approving, or handing off a plan bundle.

## Saving Rules

Use a version 4 Markdown bundle. Never create a single plan file and never ask about storage.

- With no destination, create `./plans/YYYY-MM-DD-<slug>/` relative to the working directory captured at entry.
- Treat an explicit directory or its `index.md` as a bundle destination. Reject other file destinations.
- Use lowercase ASCII slugs and reserve the lowest collision-free sibling (`-2`, `-3`, and so on).
- Create missing ancestors automatically, reject Git metadata locations and escaping symlinks, then freeze the canonical bundle root.
- When entered from `/workflow-discuss`, create a separate plan bundle and record the source discussion bundle in `context.md` and `evidence.md`.
- Tell the user `Use /workflow-plan and continue the draft bundle at <root>`; after approval use `Use /workflow-execute and read the plan bundle at <root>`.

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

`Depends on` is authoritative; wave is derived. Links and metadata in `plan.md` and the phase file must agree before `write-close`.

## Persistence Contract

- Snapshot sync reads only the Active Snapshot in `index.md`; record sync reads the complete manifest.
- Before post-activation edits, run `write-open --record <root> --previous-revision <revision>`, declaring each new phase or optional file with `--path`.
- Update all affected files and cross-links, then run `write-close --record <root>`. A failed close leaves the transaction open for repair.
- Do not transition, checkpoint, stop, or mutate outside the bundle while the transaction is open.
- After close, checkpoint the turn. A no-change checkpoint is valid only when the bundle remains accurate.

## Approval and Execute Handoff

Approval requires a decision-complete bundle: concrete goal and scope, verified baseline, preservation criteria, accepted decisions, no blocking questions, complete phase dependencies and ownership, implementation logic, verification, integration gates, and rollback.

After explicit approval, update the same bundle:

```markdown
Status: Approved plan, not yet implemented
Plan mode: Exited
Execution readiness: Ready
Execute mode: Ready
Resume instruction: Invoke /workflow-execute, read index.md and every manifest file, keep this exact bundle as the execution source of truth, and continue updating it until explicit exit.
```

Set the profile to `Durable` unless already `Audited`, change Required references to the execute minimum, record approval in `evidence.md`, update the checkpoint, close the transaction, checkpoint, then run `transition execute --record <root>`.

## Quality Bar

- Make the plan operational and decision-complete without preserving a raw transcript.
- Record current behavior and evidence before changing an existing mechanism.
- Give each material risk a targeted check and each intentional behavior change explicit acceptance criteria.
- Keep phase IDs, filenames, dependencies, waves, ownership, outputs, verification, and manifest internally consistent.
- Mark subagent eligibility only for bounded, independently verifiable, non-overlapping ownership.
- Label unknowns and state how execution will resolve them; unresolved outcome-changing choices block approval.

## Repository Ignore Rule

When inside a Git worktree, idempotently ignore the containing plans directory with one root-anchored trailing-slash rule, normally `/plans/`. Preserve existing `.gitignore` content and index state. If ignore maintenance fails, retain the bundle and report the limitation.
