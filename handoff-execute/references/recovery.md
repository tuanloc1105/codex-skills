# Worker Recovery

Read this reference before acting on an interrupted, crashed, timed-out, missing, or uncertain Codex CLI worker.

## Establish State

Recover the exact canonical bundle root, tracker ID, runtime directory, log, receipt, dedicated worktree mappings, branches, starting heads, and open handoff action from durable evidence. Do not infer a different record or runtime directory by recency.

Determine through read-only checks whether the recorded process or Codex session is still active. If it may still be writing, keep the parent read-only. Do not launch a replacement, simplify, commit, or repair the bundle concurrently.

## Reconcile an Inactive Worker

When the worker is confirmed inactive:

1. Read the full log and receipt when present; treat malformed or absent receipts as incomplete evidence.
2. Read and validate the complete bundle, including open action markers and the resume checkpoint.
3. Inspect each recorded worktree's branch, `HEAD`, status, diff, untracked paths, and commits since its starting head.
4. Match observable changes and checks to plan items and evidence; preserve coherent partial work.
5. Repair incomplete record transactions only after comparing all current files and ruling out another writer. Never blindly restore an old snapshot over newer work.
6. Close or supersede the handoff action with the actual result and record residual work.

Resume the saved Codex session only when its identity is known, its ownership can be exclusive, and continuing it is safer than a fresh run. Otherwise the parent may complete recoverable in-scope work locally under `$execute`, but do not automatically launch another lower-cost worker. Ask the user when choosing a replacement model/session or materially different approach changes the agreed handoff.

Worker failure, unavailable delegation, a failed check, or partial implementation is not by itself a genuine blocker. Continue safe independent recovery work; use `Blocked` only under `$execute`'s genuine blocker definition.
