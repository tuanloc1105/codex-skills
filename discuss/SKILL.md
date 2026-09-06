---
name: discuss
description: Use when the user invokes $discuss or requests discussion with a persistent version 4 Markdown record bundle. Keep decisions and evidence resumable across scoped actions, with explicit exit, pause, or handoff to plan or execute.
---

# Discuss

## Core Contract

Keep one Markdown record bundle for the discussion. Default mutations are limited to that bundle, its missing parents, and its repository ignore entry. Clearly authorized bounded non-source actions may temporarily extend that scope; completing an action returns to discussion without changing modes. Source-code mutation requires an execution request and a completed handoff to execute; there is no temporary source-code exception inside discuss.

The user controls the lifecycle. An explicit request to exit, stop, pause, or cancel discuss must be honored without requiring `$plan` or `$execute`. Persist the checkpoint and actual action results, set `Mode status: Paused` for a pause or `Exited` for exit/cancel, then deactivate the hook. Keep unfinished questions and work accurate. Do not ask for confirmation of a clear stop instruction. A request to stop one action need not exit the surrounding discussion; use the user's stated scope.

A request to discuss a workflow, read its files, or review this skill is not an invocation of that workflow. Follow explicit instructions not to activate it.

## Required Record Completeness

Keep the discussion bundle complete. Save material requirements and constraints, verified findings with evidence locators, alternatives and tradeoffs, accepted/rejected decisions and rationale, pending questions with their displayed options, authorized action results, scope changes, and the next safe action. Preserve unresolved and superseded items accurately.

Persist related changes at meaningful checkpoints, before a dependent handoff, and reconcile the current turn against the bundle before the final response. Completeness means enough accurate information to resume without losing material facts, not a raw transcript or hidden reasoning. Do not defer all recording until task completion or treat a hook acknowledgment/no-change flag as proof that nothing was missed. Verify the affected files were actually saved and their cross-file state agrees.

Hook acknowledgments are optional integration metadata; complete tracker/plan content is mandatory even when hooks are absent, quiet, stale, or failing. If persistence fails, retain unsaved facts in the current task context, repair from known evidence, and continue independent in-scope work only while its prerequisites remain known. Disclose the failed files, last durable checkpoint, and unsaved material facts in the final response if repair cannot finish. Never claim they were saved or mark unfinished work complete. Honor a user stop immediately; recording must not become a reason to continue implementation after it.

## Reference Routing

Read each routed reference completely before applying it:

- [references/tracker.md](references/tracker.md): creating, resuming, updating, exiting, or handing off a bundle. Always include it in Required references while discussing.
- [references/actions.md](references/actions.md): behavioral baseline, scoped mutation, or combining skills. Include it in Required references only while those activities apply.

Restore the entrypoint and applicable references after activation, compaction, or a reference-set change, honoring user exclusions; reconcile hook acknowledgments when available. Reference routing does not require rereading unchanged material on every tool call.

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

## Mandatory Recovery After Compaction

After compaction, restore the current tracker/plan, every manifest file, the active mode's `SKILL.md`, and only its applicable Required references before task mutations, worker dispatch, or conclusions that depend on lost context. Read mode instructions as recovery context; this does not activate other skills. Reassess Supporting skills and honor user exclusions instead of loading all recorded skill names.

With the compatible hook, `PostCompact` opens a one-time read gate. Use `restore-status --marker workflow-modes-v1` on the exact installed control script to get the next required absolute path, character offset, and epoch. Run `restore-read --record <root> --path <path> --offset <offset> --epoch <epoch> --marker workflow-modes-v1` as a standalone shell call with `max_output_tokens` at least 6000. Read its returned content and repeat using the next status until `PostToolUse` reports `WORKFLOW_CONTEXT_RESTORED`. Large files are paged automatically. The observer checks actual complete successful output against the current file; a failed/truncated read, a pre-tool request, ordinary file reads, and `sync`/`rules-sync` alone do not clear this gate. If the file changed, reread from the offset requested by status.

Read-only inspection, asking questions, interrupting owned work, direct Markdown repairs inside the bound record, and honest blocker/stop reporting remain available. Do not repair from guesses or resume stopped work. Missing documents or unsupported result routing require an accurate report; do not bypass the gate, claim restoration succeeded, or loop on the same failure. Do not present context-dependent conclusions until the necessary context is restored. Once restored, action/transaction/checkpoint bookkeeping returns to advisory behavior; complete record content remains mandatory.

If only `functions.exec` is available, the hook recognizes exactly one `text(await tools.exec_command(<JSON object>));` call, or `text(await tools.apply_patch(<JSON string>));` for record repair. Use literal JSON arguments without extra JavaScript. Other opaque wrappers remain gated during recovery. Without a compatible optional hook, perform the same complete recovery manually and disclose the unavailable observation mechanism when relevant; do not pretend a read receipt exists.

## Workflow Modes Hook

The optional hook reminds the agent of the current mode and required record completeness. Outside the post-compact recovery gate, it never grants or denies tool permissions. It never blocks a final response. Discuss focuses on discussion and avoiding premature source changes; plan focuses on planning; execute carries out delegated work. Actual user instructions control authority, stops, and skill activation.

When the plugin is installed and trusted, use its exact `workflow_modes_control.py` path with the configured Python interpreter. Run each lifecycle request alone with `--marker workflow-modes-v1` last. Verify model-visible `WORKFLOW_*` confirmation; a successful CLI process alone does not prove a state update.

- On fresh entry, save the bundle and attempt `activate discuss --record <root>`. On adoption/compaction, read the full bundle and applicable references; on later prompts use `sync_status` to focus rereads. Use `sync` and `rules-sync` when supported, without activating excluded skills.
- Save affected record files consistently. Optional `write-open --record <root> --previous-revision <revision>` and `write-close --record <root>` track these edits; declare new Markdown paths with `--path` when using them. An absent or failed transaction acknowledgment does not prevent direct record maintenance.
- Actions are optional tracking metadata, not mutation permissions. Record an authorized action's scope and actual result in the bundle whether or not `action-open`/`action-close` is used. Inspect actual effects of shell, Git, wrappers, and external tools; tool classification alone does not establish source impact or authority.
- Reconcile every material turn delta before the final response or handoff, and attempt `checkpoint --record <root>` when supported. Use `--no-change` only after checking that the bundle remains complete and accurate. Progress commentary needs no checkpoint.

For a plan handoff, save discussion deltas and the source link, then use `transition plan --record <root>` when available; plan creates a separate bundle. For direct execute, persist the execution-ready handoff in this exact bundle and use `transition execute --record <root>`. A clear implementation request needs no second permission question. Source work belongs to execute; a failed hook acknowledgment does not invalidate a handoff already saved under the user's request. For exit/pause, save the actual mode status and unfinished work, reconcile any opened actions/writes, and attempt `deactivate`.

`WORKFLOW_CONTROL_NOT_APPLIED` means the requested lifecycle update was not acknowledged. Correct it when possible without fabricating success or repeatedly asking for already granted authority. Maintain the complete bundle directly if integration is unavailable. A bookkeeping control failure adds no tool or reporting gate; the independent post-compact read gate remains until actual context delivery is verified.

For persistence trouble, optionally record `suspend --record <root> --reason persistence-failed`, repair the exact bundle from known facts, reconcile metadata, and attempt `recover`. For an actual user stop, `--reason user-stop` preserves that instruction: resume task work only when the user resumes it. Both states produce reminders, not tool denials; repeated Stop events do not auto-suspend. Follow Required Record Completeness for unsaved facts.

Check installed `--help` before relying on new commands. An older installed hook may still deny calls; do not bypass an actual denial, alter trust, or reinstall during an active task. Use supported recovery and report the exact compatibility limitation if necessary. An absent optional hook does not block in-scope work or direct tracker/plan maintenance.
