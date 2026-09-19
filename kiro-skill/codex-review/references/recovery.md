# Codex Reviewer Recovery

Read this reference before acting on an interrupted, crashed, timed-out, missing, malformed, or uncertain Codex reviewer run.

## Establish Exclusive State

Recover the canonical bundle root, tracker ID, review ID, allowed paths, runtime directory, log, receipt, repository observation boundary, and open action from durable bundle evidence. Never infer another bundle, review, or runtime directory by recency.

Use read-only checks to determine whether the recorded Codex process may still be writing. While it may be active, Kiro must not edit the bundle, launch a replacement reviewer, adjudicate findings, or resume source-mode mutation.

## Reconcile an Inactive Reviewer

After proving the reviewer inactive:

1. Read the full log and receipt when present; malformed or missing output is incomplete evidence.
2. Read and validate the complete current bundle before changing it.
3. Compare all bundle paths with the pre-launch snapshot and identify writes outside `index.md`, `evidence.md`, and the declared review artifact.
4. Compare repository and Git state with the saved observation boundary. Preserve and report unrelated user changes; do not revert them.
5. Preserve a coherent partial review. Repair an incomplete bundle transaction only after ruling out another writer and comparing current content with the saved state.
6. Close or supersede the review action with its actual `completed`, `blocked`, or `failed` result, record discrepancies and limitations, and restore an accurate source-mode Resume Checkpoint.

Do not automatically relaunch. Resume a known Codex session only when its identity is durable, exclusive ownership is certain, and continuation is safer than a fresh review. Otherwise ask the user before spending quota on a replacement run when the existing evidence cannot satisfy the request.

Reviewer failure is not permission to discard its partial tracker or to accept unsupported findings. Kiro remains responsible for final adjudication and bundle consistency.
