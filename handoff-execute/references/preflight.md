# Handoff Preflight

Run this evaluation in the parent session before transferring ownership or launching Codex. Approval permits evaluation; it does not by itself prove handoff safety or authorize implementation.

## Intake Gate

Verify the exact record with `$execute` intake rules. Accept only:

- an approved version 4 `$plan` bundle; or
- a version 4 `$discuss` tracker with `Mode status: Exited`, `Status: Approved for execution`, and a completed `Direct Execute Handoff`.

Require a valid manifest; readable `index.md`, `context.md`, `plan.md`, `verification.md`, `evidence.md`, and declared phase files; a stable tracker ID; no execution-blocking unresolved decision; and a clear current-session request to implement. Preserve the supplied bundle as the sole execution record.

## Eligibility Checks

Inspect repository evidence as needed and decide whether the lower-cost worker can execute without making user-owned product or architecture decisions. Verify:

- desired behavior, scope, exclusions, invariants, and acceptance criteria are concrete;
- phase dependencies, owned paths or mutable resources, outputs, integration gates, and verification are sufficient;
- safe assumptions resolve only factual or mechanical gaps and do not change the approved outcome;
- the target repositories and dedicated worktrees can be resolved without touching the user's existing checkout;
- pre-existing user changes can be distinguished and preserved;
- the worker has the required local tools and permissions within already-authorized scope;
- no pending approval is needed for push, deploy, merge, destructive work, external mutation, secrets, or credentials;
- the work's coupling and ambiguity are suitable for the configured worker model;
- ownership can remain exclusive for the complete worker interval.

Do not rerun planning merely to make a handoff possible. Do not weaken acceptance criteria or invent missing user decisions.

## Classification

Return exactly one classification and record its rationale:

- `READY`: the record is executable as written.
- `READY_WITH_CONSTRAINTS`: only safe, non-material repository facts or operational boundaries need to be added to the worker contract. List every added constraint and its evidence; do not modify the approved outcome.
- `NOT_READY`: an unresolved decision, unsafe overlap, missing authorization, invalid record, unsuitable complexity, unavailable configured model, or another material deficiency prevents a reliable handoff.

For `NOT_READY`, do not launch and do not silently fall back to parent-side `$execute`. Explain the earliest concrete deficiency and the required next action. For model availability failures, preserve the configured values and ask the user to override or update the config rather than substituting silently.
