---
name: plan
description: Plan-first collaboration with one version 4 Markdown record bundle under ./plans/. Inspect the problem, preserve decisions and verification, obtain approval, and hand the same bundle to execute only when execution is requested.
---

# Plan

## Boundaries and Lifecycle

Plan the requested work without implementing it. Read repository instructions and inspect relevant context, but do not edit production code, commit, push, deploy, or mutate external systems. Plan housekeeping is allowed.

Keep the same bundle through draft, approval, revisions, and execution handoff. Approval accepts a plan; it does not itself request implementation or change the active mode. A clear instruction such as “approve and implement” supplies both decisions and may trigger handoff after the approved bundle is saved.

Honor an explicit exit, pause, or cancellation without requiring execute. Persist current decisions and unfinished work, set `Plan mode: Paused` or `Exited`, close transactions, checkpoint, and deactivate. Do not mark unfinished planning complete or ask for confirmation of a clear stop. A review of this skill or a supplied plan is not by itself an instruction to activate a persistent mode.

## Required Record Completeness

Keep the plan bundle complete. Save the goal, scope and constraints, baseline evidence, accepted decisions and rationale, assumptions and open questions, implementation steps and dependencies, acceptance and verification criteria, risks/recovery, revisions, and the exact approval and execution-authorization status. Update all affected phase files and cross-links.

Persist related changes at meaningful checkpoints, before a dependent handoff, and reconcile the current turn against the bundle before the final response. Completeness means enough accurate information to resume without losing material facts, not a raw transcript or hidden reasoning. Do not defer all recording until task completion or treat a hook acknowledgment/no-change flag as proof that nothing was missed. Verify the affected files were actually saved and their cross-file state agrees.

Hook acknowledgments are optional integration metadata; complete tracker/plan content is mandatory even when hooks are absent, quiet, stale, or failing. If persistence fails, retain unsaved facts in the current task context, repair from known evidence, and continue independent in-scope work only while its prerequisites remain known. Disclose the failed files, last durable checkpoint, and unsaved material facts in the final response if repair cannot finish. Never claim they were saved or mark unfinished work complete. Honor a user stop immediately; recording must not become a reason to continue implementation after it.

## Reference Routing

Read the relevant reference completely:

- [references/plan-record.md](references/plan-record.md): creating, updating, approving, exiting, or handing off a bundle. Always required while planning.
- [references/phase-planning.md](references/phase-planning.md): only when phases, dependencies, waves, or delegation materially improve the plan.

Keep Required references minimal, read applicable context, and reconcile acknowledgments at a meaningful checkpoint; a missing acknowledgment does not gate work. For an ambiguous request, clarify within this same draft bundle; do not activate discuss or create a second tracker. Direct discuss-to-execute handoffs remain valid and do not require a plan bundle.

## Planning Sequence

1. Resolve and initialize the supplied destination or `./plans/YYYY-MM-DD-<slug>/`, with collision handling, before substantive planning. Freeze its canonical path and maintain the narrow ignore rule.
2. Record the concrete goal and relevant constraints. Inspect missing facts that can be found safely in the workspace before asking the user.
3. For a change to existing behavior, establish a proportionate baseline: evidence and its confidence, affected consumers, preserved contracts, intentional differences, regression risks, and targeted checks. Label material unknowns and their resolution steps.
4. Apply the Decision Gate before developing any strategy that depends on an unresolved material choice. Within settled scope, develop intended behavior, implementation strategy, verification, and recovery proportional to the change. Use a linear checklist for a small task; introduce phases only when useful. Record only decisions and evidence needed for handoff, not a transcript.
5. Ask for approval when the plan is decision-complete. Offer revision or pause when relevant. Existing unambiguous approval need not be requested again.
6. Save approval in the same bundle with `Plan mode: Active` and `Execute mode: Inactive`. Remain available for revisions. If a revision changes the approved outcome, invalidate the affected approval and obtain acceptance of that change.
7. Only on an explicit execution request, persist the execute handoff metadata and transition to `$execute` with this exact bundle. Do not implement under plan mode.

## Decision Gate

Before recommending a direction or developing its implementation details, check whether it depends on an unresolved user-owned decision about scope, behavior semantics, authority, or consequential tradeoffs. If so, present verified evidence and impact, ask one choice question, and wait before selecting or developing the dependent solution. Help the user choose: recommend an option when evidence, goals, or constraints support a defensible preference, explaining the reason. A conditional recommendation may state its assumption beside the option; that assumption is not an accepted requirement. Leave options neutral only when there is no defensible basis to favor one, briefly saying what is missing. Never treat a recommendation as an accepted decision. Resolve factual unknowns through evidence and label remaining uncertainty; do not turn an unverified claim into either a fact or a user preference.

When asked to go through issues one at a time, finish the current issue's evidence, impact, and any necessary decision question before moving to the next conversational issue. Wait at a blocking choice. If no material choice is missing, explain the conclusion and continue without inventing a question. Independent read-only inspection may still be batched.

A reply answers only the pending question: a number, agreement with a behavior option, or approval of a recommendation does not authorize implementation. Keep accepted requirements, plan approval, and execution authorization separate in both the record and the response. Say a requirement is settled when only its meaning has been agreed; report implementation only after authorized changes and verification.

## Questions and Independent Work

Ask only for missing choices that materially change the plan. Never ask a storage-choice question when the default applies.

Ask one choice question at a time in a plain-text chat message, with the question on its own line followed by a blank line and 2-4 concrete options numbered consecutively as `1.`, `2.`, `3.`, `4.`. Never use letter labels or pad the list to reach four options. Use this format instead of a question tool unless higher-priority instructions require that tool. Put the recommended option first when justified and mark it with `Recommended — <brief reason>` in the user's language on the same line.

Give each clarification, confirmation, approval, or transition decision its own practical, mutually distinguishable alternatives. Include `Other — specify` within the 2-4 total when the choices may not cover the user's intent; omit it when the question tool already provides free-text input. Never combine unrelated decisions under one option list. For plan approval, offer approval, targeted revision, broader rework, or pause/cancel only as applicable; approval alone keeps implementation unauthorized.

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

Record which question blocks dependent planning, approval, or execution, and name the affected work. Do not fill the blocked part of the plan with an assumed answer or present it as decision-complete. Continue safe independent inspection while waiting. Use reasonable assumptions only for reversible implementation details within agreed scope; optional preferences may use a stated reasonable default. Ask the earliest blocking question first and keep only one choice question pending. This does not limit batching independent read-only tool calls.

For metric scope, first establish whether the value represents the visible page, all filtered results, or the whole portfolio. Explain observed data coverage and each option's meaning. Recommend the scope best supported by the intended use, stating any assumption explicitly; do not select backend aggregation before scope is settled. A reply choosing the visible page settles that requirement only. Then plan calculation and data retrieval within that scope. See [references/decision-scenarios.md](references/decision-scenarios.md) when checking question behavior or rehearsing these boundaries.

## Mandatory Recovery After Compaction

After compaction, restore the current tracker/plan, every manifest file, the active mode's `SKILL.md`, and only its applicable Required references before task mutations, worker dispatch, or conclusions that depend on lost context. Read mode instructions as recovery context; this does not activate other skills. Reassess Supporting skills and honor user exclusions instead of loading all recorded skill names.

With the compatible hook, `PostCompact` opens a one-time read gate. Use `restore-status --marker workflow-modes-v1` on the exact installed control script to get the next required absolute path, character offset, and epoch. Run `restore-read --record <root> --path <path> --offset <offset> --epoch <epoch> --marker workflow-modes-v1` as a standalone shell call with `max_output_tokens` at least 6000. Read its returned content and repeat using the next status until `PostToolUse` reports `WORKFLOW_CONTEXT_RESTORED`. Large files are paged automatically. The observer checks actual complete successful output against the current file; a failed/truncated read, a pre-tool request, ordinary file reads, and `sync`/`rules-sync` alone do not clear this gate. If the file changed, reread from the offset requested by status.

Read-only inspection, asking questions, interrupting owned work, direct Markdown repairs inside the bound record, and honest blocker/stop reporting remain available. Do not repair from guesses or resume stopped work. Missing documents or unsupported result routing require an accurate report; do not bypass the gate, claim restoration succeeded, or loop on the same failure. Do not present context-dependent conclusions until the necessary context is restored. Once restored, action/transaction/checkpoint bookkeeping returns to advisory behavior; complete record content remains mandatory.

If only `functions.exec` is available, the hook recognizes exactly one `text(await tools.exec_command(<JSON object>));` call, or `text(await tools.apply_patch(<JSON string>));` for record repair. Use literal JSON arguments without extra JavaScript. Other opaque wrappers remain gated during recovery. Without a compatible optional hook, perform the same complete recovery manually and disclose the unavailable observation mechanism when relevant; do not pretend a read receipt exists.

## Workflow Modes Hook

The optional hook reminds the agent of the current mode and required record completeness. Outside the post-compact recovery gate, it never grants or denies tool permissions. It never blocks a final response. Discuss focuses on discussion and avoiding premature source changes; plan focuses on planning; execute carries out delegated work. Actual user instructions control authority, stops, and skill activation.

When the plugin is installed and trusted, use its exact `workflow_modes_control.py` path with the configured Python interpreter. Run each lifecycle request alone with `--marker workflow-modes-v1` last. Verify model-visible `WORKFLOW_*` confirmation; a successful CLI process alone does not prove a state update.

- On fresh entry, save the bundle and attempt `activate plan --record <root>`. On adoption/compaction, read the full bundle and applicable references; on later prompts use `sync_status` to focus rereads. Use `sync` and `rules-sync` when supported, without activating excluded skills.
- Save affected record files consistently. Optional `write-open --record <root> --previous-revision <revision>` and `write-close --record <root>` track these edits; declare new Markdown paths with `--path` when using them. An absent or failed transaction acknowledgment does not prevent direct record maintenance.
- Actions are optional tracking metadata, not mutation permissions. Record an authorized action's scope and actual result in the bundle whether or not `action-open`/`action-close` is used. Inspect actual effects of shell, Git, wrappers, and external tools; tool classification alone does not establish source impact or authority.
- Reconcile every material turn delta before the final response or handoff, and attempt `checkpoint --record <root>` when supported. Use `--no-change` only after checking that the bundle remains complete and accurate. Progress commentary needs no checkpoint.

From discuss, save the source handoff and initialize a separate plan bundle. When supported, use `transition plan`, `plan-init --record <discussion-root> --target <plan-root>`, then `activate plan --record <plan-root>`. These commands track the handoff, not permission to write the plan. `plan-cancel` preserves partial files; never delete partial work automatically. On an execution request, save the approved scope and execute handoff in this exact bundle, then attempt `transition execute --record <root>`. Approval alone does not request execution. A failed acknowledgment does not invalidate a saved handoff authorized by the user.

`WORKFLOW_CONTROL_NOT_APPLIED` means the requested lifecycle update was not acknowledged. Correct it when possible without fabricating success or repeatedly asking for already granted authority. Maintain the complete bundle directly if integration is unavailable. A bookkeeping control failure adds no tool or reporting gate; the independent post-compact read gate remains until actual context delivery is verified.

For persistence trouble, optionally record `suspend --record <root> --reason persistence-failed`, repair the exact bundle from known facts, reconcile metadata, and attempt `recover`. For an actual user stop, `--reason user-stop` preserves that instruction: resume task work only when the user resumes it. Both states produce reminders, not tool denials; repeated Stop events do not auto-suspend. Follow Required Record Completeness for unsaved facts.

Check installed `--help` before relying on new commands. An older installed hook may still deny calls; do not bypass an actual denial, alter trust, or reinstall during an active task. Use supported recovery and report the exact compatibility limitation if necessary. An absent optional hook does not block in-scope work or direct tracker/plan maintenance.
