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
4. Develop an executable strategy, intended behavior, affected scope, verification, and recovery proportional to the change. Use a linear checklist for a small task; introduce phases only when useful. Record only decisions and evidence needed for handoff, not a transcript.
5. Ask for approval when the plan is decision-complete. Offer revision or pause when relevant. Existing unambiguous approval need not be requested again.
6. Save approval in the same bundle with `Plan mode: Active` and `Execute mode: Inactive`. Remain available for revisions. If a revision changes the approved outcome, invalidate the affected approval and obtain acceptance of that change.
7. Only on an explicit execution request, persist the execute handoff metadata and transition to `$execute` with this exact bundle. Do not implement under plan mode.

## Questions and Independent Work

Ask only for missing choices that materially change the plan. Never ask a storage-choice question when the default applies.

Ask one choice question at a time in a plain-text chat message, with the question on its own line followed by a blank line and 2-4 concrete options numbered consecutively as `1.`, `2.`, `3.`, `4.`. Never use letter labels or pad the list to reach four options. Use this format instead of a question tool unless higher-priority instructions require that tool. Put the recommended option first when justified and mark it with `Recommended — <brief reason>` in the user's language on the same line.

Accept a bare number such as `1`, a number with an explanation such as `2. user's reason`, or a free-form answer. Map the number to the current pending question and honor any accompanying reason or constraint; clarify only if the answer is ambiguous or contradictory. Keep the pending question and its number-to-option mapping in the record so a short reply remains interpretable after resuming. Do not repeat a clearly answered question merely to confirm the selection.

For example:

```text
Which rollout scope do you prefer?

1. New data first — Recommended: limits risk and makes verification easier.
2. All existing and new data.
3. A pilot group first.
```

For a required URL, identifier, credential location, or other factual value, ask directly rather than inventing options. Never invent missing values.

Record whether each question blocks execution and which work depends on it. Continue safe independent inspection while waiting; do not assume an answer to a blocking question. Optional preferences may use a stated reasonable default. Ask the earliest blocking question first and keep only one choice question pending. This does not limit batching independent read-only tool calls.

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
