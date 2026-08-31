---
name: workflow-discuss
description: Use when the user invokes /workflow-discuss or requests discussion work with a persistent version 4 Markdown record bundle. Keep discuss active across scoped actions and exit only through /workflow-plan or /workflow-execute. Without a destination, create a dated topic directory under ./discussion/, maintain its manifest and repository ignore rule, and persist discussion state across focused Markdown files.
---

# Discuss

## Core Contract

Operate as a discussion partner and keep one Markdown record bundle for the conversation. By default, the only allowed mutations are creating or transactionally updating that bundle, creating missing parent directories, and maintaining its repository `.gitignore` entry.

Keep the mode active across analysis and every scoped action. Completing an action, including an authorized source-code change, automatically returns control to `discuss`; it never exits the mode. Only an explicit transition to `/workflow-plan` or `/workflow-execute` may durably set the tracker to `Mode status: Exited`, and only after the applicable handoff state is persisted. If the user asks to "exit discuss", "turn off discuss", "start coding", or uses similar wording without choosing `/workflow-plan` or `/workflow-execute`, keep discuss active and apply `Settled Discussion Transition Gate` so the user chooses one of those workflows.

## Workflow Modes Hook

Kiro IDE 1.x and CLI 3.x load this distribution's standalone v1 command hooks from the active Kiro scope. Resolve `workflow_modes_control.py` from `<project>/.kiro/workflow-modes/scripts/` when the project-owned marker is present; otherwise resolve it from `${KIRO_HOME:-<user-home>/.kiro}/workflow-modes/scripts/`. Run it with the configured Python interpreter and exact absolute path. Every lifecycle call must end with `--marker workflow-modes-v1`; confirm successful calls yield model-visible `WORKFLOW_*` context.
- After the bundle is established and its active metadata is persisted, run `activate discuss --record <bundle-root>`.
- After activation, recovery-anchor reconciliation, or any Required references change, read this complete entrypoint and every named reference, sync the required bundle scope, then run `rules-sync --record <bundle-root> --reference <path>...`.
- At activation and after the next active `UserPromptSubmit` or `PreToolUse` recovery anchor, read `index.md` and every manifest file completely, then run record-scope sync.
- After `UserPromptSubmit`, follow the hook's `sync_status`: `current` requires no reread; `snapshot` requires reading only the delimited Active Snapshot and running `sync --record <tracker> --scope snapshot`; `record` requires a complete read and record-scope sync. A changed or unacknowledged required scope remains a hard boundary for non-record mutation.
- Before bundle edits, run `write-open --record <bundle-root> --previous-revision <acknowledged revision>` and declare new Markdown paths with `--path`. After all cross-file state is consistent, run `write-close --record <bundle-root>`. Repair a denied close; never bypass it.
- Before any authorized non-source-code mutation, persist the action and run `action-open --record <tracker> --impact non-source`, adding one `--path <absolute-path>` for each known local target. When the required mutation tool has no inspectable file target, also add the narrow matching `--unscoped <shell|external>` classification.
- Before an authorized source-code mutation, persist its confirmation and scope, then run `action-open --record <tracker> --impact source-confirmed --path <absolute-path>...`. File-targeted mutation outside those paths must remain blocked. For a repository-scoped Git mutation such as merge or rebase, include the repository root as `--path` and add `--unscoped git`; this authorizes only that tool class for the current bounded action.
- After persisting an action's terminal result, run `action-close --result <completed|failed|blocked>` before the user-facing response. A failed action still requires closure and returns to discuss.
- Before every user-facing response, run `checkpoint --record <tracker>` after all material turn deltas are durable. When the turn genuinely changes nothing in the tracker, run `checkpoint --record <tracker> --no-change`; never use `--no-change` to skip a required update.
- After the `/workflow-plan` durability gate, run `transition plan --record <tracker>` before invoking `/workflow-plan`.
- After a successful Direct Execute Handoff, run `transition execute --record <tracker>` before invoking `/workflow-execute`.

Kiro `Stop` is warning-only. The hook persists pending reconciliation for an uncheckpointed turn, and later prompt/tool boundaries deny mutation until synchronization and checkpoint repair succeed.

If the Kiro hook or control script is unavailable, continue read-only discussion and tracker maintenance, state that lifecycle enforcement is unavailable, and do not perform an otherwise authorized mutation until the user installs and trusts the hook or explicitly chooses `/workflow-plan` or `/workflow-execute`. Never bypass a denied hook decision.

New discussion bundles use the `Lightweight` profile. Profiles change persistence and reread cadence, never authorization or mutation enforcement. Only workflow-record version 4 bundles are accepted.

## Reference Routing

Load only the reference needed for the current stage, and read that reference completely before applying it.

- Read [references/tracker.md](references/tracker.md) before creating, resuming, migrating, persisting, or handing off a discussion tracker.
- Read [references/actions.md](references/actions.md) before baseline analysis of an existing mechanism, any scoped mutation, or combining discuss with another skill.
- Keep `Required references` minimal: always `references/tracker.md`; add `references/actions.md` while baseline analysis, a scoped action, or a skill combination is active. Persist and acknowledge each set change, read newly required references, and run `rules-sync` before the next mutation.
- The decision gate, question rules, and response sequence remain in this entrypoint and apply throughout the mode.

## Immediate Decision Gate

After completing required tracker housekeeping, work in bounded increments. As soon as the first material issue is encountered whose resolution requires the user's preference, scope choice, authorization, or acceptance of a consequential tradeoff, stop all substantive work for the turn.

- Do not continue inspection, analyze later branches, complete later workflow steps, collect more decisions, or apply a default.
- Finish only an already-running atomic read-only operation. Start no further substantive tool call. Make only the minimal tracker update needed to record progress, evidence, the blocking decision, and deferred work.
- Ask exactly one decision question with 2-4 options total, then end the response and wait for the user's answer. Count `Other — specify` toward the 2-4 total.
- After the user answers, record the decision, resume from the checkpoint, and apply this gate again at the next material decision.
- Do not treat a factual unknown that can be resolved through safe, proportionate read-only inspection as a decision gate. If that inspection exposes a material user-owned decision, stop immediately after the current atomic operation.
- If one result exposes several material decisions, ask only the one that blocks the earliest next action; prioritize safety or irreversibility when tied. Record later decisions as deferred without asking them yet.
- Keep inspection batches narrow enough that they do not knowingly cross a foreseeable decision gate.

This gate applies only while full `discuss` mode is active. A `/workflow-plan` discuss fallback inherits `Question Style`, but not this gate, unless that skill explicitly opts into it.

## Question Style

Every question that requires a user response must include concrete options. Do not ask a bare open-ended question, including when requesting clarification, confirmation, approval, or permission to exit this mode. Never ask a storage-choice question for the tracker.

- For a material decision gate, present only the first unresolved issue as a single question block. Do not batch multiple decision questions; defer later issues to subsequent turns.
- Provide 2-4 total practical, mutually distinguishable options that answer that question.
- Mark one option as `Recommended` or `Default` when there is a reasonable choice.
- Include `Other — specify` when the listed choices may not cover the user's intent.
- When the user must supply a free-form value unrelated to tracker storage, such as a URL or external resource name, offer useful defaults or actions first and include an option to provide a different value. Never invent the free-form value.
- If a question is non-blocking and outside a material decision gate, state which default the agent will use if the user does not answer. Never apply a default to a material decision gate; wait for the user's answer.
- Apply these rules to questions in chat and to every item recorded under `Open Questions` in the tracker.
- Before sending a response, check that no user-facing question lacks its own option list.

Example:

Instead of:
"What approach do you want?"

Prefer:
"Ban muon di huong nao?
1. Minimal fix: chi sua dung loi hien tai. Recommended.
2. Broader cleanup: sua loi va don phan lien quan.
3. Planning only: minh viet ke hoach truoc, chua sua gi.
4. Khac: ban mo ta huong ban muon."

## Response Pattern

When a user asks for something actionable while this mode is active:

Apply `Immediate Decision Gate` throughout every step below. When it triggers, stop at the current step and do not advance until the user answers.

1. Resolve the Markdown bundle destination automatically. If an existing bundle or its `index.md` is supplied, adopt and freeze its canonical root. Otherwise default to `./discussion/YYYY-MM-DD-<discussion-name>/` and select a numbered variant on collision.
2. For a new bundle, create missing parents, reserve the collision-free directory, and initialize its required Markdown files and manifest. For a handoff, validate it without replacing content.
3. Identify any containing Git worktree from the selected path's nearest existing ancestor and create or update the root `.gitignore` idempotently according to `Repository Ignore Rule`.
4. If the bundle is a handoff, read `index.md` and every manifest file, adopt the exact root, and restore its checkpoint before changing content.
5. Initialize or transactionally update the selected bundle with current discussion state and housekeeping.
6. For a handoff, revalidate material drift before relying on recorded external facts.
7. If the discussion concerns changing an existing mechanism, establish and record the behavioral baseline, preservation requirements, regression risks, and evidence gaps before recommending the change.
8. Determine whether the user already chose a `/workflow-plan` or `/workflow-execute` transition for the active tracker.
9. If `/workflow-plan` was chosen, durably exit discuss under `Settled Discussion Transition Gate` and hand the complete tracker to `/workflow-plan` as context.
10. If `/workflow-execute` was chosen, apply `Direct Execute Handoff`; remain in discuss when its gate cannot pass, otherwise persist the exit and hand the exact bundle to `/workflow-execute` without creating a separate plan bundle.
11. Otherwise, when the discussion is settled and no blocking question remains, apply `Settled Discussion Transition Gate`, ask whether the user wants `/workflow-plan` or `/workflow-execute`, and wait.
12. Otherwise determine whether the requested action would mutate source code.
13. If it would mutate source code, apply `Temporary Source-Code Actions`: disclose the impact, obtain confirmation when the request is not already unambiguous, persist authorization, perform and verify only the bounded action, persist its result, and automatically resume discuss.
14. If it is a non-source-code mutation and the user's instruction clearly authorizes it, record the scope, perform the change, and verify it proportionately.
15. If mutation has not been clearly authorized, provide analysis, options, pseudocode, or a step-by-step plan without applying it.
16. Apply `Tracker Durability Gate` before every response after substantive work.
17. Clarify that `discuss` remains active after every scoped action. Only a persisted transition to `/workflow-plan` or `/workflow-execute` exits it.
18. Format every question that needs a user response as its own option block under the mandatory `Question Style` contract.
