# Execute Record Intake

Read this reference completely before validating or adopting a supplied record, including fresh-session adoption, re-entry, or a direct handoff. Read it before the initial validation; once the record is accepted, persist `references/intake.md` in Required references and complete rules-sync under the entrypoint lifecycle before substantive work.

## Plan and Tracker Intake

Read `index.md` and every manifest file before substantive work, adopt the canonical root, and apply the metadata update through the applicable sequence below. Never copy a direct discussion handoff into another bundle.

Verify these basics:

- The bundle is version 4 with a valid manifest and is either an approved plan or exited, execution-ready discussion record.
- `context.md`, `plan.md`, `verification.md`, and `evidence.md` exist, and every declared phase has one valid phase file.
- No unresolved item in `decisions.md` blocks execution.
- The record status is approved or the user explicitly asked to execute it.
- For a phased plan, read `## Execution Structure` and capture each phase's ID, dependencies, wave, subagent eligibility, owned scope, produced output, and verification or integration requirements.

Reject an active or not-ready discussion tracker as an execution input. Do not silently finish its discussion, choose unresolved options, or manufacture a plan inside execute mode. In the same task, keep `$discuss` active and complete its `Direct Execute Handoff`; in a fresh task, tell the user to resume `$discuss` on that exact tracker before trying `$execute` again.

For an accepted discussion tracker, preserve `Mode status: Exited`, set `Execute mode: Active`, apply the standard execute resume instruction, and use the tracker as the sole execution source of truth. Missing scheduling metadata remains subject to the sequential backward-compatibility rule below.

Treat an explicit user request to execute the supplied record as execution approval even when its status is missing or still says `Draft`, `Ready`, or `Awaiting execution`. A request only to read, inspect, summarize, or adopt the record activates execute mode and its bookkeeping but does not authorize implementation.

Ask for confirmation only when the record explicitly says not to implement, an unresolved choice materially changes the desired outcome, repository drift invalidates the approved goal or requires materially different scope, or two authoritative requirements cannot both be satisfied. Do not invent a materially different plan.

Treat `Depends on` as authoritative and any declared wave as a scheduling hint that must agree with it. Revalidate phase independence against the current repository and runtime before dispatch. An eligibility note never overrides overlapping files, shared mutable state, unstable contracts, or newly discovered dependencies.

Reject phased plans with missing dependency, wave, ownership, output, phase-file, or acceptance metadata. Simple plans without phases execute sequentially; do not infer parallel permission from numbered steps.

When working in a git repository, capture the initial status and current diff boundaries before parallel dispatch so pre-existing user changes can be distinguished and preserved.

## Fresh-Session Bootstrap

Use this sequence only when the hook is dormant and no workflow is active in the current session. A supplied record path and an explicit request to implement it authorize execution within that record's accepted scope; a read-, summary-, or adoption-only request authorizes bookkeeping only. Do not request redundant confirmation.

1. Read this entrypoint's required intake guidance and every manifest file, validate the accepted record, and resolve its exact canonical root. Do not create a replacement bundle or use bootstrap to repair an invalid, unapproved discussion record.
2. Before activation, perform only the initial record housekeeping: in `index.md`, set `Execute mode: Active`, `Last updated`, the execute resume instruction, the current Active Snapshot with `references/intake.md`, and `Durable` unless already `Audited`. Record the adoption and whether the current request authorizes implementation in the existing `evidence.md`. Preserve the manifest, identity, scope, decisions, phase files, implementation status, and existing action/evidence markers. Write complete files and revalidate the bundle before activating.
3. This initial housekeeping is the only pre-activation exception to `write-open`/`write-close`: no active workflow or acknowledged revision exists yet. Do not run `sync` or `write-open` before activation, fabricate a revision, deactivate another workflow, or change source code, Git state, or external systems under this exception. If another workflow is active, use its handoff instead; a hook denial must never be bypassed as bootstrap.
4. Run `activate execute --record <root>`. Require the model-visible activation confirmation. Read the full record and required rules, run `sync --record <root> --scope record`, then `rules-sync --record <root> --reference references/intake.md`. After activation, every further record edit uses the normal acknowledged-revision transaction.
5. For a read-only request, persist any remaining evidence and checkpoint without changing implementation status or opening an implementation action. For an execution request, load/add/sync `references/implementation.md`, then proceed through its evidence and scoped-action gates. Adoption never grants push, deploy, or unrelated mutation permission.

## Active-Session Handoff

Use this sequence after the source skill has successfully run `transition execute` on the same bundle. Do not use the dormant bootstrap exception here.

1. Read the complete entrypoint, this reference, and every manifest file. Keep the source mode's Required references unchanged until the transition has succeeded. The transition resets acknowledgement, so run `sync --record <root> --scope record` before `write-open`; do not attempt execute `rules-sync` against the source reference set.
2. Run `write-open --record <root> --previous-revision <revision acknowledged by sync>`. Within that transaction, replace source references with `references/intake.md`, persist Active metadata and the current request's authorization/evidence, and preserve all other accepted record content. Close with `write-close --record <root>`.
3. Run `activate execute --record <root>` to confirm the same record, reread its complete manifest and required rules, run record-scope `sync`, then `rules-sync --record <root> --reference references/intake.md`.
4. Continue only the work the user requested: a clear execution request proceeds through implementation reference loading and scoped-action gates; approval/read-only intent performs bookkeeping and a checkpoint only. Do not ask for execution approval twice.

For an already active execute session, reuse its exact bundle and acknowledged-revision write protocol; do not bootstrap, transition again, or reset the existing action state merely to process another request.
