---
name: execute
description: Persistent execution and evidence-tracking mode for an approved version 4 Markdown record bundle produced by $plan or execution-ready $discuss. Keep the exact bundle active, execute dependency-ready phase files, update evidence and verification transactionally, and remain active until explicit exit.
---

# Execute

## Workflow Modes Hook

When the `workflow-modes` plugin is installed and its hooks are trusted, resolve `workflow_modes_control.py` from the installed plugin bundle, normally `<user-home>/plugins/workflow-modes/scripts/`, and run lifecycle calls with the exact absolute path and `--marker workflow-modes-v1`.

- On fresh-session adoption, after validating and persisting `Execute mode: Active`, run `activate execute --record <execution-record>` before implementation.
- After activation, compaction, or any Required references change, read this complete entrypoint and every named reference, sync the required record scope, then run `rules-sync --record <execution-record> --reference <path>...` before substantive work or a final response.
- On handoff from `$plan` or `$discuss`, require the source skill's successful `transition execute --record <execution-record>` result, then run `activate execute --record <execution-record>` to confirm or rebind the same active record. Execute always keeps that exact record; `plan-init` applies only to the separate-bundle `$discuss` → `$plan` bootstrap and must never run during an execute handoff.
- When the user explicitly exits execute and the exit metadata is durable, run `deactivate`. Implementation completion alone must never call `deactivate`.
- At activation and after every `PostCompact` reminder, read `index.md` and every manifest file completely and run record-scope sync before substantive work.
- After `UserPromptSubmit`, follow `sync_status`: `current` requires no reread; `snapshot` requires reading only the delimited Active Snapshot and running snapshot-scope sync; `record` requires a complete read and record-scope sync. Never open an action or mutate outside the record while the required scope is unacknowledged.
- Before record edits, run `write-open` with the acknowledged bundle revision; update only allowed manifest paths and run `write-close` after all cross-file state is consistent.
- Before every user-facing response, run `checkpoint --record <execution-record>` after all material amendments, evidence, progress, verification, and action results are durable. Use `--no-change` only for a genuinely evidence-free turn after confirming the record remains accurate.

Before each bounded work unit of source, Git, external-system, or other mutating actions in execute mode, open one action that covers the complete unit's declared paths and mutation classes. Do not open a separate action per file or tool call, and do not carry an action into an unrelated goal or materially different scope:

1. Persist a stable evidence ID and `<!-- workflow-action:<ID> status:open -->` in `evidence.md`, plus the matching active-action summary in `index.md`, through one write transaction.
2. Close the record write, then run `action-open --record <bundle-root> --evidence-id <ID> --impact <non-source|source-confirmed>` with the exact paths and minimum unscoped classes.
3. Perform only the mutations covered by that checkpoint. Do not carry an action across an unrelated user request or materially different mutation group.
4. Through one write transaction, persist terminal evidence, update the affected phase and verification files, clear the active-action summary, and replace the open marker with the matching terminal marker.
5. Close the record write, then run `action-close --result <completed|failed|blocked>` before a final response, deactivation, or unrelated mutation group.

The execute hook must deny non-record mutations without an open action, deny opening when the evidence ID/open marker is absent from the tracker, deny paths or unscoped mutation classes outside the action, deny closing until the matching terminal marker is persisted, and block Stop while an execute action remains open. If the active record becomes genuinely unreadable while an action is open, use `action-abort --reason record-unreadable`, repair or restore the tracker, and do not mutate other state until execute is rebound. These controls enforce bookkeeping and scope; they do not grant mutation authority that the user, plan, or a higher-priority policy withheld.

The hook treats bundle and Active Snapshot revisions as workflow boundaries. A write transaction blocks non-record mutation, transition, checkpoint, and Stop until a valid bundle revision is closed.

Confirm every control call returns model-visible `WORKFLOW_*` context. If the plugin or control script is unavailable, read-only adoption and evidence updates may continue, but do not begin or resume implementation; report that lifecycle enforcement must be installed and trusted. Never bypass a denied hook decision.

Use this skill to adopt either an approved plan bundle or an execution-ready discussion bundle as the persistent execution record.

Execute accepts only workflow-record version 4 bundles and defaults to `Durable`. Upgrade `Lightweight` to `Durable` on adoption and preserve `Audited`.

## Reference Routing

Load only the reference needed for the current stage, and read it completely before applying it.

- Read [references/implementation.md](references/implementation.md) before implementation, tracker amendments, commits, worktree setup, phase scheduling, recovery, or any mutating work unit.
- Read [references/completion.md](references/completion.md) after implementation work is integrated and before claiming completion, simplifying, updating agent docs, offering security review, or sending the final implementation response.
- Read-only adoption and summary turns do not require either implementation reference unless their conditions arise.
- Keep `Required references: None` for read-only adoption when neither routed reference applies. Add `references/implementation.md` before implementation, amendment, commit, or recovery; add `references/completion.md` before simplify or completion. Persist and acknowledge each set change, read newly required references, and run `rules-sync` before the next mutation.

## Persistent Mode Contract

Enter execute mode immediately when the user explicitly invokes `$execute` or asks to read, adopt, resume, continue, execute, or amend an accepted execution record. Accepted records are `$plan` handoffs and `$discuss` trackers that passed `Direct Execute Handoff`. Activate the mode in a fresh session and regardless of whether the implementation status is approved, in progress, blocked, paused, implemented, or previously exited. Supplying the record again or asking to read it is an explicit re-entry.

- Bind the mode to the canonical bundle root. Keep that bundle as the sole execution source of truth unless the user explicitly switches records.
- Keep execute mode active across later turns, completion reports, and `Status: Implemented`. Completing the baseline plan does not end the mode.
- Exit only when the user clearly says to exit or turn off execute, such as `exit execute`, `turn off execute`, `thoat execute`, or equivalent explicit wording.
- Treat requests to handle work separately, keep it outside the approved scope, or avoid changing the baseline as scope instructions, not as a mode exit. Record the boundary and material handoff or evidence in the adopted plan while the mode remains active.
- Do not treat reading or adopting a plan as authorization to implement code, mutate external systems, commit, push, or deploy. Wait for a clear current-session request authorizing the relevant action. In a git repository, a clear request to implement the adopted record authorizes local incremental commits for that implementation unless the user or plan explicitly forbids commits; it does not authorize pushing or deploying.

On every adoption or re-entry, read the complete manifest before substantive work and transactionally ensure `index.md` contains:

```markdown
Execute mode: Active
Last updated: <timestamp and timezone>
Resume instruction: Invoke $execute, read index.md and every manifest file, keep this exact bundle as the execution source of truth, and continue updating it until explicit exit.
```

Preserve the implementation `Status` independently from the execute mode. An implemented plan may remain `Status: Implemented` while `Execute mode: Active`; reopen the implementation status only when new executable work starts.

Ensure Active Snapshot version 2 is current and keep the workflow-record header at version 4. Do not accept or migrate older single-file records.

## Completion Contract

Execute the entire approved plan, not only the current phase or execution wave.

Treat every material correction, added deliverable, decision, evidence item, or out-of-scope handoff the user provides while execute mode is active as an amendment or evidence record. Update the adopted plan even when its approved baseline is already complete. Only an explicit execute exit stops this recording contract.

Do not send the final response while any in-scope plan item remains pending `[ ]` or in progress `[~]`, unless a genuine blocker requires user input or an external state change. Progress reports, completed phases, failed checks, subagent results, context pressure, tool failures, and unavailable delegation are intermediate states, not completion conditions. Continue recovering and executing within the current task.

Before claiming that implementation is complete, blocked, or intentionally paused, ensure exactly one of these conditions is true:

1. Every in-scope plan item is completed `[x]`, final verification has been attempted, and the plan status is `Implemented`.
2. All safe independent work is complete, at least one item has a documented genuine blocker `[!]`, and the plan status is `Blocked`.
3. The user explicitly exited execute with unfinished work, the incomplete checklist remains accurate, the plan status is `Paused`, and the execute mode is `Exited`.

A final response for a completed implementation is a checkpoint, not a mode exit. State that execute remains active and name the adopted execution-record path unless the user explicitly exited it.

For a read-, inspection-, summary-, or adoption-only turn without implementation authorization, preserve the existing implementation status and checklist, persist the mode metadata plus any material evidence, and send a checkpoint response stating that no implementation was performed. This response does not need to satisfy an implementation completion condition and does not exit execute.

## Mode Exit

When the user explicitly exits execute:

1. Stop accepting new amendments under this mode after the exit instruction.
2. Persist all material current-turn deltas, evidence, checklist state, and verification results first.
3. Set `Execute mode: Exited` and update `Last updated`.
4. Add an `Exit` entry to `evidence.md` with the instruction and timestamp.
5. Keep `Status: Implemented` or `Status: Blocked` when accurate; use `Status: Paused` when executable items remain unfinished without a genuine blocker.
6. Report the exact execution-record path and remaining work. Do not treat exit as authorization to discard or complete pending work.

## Genuine Blocker Definition

A genuine blocker exists only when meaningful progress requires one of:

- A user decision whose alternatives materially change the approved outcome
- A credential, permission, approval, or secret that cannot be obtained within the current task
- An unavailable external system or state required for the next dependent work
- An action prohibited by higher-priority instructions
- An irreconcilable conflict with pre-existing user changes where proceeding could overwrite or corrupt them

The following are not blockers by themselves:

- A failed test, build, lint, verification, or integration check
- A crashed, timed-out, unavailable, or rejected subagent
- Lack of parallel-agent capacity
- A failed implementation attempt
- Missing optional tooling or skills
- Repository drift that can be reconciled without materially changing the approved goal
- Ambiguity that repository evidence or a safe, non-material assumption can resolve
- An optional documentation, simplification, or review step that can be performed locally or reported as unavailable

## Required Input

Require a path to the execution bundle directory or its `index.md` unless an exact bundle is already active. A direct `$discuss` handoff supplies its root automatically.

- If the user supplied a plan or tracker path, resolve it before doing implementation work.
- If the current task already has one adopted execution-record path, reuse it for later turns without asking again.
- If the user did not supply a path and no exact active path exists, ask where the execution record is and stop until they answer.
- If the path does not exist or is not readable, report that clearly and ask for the correct path.

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
