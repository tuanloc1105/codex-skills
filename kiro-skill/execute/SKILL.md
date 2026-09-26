---
name: kiro-execute
description: Persistent execution and evidence-tracking mode for an approved version 4 Markdown record bundle produced by $plan or execution-ready $discuss. Keep the exact bundle active, execute dependency-ready phase files, update evidence and verification transactionally, and remain active until explicit exit. Kiro port of the Codex `execute` skill.
---

# Execute (Kiro / Kiro Crew)

This is the Kiro-native port of the Codex `execute` skill. Same persistent bundle,
evidence, and worktree contract; phase delegation uses Kiro Crew's `spawn_run` /
`spawn_sub_agents` (never any other subagent mechanism), every user-facing question routes
through the interactive selection mechanism of the active Kiro surface (`Question Routing`
below), and the required post-implementation review pass is `kiro-simplify` instead of
Codex's `simplify`.

## Skill-Managed Lifecycle

Apply this skill directly through conversation state and its Markdown record. The bundle files are the state machine; do not invent an external control script or hook system for the mode lifecycle. Continue to respect independently enforced runtime restrictions (safety guardrails, git-push protections to protected branches, destructive-command denials); this instruction does not authorize bypassing them.

- On entry, resume, and after compaction, read this complete entrypoint, every currently required reference, `index.md`, and every manifest file before substantive work. For a new bundle, read the initialization guidance first, create the bundle, then verify its complete contents.
- Treat compaction recovery as a hard gate, not as optional rereading. Before the first substantive tool call after compaction (or a `REINJECTED AFTER COMPACTION` / `SESSION RESUMED` marker), recover the active mode, canonical bundle root, and tracker ID from durable state; read and validate the bundle; reconcile open action markers and any completed but unrecorded work; and verify the Active Snapshot, Resume Checkpoint, implementation status, and next safe action. If the exact active bundle cannot be resolved, do not guess from the newest directory: ask for its path and stop substantive work.
- On later turns, reuse current context only while it remains reliable. Reread the Active Snapshot for snapshot-only changes; reread the complete bundle when record content changes outside known writes or its state is uncertain.
- Treat a record write transaction as one coordinated file update: read the affected current files, declare new Markdown files in the manifest, update all affected content and cross-links, then verify identity, metadata, phase links, dependencies, and evidence agree. Finish or repair that update before unrelated mutation, handoff, or a final response. If persistence fails, report the blocker instead of treating unsaved state as durable.
- Before every user-facing response, persist material turn deltas and the resume checkpoint. A genuinely unchanged turn requires only verifying that the saved state remains accurate.
- Keep the exact canonical bundle root and tracker ID in the durable resume instruction and checkpoint so compaction can preserve the recovery key. A compacted conversation summary is context only; the validated bundle is authoritative workflow state. Use `session_ledger_record`/`session_ledger_read` as a secondary durable pointer (`goal`, `phase`, `next`, `artifacts.bundle_root`/`artifacts.worktree`/`artifacts.branch`/`artifacts.pr`) that survives compaction even faster than a bundle reread — but the bundle remains authoritative; reconcile the ledger against it, never the reverse.

On adoption or handoff, follow [references/intake.md](references/intake.md) and keep the exact accepted bundle. Persist exit metadata only when the user explicitly exits; implementation completion alone does not exit execute.

Before each bounded mutating work unit, record one action covering its declared paths and source, Git, or external effects:

1. Persist a stable evidence ID and `<!-- workflow-action:<ID> status:open -->` in `evidence.md`, its authorization and scope, and the matching active-action summary in `index.md`.
2. Verify the saved action before performing only the covered mutations. Use one action per complete work unit, not per file or tool call; never carry it into an unrelated goal or materially different scope.
3. Persist terminal evidence with result `completed`, `failed`, or `blocked`, update affected phase and verification files, clear the active-action summary, and replace the open marker with its matching terminal marker before a final response, exit, or unrelated work unit.

If the record becomes unreadable during an action, stop other mutations, repair or restore the record, and reconcile the action evidence before resuming. Recorded scope and evidence never grant authority withheld by the user, plan, or higher-priority instructions — including this agent's own safety guardrails and the git-push/destructive-command floor.

Use this skill to adopt either an approved plan bundle or an execution-ready discussion bundle as the persistent execution record.

Before any directory change on adoption, capture the user's initial terminal working directory as an absolute path (Kiro's `[PROJECT]` active project directory for a dashboard session, or the shell's current working directory otherwise). New and replacement worktrees must be created inside `<worktree-anchor>/.worktrees/`. Preserve the initial directory for worktree placement under `Dedicated Worktree` in [references/implementation.md](references/implementation.md); on resume, retain the recorded anchor unless the user explicitly changes it. Repository discovery or a tool's later working-directory override must not replace that anchor.

Execute accepts only workflow-record version 4 bundles and defaults to `Durable`. Upgrade `Lightweight` to `Durable` on adoption and preserve `Audited`.

## Scripted Bundle Updates

Prefer a short Python standard-library script (via the `shell` tool) when one record update must coordinate several Markdown files, such as the index, decisions, phase files, and evidence. Use the `write` tool's `strReplace`/`insert` for a small local edit when it is clearer; a script is a preferred method for coordinated persistence, not a requirement for unrelated file edits. Keep the existing authorization, decision, and handoff gates unchanged.

- Use a literal script input (heredoc via `shell`, or a script file written first) so Markdown backticks, dollar signs, and newlines are not evaluated by the shell. Use explicit UTF-8 encoding and preserve existing newline style and file permissions.
- Resolve the bound bundle root, use an explicit path allowlist from its manifest plus declared additions, and reject escaping paths or symlink targets. Do not discover mutation targets through a broad recursive glob.
- Read the affected files into a before-snapshot and construct all proposed contents in memory before writing. For replacements, check the expected occurrence count or unique section markers and raise an explicit error on missing or ambiguous matches; never rely on an unchecked `.replace()` or an unguarded assertion for write-safety checks. Preserve unrelated content and skip unchanged files.
- Validate the proposed bundle before the first write: identity, manifest, metadata, links, question mappings, and phase/dependency/evidence consistency where applicable. Keep one writer for the bundle and recheck that source files still match the snapshot before replacement; if they changed, reread and reconcile instead of overwriting.
- For whole-file rewrites, stage complete contents in temporary sibling files (under `$KIROCREW_SCRATCH` when available) and replace each destination with an atomic rename, writing `index.md` last. Temporary staging files are not record artifacts; clean up only those created by this operation. Per-file replacement does not make a multi-file bundle atomic. On interruption or failure, inspect which replacements succeeded and repair the coordinated update before continuing; never blindly restore over another writer's changes.
- Read back the saved files, compare them with the intended contents, and revalidate the complete bundle and scoped diff. Report validation failures accurately; successful script exit alone does not prove that the update is consistent.

## Reference Routing

Remove a conditional reference from `Required references` only after its stage and any dependent work have ended; persist and verify the set change under the record persistence contract. After compaction, reread every reference still required.

Load only the reference needed for the current stage, and read it completely before applying it.

- Read [references/implementation.md](references/implementation.md) before implementation, tracker amendments, commits, worktree setup, phase scheduling, recovery, or any mutating work unit.
- Read [references/completion.md](references/completion.md) after implementation work is integrated and before claiming completion, simplifying, updating agent docs, offering security review, handling a user-requested PR/MR merge or post-merge worktree cleanup, or sending the final implementation response.
- Read [references/intake.md](references/intake.md) before record validation or adoption.
- Read [references/parallel-execution.md](references/parallel-execution.md) before evaluating delegation, dispatching subagents via `spawn_run`, or recovering delegated work.
- Read [references/post-merge-cleanup.md](references/post-merge-cleanup.md) before a user-requested PR/MR merge or dedicated-worktree cleanup.
- Read-only adoption and summary turns do not require either implementation reference unless their conditions arise.
- Keep `references/intake.md` required through adoption or re-entry. For a later read-only summary with no intake or other routed work, `Required references: None` is permitted. Add `references/implementation.md` before implementation, amendment, commit, or recovery; add `references/completion.md` before simplify, completion, or a user-requested PR/MR merge and its cleanup. Add `references/parallel-execution.md` while evaluating delegation or while delegated work, integration, or recovery is active; add `references/post-merge-cleanup.md` while handling a requested merge or cleanup. Persist and verify each set change and read newly required references before the next mutation.

## Persistent Mode Contract

Enter execute mode immediately when the user explicitly invokes `$execute` or asks to read, adopt, resume, continue, execute, or amend an accepted execution record. Accepted records are `$plan` handoffs and `$discuss` trackers that passed `Direct Execute Handoff`. Activate the mode in a fresh session and regardless of whether the implementation status is approved, in progress, blocked, paused, implemented, or previously exited. Supplying the record again or asking to read it is an explicit re-entry.

- Bind the mode to the canonical bundle root. Keep that bundle as the sole execution source of truth unless the user explicitly switches records.
- Keep execute mode active across later turns, completion reports, and `Status: Implemented`. Completing the baseline plan does not end the mode.
- Exit only when the user clearly says to exit or turn off execute, such as `exit execute`, `turn off execute`, `thoát execute`, or equivalent explicit wording.
- Treat requests to handle work separately, keep it outside the approved scope, or avoid changing the baseline as scope instructions, not as a mode exit. Record the boundary and material handoff or evidence in the adopted plan while the mode remains active.
- Do not treat reading or adopting a plan as authorization to implement code, mutate external systems, commit, push, or deploy. Wait for a clear current-session request authorizing the relevant action. In a git repository, a clear request to implement the adopted record authorizes local incremental commits for that implementation unless the user or plan explicitly forbids commits; it does not authorize pushing to a protected branch or deploying — pushing a feature branch by explicit name for a PR workflow remains allowed per this agent's own git-safety rules.

On every adoption or re-entry, read the complete manifest before substantive work and use the applicable intake bootstrap or active-session transaction to ensure `index.md` contains:

```markdown
Execute mode: Active
Last updated: <timestamp and timezone>
Resume instruction: Invoke $execute on <canonical bundle root> (tracker <tracker ID>), read index.md and every manifest file, keep this exact bundle as the execution source of truth, and continue updating it until explicit exit.
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
- A credential, permission, approval, or secret that cannot be obtained within the current task (including a Kiro Crew tool call blocked by policy — see the `blocked-by-policy` skill before treating a refusal as a puzzle)
- An unavailable external system or state required for the next dependent work
- An action prohibited by higher-priority instructions
- An irreconcilable conflict with pre-existing user changes where proceeding could overwrite or corrupt them

The following are not blockers by themselves:

- A failed test, build, lint, verification, or integration check
- A crashed, timed-out, unavailable, or rejected `spawn_run` subagent
- Lack of parallel-agent capacity (check `resource_status` and fall back to serial execution)
- A failed implementation attempt
- Missing optional tooling or skills
- Repository drift that can be reconciled without materially changing the approved goal
- Ambiguity that repository evidence or a safe, non-material assumption can resolve
- An optional documentation, simplification, or review step that can be performed locally or reported as unavailable

## Question Routing

Execute asks the user as little as possible, but every question it does ask must carry concrete options and must be routed through the interactive selection mechanism of the active Kiro surface. Never hand the user a decision as prose they have to answer by typing.

- **Kiro Crew dashboard session:** call `ask_question` with exactly one question and 2-4 options, marking the recommended one in its `description`, then **end the turn in the same step**. The tool is non-blocking: it returns as soon as the card is requested, and the selection arrives as the user's next message, never as the tool's result. Do not also print the question or its option list as chat text.
- **Kiro IDE or Kiro CLI (`kiro-cli` runtime):** raise the runtime's own `AskUserQuestion` card with the same one-question, 2-4-option shape. That card is blocking: it is raised while the turn is still running, and the selection is steered back into the waiting turn, so continue in the same turn when it returns instead of ending the turn first. If the turn already ended when the user answers, treat the answer as an ordinary next message and resume from the recorded checkpoint.
- **A Kiro surface offering neither tool:** put the choices in one trailing `[OPTIONS: A | B | C]` line as the very last line of the message, with nothing after it. Write each label in the user's voice and self-contained, because the label is sent verbatim as the user's next message.
- **Plain numbered prose is a last resort, not a style choice.** Use it only when an interactive call is denied, errors as unavailable, or the surface renders no options at all. State that the interactive question was unavailable and give each option its own consecutively numbered line.

While a question is pending, keep only that one question outstanding, persist the blocking question and its options in the record before responding, and never apply a default to a decision the user owns. Record the question, its numbered options, and the user's selection in `evidence.md` so a resumed session can read the outcome without the surface's card history. An approval or authorization question stays single-select; use `multiSelect` only where the options can genuinely be combined.

## Required Input

Require a path to the execution bundle directory or its `index.md` unless an exact bundle is already active. A direct `$discuss` handoff supplies its root automatically.

- If the user supplied a plan or tracker path, resolve it before doing implementation work.
- If the current task already has one adopted execution-record path, reuse it for later turns without asking again.
- If the user did not supply a path and no exact active path exists, ask where the execution record is under `Question Routing` and stop until they answer. Offer the candidate bundles you can see as options plus one option for a different path; never guess from the newest directory.
- If the path does not exist or is not readable, report that clearly and ask for the correct path under `Question Routing`.

## Plan and Tracker Intake

Before validating or adopting a record, read and follow [references/intake.md](references/intake.md). Adopt the exact bundle only after its intake checks pass; reading or adopting it does not authorize implementation.
