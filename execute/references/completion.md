# Execute Completion Reference

Read before reporting an implementation outcome. Read this reference and record it in Required references at the next checkpoint; missing hook acknowledgment does not block reporting. This reference does not independently grant commit authority or require using a review skill or completing work after a user stop. Apply the entrypoint's local incremental commit authorization and the implementation reference's mandatory cadence.

## Outcome-Specific Gate

Apply only the row matching the actual outcome:

| Outcome | Required evidence | Unfinished work |
| --- | --- | --- |
| Implemented | Every authorized in-scope item completed; meaningful verification run or a concrete limitation and residual risk recorded | None in scope; explicitly superseded items may remain in history |
| Blocked | Specific genuine blockers recorded; all authorized safe independent work exhausted; completed changes and available checks reconciled | Blocked items and their dependent pending items remain accurate |
| Paused / cancelled / exited unfinished | User's stop instruction and actual effects recorded; running work interrupted/reconciled as appropriate | Pending/in-progress items may remain, annotated with the pause; do not execute them to pass this gate |
| Read-only checkpoint | Relevant evidence recorded; no change to implementation status unless supported | Existing checklist preserved |

If a substantive issue invalidates completion, continue authorized recovery. If the user stopped, or a genuine blocker prevents progress, report that state instead. A persistence failure uses the entrypoint repair protocol; do not claim unsaved evidence was recorded successfully.

## Proportionate Verification and Review

For Implemented, inspect the complete task diff against its starting boundary, confirm preserved behavior and acceptance criteria, and run the meaningful checks required by the plan and repository. Do not repeat already passed checks without a relevant change or unresolved concern.

Run `$simplify` after every execution batch that changes code and before reporting that batch complete, even for a small change, a single phase or step, or a follow-up amendment. Do not defer it until the entire plan is complete. Load the skill and its required references and perform its workflow; merely inspecting the diff or mentioning the skill does not satisfy this step. Honor an explicit user exclusion, and do not run cleanup after a user stop or as a prerequisite to an honest blocker report. Read-only and documentation-only batches need no code simplification.

Scope the pass to current-task changes from the recorded starting boundary, including committed changes and in-scope working-tree changes; preserve unrelated and concurrent work. Reuse recorded coverage for unchanged code, and review new changes and their interactions when execution resumes. Do not manufacture edits when no verified improvement exists or demand a preferred reviewer layout. Verify resulting fixes and follow the authorized incremental commit cadence without rewriting earlier history. Record the reviewed scope, applied improvements or no-change result, checks, and any explicit exclusion in `verification.md` with supporting evidence as needed. If the skill is unavailable, disclose that limitation, perform a proportionate local cleanup review, and record it as a fallback rather than claiming `$simplify` ran.

Update agent docs only when this task changes durable guidance that existing docs no longer cover. If `$update-agent-docs` is appropriate and available, constrain it to current-task changes plus necessary documentation context. Optional documentation or review work must not prevent reporting a stop or genuine blocker.

Run or offer security review only when requested or when the change exposes a concrete security-sensitive concern worth the user's attention. Do not append a standard security-review question to every completion report.

## Final Record Reconciliation

- Preserve the exact adopted record and classify the actual outcome above.
- Confirm phase acceptance, dependency gates, amendments, and verification agree. Do not require all phases to be completed for Blocked or Paused.
- For Git implementation, verify and record the dedicated linked worktree path and branch, and confirm implementation tools and subagents used it. A clean original checkout or a large/small plan is not an exception. For non-Git work, record that Git worktree setup is inapplicable. A Blocked or Paused report remains valid when worktree setup failed; do not claim implementation completion or continue in the original checkout to satisfy this gate. If implementation occurred in the wrong checkout, disclose it and reconcile only task-owned changes safely before claiming compliance; creating a worktree afterward does not retroactively prove isolation.
- If commits were authorized, confirm each smallest complete verified implementation unit was committed at the required cadence, and record its SHA, subject, branch, and associated work. Do not defer separable units to a final batch. If cadence was missed, disclose it; splitting commits afterward does not prove the required cadence occurred. A user stop or genuine commit blocker permits an accurate Paused/Blocked report with uncommitted work preserved. If commits were not authorized, do not create them just to satisfy completion.
- Reconcile any opened action markers with the actual terminal result, close the record transaction, and attempt a checkpoint. Hook bookkeeping alone must not prevent the final report. Disclose unresolved persistence or control failures without claiming they succeeded.
- Keep Execute mode Active for a normal task checkpoint; use Paused/Exited and deactivate on a user stop or clear switch to a separate task.

## Final Response

Lead with the outcome, what changed, meaningful verification, and material limitations or remaining blockers. Include workspace/branch and commit information when it helps locate the result, and the adopted record path when useful for resuming. Mention important delegation or integration issues only when they affect confidence or remaining work. For unfinished work, state exactly what remains and why. Never require the user to read earlier progress updates to understand the result.
