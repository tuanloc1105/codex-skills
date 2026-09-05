# Execute Completion Reference

Read before reporting an implementation outcome. Add this reference to Required references through a record write and acknowledge rules. This reference does not require using a review skill, creating commits, or completing work after a user stop.

## Outcome-Specific Gate

Apply only the row matching the actual outcome:

| Outcome | Required evidence | Unfinished work |
| --- | --- | --- |
| Implemented | Every authorized in-scope item completed; meaningful verification run or a concrete limitation and residual risk recorded | None in scope; explicitly superseded items may remain in history |
| Blocked | Specific genuine blockers recorded; all authorized safe independent work exhausted; completed changes and available checks reconciled | Blocked items and their dependent pending items remain accurate |
| Paused / cancelled / exited unfinished | User's stop instruction and actual effects recorded; running work interrupted/reconciled as appropriate | Pending/in-progress items may remain, annotated with the pause; do not execute them to pass this gate |
| Read-only checkpoint | Relevant evidence recorded; no change to implementation status unless supported | Existing checklist preserved |

If a substantive issue invalidates completion, continue authorized recovery. If the user stopped, or a genuine blocker prevents progress, report that state instead. A persistence failure uses the entrypoint suspend protocol; do not claim unsaved evidence was recorded successfully.

## Proportionate Verification and Review

For Implemented, inspect the complete task diff against its starting boundary, confirm preserved behavior and acceptance criteria, and run the meaningful checks required by the plan and repository. Do not repeat already passed checks without a relevant change or unresolved concern.

Use `$simplify` when requested, required by repository policy, or when the implementation has enough complexity that focused cleanup materially helps. Keep it within current-task changes; do not refactor unrelated code or demand a preferred reviewer layout. If a skill is unavailable, use a proportionate local review when needed. A small coherent change needs no ceremonial simplify pass. Check and record any resulting fixes; commit them only when commits are authorized.

Update agent docs only when this task changes durable guidance that existing docs no longer cover. If `$update-agent-docs` is appropriate and available, constrain it to current-task changes plus necessary documentation context. Optional documentation or review work must not prevent reporting a stop or genuine blocker.

Run or offer security review only when requested or when the change exposes a concrete security-sensitive concern worth the user's attention. Do not append a standard security-review question to every completion report.

## Final Record Reconciliation

- Preserve the exact adopted record and classify the actual outcome above.
- Confirm phase acceptance, dependency gates, amendments, and verification agree. Do not require all phases to be completed for Blocked or Paused.
- Record the actual workspace and branch; a worktree is required only when chosen or mandated by repository/user policy.
- If commits were authorized and created, record their SHA, subject, branch, and associated work. Do not create commits just to satisfy completion.
- Close action markers with the actual terminal result and close the record transaction. Checkpoint material deltas.
- Keep Execute mode Active for a normal task checkpoint; use Paused/Exited and deactivate on a user stop or clear switch to a separate task.

## Final Response

Lead with the outcome, what changed, meaningful verification, and material limitations or remaining blockers. Include workspace/branch and commit information when it helps locate the result, and the adopted record path when useful for resuming. Mention important delegation or integration issues only when they affect confidence or remaining work. For unfinished work, state exactly what remains and why. Never require the user to read earlier progress updates to understand the result.
