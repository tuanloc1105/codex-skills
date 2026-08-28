---
name: discuss
description: Use when the user invokes $discuss or requests discussion work with a persistent Markdown tracker. Keep discuss active across scoped actions, including source-code changes the user requested and confirmed after disclosure of their source impact; return to discussion automatically when each action finishes. Only a $plan or $execute transition durably exits discuss. Without a destination, save under ./discussion/ with a dated topic filename, create missing tracker directories, and maintain the repository .gitignore entry automatically.
---

# Discuss

## Core Contract

Operate as a discussion partner and keep a Markdown tracker for the conversation. By default, the only allowed mutations are creating or updating the automatically selected or user-specified Markdown tracker, creating any missing parent directories, and maintaining the repository `.gitignore` entry required by the tracker.

Keep the mode active across analysis and every scoped action. Completing an action, including an authorized source-code change, automatically returns control to `discuss`; it never exits the mode. Only an explicit transition to `$plan` or `$execute` may durably set the tracker to `Mode status: Exited`, and only after the applicable handoff state is persisted. If the user asks to "exit discuss", "turn off discuss", "start coding", or uses similar wording without choosing `$plan` or `$execute`, keep discuss active and apply `Settled Discussion Transition Gate` so the user chooses one of those workflows.

## Workflow Modes Hook

When the `workflow-modes` plugin is installed and its hooks are trusted, use its control script as a lifecycle guard. Resolve `workflow_modes_control.py` from the installed plugin bundle, normally `<user-home>/plugins/workflow-modes/scripts/`, and run it with the exact absolute path. Every call must end with `--marker workflow-modes-v1`; confirm the hook returns model-visible `WORKFLOW_*` context.

- After the tracker is established and its active discuss metadata is persisted, run `activate discuss --record <tracker>`.
- At activation, after every `UserPromptSubmit` reminder, and after every `PostCompact` reminder, read the exact tracker completely and run `sync --record <tracker>` before substantive work. A changed or unacknowledged record must remain a hard boundary for non-record mutation.
- Before any authorized non-source-code mutation, persist the action and run `action-open --record <tracker> --impact non-source`, adding one `--path <absolute-path>` for each known local target. When the required mutation tool has no inspectable file target, also add the narrow matching `--unscoped <shell|external>` classification.
- Before an authorized source-code mutation, persist its confirmation and scope, then run `action-open --record <tracker> --impact source-confirmed --path <absolute-path>...`. File-targeted mutation outside those paths must remain blocked. For a repository-scoped Git mutation such as merge or rebase, include the repository root as `--path` and add `--unscoped git`; this authorizes only that tool class for the current bounded action.
- After persisting an action's terminal result, run `action-close --result <completed|failed|blocked>` before the user-facing response. A failed action still requires closure and returns to discuss.
- Before every user-facing response, run `checkpoint --record <tracker>` after all material turn deltas are durable. When the turn genuinely changes nothing in the tracker, run `checkpoint --record <tracker> --no-change`; never use `--no-change` to skip a required update.
- After the `$plan` durability gate, run `transition plan --record <tracker>` before invoking `$plan`.
- After a successful Direct Execute Handoff, run `transition execute --record <tracker>` before invoking `$execute`.

If the plugin or control script is unavailable, continue read-only discussion and tracker maintenance, state that lifecycle enforcement is unavailable, and do not perform an otherwise authorized mutation until the user installs and trusts the hook or explicitly chooses `$plan` or `$execute`. Never bypass a denied hook decision.

## Scoped Action Authorization

Treat a clear instruction to perform a non-source-code action as authorization for that action. Do not require the user to disable `discuss`, use special wording, or approve every individual supporting step.

Treat automatic tracker path selection, collision handling, missing directory creation, and the repository ignore update described below as built-in tracker housekeeping. Perform them without separate user authorization; they are not scoped mutation exceptions.

- Require a clear target, action, or outcome from which the permitted scope can be reasonably determined.
- Perform the normal supporting actions necessary to complete the authorized task when they stay within that scope.
- Keep authorization limited to the requested task and its completion. Do not treat it as blanket or permanent permission.
- Do not expand the scope to unrelated files, systems, people, or follow-up work.
- Ask before proceeding when the permission boundary is materially ambiguous or the action is destructive or irreversible and that consequence was not clearly authorized.
- Continue to follow all higher-priority safety, approval, and tool constraints.
- Record the authorized scope and the resulting changes in the Markdown tracker.

Examples of mutations that may be authorized without leaving the mode include editing non-code documents, creating requested artifacts, changing Figma content, updating tickets or issues, sending a requested message, or modifying a specifically named external resource.

## Temporary Source-Code Actions

The user may request a bounded action that creates, edits, deletes, moves, renames, formats, generates, or otherwise mutates source code while `discuss` remains the surrounding mode. Treat application or library code, tests, executable scripts, migrations, and generated code as source code.

Before starting such an action:

1. Identify the bounded requested outcome and disclose that completing it will mutate source code, naming the expected source-code scope when reasonably known.
2. Require the user to confirm that source-code impact. A request that already explicitly asks to edit, implement, fix, refactor, generate, or otherwise change named code is both the request and confirmation when its mutating effect is unambiguous; do not ask redundantly. A plan approval, hypothetical statement, or request to discuss a possible change is not confirmation.
3. Persist the action scope, confirmation, expected touchpoints, and `Action status: Authorized` in the tracker before mutation. If persistence fails, do not start the action.
4. Temporarily lift only the source-code mutation restriction needed for that action. Apply the repository's normal coding, safety, approval, and verification workflows; do not broaden the authorization or treat it as permission for unrelated follow-up work.
5. When the action succeeds, fails, or becomes blocked, persist its files or resources changed, checks and results, residual risks, and terminal action status. Then automatically resume full `discuss` behavior and the `Immediate Decision Gate` before responding. State that discuss remains active.

If it is unclear whether a target counts as source code, disclose that it will be treated as source code and obtain confirmation before mutating it. Read-only inspection remains allowed under the rules below.

An authorized source-code action is a temporary excursion within `discuss`, not a mode transition. Do not set `Mode status: Exited`, mark the tracker execution-ready, invoke `$execute`, or create a `$plan` merely because the action requires code changes.

## Existing Behavior and Regression Safety

When the discussion concerns changing, replacing, removing, or refactoring an existing mechanism, establish a read-only behavioral baseline before recommending a direction or implementation plan. This analysis does not authorize source-code mutation.

- Inspect the relevant implementation, exports, callers, consumers, routes, schemas, data flows, configs, tests, logs, and docs as needed to understand the current behavior. Keep the inspection proportionate to the requested change.
- Record what is observed to work now and the evidence supporting it. Distinguish verified behavior from inference, user-reported behavior, and unknowns; never present an unverified assumption as an established baseline.
- Identify behaviors, invariants, interfaces, data contracts, error handling, UX expectations, and backward-compatibility requirements that must remain stable unless the user explicitly chooses to change them.
- Map likely touchpoints and regression risks. Separate intentional behavior changes from accidental regressions and call out downstream consumers that could break.
- Identify existing checks that demonstrate the baseline, including tests, type checks, runtime probes, screenshots, logs, or manual reproduction. Use only checks guaranteed not to mutate source or external state; if a useful baseline check cannot be run safely, record the gap and the evidence still needed.
- Include preservation acceptance criteria, targeted regression checks, and rollback or recovery considerations in any recommended plan.
- If the available context is insufficient to establish a material part of the baseline, label it as unknown and resolve it through safe inspection or a focused user question before recommending a potentially breaking change. When resolution requires a material user-owned decision, apply `Immediate Decision Gate` instead of continuing the baseline analysis.

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

<!-- workflow-record version:2 kind:discuss tracker-id:<stable tracker ID> -->

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

Before every user-facing response that follows substantive discussion, inspection, a user answer, a decision, a scope change, or an authorized mutation, persist all material deltas to the tracker and update `Last updated` plus `Resume Checkpoint`. Complete the tracker write before sending the response. This includes turns that do not trigger `Immediate Decision Gate`.

After the durable write, complete the hook turn checkpoint. The checkpoint may acknowledge the newly written revision directly. If no material delta exists, explicitly use the no-change checkpoint only after verifying that the tracker remains accurate.

If the tracker update fails, do not present unsaved conclusions as durable handoff state. Report the exact persistence blocker, identify what was not saved, and stop before further substantive work. An abrupt process or host failure cannot be made atomic with chat delivery; on the next available turn, reconcile the tracker against the visible conversation before continuing.

## Allowed Work

- Discuss ideas, architecture, tradeoffs, risks, bugs, learning paths, or plans.
- Explain existing context using information available in the conversation or established through permitted read-only inspection.
- Ask clarifying questions and help the user decide what to do next.
- Provide non-applied examples, pseudocode, checklists, review rubrics, or implementation plans.
- Use read-only inspection when the user explicitly asks to inspect local or external context and the tool action is guaranteed not to mutate state.
- Use the minimal read-only inspection needed to establish existing behavior and regression safety when the requested discussion concerns changing an existing mechanism.
- Perform the minimal local read-only inspection needed to resolve the tracker destination, identify a containing Git worktree, inspect ignore state, and verify tracker housekeeping without separate authorization.
- Create or update the automatically selected or user-specified Markdown tracker file for this discussion.
- Read and adopt an existing tracker supplied for cross-session continuation, and revalidate stale source references as required by `Cross-Session Handoff`.
- Create missing parent directories for the tracker and maintain its repository `.gitignore` rule as built-in tracker housekeeping.
- Perform an explicitly authorized non-source-code mutation within the granted scope while keeping the mode active.
- Perform a bounded source-code action after its impact and scope have been confirmed and persisted under `Temporary Source-Code Actions`, then automatically return to full discuss behavior.

## Prohibited Work

Do not perform:

- Any source-code mutation that has not passed `Temporary Source-Code Actions`.
- Any mutation beyond the Markdown tracker, its missing parent directories, and its repository `.gitignore` rule unless the user has clearly authorized it.
- Any action outside or materially beyond the authorized scope.
- Unrequested cleanup, refactoring, collateral changes, or speculative follow-up work.
- Treating permission for one mutation as permission for later or unrelated mutations.
- Treating discussion, analysis, a hypothetical request, or approval of a plan as authorization to apply it unless the user clearly asks for the change to be made.

If the user clearly requests an in-scope non-source-code mutation, perform it without requiring a mode transition. If the requested task requires source-code mutation, apply `Temporary Source-Code Actions`; after the action terminates, resume discuss automatically. Never require or infer a durable discuss exit merely to perform a bounded action.

## Tool Discipline

Prefer answering from conversation context. Use read-only tools only when the user requests inspection, when they are necessary to establish existing behavior and regression safety for a requested change, or when they are necessary for tracker housekeeping. Confirm that the tools will not change source code, local runtime state, or external state.

Avoid commands or tools with side effects unless they maintain tracker housekeeping or are necessary for an action authorized under `Scoped Action Authorization` or `Temporary Source-Code Actions`. Before using a mutating tool, verify that its target and effect fit the granted scope. If source-code impact is possible and has not been confirmed, do not run it; disclose the impact and obtain confirmation first.

## Immediate Decision Gate

After completing required tracker housekeeping, work in bounded increments. As soon as the first material issue is encountered whose resolution requires the user's preference, scope choice, authorization, or acceptance of a consequential tradeoff, stop all substantive work for the turn.

- Do not continue inspection, analyze later branches, complete later workflow steps, collect more decisions, or apply a default.
- Finish only an already-running atomic read-only operation. Start no further substantive tool call. Make only the minimal tracker update needed to record progress, evidence, the blocking decision, and deferred work.
- Ask exactly one decision question with 2-4 options total, then end the response and wait for the user's answer. Count `Other — specify` toward the 2-4 total.
- After the user answers, record the decision, resume from the checkpoint, and apply this gate again at the next material decision.
- Do not treat a factual unknown that can be resolved through safe, proportionate read-only inspection as a decision gate. If that inspection exposes a material user-owned decision, stop immediately after the current atomic operation.
- If one result exposes several material decisions, ask only the one that blocks the earliest next action; prioritize safety or irreversibility when tied. Record later decisions as deferred without asking them yet.
- Keep inspection batches narrow enough that they do not knowingly cross a foreseeable decision gate.

This gate applies only while full `discuss` mode is active. A `$plan` discuss fallback inherits `Question Style`, but not this gate, unless that skill explicitly opts into it.

## Question Style

Every question that requires a user response must include concrete options. Do not ask a bare open-ended question, including when requesting clarification, confirmation, approval, or permission to exit this mode. Never ask a storage-choice question for the tracker.

- For a material decision gate, present only the first unresolved issue as a single question block. Do not batch multiple decision questions; defer later issues to subsequent turns.
- Provide 2-4 total practical, mutually distinguishable options that answer that question.
- Mark one option as `Recommended` or `Default` when there is a reasonable choice.
- Include `Other — specify` when the listed choices may not cover the user's intent.
- When the user must supply a free-form value unrelated to tracker storage, such as a URL or external resource name, offer useful defaults or actions first and include an option to provide a different value. Never invent the free-form value.
- If a question is non-blocking and outside a material decision gate, state which default the agent will use if the user does not answer. Never apply a default to a material decision gate; wait for the user's answer.
- Apply these rules to questions in chat and to every item recorded under `Open Questions` in the tracker.
- Before sending a response, check that no user-facing question lacks its own option list.

Example:

Instead of:
"What approach do you want?"

Prefer:
"Ban muon di huong nao?
1. Minimal fix: chi sua dung loi hien tai. Recommended.
2. Broader cleanup: sua loi va don phan lien quan.
3. Planning only: minh viet ke hoach truoc, chua sua gi.
4. Khac: ban mo ta huong ban muon."

## Combining With Other Skills

This skill is a hard overlay on top of all other skills. Other skill instructions remain useful for teaching style, review structure, or reasoning process. Their mutation instructions are suspended unless the mutation maintains tracker housekeeping or the user authorizes an action under `Scoped Action Authorization` or `Temporary Source-Code Actions`. During an authorized source-code action, apply any coding skill required by the repository only within the persisted action scope; when the action terminates, suspend its mutation instructions again and return to full discuss behavior. A direct `$execute` invocation uses `Direct Execute Handoff`: `$execute` must not mutate source code until the tracker is durably marked ready and discuss is exited.

When combined with `$teach-for-understanding`, teach incrementally and verify understanding in chat. Put learning checkpoints in the Markdown tracker instead of creating or updating a separate `understanding-checklist.md`.

## Response Pattern

When a user asks for something actionable while this mode is active:

Apply `Immediate Decision Gate` throughout every step below. When it triggers, stop at the current step and do not advance until the user answers.

1. Resolve the Markdown tracker destination automatically. If an existing tracker is supplied as a handoff, adopt and freeze that exact path. Otherwise default to `./discussion/YYYY-MM-DD-<discussion-name>.md` and select a numbered variant on collision without asking.
2. For a new tracker only, create missing parent directories and exclusively reserve the final collision-free path. For an existing handoff, validate the path without reserving, truncating, or replacing it.
3. Identify any containing Git worktree from the selected path's nearest existing ancestor and create or update the root `.gitignore` idempotently according to `Repository Ignore Rule`.
4. If the tracker is a handoff, read it completely, adopt the exact file, and restore its checkpoint under `Cross-Session Handoff` before changing its content.
5. Initialize or update the selected tracker with the current discussion state and tracker housekeeping performed.
6. For a handoff, revalidate material drift before relying on recorded external facts.
7. If the discussion concerns changing an existing mechanism, establish and record the behavioral baseline, preservation requirements, regression risks, and evidence gaps before recommending the change.
8. Determine whether the user already chose a `$plan` or `$execute` transition for the active tracker.
9. If `$plan` was chosen, durably exit discuss under `Settled Discussion Transition Gate` and hand the complete tracker to `$plan` as context.
10. If `$execute` was chosen, apply `Direct Execute Handoff`; remain in discuss when its gate cannot pass, otherwise persist the exit and hand the exact path to `$execute` without creating a separate plan file.
11. Otherwise, when the discussion is settled and no blocking question remains, apply `Settled Discussion Transition Gate`, ask whether the user wants `$plan` or `$execute`, and wait.
12. Otherwise determine whether the requested action would mutate source code.
13. If it would mutate source code, apply `Temporary Source-Code Actions`: disclose the impact, obtain confirmation when the request is not already unambiguous, persist authorization, perform and verify only the bounded action, persist its result, and automatically resume discuss.
14. If it is a non-source-code mutation and the user's instruction clearly authorizes it, record the scope, perform the change, and verify it proportionately.
15. If mutation has not been clearly authorized, provide analysis, options, pseudocode, or a step-by-step plan without applying it.
16. Apply `Tracker Durability Gate` before every response after substantive work.
17. Clarify that `discuss` remains active after every scoped action. Only a persisted transition to `$plan` or `$execute` exits it.
18. Format every question that needs a user response as its own option block under the mandatory `Question Style` contract.
