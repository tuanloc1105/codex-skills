---
name: discuss
description: Use when the user invokes $discuss or requests discussion with a persistent version 4 Markdown record bundle. Keep decisions and evidence resumable across scoped actions, with explicit exit, pause, or handoff to plan or execute.
---

# Discuss

## Core Contract

Keep one Markdown record bundle for the discussion. Default mutations are limited to that bundle, its missing parents, and its repository ignore entry. Clearly authorized bounded actions may temporarily extend that scope; completing an action returns to discussion without changing modes.

The user controls the lifecycle. An explicit request to exit, stop, pause, or cancel discuss must be honored without requiring `$plan` or `$execute`. Persist the checkpoint and actual action results, set `Mode status: Paused` for a pause or `Exited` for exit/cancel, then deactivate the hook. Keep unfinished questions and work accurate. Do not ask for confirmation of a clear stop instruction. A request to stop one action need not exit the surrounding discussion; use the user's stated scope.

A request to discuss a workflow, read its files, or review this skill is not an invocation of that workflow. Follow explicit instructions not to activate it.

## Reference Routing

Read each routed reference completely before applying it:

- [references/tracker.md](references/tracker.md): creating, resuming, updating, exiting, or handing off a bundle. Always include it in Required references while discussing.
- [references/actions.md](references/actions.md): behavioral baseline, scoped mutation, or combining skills. Include it in Required references only while those activities apply.

Keep the entrypoint and current Required references acknowledged after activation, compaction, or a reference-set change. Reference routing does not require rereading unchanged material on every tool call.

## Decision Gate

Ask when a user-owned choice materially changes the outcome, scope, authority, or consequential tradeoff. Record the blocking choice and stop work that depends on its answer. Safe, proportionate read-only inspection of independent questions may continue while awaiting the answer; do not implement a default for the blocked branch.

- Ask the earliest blocking question first. Batch related questions only when they can be answered independently and doing so reduces back-and-forth.
- Resolve factual unknowns through available evidence before asking the user.
- Use reasonable assumptions for reversible implementation details within an already agreed scope; record assumptions only when useful for resuming.
- Keep tool batches bounded by dependencies and authorization, not by an arbitrary one-question-per-turn rule.

## Question Style

Use concise questions. For a real choice, provide 2-3 concrete alternatives and a recommendation when justified. Respect the question tool's option limits and built-in free-text option. For a required URL, identifier, credential location, or other factual value, ask directly rather than inventing artificial options. Never invent missing values.

Distinguish blocking questions from optional preferences. A blocking question requires an answer; elapsed time is not approval. For an optional preference, state the intended default and continue independent work. Record open questions with stable IDs, their blocking scope, and options only when there are actual alternatives. Do not ask where to store a new tracker when the default can be resolved.

## Working Sequence

1. Resolve the supplied bundle directory or `index.md`, or reserve `./discussion/YYYY-MM-DD-<slug>/` with a numbered suffix on collision. Freeze its canonical root.
2. Read an existing bundle completely before adoption; initialize a new bundle using the tracker reference. Maintain its narrow repository ignore rule.
3. Restore the checkpoint and revalidate material live facts. For changes to an existing mechanism, record a proportionate baseline, preservation requirements, and evidence gaps before recommending a direction.
4. Apply the decision gate. Perform an authorized scoped action only under the actions reference, then reconcile its actual result and return to discussion.
5. If the user requests `$plan`, persist the handoff and transition to a separate plan bundle. If the user requests `$execute`, satisfy Direct Execute Handoff and retain this exact bundle.
6. When the discussion is settled, summarize the outcome and the available next steps: stop here, plan, or execute. Do not force a transition or ask the same transition question repeatedly when the user only wanted analysis.
7. Persist material decisions, evidence, and the next safe action before the final response. Mention the record path on creation, handoff, exit, or when it helps the user resume; avoid repeating lifecycle boilerplate in every progress update.

## Workflow Modes Hook

When the plugin is installed and trusted, resolve its exact `workflow_modes_control.py` path from the installed bundle. Run each lifecycle command alone with the configured Python interpreter and end it with `--marker workflow-modes-v1`. Verify model-visible `WORKFLOW_*` confirmation; the control script's own output is not proof that a hook ran.

- After bundle initialization, run `activate discuss --record <root>`. Read the required scope, run `sync --record <root> --scope record`, then `rules-sync --record <root> --reference <relative-reference>...`.
- At activation and after `PostCompact`, read `index.md` and all manifest files. After `UserPromptSubmit`, obey `sync_status`: `current` needs no reread; `snapshot` needs only the delimited Active Snapshot and snapshot sync; `record` needs a complete bundle read and record sync.
- Before bundle edits, run `write-open --record <root> --previous-revision <acknowledged revision>`, declaring new Markdown files with `--path`. Update affected files together, then `write-close --record <root>`. An unchanged valid transaction may close normally.
- Before an authorized mutation, persist its scope and authorization, then `action-open --record <root> --impact <non-source|source-confirmed> --path <absolute-file>...`. Add only necessary `--unscoped <shell|git|external>` classes for operations without inspectable file targets. Close after recording its result with `action-close --result <completed|failed|blocked|paused|cancelled>`.
- Before a final response, checkpoint material deltas with `checkpoint --record <root>`. Use `--no-change` for a genuinely unchanged turn. Routine progress commentary does not require closing a work unit or checkpointing.
- For a handoff, finish the source checkpoint before changing the required references to the destination set, close that write, and run `transition <plan|execute> --record <root>`. The destination then reads/syncs its rules. For exit/pause, persist terminal mode metadata, close actions/writes, checkpoint, then `deactivate`.

The hook checks known tool schemas and conservatively treats opaque execution as potentially mutating. It is bookkeeping and scope assistance, not a sandbox: shell/external classes do not prove individual file/resource boundaries, and the model must inspect effects and honor the user's authority. Prefer file tools with inspectable targets; never disguise mutations as reads or bundle unrelated commands with a lifecycle call.

If persistence fails, use `suspend --record <root> --reason persistence-failed` and report the failed write and last durable checkpoint. For an immediate user stop that cannot be reconciled, use `--reason user-stop`. Suspended mode permits an honest final response while preserving open state and denying non-record mutation. Repair only recorded bundle paths in a write transaction, close it, reconcile actions, sync record/rules, then `recover --record <root>` before resuming or deactivating. A repeated unresolved Stop block also suspends safely instead of looping indefinitely.

Check the installed control script's `--help` before relying on new recovery commands. An older hook may not support this lifecycle; report the version mismatch and do not bypass a denial or reinstall during an active task. If enforcement is unavailable, continue discussion and tracker maintenance; explain the limitation before any otherwise authorized mutation. Do not begin that mutation until compatible enforcement is available or a higher-priority user instruction explicitly selects an unenforced workflow.
