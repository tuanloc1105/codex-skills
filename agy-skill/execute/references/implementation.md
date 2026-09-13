# Execute Implementation Reference (Antigravity Edition)

Read this reference completely before implementation, tracker amendments, commits, worktree setup, phase scheduling, recovery, or any mutating work unit.

## Dedicated Worktree and Isolation

Before any implementation in a Git repository, ensure work occurs in a dedicated worktree:

1. Retain the captured or recorded initial terminal anchor.
2. New and replacement worktrees must be placed under `<worktree-anchor>/.worktrees/<name>`.
3. In Antigravity, when dispatching subagents via `invoke_subagent`, specify `Workspace: 'branch'` to automatically isolate the workspace into a branch/worktree, or `Workspace: 'share'` when sharing the underlying repository directory safely.
4. For non-Git targets, continue implementation without worktrees or branches. Before the first mutation, record exact target paths and before-state evidence in `evidence.md`.

## Scoped Implementation Actions

Before each bounded mutating work unit:

1. Record one action in `evidence.md` with `<!-- workflow-action:<ID> status:open -->`.
2. Update `index.md` with the active-action summary.
3. Perform mutations using Antigravity editing tools: `replace_file_content` for surgical replacements, `write_to_file` for new files or full rewrites, and `run_command` for builds, tests, and linters.
4. Run focused verification checks.
5. Close the action in `evidence.md` with `<!-- workflow-action:<ID> status:completed -->` (or `failed`/`blocked`).
6. Update affected phase files and `index.md`.

## Execution Steps

1. Read the complete manifest and restore durable identifiers from `index.md`.
2. Follow `Dedicated Worktree` or isolated Antigravity workspace layout.
3. Inspect repository context safely with Antigravity read tools (`view_file`, `grep_search`, `find_by_name`, `list_dir`).
4. Read [parallel-execution.md](parallel-execution.md) before delegating eligible phases.
5. Select a safe execution wave; serialize coupled or unannotated phases.
6. Dispatch eligible phases using `invoke_subagent` (specifying `Role`, `TypeName`, `Workspace: 'branch'`, and bounded task prompt).
7. Execute coordinator-owned phases concurrently if safe.
8. Reconcile subagent reports and verify actual changes made against the baseline.
9. Run phase-local checks, commit coherent units for Git targets, and update `evidence.md`.
10. Run wave integration gates before unlocking dependent phases.
11. Repeat until all phases are accepted.
12. Run final checks from `verification.md`.
13. **Mandatory Simplify Pass**: Use the `simplify` skill to review current-session changes and apply focused improvements.
14. Fix confirmed or plausible simplify findings.
15. Re-run focused checks after simplify fixes.
16. **Agent Docs Update**: If substantial agent-facing changes occurred, run the `update-agent-docs` skill constrained to current-session changes.
17. Re-run checks after agent-doc updates.
18. Update plan status, checklist, evidence, and residual risks.
19. If the user requested merging the associated PR/MR, perform merge verification and post-merge cleanup under [post-merge-cleanup.md](post-merge-cleanup.md).
20. Apply the final completion gate in [completion.md](completion.md).
