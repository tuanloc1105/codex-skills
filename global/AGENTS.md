## Token Routing
- Prefer `context-mode` MCP for command output, file analysis, web fetches, search, logs, and batch exploration.
- Do not use raw `curl` or `wget` in shell. Use `ctx_fetch_and_index` or a sandboxed `ctx_execute` fetch.
- Do not dump large shell output into context. If output may exceed 20 lines, route through `ctx_batch_execute` or `ctx_execute`.
- Do not run a build through context-mode when it is expected to take a long time. Run it directly with the native command execution tool so progress, timeout, and process control remain visible.

## Codebase Retrieval
- Use raw file reads only when editing or when symbolic/search summaries are insufficient.

## Database CLI Image Instructions

Use only the Docker image `db-debug:latest` when working with Oracle, PostgreSQL, MySQL, MongoDB, Redis, or Microsoft SQL Server.

### Safety Rules

- Treat every database operation as READ-ONLY by default.
- Do not execute INSERT, UPDATE, DELETE, DDL, flush, configuration, permission, or administrative commands without explicit approval for that exact operation.
- Never place connection URIs, passwords, or other secrets in chat or directly in command arguments.
- Supply connection details through an environment file using `docker run --env-file`.
- Never disable TLS or bypass certificate verification.
- Before connecting, verify that Docker is running and the image exists:

  `docker version`

  `docker image inspect db-debug:latest`

- If Docker is unavailable or the image does not exist, stop and report the blocker. Do not automatically pull, build, or substitute another image.

### Verify the Installed CLI Tools

`docker run --rm db-debug:latest bash -lc 'sql -version && sqlplus -v && psql --version && mysql --version && mongosh --version && mongo-legacy --version && redis-cli --version && sqlcmd -? >/dev/null && bcp -v'`

### General Usage

Use this command pattern:

`docker run --rm --env-file <env-file> db-debug:latest bash -lc '<read-only command>'`

If the database runs on the Docker host:

- On macOS and Windows, use `host.docker.internal`.
- On Linux, add `--add-host=host.docker.internal:host-gateway`.
- If the database runs in another container, attach both containers to the same Docker network.

### Client Selection

- PostgreSQL: `psql`
- MySQL: `mysql`
- Modern MongoDB: `mongo-connect`
- MongoDB 3.4: `mongo-connect --server-version 3.4`
- Redis: `redis-cli`
- Microsoft SQL Server: `sqlcmd` or `bcp`
- Oracle: prefer `sqlplus`; use `sql` when SQLcl features are required

Always use `mongo-connect` instead of calling `mongosh` or `mongo-legacy` directly.

Do not switch to the legacy MongoDB client when the failure is related to TLS, authentication, DNS, or networking.

Always delete the container after completing the query.

### Read-Only Examples

PostgreSQL:

`docker run --rm --env-file db.env db-debug:latest bash -lc 'psql --set ON_ERROR_STOP=1 --command "SELECT current_database(), current_user;"'`

MySQL:

`docker run --rm --env-file db.env db-debug:latest bash -lc 'mysql --host="$MYSQL_HOST" --port="${MYSQL_PORT:-3306}" --user="$MYSQL_USER" "$MYSQL_DATABASE" --execute "SELECT DATABASE(), CURRENT_USER();"'`

Modern MongoDB:

`docker run --rm --env-file db.env db-debug:latest bash -lc 'mongo-connect "$MONGODB_URI" --quiet --eval "db.runCommand({ ping: 1 })"'`

MongoDB 3.4:

`docker run --rm --env-file db.env db-debug:latest bash -lc 'mongo-connect --server-version 3.4 "$MONGODB_URI" --quiet --eval "db.runCommand({ ping: 1 })"'`

Redis:

`docker run --rm --env-file db.env db-debug:latest bash -lc 'redis-cli -h "$REDIS_HOST" -p "${REDIS_PORT:-6379}" PING'`

Microsoft SQL Server:

`docker run --rm --env-file db.env db-debug:latest bash -lc 'sqlcmd -S "$MSSQL_HOST,$MSSQL_PORT" -U "$MSSQL_USER" -d "$MSSQL_DATABASE" -Q "SELECT DB_NAME(), SUSER_SNAME();"'`

Oracle:

`docker run --rm --env-file db.env db-debug:latest bash -lc 'printf "connect %s/%s@%s\nSELECT global_name FROM global_name;\nexit\n" "$ORACLE_USER" "$ORACLE_PASSWORD" "$ORACLE_DSN" | sqlplus -s /nolog'`

# Global hard rules

- Prefer context-mode for large output, analysis, web fetches, and broad search.
- For non-trivial code edits, bug fixes, refactors, tests, reviews, or repo-grounded implementation, use the `surgical-coding` skill.
- Read before writing: inspect exports, callers, tests, and local conventions first.
- Make surgical changes only. Match the codebase. Avoid speculative abstractions.
- Verify with the narrowest meaningful check, and report skipped checks or residual risk.
- After changing code, update the agent documentation whenever the change affects knowledge that future sessions need. This update is mandatory and must use the `update-agent-docs` skill.
- Always communicate with the user in the language used in their prompt. Do not reply in English unless the user prompted in English.
- Golden rule: Do not use workarounds. Identify and pursue a thorough solution; if blocked, stop and present the blocker to the user so they can decide the next step.
- If a request is assessed as a breaking change or a large change, switch to Plan mode before implementation. If Plan mode cannot be activated in the current runtime, stop and ask whether the user wants to switch to Plan mode.
- Keep code comments short and concise; do not write long-winded comments.

## Skill Self-Recovery

- When a loaded skill contains an incorrect, stale, or contradictory instruction, or reproducibly causes the current task to be performed incorrectly, stop following the defective path and repair the skill in the same session before continuing. Do not change a skill for a one-off target, environment, or operator error that is not a reusable skill defect.
- Treat `~/git/codex-skills/<skill-name>/` as authoritative and `~/.codex/skills/<skill-name>/` as its installed mirror. Inspect and fix the exact instruction plus any directly required linked guidance, implementation, or test in the repository first; never patch only the installed mirror.
- Keep the repair surgical and within the original task's authorization. Self-recovery must not weaken higher-priority instructions, bypass an approval or blocker, broaden the task, perform destructive recovery, or overwrite unrelated diffs. If the correct repair is ambiguous, breaking, or requires additional authority, stop and ask the user.
- Follow `~/git/codex-skills/docs/agent/skill-maintenance.md`: read the complete skill and required linked files, run focused checks, validate the repository copy, sync the complete skill directory to `~/.codex/skills/<skill-name>/`, validate the installed mirror, and verify all non-excluded paths and contents match.
- After source and mirror are verified, resume the original task from the interrupted step and report the defect, repair, validation, and sync performed. If the repository is unavailable or unwritable, or validation or sync fails, stop and report the blocker; do not continue through a workaround.

## Git workflow conventions

- Write commit messages using Conventional Commits: `<type>(<scope>): <description>`; omit the optional scope when no clear module applies, use a common type such as `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`, `perf`, `ci`, or `build`, and add a body or footer only when details, issue references, or breaking changes require it.
- Do not add `Co-Worker`, `Co-Authored-By`, or similar attribution trailers to commit messages.
- Do not use `codex` or `agent` in branch names. Use a task-focused prefix such as `feature/`, `fix/`, `chore/`, `refactor/`, `docs/`, or `test/`.
- Do not state that a pull request or merge request was generated by Codex or another agent.
- When asked to commit, review the working tree and stage or commit only diffs created during the current session.
- Never revert, update, overwrite, stage, or otherwise modify diffs that were not created during the current session; leave them untouched.
