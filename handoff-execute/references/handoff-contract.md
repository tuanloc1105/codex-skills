# Codex CLI Handoff Contract

## Ownership Transfer

The parent is the sole coordinator before and after the worker interval. The independent worker becomes the sole writer only for that bounded interval. Before launch, persist an open workflow action containing:

- canonical bundle root and tracker ID;
- source repository, dedicated worktree, branch, and starting `HEAD` for every target;
- preflight classification and constraints;
- effective model and reasoning effort;
- exact runtime directory, log path, receipt path, and receipt schema path;
- authorized mutations and explicit exclusions;
- a resume checkpoint that identifies the handoff as pending or active.

Verify the saved action before launch. While the worker is active, the parent must not edit source, Git state, external resources, or the bundle. Read-only process monitoring is allowed.

## Launch

Use `scripts/launch_worker.py`; do not assemble the prompt in the shell. Pass absolute paths for the bundle, worktree, and runtime directory. The runtime directory must be outside every repository, dedicated worktree, and workflow bundle. Preserve it until reconciliation is complete.

The launcher reads `config/worker.toml` unless explicit, user-supplied overrides are provided. It validates settings against the local Codex model catalog and runs a command equivalent to:

```sh
codex exec -C <worktree> \
  --add-dir <bundle-root> \
  -c 'model="<model>"' \
  -c 'model_reasoning_effort="<effort>"' \
  --output-schema <schema> \
  --output-last-message <receipt> \
  -
```

Do not add `--dangerously-bypass-approvals-and-sandbox`. Inherited CLI policy and higher-priority runtime restrictions remain authoritative. If non-interactive execution encounters a required approval it cannot obtain, the worker must stop and report it.

`--add-dir <bundle-root>` is required when the execution record is outside the dedicated worktree so the worker can perform `$execute`'s transactional record updates. It grants write access only; it does not broaden the user's authorization.

## Worker Prompt Requirements

The prompt must direct the new session to:

- invoke `$execute`, never `$handoff-execute`;
- adopt only the exact bundle root and tracker ID;
- read repository instructions and all `$execute` references required by the record;
- implement the entire accepted scope in the supplied dedicated worktree;
- remain the sole writer and preserve unrelated work;
- not spawn subagents or delegate implementation to another agent/session;
- make only authorized local commits and never push, deploy, merge, rewrite history, or perform destructive/external actions without explicit authorization;
- update the execution bundle transactionally throughout implementation;
- run phase-local and final verification;
- not run the final `$simplify` pass, which belongs to the parent;
- return one receipt matching `references/worker-receipt.schema.json`.

## Monitoring and Reconciliation

Stream combined worker output to the terminal and `worker.log`. Waiting must follow the actual process handle; do not infer completion from silence or use a fixed sleep as the state machine.

After the process terminates, the parent must read and validate the receipt, then independently inspect:

- the complete execution record and every action marker;
- source/worktree/branch mappings and current `HEAD` values;
- commits and subjects against the recorded starting heads;
- staged, unstaged, untracked, and out-of-scope changes;
- phase checklist, dependency, integration, verification, and blocker states;
- whether the worker respected authorization and exclusions.

Reclaim write ownership only after confirming that no worker process is still writing. Close the handoff action as completed, failed, or blocked and record discrepancies. Never equate process exit code zero, valid JSON, or a worker claim with accepted implementation.
