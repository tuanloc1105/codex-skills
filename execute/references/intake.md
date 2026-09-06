# Execute Record Intake

Read this reference completely before validating or adopting a supplied record, including fresh-session adoption, re-entry, or a direct handoff. Read it before the initial validation; once the record is accepted, persist `references/intake.md` in Required references and complete rules-sync under the entrypoint lifecycle before substantive work.

## Plan and Tracker Intake

Read `index.md` and every manifest file before substantive work, adopt the canonical root, and apply the metadata update transactionally. Never copy a direct discussion handoff into another bundle.

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
