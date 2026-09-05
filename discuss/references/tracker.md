# Discuss Record Bundle Reference

Read this reference completely before creating, adopting, persisting, or handing off a discussion record bundle.

## Bundle Requirement

Use a version 4 Markdown bundle, never a single tracker file. Resolve every relative destination against the working directory captured at skill entry and never ask a storage-choice question.

- With no destination, create `./discussion/YYYY-MM-DD-<slug>/`.
- Treat an explicit directory or its `index.md` as an existing bundle to adopt. Other file paths are invalid record destinations.
- Use lowercase ASCII slugs. On collision, reserve the lowest available sibling such as `-2`, then `-3`.
- Create missing ancestors automatically. Reject Git metadata locations, path traversal, and symlinks that escape the bundle.
- Freeze the canonical bundle root for the mode lifetime. Tell the user that root and the resume prompt `Use $discuss and continue the record bundle at <root>`.

Create these files initially:

```text
<bundle>/
├── index.md
├── context.md
├── decisions.md
├── actions.md
└── evidence.md
```

`index.md` is the control plane. Its manifest lists every bundle-owned Markdown path, beginning with `index.md`. `context.md` holds goal, scope, current state, source-of-truth evidence, baseline, preservation requirements, risks, and constraints. `decisions.md` holds assumptions, decisions, requirements, and open questions. `actions.md` holds scoped-action authorization and results. `evidence.md` holds the log, handoff evidence, amendments, commit records, and execute action markers.

A Direct Execute Handoff may add `plan.md`, `verification.md`, and `phases/P<NN>-<slug>.md`. Declare new paths with `write-open --path` and add them to the manifest in the same transaction.

## Index Contract

Use this shape in `index.md`:

```markdown
# Discussion Record

<!-- workflow-record version:4 kind:discuss tracker-id:<stable ID> -->

Tracker ID: <stable non-secret ID>
Created: <timestamp and timezone>
Last updated: <timestamp and timezone>
Mode: $discuss
Mode status: <Active | Awaiting decision | Paused | Exited>
Execution readiness: <Not ready | Ready>
Execute mode: <Inactive | Ready | Active | Paused | Exited>
Resume instruction: Invoke $discuss, read index.md and the manifest files required by the current state, and continue this exact bundle before substantive work.
Workspace: <captured working directory>
Repository: <root, branch, commit>
Mutation boundary: <current boundary>
Active action: <ID and status, or None>

<!-- workflow-active-snapshot:start version:2 -->
## Active Snapshot

Profile: <Lightweight | Durable | Audited>
Required references: <references/tracker.md[, references/actions.md]>
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
- Authorization record:
- Revalidation required:

<!-- workflow-manifest:start -->
index.md
context.md
decisions.md
actions.md
evidence.md
<!-- workflow-manifest:end -->
```

Every declared path must be a relative `.md` path inside the bundle, unique, non-symlinked, and readable. Do not keep record content in undeclared files.

## Persistence and Sync

- Snapshot sync requires reading only the delimited Active Snapshot in `index.md`.
- Record sync requires reading `index.md` and every manifest file completely.
- Before any post-activation bundle edit, run `write-open --record <root> --previous-revision <acknowledged revision>`. Add one `--path <absolute path>` for each new Markdown file.
- While the transaction is open, mutate only allowed bundle paths. Update every affected cross-file reference before closing.
- Run `write-close --record <root>` only after the manifest, tracker identity, state, phase links, and evidence markers are consistent. A failed close leaves the transaction open for repair.
- Never transition, checkpoint, stop, or perform non-record mutation while a write transaction is open.
- After a successful close, complete the normal checkpoint. Use `checkpoint --no-change` only for a genuinely unchanged turn.

If persistence fails, do not present unsaved conclusions as durable state. Report the failed files and stop before further substantive work.

## Cross-Session Handoff

On resume, canonicalize the supplied directory or `index.md`, read the complete bundle, validate its identity and manifest, restore the Active Snapshot and Resume Checkpoint, then compare recorded repository/external revisions with live state when they matter. Preserve earlier authorization for the same task and scope unless revoked or invalidated by material drift; adoption or inspection alone adds no new authority.

If two bundles claim the same tracker ID or the lineage is ambiguous, preserve both, record the conflict, and apply the Decision Gate.

## Transition Gate

When discussion is settled, persist the outcome. Offer these handoffs when further work is wanted; stopping after discussion is also valid:

1. `$plan` — close this bundle and create a separate plan bundle linked back to it.
2. `$execute` — make this same bundle execution-ready and let execute adopt it.

For an explicit exit or pause, preserve the discussion and its unfinished items, set `Mode status: Exited` or `Paused`, record the request, close actions and writes, checkpoint, then deactivate. Do not turn cancellation into an execution handoff. If persistence is unavailable, use the entrypoint recovery procedure and disclose what remains unsaved.

For `$plan`, set `Mode status: Exited`, record the transition in `evidence.md`, close the write transaction, checkpoint, then run `transition plan --record <root>`. `$plan` creates a distinct bundle under its own saving rules.

For direct `$execute`, require concrete goal/scope/requirements/constraints, no blocking question, verified baseline and preservation criteria, an executable plan, verification, and initialized evidence/handoff state. Add:

- `plan.md` with the execution strategy and links to phase files. Phase files own scheduling metadata; a small linear task needs only a checklist.
- One self-contained `phases/P<NN>-<slug>.md` for each declared phase.
- `verification.md` with phase, integration, regression, and final checks.

Then atomically persist in the bundle:

```markdown
Mode status: Exited
Status: Approved for execution
Execution readiness: Ready
Execution authorization: Granted
Execute mode: Ready
Resume instruction: Invoke $execute, read index.md and every manifest file, keep this exact bundle as the execution source of truth, and continue updating it until explicit exit or pause.
```

The explicit request to execute supplies `Execution authorization: Granted`; record its source and scope in evidence. First checkpoint discussion deltas with the current reference set. Then set the profile to `Durable` unless already `Audited`, replace Required references with `None` for execute adoption, persist the handoff metadata above, and close the transaction. Run `transition execute --record <root>`; execute then acknowledges its own references. Do not run discuss rules-sync against execute reference names.

## Authority and Evidence

The bundle is authoritative for recorded discussion state, not for live repository, ticket, API, database, or external-system behavior. In `context.md`, classify material claims as verified, user-reported, inferred, proposed, or unknown and include exact locators, revisions or observation times, conflicts, and revalidation conditions. Higher-priority instructions and current live state override stale bundle content.

Use stable decision and question IDs. Preserve superseded history without leaving contradictory entries active. Do not store transcripts, hidden reasoning, secrets, unrelated chat, or raw implementation output. In Lightweight records, keep each section concise and use IDs/links instead of duplicating evidence. Batch related turn deltas in one transaction; unchanged turns use a no-change checkpoint without timestamp-only edits. Summarize superseded details while preserving decisions, authority, unresolved items, evidence locators, and revalidation needs. The hook accepts bundles up to 2 MiB; compact history well before that limit, never by deleting unresolved work.

## Repository Ignore Rule

When the bundle is inside a Git worktree, idempotently add one root-anchored trailing-slash rule for this exact bundle, such as `/discussion/2026-09-05-topic/`. Preserve existing `.gitignore` content and ordering, never alter the index, and verify the bundle is ignored. Reuse an existing broader matching rule without adding another; do not add a broad rule that would hide unrelated files. If ignore maintenance fails, retain the selected bundle and report the limitation.
