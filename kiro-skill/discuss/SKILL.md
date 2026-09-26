---
name: kiro-discuss
description: Use when the user invokes $discuss or requests discussion work with a persistent version 4 Markdown record bundle. Start a new dated, daily-sequenced bundle by default, even when an older bundle is supplied; reuse an older bundle only when the user explicitly asks to continue it. Keep discuss active across scoped actions and exit only through $plan or $execute. Kiro / Kiro Crew port of the Codex `discuss` skill.
---

# Discuss (Kiro / Kiro Crew)

This is the Kiro-native port of the Codex `discuss` skill. It keeps the same persistent
Markdown record-bundle contract, but routes every user-facing question through the
interactive selection mechanism of the active Kiro surface — `ask_question` on a Kiro Crew
dashboard session, the runtime's own `AskUserQuestion` card in Kiro IDE and Kiro CLI, and a
trailing `[OPTIONS: ...]` line where neither exists — and treats Kiro's own memory/ledger
tools as supplementary recovery aids rather than replacements for the bundle.

## Core Contract

Operate as a discussion partner and keep one Markdown record bundle for the active discuss-mode lifetime. On a new invocation, always create a new bundle unless the user explicitly asks to continue, resume, or update a specific existing bundle. Merely supplying, linking, or mentioning an existing bundle does not authorize adopting or modifying it; treat it as read-only context for the new bundle when relevant. Once the bundle is selected, keep using it on later turns and during compaction recovery until the mode exits.

By default, the only allowed mutations are creating or transactionally updating the active bundle, creating missing parent directories, and maintaining its repository `.gitignore` entry.

Keep the mode active across analysis and every scoped action. Completing an action, including an authorized source-code change, automatically returns control to `discuss`; it never exits the mode. Only an explicit transition to `$plan` or `$execute` may durably set the tracker to `Mode status: Exited`, and only after the applicable handoff state is persisted. If the user asks to "exit discuss", "turn off discuss", "start coding", or uses similar wording without choosing `$plan` or `$execute`, keep discuss active and apply `Settled Discussion Transition Gate` so the user chooses one of those workflows.

## Skill-Managed Lifecycle

Apply this skill directly through conversation state and its Markdown record. Do not invent or rely on an external control script or hook system for the mode lifecycle — the bundle files ARE the state machine. Continue to respect independently enforced runtime restrictions (safety guardrails, git-push protections, destructive-command denials); this instruction does not authorize bypassing them.

- On a new invocation, read the initialization guidance first and create and verify a new bundle. Adopt an existing bundle only when the same request explicitly says to continue, resume, or update that bundle; a path or attachment alone is not continuation intent. On later turns within the active mode and after compaction, read this complete entrypoint, every currently required reference, `index.md`, and every manifest file before substantive work as required by the recovery rules.
- Treat compaction recovery as a hard gate, not as optional rereading. Before the first substantive tool call after compaction (or after a `REINJECTED AFTER COMPACTION` / `SESSION RESUMED` marker), recover the active mode, canonical bundle root, and tracker ID from durable state; read and validate the bundle; reconcile any completed but unrecorded work; and verify the Active Snapshot, Resume Checkpoint, and next safe action. If the exact active bundle cannot be resolved, do not guess from the newest directory: ask for its path and stop substantive work.
- When this session has a `session_ledger_read`/`session_ledger_record` pair available (Kiro Crew sessions), treat the bundle's `index.md` as authoritative and use the session ledger only as a secondary breadcrumb (`goal`, `next`, and an `artifacts.bundle_root` pointer) so a mid-turn interruption can point back at the exact bundle path even before the bundle itself is reread. Never let the ledger's cached text substitute for rereading the bundle.
- On later turns, reuse current context only while it remains reliable. Reread the Active Snapshot for snapshot-only changes; reread the complete bundle when record content changes outside known writes or its state is uncertain.
- Treat a record write transaction as one coordinated file update: read the affected current files, declare new Markdown files in the manifest, update all affected content and cross-links, then verify identity, metadata, phase links, dependencies, and evidence agree. Finish or repair that update before unrelated mutation, handoff, or a final response. If persistence fails, report the blocker instead of treating unsaved state as durable.
- Before every user-facing response, persist material turn deltas and the resume checkpoint. A genuinely unchanged turn requires only verifying that the saved state remains accurate.
- Keep the exact canonical bundle root and tracker ID in the durable resume instruction and checkpoint so compaction can preserve the recovery key. A compacted conversation summary is context only; the validated bundle is authoritative workflow state.

Before an authorized mutation, persist its scope, confirmation when required, local targets, and external or Git effects. Perform only that bounded action, then persist its completed, failed, or blocked result before responding and resume discuss. If the record becomes unreadable, restore its readability before further mutation. Hand off only after the applicable transition gate and exit metadata are durable.

New discussion bundles use the `Lightweight` profile. Profiles change persistence and reread cadence, never authorization or mutation enforcement. Only workflow-record version 4 bundles are accepted.

## Scripted Bundle Updates

Prefer a short Python standard-library script (run via the `shell` tool) when one record update must coordinate several Markdown files, such as the index, decisions, phase files, and evidence. Use the `write` tool's `strReplace`/`insert` for a small local edit when it is clearer; a script is a preferred method for coordinated persistence, not a requirement for unrelated file edits. Keep the existing authorization, decision, and handoff gates unchanged.

- Use a literal script input (a heredoc passed to `shell`, or a script file written first with `write`) so Markdown backticks, dollar signs, and newlines are not evaluated by the shell. Use explicit UTF-8 encoding and preserve existing newline style and file permissions.
- Resolve the bound bundle root, use an explicit path allowlist from its manifest plus declared additions, and reject escaping paths or symlink targets. Do not discover mutation targets through a broad recursive glob.
- Read the affected files into a before-snapshot and construct all proposed contents in memory before writing. For replacements, check the expected occurrence count or unique section markers and raise an explicit error on missing or ambiguous matches; never rely on an unchecked `.replace()` or an unguarded assertion for write-safety checks. Preserve unrelated content and skip unchanged files.
- Validate the proposed bundle before the first write: identity, manifest, metadata, links, question mappings, and phase/dependency/evidence consistency where applicable. Keep one writer for the bundle and recheck that source files still match the snapshot before replacement; if they changed, reread and reconcile instead of overwriting.
- For whole-file rewrites, stage complete contents in temporary sibling files (under `$KIROCREW_SCRATCH` when available, never `/tmp`) and replace each destination with an atomic rename, writing `index.md` last. Temporary staging files are not record artifacts; clean up only those created by this operation. Per-file replacement does not make a multi-file bundle atomic. On interruption or failure, inspect which replacements succeeded and repair the coordinated update before continuing; never blindly restore over another writer's changes.
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
- Ask exactly one decision question with 2-4 options total through the surface's interactive mechanism under `Interactive Question Routing`, then stop substantive work until the answer arrives: end the turn in the same step on a non-blocking card, or wait on the blocking card's return without ending the turn. Count `Other — specify` toward the 2-4 total.
- After the user answers, record the decision, resume from the checkpoint, and apply this gate again at the next material decision.
- Do not treat a factual unknown that can be resolved through safe, proportionate read-only inspection as a decision gate. If that inspection exposes a material user-owned decision, stop immediately after the current atomic operation.
- If one result exposes several material decisions, ask only the one that blocks the earliest next action; prioritize safety or irreversibility when tied. Record later decisions as deferred without asking them yet.
- Keep inspection batches narrow enough that they do not knowingly cross a foreseeable decision gate.

This gate applies only while full `discuss` mode is active. A `$plan` discuss fallback inherits `Question Style`, but not this gate, unless that skill explicitly opts into it.

## Question Style

Every question that requires a user response must include concrete options. Do not ask a bare open-ended question, including when requesting clarification, confirmation, approval, or permission to exit this mode. Never ask a storage-choice question for the tracker.

### Interactive Question Routing

Never hand the user a decision as prose they have to answer by typing. Every Kiro surface has an interactive selection mechanism; choose the route by surface, not by preference:

- **Kiro Crew dashboard session:** call `ask_question` with exactly one question and 2-4 options, marking the recommended one in its `description`, then **end the turn in the same step**. The tool is non-blocking: it returns as soon as the card is requested, and the selection arrives as the user's next message, never as the tool's result. Do not also print the question or its option list as chat text — the card is the question.
- **Kiro IDE or Kiro CLI (`kiro-cli` runtime):** raise the runtime's own `AskUserQuestion` card with the same one-question, 2-4-option shape. That card is blocking: it is raised while the turn is still running, and the selection is steered back into the waiting turn, so continue in the same turn when it returns instead of ending the turn first. If the turn has already ended by the time the user answers, treat the answer as an ordinary next message and resume from the checkpoint.
- **A Kiro surface offering neither tool:** put the choices in one trailing `[OPTIONS: A | B | C]` line as the very last line of the message, with nothing after it. Write each label in the user's voice and self-contained, because the label is sent verbatim as the user's next message.
- **Plain numbered prose is a last resort, not a style choice.** Use it only when an interactive call is denied, errors as unavailable, or the surface renders no options at all. State that the interactive question was unavailable, then apply the recorded format below to the chat message as well.

On a card surface the user supplies a free-form answer through the card's own custom-answer field, so `Other — specify` needs no separately typed instruction; it still counts toward the 2-4 options and is still saved as a numbered option. Use `multiSelect` only when the options can genuinely be combined — a material decision gate stays single-select.

### Recorded Question Format

The Markdown record must stay self-describing for a future session that has no card history, so every question saved under `decisions.md`'s `Open Questions` and `Decisions` carries its own numbered option list, whichever surface presented it. These rules govern the saved record always, and a chat message only in the last-resort case above:

- For a material decision gate, present only the first unresolved issue as a single question block. Do not batch multiple decision questions; defer later issues to subsequent turns.
- Provide 2-4 total practical, mutually distinguishable options that answer that question, counting `Other — specify` toward the total.
- In the saved record, and in a last-resort chat message, put each option on its own line with an explicit consecutive number: `1.`, `2.`, `3.`, `4.` as needed. Start at `1.`, leave a blank line between the question and its list, and never substitute bullets (`-`, `*`, `•`), checkboxes, letters, inline choices, or repeated `1.` markers. This is a required record format, not merely an example style.
- Keep only one user-facing question awaiting an answer at a time so a short reply is unambiguous. A record may retain multiple open questions, each with its own numbered options and stable question ID; present only the next question to the user.
- Accept a selection in whatever form it arrives: a card answer, a clicked `[OPTIONS:]` label sent verbatim, a bare number such as `1`, or a number plus detail such as `4. đánh giá lại phương án fix`. Apply any supplied qualification; do not require the user to repeat the option label. A bare selection of `Other` or an option needing a value does not supply the missing detail: ask a focused follow-up question through the same interactive route. If the answer is out of range or its question is ambiguous, clarify with a new interactive question instead of guessing.
- Preserve the pending question's number-to-option mapping in the record so resumed sessions interpret short replies consistently. If choices must change, present the revised question before accepting a selection against it.
- When a card or an `[OPTIONS:]` line presented the question, still record that question, its options, and the user's selection into `decisions.md`'s `Open Questions`/`Decisions` using the numbered mapping, so the durable record does not depend on the surface's card history.
- Mark one option as `Recommended` or `Default` when there is a reasonable choice.
- Include `Other — specify` when the listed choices may not cover the user's intent.
- When the user must supply a free-form value unrelated to tracker storage, such as a URL or external resource name, offer useful defaults or actions first and include an option to provide a different value. Never invent the free-form value.
- If a question is non-blocking and outside a material decision gate, state which default the agent will use if the user does not answer. Never apply a default to a material decision gate; wait for the user's answer.
- Apply these rules to every question put to the user and to every item recorded under `Open Questions` in the tracker.
- Before sending a response or saving open questions, check that the question was routed through the surface's interactive mechanism, that every recorded question has its own consecutively numbered option list, and that only one question is pending. Rewrite any bulleted choices before sending.

Recorded and last-resort format (wording and language may adapt to the user):

```text
Bạn muốn đi hướng nào?

1. Minimal fix: chỉ sửa đúng lỗi hiện tại. Recommended.
2. Broader cleanup: sửa lỗi và dọn phần liên quan.
3. Planning only: mình viết kế hoạch trước, chưa sửa gì.
4. Khác: bạn mô tả hướng bạn muốn.
```

The user can reply `1` or `4. đánh giá lại phương án fix`. The same choices written with `-` bullets do not satisfy this contract, and neither does presenting this block in chat while `ask_question` or `AskUserQuestion` was available, nor an interactive call with more than 4 options or more than one question pending at once during a decision gate.

## Response Pattern

Before handling an actionable request, read and follow [references/response-workflow.md](references/response-workflow.md). Apply `Immediate Decision Gate` throughout that workflow; keep `Question Style` mandatory for every question.
