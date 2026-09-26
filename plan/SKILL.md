---
name: plan
description: Plan-first collaboration workflow for Codex. Creates one dated, daily-sequenced version 4 Markdown plan bundle under ./plans/, keeps it active through approval and execute handoff, and stores every declared phase in its own self-contained, stable-ID Markdown file under phases/. Use for reviewed implementation planning and durable cross-session handoff.
---

# Plan

## Skill-Managed Lifecycle

Apply this skill directly through conversation state and its Markdown record. Continue to respect independently enforced runtime restrictions; this instruction does not authorize bypassing them.

- On entry, resume, and after compaction, read this complete entrypoint, every currently required reference, `index.md`, and every manifest file before substantive work. For a new bundle, read the initialization guidance first, create the bundle, then verify its complete contents.
- Treat compaction recovery as a hard gate, not as optional rereading. Before the first substantive tool call after compaction, recover the active mode, canonical bundle root, and tracker ID from durable state; read and validate the bundle; reconcile pending questions, lifecycle transitions, and any completed but unrecorded work; and verify the Active Snapshot, Resume Checkpoint, plan status, and next safe action. If the exact active bundle cannot be resolved, do not guess from the newest directory: ask for its path through `request_user_input` under `Question and Open-Issue Contract` and stop substantive work.
- On later turns, reuse current context only while it remains reliable. Reread the Active Snapshot for snapshot-only changes; reread the complete bundle when record content changes outside known writes or its state is uncertain.
- Treat a record write transaction as one coordinated file update: read the affected current files, declare new Markdown files in the manifest, update all affected content and cross-links, then verify identity, metadata, phase links, dependencies, and evidence agree. Finish or repair that update before unrelated mutation, handoff, or a final response. If persistence fails, report the blocker instead of treating unsaved state as durable.
- Before every user-facing response, persist material turn deltas and the resume checkpoint. A genuinely unchanged turn requires only verifying that the saved state remains accurate.
- Keep the exact canonical bundle root and tracker ID in the durable resume instruction and checkpoint so compaction can preserve the recovery key. A compacted conversation summary is context only; the validated bundle is authoritative workflow state.

On fresh entry, reserve and initialize the draft bundle before substantive inspection. Keep that exact bundle through approval and execute handoff. On entry from `$discuss`, require its persisted handoff and create a separate plan bundle under the saving rules. Hand off to `$execute` only after approval and execute-ready metadata are durable; upgrade the profile to `Durable` unless already `Audited`. Approval alone does not authorize implementation.

New plans use a version 4 bundle and the `Lightweight` profile. Profiles affect reread and persistence cadence only. Single-file and pre-v4 records are unsupported.

Use this skill to turn an ambiguous or important request into an approved execution plan while keeping one durable Markdown bundle from the beginning of planning.

## Scripted Bundle Updates

Prefer a short Python standard-library script when one record update must coordinate several Markdown files, such as the index, decisions, phase files, and evidence. Use `apply_patch` for a small local edit when it is clearer; Python is a preferred method for coordinated persistence, not a requirement for unrelated file edits. Keep the existing authorization, decision, and handoff gates unchanged.

- Use a literal script input (for example, a quoted heredoc in a compatible shell) so Markdown backticks, dollar signs, and newlines are not evaluated by the shell. Use explicit UTF-8 encoding and preserve existing newline style and file permissions.
- Resolve the bound bundle root, use an explicit path allowlist from its manifest plus declared additions, and reject escaping paths or symlink targets. Do not discover mutation targets through a broad recursive glob.
- Read the affected files into a before-snapshot and construct all proposed contents in memory before writing. For replacements, check the expected occurrence count or unique section markers and raise an explicit error on missing or ambiguous matches; never rely on an unchecked `.replace()` or Python `assert` for write-safety checks. Preserve unrelated content and skip unchanged files.
- Validate the proposed bundle before the first write: identity, manifest, metadata, links, question mappings, and phase/dependency/evidence consistency where applicable. Keep one writer for the bundle and recheck that source files still match the snapshot before replacement; if they changed, reread and reconcile instead of overwriting.
- For whole-file rewrites, stage complete contents in temporary sibling files and replace each destination with `os.replace`, writing `index.md` last. Temporary staging files are not record artifacts; clean up only those created by this operation. Per-file replacement does not make a multi-file bundle atomic. On interruption or failure, inspect which replacements succeeded and repair the coordinated update before continuing; never blindly restore over another writer's changes.
- Read back the saved files, compare them with the intended contents, and revalidate the complete bundle and scoped diff. Report validation failures accurately; successful script exit alone does not prove that the update is consistent.

## Reference Routing

Remove a conditional reference from `Required references` only after its stage and any dependent work have ended; persist and verify the set change under the record persistence contract. After compaction, reread every reference still required.

Load only the reference needed for the current stage, and read it completely before applying it.

- Read [references/plan-record.md](references/plan-record.md) before creating, updating, approving, or handing off the Markdown plan.
- Read [references/phase-planning.md](references/phase-planning.md) only when phases, dependencies, waves, or subagent eligibility materially improve the plan.
- Read [references/planning-workflow.md](references/planning-workflow.md) before creating or revising a plan, baseline analysis, or requesting approval.
- Keep `Required references` minimal: always `references/plan-record.md`; add `references/planning-workflow.md` while creating or revising a plan, analyzing its baseline, or obtaining approval; add `references/phase-planning.md` while phases, dependencies, waves, or subagent eligibility are in use. Persist and verify each set change and read the new reference before continuing.

## Plan-First Boundary

Follow the `$plan` workflow directly without attempting to switch or discuss the runtime's collaboration mode.

- Do not make production code edits, run destructive commands, commit, push, deploy, or implement the planned work while using this skill.
- After saving the approved plan, begin implementation only when the user explicitly requests execution; hand the saved plan to `$execute` for that work.
- Read and respect repository instructions, user rules, AGENTS.md, active developer instructions, and higher-priority safety constraints.

## Relationship to Direct Discuss Handoffs

`$plan` remains the full plan-first workflow when the user wants a separate reviewed handoff. It is not mandatory between `$discuss` and `$execute`: an execution-ready discussion bundle may be adopted directly. Do not create a duplicate plan bundle for that route.

## Discuss Fallback

Follow the conversational restrictions and question style of `$discuss` before planning when the current session has no reliable clue about what the user wants, or when the agent is confused about the right direction. Do not activate a separate discuss tracker lifecycle during this fallback; the already-created `$plan` draft remains the only Markdown planning artifact.

Use this fallback when:

- The user's goal is too vague to form an actionable plan.
- The workspace or task context is missing and cannot be inferred safely.
- Multiple materially different approaches are possible and choosing one would be guesswork.
- The agent feels uncertain, stuck, or confused about the user's intent.
- More conversation is needed before writing a useful "How to do it" handoff plan.

While in this fallback, keep using the already established draft plan as the planning record:

- Do not edit source files, create unrelated artifacts, implement changes, or mutate external state. Draft-plan housekeeping and persistence remain required.
- Ask concise clarifying questions and follow the mandatory `Question and Open-Issue Contract` below.
- Help the user choose the target outcome, constraints, and preferred approach.
- Summarize the agreed direction before returning to the `$plan` workflow.

## Conversation Workflow

Before creating or revising a plan, establishing its baseline, or requesting approval, read and follow [references/planning-workflow.md](references/planning-workflow.md). Keep the `Plan-First Boundary` and `Question and Open-Issue Contract` in force.

## Question and Open-Issue Contract

Use `request_user_input` for every user-facing clarification, preference, workflow choice, and free-form value when the tool is available and its runtime contract permits that question. Apply this contract to every reference and the discuss fallback. Do not substitute a prose question for an eligible tool question. Higher-priority tool restrictions take precedence: when the runtime excludes permission or approval requests, use its permitted approval mechanism or a concise final-response question for those requests, never `request_user_input`. Never ask a storage-choice question for the plan bundle.

- Present each distinct issue as a separate question entry in `request_user_input`. Do not combine unrelated decisions under one option list.
- Follow the tool schema exactly: provide 1-3 questions per call only when they can be answered independently, give each question 2-3 practical and mutually exclusive options, put the recommended option first, and suffix its label with `(Recommended)`. Prefer one question per call when a prior answer may change later choices.
- Do not add an `Other` option when the client supplies it automatically. Keep headers, prompts, labels, and descriptions concise; descriptions should explain the impact or tradeoff of choosing an option.
- Keep only one dependent user-facing question awaiting an answer at a time. A record may retain multiple open questions, each with its own stable question ID; send only the next dependent question through the tool.
- If the user selects the client-provided free-form `Other` path without enough detail, ask a focused follow-up through `request_user_input`; never fall back to a prose question.
- Preserve the displayed option order and returned selection in the record. If choices must change, send the revised question through `request_user_input` before accepting a selection against it.
- Do not duplicate the tool's questions or options in commentary or the final response.
- When there is a reasonable choice, make it the first tool option and mark it `(Recommended)`; record the same recommendation or default in Markdown.
- When the listed choices may not cover the user's intent, rely on the client's automatically supplied free-form alternative and record that path as `Other — specify` only in Markdown.
- When the user must supply a free-form value unrelated to plan-file storage, such as a URL or external resource name, offer useful defaults or actions through `request_user_input`; rely on its client-provided free-form path for a different value. Never invent the value.
- Prefer concrete selectable options so the user can answer without typing; use the client-provided free-form path only when the user wants a different choice or must supply an unknown value.
- If the question tool returns without an answer, times out, or reports dismissal, stop substantive work for the turn. Persist the unanswered question, displayed options, and exact resume checkpoint, then send a brief awaiting-answer status without repeating the question. Do not apply a recommendation or default, resend the question in that turn, treat silence as approval, or begin dependent work. Keep the workflow active and retain its existing lifecycle status; resume only after the user answers or explicitly changes the request. The same stop rule applies to unanswered permission or approval requests sent through a runtime-permitted route.
- Timeout duration and cancellation belong to the runtime. Do not invent a timeout parameter for `request_user_input`, claim a configurable waiting period, or start background work while waiting.
- In saved Markdown, keep each option on its own line with an explicit consecutive number so the durable mapping remains unambiguous. This numbered format is for the record only, not a substitute for invoking `request_user_input`.
- Apply these rules to every user-facing question and every item in the proposed or saved plan's `Open Questions` section.
- For each open question in a plan, record its options, recommendation/default when applicable, and whether it blocks execution.
- Before invoking the tool or saving a plan, check that dependent questions are sequenced correctly and that each saved option order matches its tool call.
- If `request_user_input` is unavailable for an otherwise eligible question, do not ask through another channel. State that the required question tool is unavailable, persist the blocked question and checkpoint, and stop until the workflow can resume in an environment that provides it.

When the runtime permits plan approval through `request_user_input`, the approval tool call should use a short header such as `Plan decision`, ask how to proceed, and offer concise labels such as `Approve plan (Recommended)`, `Request revisions`, and `Rework approach`; the client supplies the free-form alternative. Approval finalizes the plan only and does not request execution.
