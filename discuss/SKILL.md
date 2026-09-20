---
name: discuss
description: Use when the user invokes $discuss or requests discussion work with a persistent version 4 Markdown record bundle. Start a new dated, daily-sequenced bundle by default, even when an older bundle is supplied; reuse an older bundle only when the user explicitly asks to continue it. Keep discuss active across scoped actions and exit only through $plan or $execute.
---

# Discuss

## Core Contract

Operate as a discussion partner and keep one Markdown record bundle for the active discuss-mode lifetime. On a new invocation, always create a new bundle unless the user explicitly asks to continue, resume, or update a specific existing bundle. Merely supplying, linking, or mentioning an existing bundle does not authorize adopting or modifying it; treat it as read-only context for the new bundle when relevant. Once the bundle is selected, keep using it on later turns and during compaction recovery until the mode exits.

By default, the only allowed mutations are creating or transactionally updating the active bundle, creating missing parent directories, and maintaining its repository `.gitignore` entry.

Keep the mode active across analysis and every scoped action. Completing an action, including an authorized source-code change, automatically returns control to `discuss`; it never exits the mode. Only an explicit transition to `$plan` or `$execute` may durably set the tracker to `Mode status: Exited`, and only after the applicable handoff state is persisted. If the user asks to "exit discuss", "turn off discuss", "start coding", or uses similar wording without choosing `$plan` or `$execute`, keep discuss active and apply `Settled Discussion Transition Gate` so the user chooses one of those workflows.

## Skill-Managed Lifecycle

Apply this skill directly through conversation state and its Markdown record. Continue to respect independently enforced runtime restrictions; this instruction does not authorize bypassing them.

- On a new invocation, read the initialization guidance first and create and verify a new bundle. Adopt an existing bundle only when the same request explicitly says to continue, resume, or update that bundle; a path or attachment alone is not continuation intent. On later turns within the active mode and after compaction, read this complete entrypoint, every currently required reference, `index.md`, and every manifest file before substantive work as required by the recovery rules.
- Treat compaction recovery as a hard gate, not as optional rereading. Before the first substantive tool call after compaction, recover the active mode, canonical bundle root, and tracker ID from durable state; read and validate the bundle; reconcile any completed but unrecorded work; and verify the Active Snapshot, Resume Checkpoint, and next safe action. If the exact active bundle cannot be resolved, do not guess from the newest directory: ask for its path and stop substantive work.
- On later turns, reuse current context only while it remains reliable. Reread the Active Snapshot for snapshot-only changes; reread the complete bundle when record content changes outside known writes or its state is uncertain.
- Treat a record write transaction as one coordinated file update: read the affected current files, declare new Markdown files in the manifest, update all affected content and cross-links, then verify identity, metadata, phase links, dependencies, and evidence agree. Finish or repair that update before unrelated mutation, handoff, or a final response. If persistence fails, report the blocker instead of treating unsaved state as durable.
- Before every user-facing response, persist material turn deltas and the resume checkpoint. A genuinely unchanged turn requires only verifying that the saved state remains accurate.
- Keep the exact canonical bundle root and tracker ID in the durable resume instruction and checkpoint so compaction can preserve the recovery key. A compacted conversation summary is context only; the validated bundle is authoritative workflow state.

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
- Ask exactly one decision question through `request_user_input`, then end the response and wait for the user's answer.
- After the user answers, record the decision, resume from the checkpoint, and apply this gate again at the next material decision.
- Do not treat a factual unknown that can be resolved through safe, proportionate read-only inspection as a decision gate. If that inspection exposes a material user-owned decision, stop immediately after the current atomic operation.
- If one result exposes several material decisions, ask only the one that blocks the earliest next action; prioritize safety or irreversibility when tied. Record later decisions as deferred without asking them yet.
- Keep inspection batches narrow enough that they do not knowingly cross a foreseeable decision gate.

This gate applies only while full `discuss` mode is active. A `$plan` discuss fallback inherits `Question Style`, but not this gate, unless that skill explicitly opts into it.

## Question Style

Every question that requires a user response must use `request_user_input`. This is mandatory in every collaboration mode where the tool is available, including Default and Plan modes. Do not ask a user-facing question in prose, commentary, or the final response, including when requesting clarification, confirmation, approval, a free-form value, or permission to exit this mode. Never ask a storage-choice question for the tracker.

- For a material decision gate, send only the first unresolved issue in one `request_user_input` call. Do not batch multiple decision questions; defer later issues to subsequent turns.
- Follow the tool schema exactly: provide one question with 2-3 practical, mutually exclusive options, put the recommended option first, and suffix its label with `(Recommended)`. Do not add an `Other` option when the client supplies it automatically.
- Keep the header, prompt, labels, and descriptions concise. Options must answer the question directly; descriptions should explain the impact or tradeoff of choosing them.
- Keep only one user-facing question awaiting an answer at a time. A record may retain multiple open questions, each with its own stable question ID; send only the next question through the tool.
- If the user selects the client-provided free-form `Other` path without enough detail, ask one focused follow-up through `request_user_input`; never fall back to a prose question.
- Preserve the displayed option order and returned selection in the record. If choices must change, send the revised question through `request_user_input` before accepting a selection against it.
- Do not duplicate the tool's question or options in commentary or the final response.
- When there is a reasonable choice, make it the first tool option and mark it `(Recommended)`; record the same recommendation in Markdown.
- When the listed choices may not cover the user's intent, rely on the client's automatically supplied free-form alternative and record that path as `Other — specify` only in Markdown.
- When the user must supply a free-form value unrelated to tracker storage, such as a URL or external resource name, offer useful defaults or actions through `request_user_input`; rely on its client-provided free-form path for a different value. Never invent the value.
- If a question is non-blocking and outside a material decision gate, state which default the agent will use if the user does not answer. Never apply a default to a material decision gate; wait for the user's answer.
- In saved Markdown, keep each option on its own line with an explicit consecutive number so the durable mapping remains unambiguous. This numbered format is for the record only, not a substitute for invoking `request_user_input`.
- Apply these rules to every user-facing question and every item recorded under `Open Questions` in the tracker.
- Before invoking the tool or saving open questions, check that only one question is pending in the UI and that the saved option order matches the tool call.
- If `request_user_input` is unavailable, do not ask through another channel. State that the required question tool is unavailable, persist the blocked question and checkpoint, and stop until the workflow can resume in an environment that provides it.

The corresponding tool call should use a short header such as `Fix scope`, ask which scope to take, and offer concise labels such as `Minimal fix (Recommended)`, `Broader cleanup`, and `Planning only`; the client supplies the free-form alternative.

## Response Pattern

Before handling an actionable request, read and follow [references/response-workflow.md](references/response-workflow.md). Apply `Immediate Decision Gate` throughout that workflow; keep `Question Style` mandatory for every question.
