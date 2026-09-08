---
name: plan
description: Plan-first collaboration workflow for Codex. Creates one version 4 Markdown plan bundle under ./plans/, keeps it active through approval and execute handoff, and stores every declared phase in its own self-contained, stable-ID Markdown file under phases/. Use for reviewed implementation planning and durable cross-session handoff.
---

# Plan

## Skill-Managed Lifecycle

Apply this skill directly through conversation state and its Markdown record. Do not automatically activate `workflow-modes`, invoke its control script, or run its hooks or lifecycle commands, even when the plugin is installed. Plugin availability is not a prerequisite for this skill. Continue to respect independently enforced runtime restrictions; this instruction does not authorize bypassing them.

- On entry, resume, and after compaction, read this complete entrypoint, every currently required reference, `index.md`, and every manifest file before substantive work. For a new bundle, read the initialization guidance first, create the bundle, then verify its complete contents.
- On later turns, reuse current context only while it remains reliable. Reread the Active Snapshot for snapshot-only changes; reread the complete bundle when record content changes outside known writes or its state is uncertain.
- Treat a record write transaction as one coordinated file update: read the affected current files, declare new Markdown files in the manifest, update all affected content and cross-links, then verify identity, metadata, phase links, dependencies, and evidence agree. Finish or repair that update before unrelated mutation, handoff, or a final response. If persistence fails, report the blocker instead of treating unsaved state as durable.
- Before every user-facing response, persist material turn deltas and the resume checkpoint. A genuinely unchanged turn requires only verifying that the saved state remains accurate.

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

Every question that requires a user response must include concrete options. Do not ask a bare open-ended question, including when requesting clarification, confirmation, or approval. Never ask a storage-choice question for the plan bundle.

- Present each distinct issue as a separate question block. Do not combine unrelated decisions under one option list.
- Provide 2-4 total practical, mutually distinguishable options that answer that question, counting `Other — specify` toward the total.
- In chat and saved Markdown, put each option on its own line with an explicit consecutive number: `1.`, `2.`, `3.`, `4.` as needed. Start at `1.`, leave a blank line between the question and its list, and never substitute bullets (`-`, `*`, `•`), checkboxes, letters, inline choices, or repeated `1.` markers. This is a required response format, not merely an example style.
- Keep only one user-facing question awaiting an answer at a time so a bare number is unambiguous. A record may retain multiple open questions, each with its own numbered options and stable question ID; present only the next question in chat.
- Accept a bare number such as `1` as selection of that option in the pending question, or a number plus detail such as `4. đánh giá lại phương án fix`. Apply any supplied qualification; do not require the user to repeat the option label. A bare selection of `Other` or an option needing a value does not supply the missing detail: ask a focused numbered follow-up. If the number is out of range or its question is ambiguous, clarify with numbered options instead of guessing.
- Preserve the pending question's number-to-option mapping in the record so resumed sessions interpret short replies consistently. If choices must change, present the revised question before accepting a selection against it.
- Use this numbered chat format when the interaction channel is optional. If higher-priority instructions require a structured question tool, follow its schema and selection behavior; do not add unsupported fields or duplicate its question in chat. Preserve the displayed option order when recording the question.
- Mark one option as `Recommended` or `Default` when there is a reasonable choice.
- Include `Other — specify` when the listed choices may not cover the user's intent.
- When the user must supply a free-form value unrelated to plan-file storage, such as a URL or external resource name, offer useful defaults or actions first and include an option to provide a different value. Never invent the free-form value.
- If a question is non-blocking, state which default the agent will use if the user does not answer.
- Apply these rules to questions in chat and to every item in the proposed or saved plan's `Open Questions` section.
- For each open question in a plan, record its options, recommendation/default when applicable, and whether it blocks execution.
- Before sending a response or saving a plan, check that every user-facing question and open issue has its own consecutively numbered option list and that chat has only one pending question. Rewrite any bulleted choices before sending.

Required chat format (wording and language may adapt to the user):

```text
Ban muon xu ly ban ke hoach nay the nao?

1. Duyet ke hoach: chot ban hien tai, chua trien khai. Recommended.
2. Sua cuc bo: ban neu phan can dieu chinh.
3. Lap lai ke hoach: danh gia lai huong tiep can.
4. Khac: ban mo ta huong ban muon.
```

The user can reply `1` or `4. đánh giá lại phương án fix`. A selection of `1` in this example approves the plan only; it does not request execution. The same choices written with `-` bullets do not satisfy this contract.
