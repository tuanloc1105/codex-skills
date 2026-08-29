# Discuss Tracker Reference

Read this reference completely before tracker creation, adoption, migration, persistence, or a plan/execute handoff.

## Markdown Tracker Requirement

Before starting any substantive discussion, automatically resolve and establish the Markdown tracker. Never ask the user about its save location, directory, filename, reuse, or overwrite behavior.

- Capture the current working directory when the skill starts and resolve every relative destination against it.
- Classify a user-provided destination without asking: an existing directory, a path ending in a separator, or explicit directory wording is a directory; otherwise treat it as a file path.
- If the user provides any file path, including a bare filename, preserve it exactly after resolving relative paths against the captured current working directory.
- If the user provides a directory, generate the tracker filename inside it.
- If the user provides no destination, use `./discussion/` relative to the current working directory at the time the skill starts.
- For an agent-generated filename, derive `<discussion-name>` from the discussion topic or goal. Use `discussion` only when no meaningful slug can be derived.
- If the selected file or a symlink at that path already exists and the user explicitly says to reuse, continue, update, append, or overwrite it, follow that instruction after applying the same path-safety checks.
- Also treat an existing Markdown file presented as the tracker for this discussion, a handoff from an earlier session, or the state to read and resume as an instruction to adopt and update that exact file in place. Read the complete tracker before substantive work. Do not create a numbered sibling merely because the user said `read`, `resume`, `pick up`, or `continue the discussion` instead of `reuse the file`.
- For any other existing destination, preserve it and automatically choose the lowest available numbered sibling for that basename, such as `YYYY-MM-DD-<discussion-name>-2.md`, then `YYYY-MM-DD-<discussion-name>-3.md`.
- Create the selected parent directory and all missing ancestors automatically. Do not ask for permission.
- For a new tracker, reserve the selected file with exclusive creation and retry with the next numbered sibling if another writer wins the same path. Freeze the successfully reserved or explicitly reused path for the rest of the discussion so later turns keep updating the same tracker.
- For an agent-generated filename, use the format `YYYY-MM-DD-<discussion-name>.md`.
- For an agent-generated filename, use the current local date unless the user requests another date.
- Slugify an agent-generated `<discussion-name>` with lowercase ASCII words joined by hyphens.

Once the destination is resolved automatically, exclusively reserve a collision-free path only for a new tracker; for a handoff, adopt the existing file unchanged until it has been read completely. Freeze the selected path, perform repository ignore handling, initialize or update the tracker as applicable, and continue the discussion. Keep updating that same tracker after meaningful discussion turns and tell the user where it was saved.

### Cross-Session Handoff

Make the tracker self-contained enough that a future agent can resume safely without the original chat. Do not attempt to preserve every conversational detail; preserve the current actionable state, its authority, and the evidence needed to verify it.

For every new tracker:

- Record that `$discuss` is active, the source-code action authorization boundary, and that only `$plan` or `$execute` can durably exit the mode.
- Include this resume instruction near the top: `Invoke $discuss, read this tracker completely, and continue this exact file before substantive work.`
- Create the version 3 Active Snapshot near the top with `Profile: Lightweight`, unless an existing tracker or repository policy requires `Durable` or `Audited`. Keep it concise and update it whenever its current goal, state, accepted decisions, open items, or next safe action changes.
- Initialize `Execution readiness: Not ready` and `Execute mode: Inactive`; these markers change only through `Direct Execute Handoff`.
- Record the captured working directory, containing repository root when applicable, current branch and commit when available, creation time, last-updated time, and local timezone. Mark unavailable values explicitly instead of inventing them.
- Give the discussion a stable tracker ID that does not change when the file moves. Use a locally generated non-secret identifier; do not derive it from credentials or private data.
- Put the tracker ID and record kind in a compact machine-readable header near the top so the hook-visible session binding can be checked against the file without making the absolute path part of the document identity.
- Tell the user the exact tracker path and an explicit fresh-session resume prompt such as `Use $discuss and continue the tracker at <path>`.

When resuming an existing tracker:

1. Read the complete file and adopt that exact path before substantive work.
2. Confirm from its metadata whether `discuss` is `Active`, `Awaiting decision`, `Paused`, or `Exited`. If status is missing, treat the mutation boundary as active until the user explicitly resolves it. If the tracker says `Exited` but the user has now explicitly invoked `$discuss` to continue it, start a new active segment and record that re-entry before substantive work.
3. Restore the goal, current scope, mutation boundary, accepted decisions, open questions, and resume checkpoint. Do not revive superseded decisions or answered questions.
4. Compare recorded workspace, repository, branch, commit, and external-source revisions with current live state when those facts matter to the next action. Mark drift and revalidate affected claims before relying on them.
5. If two trackers claim the same tracker ID or the supplied file conflicts with another apparent continuation, do not merge or choose silently. Record the conflict and apply `Immediate Decision Gate` when the correct lineage requires the user's choice.

Treat every mutation authorization recorded by an earlier session as historical or pending context, never as executable permission in the current session. Before any new local or external mutation beyond tracker housekeeping, require a clear current-session user instruction for the exact remaining target and action. Mark completed or consumed authorization accordingly and never repeat a mutation merely because the tracker says it was previously authorized.

When the user chooses `$plan` or completes a successful `Direct Execute Handoff`, update the tracker status to `Exited`, record the transition instruction and time, and flush the final resume checkpoint before handing control to the selected skill. No other instruction or completed action may set discuss to `Exited`.

### Settled Discussion Transition Gate

When the goal, scope, requirements, constraints, material tradeoffs, and user-owned decisions are clear enough to proceed and no blocking discussion question remains, do not suggest only `$execute` and do not choose the next workflow on the user's behalf. Persist the settled state, then ask exactly one transition question with these two choices:

1. `$plan` — create and review a separate detailed implementation plan before any execution. Recommend this for complex, risky, cross-cutting, or delegation-worthy work.
2. `$execute` — finalize this tracker through `Direct Execute Handoff` and begin implementation from the same execution record. Recommend this for small or already implementation-ready work.

Recommend exactly one option according to the work, but always present both. Keep `discuss` active and wait for the user's choice; a conclusion that the discussion is clear is not itself permission to plan or execute.

If the user chooses `$plan`, complete `Tracker Durability Gate`, update `Mode status: Exited`, record the choice and timestamp in `## Log`, and set the resume checkpoint to the `$plan` transition. Then invoke `$plan` using the complete tracker as authoritative discussion context. Let `$plan` create and bind its separate draft plan immediately under its own saving rules; do not mark the discussion tracker execution-ready and do not apply `Direct Execute Handoff`.

If the user chooses `$execute`, apply `Direct Execute Handoff`. If that handoff exposes a missing material decision, keep `discuss` active and resolve it through `Immediate Decision Gate`; after it is resolved and persisted, ask the `$plan` or `$execute` transition question again rather than assuming the earlier choice still applies.

### Direct Execute Handoff

When the user invokes `$execute`, says to execute or implement the settled discussion, or otherwise clearly requests execution against the active tracker, use that same tracker as the execution record. Do not create a duplicate file under `./plans/` and do not require `$plan` merely to reformat settled discussion state.

Before exiting discuss for `$execute` or allowing `$execute` to mutate source code, make the tracker execution-ready and persist it. This handoff gate does not apply to an action separately authorized under `Temporary Source-Code Actions`. The handoff gate requires:

- A concrete `## Goal`, in-scope and out-of-scope boundaries, requirements, constraints, and accepted decisions.
- No unresolved open question marked as blocking execution.
- An existing-behavior baseline, preservation requirements, and regression risks or an explicit truthful `None` when they do not apply.
- A concrete `## Step-by-Step Plan` checklist and `## Verification` section derived only from accepted discussion state and verified evidence.
- `## Execution Structure` with dependency, ownership, output, and integration metadata when phases are materially useful; small linear work may omit it.
- `## Amendments and Evidence` initialized with `None at approval` and `## Handoff Notes` initialized with the exact tracker path and next safe action.

If a missing choice materially changes the outcome, apply `Immediate Decision Gate`, record the blocker, and keep discuss active. Do not mark the tracker ready, synthesize an arbitrary choice, or start implementation.

After the gate passes, update the same tracker atomically before handing control to `$execute`:

```markdown
Mode status: Exited
Status: Approved for execution
Execution readiness: Ready
Execute mode: Ready
Resume instruction: Invoke $execute, read this file completely, keep this exact file as the execution source of truth, and continue updating it until the user explicitly exits execute.
Mutation boundary: $discuss exited by direct execute handoff at <timestamp and timezone>
```

Set the Active Snapshot profile to `Durable` during this handoff unless it is already `Audited`; never downgrade `Audited`.

Record the user's transition instruction and timestamp in `## Log`, update `Last updated` and `## Resume Checkpoint`, and complete `Tracker Durability Gate`. Only then may `$execute` adopt the exact path, set `Execute mode: Active`, and begin work under its own authorization and verification rules. A bare `$execute` transition is an implementation request when the active tracker already defines concrete executable work; an explicit read-, inspect-, summarize-, or adopt-only qualifier activates execute without authorizing implementation.

### Tracker Authority and Evidence

Treat the tracker as the source of truth for the recorded discussion state: the current goal, scope, accepted user decisions, requirements, constraints, recorded authorization status, open questions, and resume checkpoint. Recorded authorization status is historical context and does not grant executable permission in a later session. A later explicit user correction supersedes the recorded state and must be written back to the tracker.

Do not treat the tracker as the live source of truth for repository behavior, tickets, documents, designs, APIs, databases, or other external systems. For each material factual claim, record the authoritative source for that domain and enough provenance to find and revalidate it. At minimum capture:

- The claim or state being supported.
- Whether it is verified, user-reported, inferred, proposed, or unknown.
- The authoritative source type and exact locator, such as a repository-relative path and symbol, URL, ticket ID, document section, command, log, or artifact.
- The relevant commit, revision, version, retrieval time, or observation time when available.
- The observed result, any unresolved conflict, and the condition that requires revalidation.

Higher-priority instructions and current live system state always override a stale tracker snapshot. Do not invent one universal precedence order for unrelated domains. Record which source is authoritative for each domain; when sources conflict, keep the conflict explicit and resolve it through safe inspection or `Immediate Decision Gate` rather than silently choosing.

### Repository Ignore Rule

After resolving the tracker destination, automatically protect it from Git tracking when it is inside a Git worktree:

1. Normalize `.` and `..` segments and resolve existing symlink components before mutating anything. Never place the tracker inside Git metadata such as `<git-root>/.git/`; report the exact blocker and stop without asking a storage-choice question.
2. Starting from the destination's parent directory, or its nearest existing ancestor directory when the parent is missing, identify the nearest containing Git worktree root. This must also work when one or more tracker directories still need to be created and when repositories are nested.
3. If the destination is inside that worktree, create or update `<git-root>/.gitignore` without asking for permission.
4. Add one valid, root-anchored ignore pattern for the tracker directory relative to the Git root, with a trailing slash, such as `/notes/discussions/`. Use `/` separators and escape Git ignore metacharacters in path components. If the tracker is directly in the Git root, ignore the tracker file itself, such as `/YYYY-MM-DD-<discussion-name>.md`; never add a rule that ignores the Git root.
5. Preserve all existing `.gitignore` content and ordering. Append the new rule without rewriting unrelated rules, and do not add a duplicate when an existing rule in that `.gitignore` already excludes the directory or file.
6. Verify that the resulting rule excludes the tracker path without staging it or otherwise changing repository state.
7. If the selected tracker directory already contains non-tracker files, warn that its folder-level rule also ignores untracked files there, but do not change the destination or ask for permission.
8. Do not modify the Git index or untrack existing files. If the tracker is already tracked, record that limitation and tell the user because `.gitignore` alone cannot untrack it.
9. If the destination is not inside a Git worktree, skip `.gitignore` handling without asking.

Record any automatically created directories and the ignore rule added or reused in the tracker.

If the resolved tracker directory or file cannot be created, stop before starting the substantive discussion and report the exact blocker without asking a storage-choice question or silently relocating an explicit destination. If only `.gitignore` maintenance fails, keep the resolved tracker destination, create or update the tracker there, and report that it could not be ignored; never relocate the tracker solely because of an ignore failure.

Use a concise, resumable Markdown format. The metadata, goal, scope, source-of-truth inventory, current state, assumptions and unknowns, decisions, requirements, constraints, open questions, and resume checkpoint are mandatory; write `None` or `Unknown` instead of omitting them. Omit only empty optional sections.

```markdown
# Discussion Tracker

<!-- workflow-record version:3 kind:discuss tracker-id:<stable tracker ID> -->

Tracker ID: <stable non-secret ID>
Created: <timestamp and timezone>
Last updated: <timestamp and timezone>
Mode: $discuss
Mode status: <Active | Awaiting decision | Paused | Exited>
Execution readiness: <Not ready | Ready>
Execute mode: <Inactive | Ready | Active | Exited>
Resume instruction: Invoke $discuss, read this tracker completely, and continue this exact file before substantive work.
Workspace: <captured working directory>
Repository: <root, branch, and commit when available>
Mutation boundary: <active boundary, or exit instruction and time when Exited>

<!-- workflow-active-snapshot:start version:1 -->
## Active Snapshot

Profile: <Lightweight | Durable | Audited>
Goal: <current concrete goal>
Current state: <current mode state and active work>
Accepted decisions: <active decision IDs or None>
Open items: <blocking or next open IDs, or None>
Next safe action: <one exact next action>
<!-- workflow-active-snapshot:end -->

## Goal

## Scope

### In Scope

### Out of Scope

## Context and Current State

## Source of Truth and Evidence

| ID | Claim or domain | Classification | Authoritative source and locator | Revision or observed at | Observation or conflict | Revalidate when |
| --- | --- | --- | --- | --- | --- | --- |

## Assumptions and Unknowns

## Existing Behavior Baseline

## Preservation Requirements

## Regression Risks and Checks

## Decisions

| ID | Status | Decision | Rationale | Supersedes |
| --- | --- | --- | --- | --- |

## Requirements

## Constraints

## Scoped Actions

<Record each authorized non-source-code or temporary source-code action with its scope, source-impact confirmation when applicable, status, changed resources, verification, and result.>

## Open Questions

| ID | Status | Question and options | Blocks | Resolution |
| --- | --- | --- | --- | --- |

## Next Steps

## Step-by-Step Plan

<Add only when preparing a direct execute handoff. Use `[ ]` checklist items.>

## Verification

<Add only when preparing a direct execute handoff.>

## Amendments and Evidence

<Add only when preparing a direct execute handoff. Initially record `None at approval`.>

## Handoff Notes

<Add only when preparing a direct execute handoff.>

## Resume Checkpoint

- Last completed:
- Current work:
- Blocking decision or dependency:
- Next safe action:
- Deferred work:
- Authorization record: <None, Completed, Expired, or Pending context requiring current-session authorization>
- Revalidation required:

## Log
```

Track the user goal, important context, decisions, requirements, constraints, options considered, open questions, and exact next safe action. Give decisions and questions stable IDs and lifecycle states such as `Proposed`, `Accepted`, `Superseded`, `Open`, or `Answered`; link replacements through `Supersedes` instead of leaving contradictory entries current. Keep the log concise; do not save a raw transcript, hidden chain-of-thought, unrelated chat, secrets, or implementation output.

### Tracker Durability Gate

Before every user-facing response that follows substantive discussion, inspection, a user answer, a decision, a scope change, or an authorized mutation, persist all material deltas to the tracker and update the Active Snapshot, `Last updated`, and `Resume Checkpoint` when their state changed. Complete any required tracker write before sending the response. Do not rewrite the tracker for explanations, status restatements, or inspections that produce no material durable-state change.

After the durable write, acknowledge its revision with `ack-write`, then complete the hook turn checkpoint. A checkpoint never substitutes for acknowledging a changed tracker. If no material delta exists, explicitly use the no-change checkpoint only after verifying that the tracker remains accurate.

If the tracker update fails, do not present unsaved conclusions as durable handoff state. Report the exact persistence blocker, identify what was not saved, and stop before further substantive work. An abrupt process or host failure cannot be made atomic with chat delivery; on the next available turn, reconcile the tracker against the visible conversation before continuing.
