---
name: discuss
description: Use when the user invokes $discuss or requests discussion work with a persistent version 4 Markdown record bundle. Keep discuss active across scoped actions and exit only through $plan or $execute. Without a destination, create a dated topic directory under ./discussion/, maintain its manifest and repository ignore rule, and persist discussion state across focused Markdown files.
---

# Discuss

## Core Contract

Operate as a discussion partner and keep one Markdown record bundle for the conversation. By default, the only allowed mutations are creating or transactionally updating that bundle, creating missing parent directories, and maintaining its repository `.gitignore` entry.

Keep the mode active across analysis and every scoped action. Completing an action, including an authorized source-code change, automatically returns control to `discuss`; it never exits the mode. Only an explicit transition to `$plan` or `$execute` may durably set the tracker to `Mode status: Exited`, and only after the applicable handoff state is persisted. If the user asks to "exit discuss", "turn off discuss", "start coding", or uses similar wording without choosing `$plan` or `$execute`, keep discuss active and apply `Settled Discussion Transition Gate` so the user chooses one of those workflows.

## Skill-Managed Lifecycle

Apply this skill directly through conversation state and its Markdown record. Do not automatically activate `workflow-modes`, invoke its control script, or run its hooks or lifecycle commands, even when the plugin is installed. Plugin availability is not a prerequisite for this skill. Continue to respect independently enforced runtime restrictions; this instruction does not authorize bypassing them.

- On entry, resume, and after compaction, read this complete entrypoint, every currently required reference, `index.md`, and every manifest file before substantive work. For a new bundle, read the initialization guidance first, create the bundle, then verify its complete contents.
- On later turns, reuse current context only while it remains reliable. Reread the Active Snapshot for snapshot-only changes; reread the complete bundle when record content changes outside known writes or its state is uncertain.
- Treat a record write transaction as one coordinated file update: read the affected current files, declare new Markdown files in the manifest, update all affected content and cross-links, then verify identity, metadata, phase links, dependencies, and evidence agree. Finish or repair that update before unrelated mutation, handoff, or a final response. If persistence fails, report the blocker instead of treating unsaved state as durable.
- Before every user-facing response, persist material turn deltas and the resume checkpoint. A genuinely unchanged turn requires only verifying that the saved state remains accurate.

Before an authorized mutation, persist its scope, confirmation when required, local targets, and external or Git effects. Perform only that bounded action, then persist its completed, failed, or blocked result before responding and resume discuss. If the record becomes unreadable, restore its readability before further mutation. Hand off only after the applicable transition gate and exit metadata are durable.

New discussion bundles use the `Lightweight` profile. Profiles change persistence and reread cadence, never authorization or mutation enforcement. Only workflow-record version 4 bundles are accepted.

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

Load only the reference needed for the current stage, and read that reference completely before applying it.

- Read [references/tracker.md](references/tracker.md) before creating, resuming, migrating, persisting, or handing off a discussion tracker.
- Read [references/actions.md](references/actions.md) before baseline analysis of an existing mechanism, any scoped mutation, or combining discuss with another skill.
- Read [references/response-workflow.md](references/response-workflow.md) before an actionable request, including initialization, baseline analysis, scoped actions, or transition.
- Keep `Required references` minimal: always `references/tracker.md`; add `references/response-workflow.md` while an actionable request is active; add `references/actions.md` while baseline analysis, a scoped action, or a skill combination is active. Persist and verify each set change and read newly required references before the next mutation.
- The decision gate and question rules remain in this entrypoint and apply throughout the mode; the response sequence is in `references/response-workflow.md`.

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
- Provide 2-4 total practical, mutually distinguishable options that answer that question, counting `Other — specify` toward the total.
- In chat and saved Markdown, put each option on its own line with an explicit consecutive number: `1.`, `2.`, `3.`, `4.` as needed. Start at `1.`, leave a blank line between the question and its list, and never substitute bullets (`-`, `*`, `•`), checkboxes, letters, inline choices, or repeated `1.` markers. This is a required response format, not merely an example style.
- Keep only one user-facing question awaiting an answer at a time so a bare number is unambiguous. A record may retain multiple open questions, each with its own numbered options and stable question ID; present only the next question in chat.
- Accept a bare number such as `1` as selection of that option in the pending question, or a number plus detail such as `4. đánh giá lại phương án fix`. Apply any supplied qualification; do not require the user to repeat the option label. A bare selection of `Other` or an option needing a value does not supply the missing detail: ask a focused numbered follow-up. If the number is out of range or its question is ambiguous, clarify with numbered options instead of guessing.
- Preserve the pending question's number-to-option mapping in the record so resumed sessions interpret short replies consistently. If choices must change, present the revised question before accepting a selection against it.
- Use this numbered chat format when the interaction channel is optional. If higher-priority instructions require a structured question tool, follow its schema and selection behavior; do not add unsupported fields or duplicate its question in chat. Preserve the displayed option order when recording the question.
- Mark one option as `Recommended` or `Default` when there is a reasonable choice.
- Include `Other — specify` when the listed choices may not cover the user's intent.
- When the user must supply a free-form value unrelated to tracker storage, such as a URL or external resource name, offer useful defaults or actions first and include an option to provide a different value. Never invent the free-form value.
- If a question is non-blocking and outside a material decision gate, state which default the agent will use if the user does not answer. Never apply a default to a material decision gate; wait for the user's answer.
- Apply these rules to questions in chat and to every item recorded under `Open Questions` in the tracker.
- Before sending a response or saving open questions, check that every question has its own consecutively numbered option list and that chat has only one pending question. Rewrite any bulleted choices before sending.

Required chat format (wording and language may adapt to the user):

```text
Ban muon di huong nao?

1. Minimal fix: chi sua dung loi hien tai. Recommended.
2. Broader cleanup: sua loi va don phan lien quan.
3. Planning only: minh viet ke hoach truoc, chua sua gi.
4. Khac: ban mo ta huong ban muon.
```

The user can reply `1` or `4. đánh giá lại phương án fix`. The same choices written with `-` bullets do not satisfy this contract.

## Response Pattern

Before handling an actionable request, read and follow [references/response-workflow.md](references/response-workflow.md). Apply `Immediate Decision Gate` throughout that workflow; keep `Question Style` mandatory for every question.
