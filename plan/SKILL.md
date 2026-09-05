---
name: plan
description: Plan-first collaboration with one version 4 Markdown record bundle under ./plans/. Inspect the problem, preserve decisions and verification, obtain approval, and hand the same bundle to execute only when execution is requested.
---

# Plan

## Boundaries and Lifecycle

Plan the requested work without implementing it. Read repository instructions and inspect relevant context, but do not edit production code, commit, push, deploy, or mutate external systems. Plan housekeeping is allowed.

Keep the same bundle through draft, approval, revisions, and execution handoff. Approval accepts a plan; it does not itself request implementation or change the active mode. A clear instruction such as “approve and implement” supplies both decisions and may trigger handoff after the approved bundle is saved.

Honor an explicit exit, pause, or cancellation without requiring execute. Persist current decisions and unfinished work, set `Plan mode: Paused` or `Exited`, close transactions, checkpoint, and deactivate. Do not mark unfinished planning complete or ask for confirmation of a clear stop. A review of this skill or a supplied plan is not by itself an instruction to activate a persistent mode.

## Reference Routing

Read the relevant reference completely:

- [references/plan-record.md](references/plan-record.md): creating, updating, approving, exiting, or handing off a bundle. Always required while planning.
- [references/phase-planning.md](references/phase-planning.md): only when phases, dependencies, waves, or delegation materially improve the plan.

Keep Required references minimal and acknowledge changes before the next substantive step. For an ambiguous request, clarify within this same draft bundle; do not activate discuss or create a second tracker. Direct discuss-to-execute handoffs remain valid and do not require a plan bundle.

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

## Workflow Modes Hook

Use the installed, trusted plugin's exact control script with the configured Python interpreter. Run one lifecycle command per call, ending with `--marker workflow-modes-v1`, and verify `WORKFLOW_*` context.

- Fresh entry: initialize the bundle, `activate plan --record <root>`, read/sync the complete bundle, then `rules-sync --record <root> --reference <relative-reference>...`.
- From discuss: require its successful `transition plan`, then `plan-init --record <discussion-root> --target <plan-root>`. Initialize only the declared target using file patches, then `activate plan --record <plan-root>`. If the user cancels during bootstrap, `plan-cancel --record <discussion-root>` preserves partial target files; reconcile the source and deactivate. Never delete partial work automatically.
- Activation and compaction require a complete manifest read and record sync. After a prompt, `current` needs no reread, `snapshot` needs only the Active Snapshot and snapshot sync, and `record` needs the full bundle.
- Before edits, `write-open --record <root> --previous-revision <acknowledged revision>` and declare new Markdown paths with `--path`; update affected files and `write-close --record <root>`. Valid no-op writes may close. Read newly required references and run rules-sync after changing that set.
- Before a final response, `checkpoint --record <root>`; use `--no-change` only when nothing material changed. Progress commentary does not require a checkpoint or interrupt an open work unit.
- On execution request, checkpoint planning deltas before replacing Required references with the execute minimum, close the handoff write, then `transition execute --record <root>`. The destination acknowledges its own rules. Approval alone must never invoke this transition.

If record persistence fails, `suspend --record <root> --reason persistence-failed` allows a blocker response while keeping all non-record mutations denied. Use `--reason user-stop` when a requested stop cannot be reconciled immediately. Repair the bundle through a write transaction, cancel an abandoned bootstrap if necessary, sync record/rules, then `recover --record <root>` before resuming or deactivating. A repeated unresolved Stop block suspends instead of looping.

Check local `--help` for these commands before depending on them. Report incompatible installed hooks without bypassing denials or reinstalling mid-task. Planning may continue without an installed hook because its mutations are limited to housekeeping; disclose the missing enforcement. The hook recognizes supported schemas and treats opaque execution conservatively; it is not proof that arbitrary tools or shell programs are read-only. Do not run opaque baseline checks in plan merely to evade that boundary.
