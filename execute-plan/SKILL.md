---
name: execute-plan
description: Execute an approved Markdown plan file produced by $plan-mode. Use when the user gives a path to a plan and wants Codex to implement the whole plan, schedule dependency-ready phases, optionally delegate parallel-safe phases to separate subagents, keep the plan updated in place, run the required integration and final verification, double-check the resulting diff with $simplify, update agent docs when substantial current-diff changes add missing agent-facing guidance, and then optionally offer a $security-review limited to the current git working-tree diff.
---

# Execute Plan

Use this skill to turn an approved `$plan-mode` handoff plan into completed work while keeping the plan file itself as the source of execution truth.

## Completion Contract

Execute the entire approved plan, not only the current phase or execution wave.

Do not send the final response while any in-scope plan item remains pending `[ ]` or in progress `[~]`, unless a genuine blocker requires user input or an external state change. Progress reports, completed phases, failed checks, subagent results, context pressure, tool failures, and unavailable delegation are intermediate states, not completion conditions. Continue recovering and executing within the current task.

Before sending the final response, ensure exactly one of these conditions is true:

1. Every in-scope plan item is completed `[x]`, final verification has been attempted, and the plan status is `Implemented`.
2. All safe independent work is complete, at least one item has a documented genuine blocker `[!]`, and the plan status is `Blocked`.

## Genuine Blocker Definition

A genuine blocker exists only when meaningful progress requires one of:

- A user decision whose alternatives materially change the approved outcome
- A credential, permission, approval, or secret that cannot be obtained within the current task
- An unavailable external system or state required for the next dependent work
- An action prohibited by higher-priority instructions
- An irreconcilable conflict with pre-existing user changes where proceeding could overwrite or corrupt them

The following are not blockers by themselves:

- A failed test, build, lint, verification, or integration check
- A crashed, timed-out, unavailable, or rejected subagent
- Lack of parallel-agent capacity
- A failed implementation attempt
- Missing optional tooling or skills
- Repository drift that can be reconciled without materially changing the approved goal
- Ambiguity that repository evidence or a safe, non-material assumption can resolve
- An optional documentation, simplification, or review step that can be performed locally or reported as unavailable

## Required Input

Require a path to the plan file.

- If the user supplied a plan path, resolve it before doing implementation work.
- If the user did not supply a plan path, ask where the plan file is and stop until they answer.
- If the path does not exist or is not readable, report that clearly and ask for the correct path.

## Plan Intake

Read the full plan before editing code.

Verify these basics:

- The plan is a Markdown handoff plan, ideally with `# How to do it: ...`.
- The plan has a concrete `## Goal`, `## Step-by-Step Plan`, and `## Verification`.
- The plan status is approved or the user explicitly asked to execute it.
- For a phased plan, read `## Execution Structure` and capture each phase's ID, dependencies, wave, subagent eligibility, owned scope, produced output, and verification or integration requirements.

Treat an explicit user request to execute the supplied plan as execution approval even when the plan status is missing or still says `Draft`, `Ready`, or `Awaiting execution`.

Ask for confirmation only when the plan explicitly says not to implement, an unresolved choice materially changes the desired outcome, repository drift invalidates the approved goal or requires materially different scope, or two authoritative requirements cannot both be satisfied. Do not invent a materially different plan.

Treat `Depends on` as authoritative and any declared wave as a scheduling hint that must agree with it. Revalidate phase independence against the current repository and runtime before dispatch. An eligibility note never overrides overlapping files, shared mutable state, unstable contracts, or newly discovered dependencies.

For backward compatibility, execute plans without dependency, wave, ownership, or subagent metadata sequentially. Missing scheduling metadata is not a blocker. Do not infer parallel permission from numbered steps alone.

When working in a git repository, capture the initial status and current diff boundaries before parallel dispatch so pre-existing user changes can be distinguished and preserved.

## Parallel Phase Scheduling

Treat `Subagent: Eligible` as permission, not a mandate. Build a dependency-ready set from phases whose prerequisites are completed and accepted, then form the safest useful execution wave from that set.

Delegate an eligible phase only when all of these are true:

- The phase has a bounded task, stable inputs, a concrete output contract, and phase-local verification.
- Its write ownership does not overlap another active phase or pre-existing user work that cannot be preserved safely.
- It neither consumes another same-wave phase's output nor mutates a shared contract, migration, lockfile, generated artifact, external resource, persistent test data, stateful process, or similarly coupled resource without an explicit safe coordination strategy.
- A separate subagent and runtime capacity are available, and delegation is likely to improve speed or quality enough to justify coordination.

Use one subagent per eligible phase. The main agent may execute another dependency-ready, non-conflicting phase concurrently. Never hardcode a concurrency count; respect the active runtime's available capacity.

If delegation is unavailable, unsafe, or not worthwhile, execute the eligible phase sequentially and add a concise plan note when the reason matters for handoff. Lack of subagent capacity is not a blocker.

## Coordinator and Subagent Ownership

The main agent is the coordinator and remains the sole writer of the original plan file. It owns dependency scheduling, shared or cross-phase files, integration, conflict resolution, final verification, the `$simplify` pass, the agent-doc decision, and the final response.

Assume subagents share the current workspace unless the runtime explicitly guarantees isolation. Enforce one writer per file or mutable touchpoint within a wave.

Before dispatch, mark the phase in progress and give the subagent a bounded task containing:

- The exact phase ID, goal, satisfied dependencies, and authoritative inputs
- Allowed files, modules, services, or mutable resources, plus explicit exclusions
- Required repository instructions and read-before-write context
- The expected output or handoff contract and phase-local checks
- A requirement not to edit the plan file, broaden scope, or run commits, pushes, deployments, destructive commands, broad formatters, or other operations outside its ownership unless separately authorized
- A return contract covering summary, files or resources changed, checks and results, assumptions, risks, and blockers

Require a subagent to stop and report before touching an unassigned or overlapping resource or materially changing the approved approach. Review its reported output and actual changes before accepting the phase; never treat a successful agent status as sufficient verification.

## Execution Rules

Follow the plan as written, subject to higher-priority instructions and current repository rules.

- Read relevant project instructions, local conventions, callers, tests, and touched files before writing.
- For non-trivial code edits, follow the active repository coding workflow and use any required coding skill or semantic retrieval tools available in the session.
- Keep changes surgical and scoped to the plan.
- Do not commit, push, deploy, run destructive commands, or broaden scope unless the plan or user explicitly says to.
- If the plan references additional skills, tools, apps, or commands, use them when available.
- Recover from failed attempts using the recovery workflow before considering a step blocked.
- Allow unrelated dependency-ready phases to continue when one phase fails, but never start a dependent phase until its prerequisite is accepted and integrated.

## Updating The Plan

Update the original plan file in place as work progresses. Do not create a separate execution-progress section unless the user asks for one.

In `## Step-by-Step Plan`, convert steps to a checklist if needed and update each item directly:

- `- [ ]` or `1. [ ]` for pending
- `- [~]` or `1. [~]` for in progress
- `- [x]` or `1. [x]` for completed
- `- [!]` or `1. [!]` for blocked

Preserve the original step text where possible. Add concise inline notes only when they help a future session understand a decision, blocker, or verification result.

The coordinator may mark multiple items in progress only when their phases are explicitly safe to run in the same wave. Mark every dispatched phase in progress before spawning its subagent, and mark it completed only after reviewing scope, accepting its output, and confirming its phase-local checks. Keep dependent phases pending until their prerequisites pass the required integration gate.

Add short notes such as `parallel wave 1` or `serialized: overlaps <path or state>` when they explain an execution decision. Do not let subagents edit the plan concurrently. Use `[!]` only for a genuine blocker that requires user input or an external state change, not merely for a crashed, timed-out, or unavailable subagent.

Also update the plan status line when present:

- Before implementation: `Status: In progress`
- After implementation and verification: `Status: Implemented`
- If blocked: `Status: Blocked`

When checks are run, update `## Verification` directly with checkboxes or short result notes. Include skipped checks and residual risk in the existing `## Verification` or `## Handoff Notes` sections.

## Implementation Workflow

1. Resolve and read the plan path.
2. Inspect enough repository context to execute safely.
3. Build the dependency and ownership map, validate declared waves, and identify the current ready set.
4. Select a safe execution wave; serialize phases that are unannotated, coupled, or not worth delegating.
5. Mark the selected phase items in progress and dispatch each eligible delegated phase with the required ownership and return contract.
6. Execute any coordinator-owned phase that can run concurrently without conflicting with active subagents.
7. Collect subagent reports, inspect actual changed files or resources against the baseline and assigned ownership, and review each implementation.
8. Run or confirm phase-local checks, then mark each accepted phase completed; recover or mark a genuine blocker as appropriate.
9. Run the wave's integration gate before unlocking dependent phases.
10. Repeat the ready-set workflow until all phases are accepted or a genuine blocker requires user input or an external state change.
11. Run the plan's final `## Verification` checks on the integrated result.
12. Use `$simplify` to review the integrated current changes.
13. Fix confirmed or plausible `$simplify` findings that are in scope.
14. Re-run the narrowest meaningful checks after any simplify-driven fixes.
15. If the current git working-tree diff contains substantial agent-facing changes that are not already covered in agent docs, use `$update-agent-docs` with the current-diff-only scope in this skill.
16. Re-run the narrowest meaningful checks after any agent-doc updates.
17. Update the plan status, checklist, verification notes, execution decisions, and residual risks.
18. Apply the final completion gate and continue working if any requirement fails.

## Recovery Before Blocking

Before declaring a blocker:

1. Inspect partial changes and the concrete failure.
2. Retry when the failure may be transient.
3. Attempt a safe in-scope alternative.
4. Replace failed delegation with coordinator-owned execution.
5. Serialize conflicting work.
6. Continue all unrelated dependency-ready phases.
7. Record skipped optional checks and residual risk when implementation can still be completed safely.

Ask the user only after these recovery paths are exhausted and the Genuine Blocker Definition is satisfied.

## Failure and Conflict Handling

A subagent failure is not automatically a plan blocker. Inspect any partial changes, preserve pre-existing user work, and choose the safest recovery: retry, reassign, finish locally, or serialize the phase. Continue unrelated ready phases when safe and keep dependent phases pending.

If ownership overlaps or an unexpected dependency appears, stop only the conflicting dispatch, preserve and inspect the current changes, update the plan note or dependency metadata, and resume in a safe sequence. Continue unrelated ready work when safe. Never use a blanket reset or discard unrelated user changes to recover from parallel work.

If a wave integration check fails, return the implicated phase items to in progress while correcting them. Mark the plan blocked only when meaningful progress truly requires user input or an external state change.

## Required Simplify Pass

After the plan is implemented, invoke `$simplify` on the current changes before the final response.

- Scope `$simplify` to the files and diff changed while executing the plan.
- Run one coordinator-owned simplify pass only after all parallel phase results have been collected and integrated; do not run independent simplify passes inside subagents.
- Allow `$simplify` to apply focused fixes for confirmed or plausible issues in scope.
- Do not let simplification broaden the plan or refactor unrelated code.
- If `$simplify` is unavailable, rejected, or lacks capacity for its preferred reviewer layout, perform all required review passes locally or with the available safe capacity and state the limitation. Do not block plan completion waiting for a specific subagent count.

## Agent Docs Update

After the plan is implemented, verified, and simplified, decide whether the current git working-tree diff introduced substantial information future agents need.

Run `$update-agent-docs` automatically only when both are true:

- The current git working-tree diff includes durable agent-facing changes, such as new or changed project structure, package boundaries, entrypoints, scripts, commands, workflows, tests, generated assets, configuration, deployment steps, migrations, or repo conventions.
- The existing agent docs do not already cover the new or changed information accurately.

When invoking `$update-agent-docs` from this skill, explicitly constrain it to the current git working-tree diff:

- Review only the current git working-tree diff and the agent docs needed to check coverage or make the update.
- Do not run a repository-wide documentation refresh.
- Do not document unrelated existing code, conventions, scripts, or workflows just because they are discovered while checking the docs.
- Keep any agent-doc changes limited to guidance made necessary by the current diff.
- If there is no git repository or no current diff to inspect, skip this step and state the limitation in the final response.
- If `$update-agent-docs` requires additional authorization, including permission to edit outside the repository, skip the optional update and record the reason unless that external documentation update is itself an explicit plan goal. Do not leave an otherwise completed implementation in progress solely because an automatic agent-doc update could not run.

## Security Review Offer

Do not run `$security-review` automatically.

The security-review offer is post-completion and must not leave the execution plan marked in progress.

At the end, ask the user whether they want a security review of the current git working-tree diff.

If the user says yes, use `$security-review` with this scope constraint:

- Review only the current git working-tree diff.
- Do not review the full repository.
- Read surrounding context, callers, or configs only as needed to validate a finding from the diff.
- Report findings first, following the `$security-review` output format.

## Final Completion Gate

Before sending the final response:

- Re-read the plan checklist and confirm no in-scope `[ ]` or `[~]` item remains.
- Confirm every `[!]` item satisfies the Genuine Blocker Definition.
- Confirm unrelated ready phases were not skipped because another phase failed.
- Confirm final verification was run or its unavailability and residual risk were documented.
- Confirm the required simplify review was completed through the skill or locally.
- Confirm optional agent-doc limitations did not prevent plan completion.
- Persist the final checklist, status, verification results, execution decisions, and residual risks to the plan file.

If any requirement above is false, continue working instead of responding finally.

## Final Response

Summarize:

- What was implemented
- Which plan steps are completed or blocked
- Which phases ran in parallel, which eligible phases were serialized and why, and any subagent recovery that was needed
- Checks run and results
- Integration-gate results for parallel waves
- `$simplify` result and any fixes it caused
- Whether `$update-agent-docs` was run, skipped, or unavailable, and any docs it changed
- Whether the plan file was updated

Then ask whether the user wants `$security-review` on the current git working-tree diff, unless they already answered that question in the current turn.
