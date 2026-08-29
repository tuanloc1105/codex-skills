# Scheduled OCB Delivery

Use this policy only when the user selects `schedule final commit + MR`. Scheduled delivery is a persistent, fail-closed execution of already approved delivery actions; it is not permission for autonomous implementation, scope repair, approval bypass, or merge.

## Timing and authorization

- Ask for an absolute execution date and time with an IANA timezone. Echo the resolved local time and UTC value before activation. Reject ambiguous relative values such as `tomorrow morning` until resolved exactly.
- Obtain separate exact authorization for creating scheduler artifacts, installing the native service, activating it, committing any verified remainder, pushing the exact source branch, and creating the exact MR. Do not infer one action from another.
- Record the repository, Jira key, source branch, expected HEAD SHA, allowed diff identity and paths, commit message, remote, Epic target branch and SHA, GitLab project, MR title, MR body file, required checks, schedule, timezone, credentials source, logs, state file, retry policy, cancellation command, and cleanup owner.
- Never schedule merge, Jira transition, deployment, release, history rewrite, force push, self-approval, or GitLab administration.

## Persistent architecture

Python is the worker, not the clock. Use only the Python standard library unless the target repository already owns and locks another dependency. The native OS scheduler must start the worker independently of Codex and the chat session:

- macOS: use a user `launchd` LaunchAgent with absolute paths, `ProgramArguments`, `WorkingDirectory`, `StandardOutPath`, and `StandardErrorPath`. Prefer a one-shot worker that records completion and exits. Verify it with `launchctl print`; do not claim persistence from file creation alone.
- Linux: use a user or system `systemd` service plus timer with absolute paths, `WorkingDirectory`, persistent missed-run behavior when required, and explicit stdout/stderr journal handling. Verify enabled and active timer state with `systemctl` and inspect the next trigger.
- If no supported persistent scheduler is available, stop and report `WAITING_EXTERNAL`. Do not substitute an in-chat timer, `sleep`, terminal-bound process, `nohup`, or an unsupervised Python scheduling loop.

The machine and required network must be available at execution time. Record whether the native scheduler catches up after sleep or downtime. Never promise execution while the machine is powered off unless an authorized always-on runner is used.

## Python worker requirements

Create a small auditable worker and immutable job configuration. The worker must:

1. Use absolute paths and `subprocess.run()` with argument arrays, `shell=False`, explicit timeouts, captured output, checked return codes, and a minimal explicit environment. Never interpolate credentials into commands or logs.
2. Acquire a per-job non-blocking lock before any mutation. Exit without mutation when another instance owns the lock.
3. Write structured timestamped logs and an atomic state file through a temporary sibling plus `os.replace()`. Redact tokens, cookies, authorization headers, credential URLs, and environment secrets.
4. Verify the job identifier and schema version, current time window, authorization record, repository identity, clean or exactly allowed status, source branch, expected HEAD, ticket-owned diff identity, remote URL, Epic target existence/SHA, ancestry, and absence of unrelated staged, unstaged, or untracked content.
5. Run every recorded required check before mutation. Stop on timeout, nonzero exit, missing executable, authentication failure, stale base, changed diff, failed size assessment, invalid indivisible-change evidence, or any ambiguity.
6. Commit only the exact verified remainder and only when authorized. Stage an explicit allowlist of paths or verified hunks; never use `git add -A`, broad globs, or an unverified working tree. Verify the resulting commit SHA and diff boundary.
7. Verify `glab` version, leaf-command help, authentication, identity, GitLab project, remote, source, and target before push or MR creation. Use explicit non-interactive arguments and a Markdown body file with real line breaks.
8. Be idempotent: before each mutation, detect whether the expected commit already exists, the exact source SHA is already pushed, or an MR for the exact source and target already exists. Reuse and verify matching state; stop on conflicting state. Never create duplicate commits or MRs.
9. Push without force. Create the MR without auto-merge, then read it back and verify project, IID/URL, source, target, title, body line breaks, and current SHA. A literal `\\n` in the body is a failure that must be corrected only when exact update authorization exists.
10. Record `succeeded`, `failed-safe`, or `already-complete` with command outcomes and identifiers. Never retry deterministic drift or authorization failures. Bound transient retries with exponential backoff, jitter, maximum attempts, and a final nonzero exit.

The worker may use `codex exec` only for a read-only verification prompt whose exact prompt, model/config, sandbox, timeout, and output are pinned. Git and GitLab mutations must remain deterministic Python subprocess steps, not delegated to an unattended model turn.

## Verification before activation

- Syntax-check the Python worker and parse the job configuration and native scheduler definition.
- Run a dry-run against the exact repository. Dry-run must execute every read-only preflight and print the planned mutations without committing, pushing, or creating an MR.
- Exercise focused failure paths with temporary fixtures or dependency injection: lock contention, HEAD drift, dirty unrelated file, failed check, missing `glab`, authentication failure, existing matching MR, conflicting MR, subprocess timeout, and state-file recovery.
- Inspect permissions. Configuration, logs, and state must not contain secrets; credential files must not be copied into the job directory.
- Install and activate only after the user authorizes the exact generated artifacts and commands. Re-read the installed native definition, verify loaded/enabled state and next run, and give the user exact status, log, cancel, rerun, and uninstall commands.

## Execution and handoff

Scheduling leaves the delivery workflow at its truthful prior state and normally records `WAITING_EXTERNAL`. After the worker runs, re-read its state and independently verify Git and GitLab results before assigning `MR_READY`. Failure remains fail-safe with no speculative recovery. Report the failed precondition, mutations completed before failure, exact resume command, cleanup owner, and whether rerunning is idempotently safe.
