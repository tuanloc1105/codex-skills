---
name: discuss
description: Use when the user invokes $discuss or requests discussion with a persistent version 4 Markdown record bundle. Keep decisions and evidence resumable across scoped actions, with explicit exit, pause, or handoff to plan or execute.
---

# Discuss

## Core Contract

Keep one Markdown record bundle for the discussion. Default mutations are limited to that bundle, its missing parents, and its repository ignore entry. Clearly authorized bounded non-source actions may temporarily extend that scope; completing an action returns to discussion without changing modes. Source-code mutation requires an execution request and a completed handoff to execute; there is no temporary source-code exception inside discuss.

The user controls the lifecycle. An explicit request to exit, stop, pause, or cancel discuss must be honored without requiring `$plan` or `$execute`. Persist the checkpoint and actual action results, set `Mode status: Paused` for a pause or `Exited` for exit/cancel, then deactivate the hook. Keep unfinished questions and work accurate. Do not ask for confirmation of a clear stop instruction. A request to stop one action need not exit the surrounding discussion; use the user's stated scope.

A request to discuss a workflow, read its files, or review this skill is not an invocation of that workflow. Follow explicit instructions not to activate it.

## Reference Routing

Read each routed reference completely before applying it:

- [references/tracker.md](references/tracker.md): creating, resuming, updating, exiting, or handing off a bundle. Always include it in Required references while discussing.
- [references/actions.md](references/actions.md): behavioral baseline, scoped mutation, or combining skills. Include it in Required references only while those activities apply.

Keep the entrypoint and current Required references acknowledged after activation, compaction, or a reference-set change. Reference routing does not require rereading unchanged material on every tool call.

## Immediate Decision Gate

As soon as a user-owned choice materially changes the outcome, scope, behavior semantics, authority, or consequential tradeoff, stop substantive work for the turn. Finish only an already-running atomic read-only operation, persist the evidence, blocking question, and deferred work, then ask exactly one decision question and wait. Do not start further inspection, analyze later issues, develop the dependent solution, or apply a default while the choice is pending.

Before recommending a direction or developing its implementation details, check whether it depends on an unresolved user-owned decision about scope, behavior semantics, authority, or consequential tradeoffs. If so, present verified evidence and impact, ask one choice question, and wait before selecting or developing the dependent solution. Help the user choose: recommend an option when evidence, goals, or constraints support a defensible preference, explaining the reason. A conditional recommendation may state its assumption beside the option; that assumption is not an accepted requirement. Leave options neutral only when there is no defensible basis to favor one, briefly saying what is missing. Never treat a recommendation as an accepted decision. Resolve factual unknowns through evidence and label remaining uncertainty; do not turn an unverified claim into either a fact or a user preference.

When asked to go through issues one at a time, finish the current issue's evidence, impact, and any necessary decision question before moving to the next conversational issue. Wait at a blocking choice. If no material choice is missing, explain the conclusion and continue without inventing a question.

A reply answers only the pending question: a number, agreement with a behavior option, or approval of a recommendation does not authorize implementation. Keep accepted requirements, plan approval, and execution authorization separate in both the record and the response. Say a requirement is settled when only its meaning has been agreed; report implementation only after authorized changes and verification.

- Ask the earliest blocking question first. Keep only one choice question pending so a bare number has an unambiguous meaning.
- Resolve factual unknowns through available evidence before asking the user.
- Use reasonable assumptions for reversible implementation details within an already agreed scope; record assumptions only when useful for resuming.
- Keep read-only batches narrow enough not to knowingly cross a foreseeable decision gate. After an answer, record its meaning and constraints, resume from the checkpoint, and apply this gate again.

## Question Style

Ask one choice question at a time in a plain-text chat message, with the question on its own line followed by a blank line and 2-4 concrete options numbered consecutively as `1.`, `2.`, `3.`, `4.`. Never use letter labels or pad the list to reach four options. Use this format instead of a question tool unless higher-priority instructions require that tool. Put the recommended option first when justified and mark it with `Recommended — <brief reason>` in the user's language on the same line.

Give each clarification, confirmation, approval, or transition decision its own practical, mutually distinguishable alternatives. Include `Other — specify` within the 2-4 total when the choices may not cover the user's intent; omit it when the question tool already provides free-text input. Never combine unrelated decisions under one option list or ask the user to choose a tracker location.

When higher-priority instructions require a question tool or prohibit choice lists in chat, preserve the alternatives through an available question tool permitted for that question type. Prefix option labels with `1.`, `2.`, etc. when supported; respect the tool's option count, label limits, and built-in free-text support. Keep the recommendation and its reason in the supported label/description fields, and preserve the displayed order in the record's number-to-option mapping. If no permitted tool can present choices, explain the limitation briefly and ask through the permitted format; do not bypass tool restrictions or imply that options were displayed.

Before sending a choice question, check that the outgoing message or tool payload actually includes the alternatives and any justified recommendation. When either presentation route is permitted, do not substitute a prose-only “X or Y?” question or a promise to provide options later. If the user reports missing options, present the current question with its options immediately through the permitted route instead of only acknowledging the omission.

Accept a bare number such as `1`, a number with an explanation such as `2. user's reason`, or a free-form answer. Map the number to the current pending question and honor any accompanying reason or constraint; clarify only if the answer is ambiguous or contradictory. Keep the pending question and its number-to-option mapping in the record so a short reply remains interpretable after resuming. Do not repeat a clearly answered question merely to confirm the selection.

For example:

```text
Which rollout scope do you prefer?

1. New data first — Recommended: limits risk and makes verification easier.
2. All existing and new data.
3. A pilot group first.
```

For a required factual value such as a URL or identifier, offer useful known defaults or actions when available, including supplying a different value. If there are no real alternatives, ask directly for the value rather than fabricate choices. Never invent missing values.

For metric scope, first establish whether the value represents the visible page, all filtered results, or the whole portfolio. Explain observed data coverage and each option's meaning. Recommend the scope best supported by the intended use, stating any assumption explicitly; do not select backend aggregation before scope is settled. A reply choosing the visible page settles that requirement only. Then discuss calculation and data retrieval within that scope. See [references/decision-scenarios.md](references/decision-scenarios.md) when checking question behavior or rehearsing these boundaries.

Distinguish blocking questions from optional preferences. A blocking question requires an answer; elapsed time is not approval. Only outside a material decision gate may an optional preference use a stated default. Record open questions with stable IDs, their blocking scope, displayed options, and any justified recommendation/default. Do not ask where to store a new tracker when the default can be resolved.

## Working Sequence

1. Resolve the supplied bundle directory or `index.md`, or reserve `./discussion/YYYY-MM-DD-<slug>/` with a numbered suffix on collision. Freeze its canonical root.
2. Read an existing bundle completely before adoption; initialize a new bundle using the tracker reference. Maintain its narrow repository ignore rule.
3. Restore the checkpoint and revalidate material live facts. For changes to an existing mechanism, record a proportionate baseline, preservation requirements, and evidence gaps before recommending a direction.
4. Apply the decision gate. Perform an authorized scoped action only under the actions reference, then reconcile its actual result and return to discussion.
5. If the user requests `$plan`, persist the handoff and transition to a separate plan bundle. If the user requests `$execute` or clearly asks to implement the agreed change, satisfy Direct Execute Handoff and retain this exact bundle. A clear execution request needs no repeated permission or special command wording; unresolved material decisions still block the dependent handoff. Never edit source while discuss remains active.
6. When the discussion is settled, summarize the outcome and the available next steps: stop here, plan, or execute. Do not force a transition or ask the same transition question repeatedly when the user only wanted analysis.
7. Persist material decisions, evidence, and the next safe action before the final response. Mention the record path on creation, handoff, exit, or when it helps the user resume; avoid repeating lifecycle boilerplate in every progress update.

## Workflow Modes Hook

When the plugin is installed and trusted, resolve its exact `workflow_modes_control.py` path from the installed bundle. Run each lifecycle command alone with the configured Python interpreter and end it with `--marker workflow-modes-v1`. Verify model-visible `WORKFLOW_*` confirmation; the control script's own output is not proof that a hook ran.

- After bundle initialization, run `activate discuss --record <root>`. Read the required scope, run `sync --record <root> --scope record`, then `rules-sync --record <root> --reference <relative-reference>...`.
- At activation and after `PostCompact`, read `index.md` and all manifest files. After `UserPromptSubmit`, obey `sync_status`: `current` needs no reread; `snapshot` needs only the delimited Active Snapshot and snapshot sync; `record` needs a complete bundle read and record sync.
- Before bundle edits, run `write-open --record <root> --previous-revision <acknowledged revision>`, declaring new Markdown files with `--path`. Update affected files together, then `write-close --record <root>`. An unchanged valid transaction may close normally.
- Before an authorized non-source mutation, persist its scope and authorization, then `action-open --record <root> --impact non-source --path <absolute-file>...`. Use `--unscoped external` only for explicitly authorized external effects without inspectable file targets. Shell/Git mutation and opaque execution wrappers require execute; prefer direct inspectable file or external tools. Close after recording its result with `action-close --result <completed|failed|blocked|paused|cancelled>`.
- Before a final response, checkpoint material deltas with `checkpoint --record <root>`. Use `--no-change` for a genuinely unchanged turn. Routine progress commentary does not require closing a work unit or checkpointing.
- For a handoff, finish the source checkpoint before changing the required references to the destination set, close that write, and run `transition <plan|execute> --record <root>`. The destination then reads/syncs its rules. For exit/pause, persist terminal mode metadata, close actions/writes, checkpoint, then `deactivate`.

The hook checks known tool schemas and conservatively treats opaque execution as potentially mutating. It is bookkeeping and scope assistance, not a sandbox: shell/external classes do not prove individual file/resource boundaries, and the model must inspect effects and honor the user's authority. Prefer file tools with inspectable targets; never disguise mutations as reads or bundle unrelated commands with a lifecycle call.

An older installed hook may still accept `source-confirmed` in discuss. That capability is not permission: follow the current source boundary, reconcile any legacy source action without further source edits, and hand off only on a real execution request. A hook or review PASS never supplies user authorization.

If persistence fails, use `suspend --record <root> --reason persistence-failed` and report the failed write and last durable checkpoint. For an immediate user stop that cannot be reconciled, use `--reason user-stop`. Suspended mode permits an honest final response while preserving open state and denying non-record mutation. Repair only recorded bundle paths in a write transaction, close it, reconcile actions, sync record/rules, then `recover --record <root>` before resuming or deactivating. A repeated unresolved Stop block also suspends safely instead of looping indefinitely.

Check the installed control script's `--help` before relying on new recovery commands. An older hook may not support this lifecycle; report the version mismatch and do not bypass a denial or reinstall during an active task. If enforcement is unavailable, continue discussion and tracker maintenance; explain the limitation before any otherwise authorized mutation. Do not begin that mutation until compatible enforcement is available or a higher-priority user instruction explicitly selects an unenforced workflow.
