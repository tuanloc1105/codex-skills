---
name: execute
description: Persistent execution and evidence-tracking mode for an approved Markdown execution record produced by $plan or by an execution-ready $discuss tracker. Use whenever the user supplies or references such a file and asks Codex to read, adopt, resume, continue, execute, amend, or record follow-up work against it, including in a fresh session and when its implementation is already complete. Keep the exact file active as the source of execution truth across later turns, record material corrections, added work, out-of-scope handoffs, evidence, and commit records in place, and remain in execute mode until the user explicitly exits it. During implementation, commit each verified unit of work, schedule dependency-ready phases, run integration and final verification, use $simplify across the session commit range, update agent docs when required, and optionally offer a current-change $security-review.
---

# Execute

## Workflow Modes Hook

When the `workflow-modes` plugin is installed and its hooks are trusted, resolve `workflow_modes_control.py` from the installed plugin bundle, normally `<user-home>/plugins/workflow-modes/scripts/`, and run lifecycle calls with the exact absolute path and `--marker workflow-modes-v1`.

- On fresh-session adoption, after validating and persisting `Execute mode: Active`, run `activate execute --record <execution-record>` before implementation.
- After activation, compaction, or any Required references change, read this complete entrypoint and every named reference, sync the required record scope, then run `rules-sync --record <execution-record> --reference <path>...` before substantive work or a final response.
- On handoff from `$plan` or `$discuss`, require the source skill's successful `transition execute --record <execution-record>` result, then run `activate execute --record <execution-record>` to confirm or rebind the same active record.
- When the user explicitly exits execute and the exit metadata is durable, run `deactivate`. Implementation completion alone must never call `deactivate`.
- At activation and after every `PostCompact` reminder, read the exact execution record completely and run `sync --record <execution-record> --scope record` before substantive work.
- After `UserPromptSubmit`, follow `sync_status`: `current` requires no reread; `snapshot` requires reading only the delimited Active Snapshot and running snapshot-scope sync; `record` requires a complete read and record-scope sync. Never open an action or mutate outside the record while the required scope is unacknowledged.
- After writing an execution record from an acknowledged revision, run `ack-write --record <execution-record> --previous-revision <last acknowledged record revision>`. If denied, completely reread and reconcile the record, then use record-scope sync.
- Before every user-facing response, run `checkpoint --record <execution-record>` after all material amendments, evidence, progress, verification, and action results are durable. Use `--no-change` only for a genuinely evidence-free turn after confirming the record remains accurate.

Before each bounded work unit of source, Git, external-system, or other mutating actions in execute mode, open one action that covers the complete unit's declared paths and mutation classes. Do not open a separate action per file or tool call, and do not carry an action into an unrelated goal or materially different scope:

1. Persist a stable amendment/evidence ID, the intended action, and the exact marker `<!-- workflow-action:<ID> status:open -->` in the active execution record.
2. Acknowledge the tracker write with `ack-write`, then run `action-open --record <execution-record> --evidence-id <ID> --impact <non-source|source-confirmed>` and add every inspectable target with `--path <path>`. For inherently unscoped mutations, add only the minimum required `--unscoped <git|external|shell>` classification; `git` also requires `source-confirmed`. Read-only tools and writes limited to the active execution record do not require an open action.
3. Perform only the mutations covered by that checkpoint. Do not carry an action across an unrelated user request or materially different mutation group.
4. Persist the terminal result, checks, identifiers, and residual state under the same evidence ID. Replace the open marker with exactly one matching terminal marker: `status:completed`, `status:failed`, or `status:blocked`.
5. Acknowledge the terminal tracker write with `ack-write`, then run `action-close --result <completed|failed|blocked>` before a final response, mode deactivation, or unrelated mutation group. Never treat a denied acknowledgement, close, or Stop hook as optional; reconcile the record and retry.

The execute hook must deny non-record mutations without an open action, deny opening when the evidence ID/open marker is absent from the tracker, deny paths or unscoped mutation classes outside the action, deny closing until the matching terminal marker is persisted, and block Stop while an execute action remains open. If the active record becomes genuinely unreadable while an action is open, use `action-abort --reason record-unreadable`, repair or restore the tracker, and do not mutate other state until execute is rebound. These controls enforce bookkeeping and scope; they do not grant mutation authority that the user, plan, or a higher-priority policy withheld.

The hook also treats record and Active Snapshot revisions as workflow boundaries. `PostCompact`, audited prompts, and external drift require the scope reported by the hook; an unchanged durable record remains acknowledged across ordinary prompts. Stop still requires a completed turn checkpoint. `ack-write` acknowledges a tracker update only when its previous revision matches the acknowledged revision.

Confirm every control call returns model-visible `WORKFLOW_*` context. If the plugin or control script is unavailable, read-only adoption and evidence updates may continue, but do not begin or resume implementation; report that lifecycle enforcement must be installed and trusted. Never bypass a denied hook decision.

Use this skill to adopt either an approved `$plan` handoff or an execution-ready `$discuss` tracker as a persistent execution and evidence record. In the rules below, “plan” means the exact adopted execution record regardless of which skill produced it.

Execute defaults to `Durable`. On adoption or handoff, set a `Lightweight` Active Snapshot to `Durable`; preserve `Audited` without downgrading it. Profiles change reread and evidence cadence, never mutation authorization: `Durable` groups evidence by complete work unit, while `Audited` retains full-record sync on each user prompt. A version 2 record without a snapshot remains `Audited` until its first valid record update migrates it to version 3.

## Reference Routing

Load only the reference needed for the current stage, and read it completely before applying it.

- Read [references/implementation.md](references/implementation.md) before implementation, tracker amendments, commits, worktree setup, phase scheduling, recovery, or any mutating work unit.
- Read [references/completion.md](references/completion.md) after implementation work is integrated and before claiming completion, simplifying, updating agent docs, offering security review, or sending the final implementation response.
- Read-only adoption and summary turns do not require either implementation reference unless their conditions arise.
- Keep `Required references: None` for read-only adoption when neither routed reference applies. Add `references/implementation.md` before implementation, amendment, commit, or recovery; add `references/completion.md` before simplify or completion. Persist and acknowledge each set change, read newly required references, and run `rules-sync` before the next mutation.

## Persistent Mode Contract

Enter execute mode immediately when the user explicitly invokes `$execute` or asks to read, adopt, resume, continue, execute, or amend an accepted execution record. Accepted records are `$plan` handoffs and `$discuss` trackers that passed `Direct Execute Handoff`. Activate the mode in a fresh session and regardless of whether the implementation status is approved, in progress, blocked, paused, implemented, or previously exited. Supplying the record again or asking to read it is an explicit re-entry.

- Bind the mode to the exact adopted execution-record path. Keep that file as the sole execution source of truth unless the user explicitly switches to another record.
- Keep execute mode active across later turns, completion reports, and `Status: Implemented`. Completing the baseline plan does not end the mode.
- Exit only when the user clearly says to exit or turn off execute, such as `exit execute`, `turn off execute`, `thoat execute`, or equivalent explicit wording.
- Treat requests to handle work separately, keep it outside the approved scope, or avoid changing the baseline as scope instructions, not as a mode exit. Record the boundary and material handoff or evidence in the adopted plan while the mode remains active.
- Do not treat reading or adopting a plan as authorization to implement code, mutate external systems, commit, push, or deploy. Wait for a clear current-session request authorizing the relevant action. In a git repository, a clear request to implement the adopted record authorizes local incremental commits for that implementation unless the user or plan explicitly forbids commits; it does not authorize pushing or deploying.

On every adoption or re-entry, read the complete plan before substantive work and ensure it contains or backfill these metadata lines near the top:

```markdown
Execute mode: Active
Last updated: <timestamp and timezone>
Resume instruction: Invoke $execute, read this file completely, keep this exact file as the execution source of truth, and continue updating it until the user explicitly exits execute.
```

Preserve the implementation `Status` independently from the execute mode. An implemented plan may remain `Status: Implemented` while `Execute mode: Active`; reopen the implementation status only when new executable work starts.

Also ensure an Active Snapshot version 2 exists near the top and contains the current goal, execution state, accepted decisions, open items, next safe action, and stage-appropriate Required references. Keep the workflow-record header at version 3. This migration is tracker housekeeping; retain existing history and evidence.

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
4. Add an `Exit` entry under `## Amendments and Evidence` with the instruction and timestamp.
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

Require a path to the Markdown execution record unless an exact adopted plan or discussion-tracker path is already active in the current task. A successful direct handoff from `$discuss` supplies its active tracker path automatically.

- If the user supplied a plan or tracker path, resolve it before doing implementation work.
- If the current task already has one adopted execution-record path, reuse it for later turns without asking again.
- If the user did not supply a path and no exact active path exists, ask where the execution record is and stop until they answer.
- If the path does not exist or is not readable, report that clearly and ask for the correct path.

## Plan and Tracker Intake

Read the full execution record before any substantive response or implementation work, adopt the exact path, and apply the `Persistent Mode Contract` metadata update. Never copy a direct discussion handoff into a separate plan file; preserve the tracker history and keep updating that same path.

Verify these basics:

- The file is either a Markdown plan, ideally with `# How to do it: ...`, or a `# Discussion Tracker` with `Execution readiness: Ready` and `Mode status: Exited`.
- The record has a concrete `## Goal`, `## Step-by-Step Plan`, and `## Verification`.
- No unresolved entry under `## Open Questions` is marked as blocking execution.
- The record status is approved or the user explicitly asked to execute it.
- For a phased plan, read `## Execution Structure` and capture each phase's ID, dependencies, wave, subagent eligibility, owned scope, produced output, and verification or integration requirements.

Reject an active or not-ready discussion tracker as an execution input. Do not silently finish its discussion, choose unresolved options, or manufacture a plan inside execute mode. In the same task, keep `$discuss` active and complete its `Direct Execute Handoff`; in a fresh task, tell the user to resume `$discuss` on that exact tracker before trying `$execute` again.

For an accepted discussion tracker, preserve `Mode status: Exited`, set `Execute mode: Active`, apply the standard execute resume instruction, and use the tracker as the sole execution source of truth. Missing scheduling metadata remains subject to the sequential backward-compatibility rule below.

Treat an explicit user request to execute the supplied record as execution approval even when its status is missing or still says `Draft`, `Ready`, or `Awaiting execution`. A request only to read, inspect, summarize, or adopt the record activates execute mode and its bookkeeping but does not authorize implementation.

Ask for confirmation only when the record explicitly says not to implement, an unresolved choice materially changes the desired outcome, repository drift invalidates the approved goal or requires materially different scope, or two authoritative requirements cannot both be satisfied. Do not invent a materially different plan.

Treat `Depends on` as authoritative and any declared wave as a scheduling hint that must agree with it. Revalidate phase independence against the current repository and runtime before dispatch. An eligibility note never overrides overlapping files, shared mutable state, unstable contracts, or newly discovered dependencies.

For backward compatibility, execute plans without dependency, wave, ownership, or subagent metadata sequentially. Missing scheduling metadata is not a blocker. Do not infer parallel permission from numbered steps alone.

When working in a git repository, capture the initial status and current diff boundaries before parallel dispatch so pre-existing user changes can be distinguished and preserved.
