---
name: data-debug
description: Safely inspect and troubleshoot Oracle, PostgreSQL, MySQL, MongoDB, Redis, or Microsoft SQL Server using the bundled Java SQL CLI or the db-debug:latest Docker image for MongoDB/Redis. Use for database connectivity checks, metadata inspection, read-only queries, query-plan analysis, or database incident debugging. All database work is read-only by default; mutations require explicit approval for the exact operation.
---

# Data Debug

Use the bundled Java CLI for Oracle, PostgreSQL, MySQL, and SQL Server. Use only `db-debug:latest` for MongoDB/Redis. Treat the database, its credentials, and returned data as sensitive.

## Workflow

1. Confirm the target engine, environment, database, and diagnostic question. Resolve ambiguity before connecting to production or another sensitive environment.
2. Route SQL engines through the Java workflow below; Docker is not a SQL prerequisite. For MongoDB/Redis, verify Docker and the required local image:

   ```sh
   docker version
   docker image inspect db-debug:latest
   ```

   If either command fails, stop and report the blocker. Do not pull, build, retag, or substitute an image unless the user explicitly asks for that exact action.
3. For MongoDB/Redis, if image client availability is uncertain, run the existing image smoke command:

   ```sh
   docker run --rm db-debug:latest bash -lc 'sql -version && sqlplus -v && psql --version && mysql --version && mongosh --version && mongo-legacy --version && redis-cli --version && sqlcmd -? >/dev/null && bcp -v && mssql-connect --version && if command -v sqlcmd17 >/dev/null; then sqlcmd17 -? >/dev/null && bcp17 -v; fi'
   ```

4. Classify the requested operation before execution:
   - Read-only: connectivity checks, metadata inspection, bounded reads, and non-mutating query plans.
   - Sensitive export: dumps, bulk reads, or queries likely to expose personal, credential, financial, or production data. Require an explicit user request and minimize the output.
   - Mutation: writes, deletes, DDL, flushes, procedure calls with side effects, configuration, permissions, maintenance, or administration. Follow the mutation boundary below.
5. Use the least-privileged, read-only database account available. Client-side intent is not a security boundary; a query that starts with `SELECT` can still call a mutating function.
6. Run the narrowest useful command, limit returned rows or keys, and summarize results without reproducing secrets or unnecessary sensitive values.

## Safety Rules

- Keep all operations read-only unless the user explicitly approves the exact mutation in the current conversation.
- Before an approved mutation, show the exact target, statement or command, expected effect, and rollback or recovery path. Do not interpret approval for one statement as approval for a batch, retry, broader target, or follow-up operation.
- Do not run stored procedures, user-defined functions, triggers, `EXPLAIN ANALYZE` on mutating statements, or commands with unclear side effects as read-only work.
- Never place connection URIs, passwords, tokens, certificates, or other secrets in chat, source files, shell command arguments, or captured logs. For SQL, only the CLI may read `.env.db` in the original terminal cwd; the agent must never read, source, copy, print, or inspect its contents. For MongoDB/Redis, pass the user-provided environment file with `docker run --env-file`.
- Keep environment files untracked and restrict their permissions. For SQL use only the original terminal cwd `.env.db`, without searching parent/home/skill directories; ask the user to prepare it if missing. Do not change the user file. Delete task-owned temporary credential files only when their lifecycle belongs to the task.
- SQL defaults to verified TLS. On a certificate/hostname validation failure, the CLI automatically makes at most one encrypted relaxed connection attempt; no repeated approval gate, authentication bypass, automatic plaintext downgrade, or SQL replay. Report the returned transport mode; relaxed TLS loses server identity validation. Plaintext SQL requires an explicit `--tls plaintext` choice. MongoDB/Redis retain the explicit transport policy below.
- For Docker, always use `--rm`. Do not mount the Docker socket, mount database data directories, use `--privileged`, or add capabilities. Avoid host filesystem mounts unless a user-requested import or export requires a specific path.
- Prefer explicit timeouts supported by the selected client or server. Avoid unbounded scans, full collection reads, keyspace-wide Redis commands, and production query-plan execution that could create material load.
- Do not switch MongoDB clients to work around authentication, DNS, or networking failures. Configure the selected client explicitly when plaintext transport or relaxed TLS verification is required.
- Report the database identity and scope before substantive diagnostics when a wrong-target connection would be risky.

## Java SQL Workflow

Read [cli/README.md](cli/README.md) for the interface, limits, driver compatibility and failure semantics. Determine the absolute root of the skill actually loaded, not a repository checkout or assumed current directory. Capture the original terminal cwd and keep it for configuration and query invocations.

1. Check `java -version` (Java 17+) and `<skill-root>/cli/target/data-debug.jar`. If the JAR is absent, verify `javac -version` (JDK 17+) and `mvn -version`, then automatically build bundled source:

   ```sh
   mvn -f "<absolute-skill-root>/cli/pom.xml" clean verify
   ```

   Maven may resolve dependencies over the network. Missing toolchain: report the missing requirement, do not install it automatically. Reuse the built JAR. Build artifacts stay under the module; do not change the query cwd or inspect `.env.db` while debugging a build.
2. Invoke `java -jar "<absolute-skill-root>/cli/target/data-debug.jar" --list-keys` in the original terminal cwd. It returns names and duplicate names only, never values; no connection is made. Choose per-field mappings from these names and user context. Ask the user when several targets/mappings remain plausible; do not guess or inspect values. Never use `cat`, `rg`, `source`, `env`, or shell expansion against `.env.db`.
3. Run `--check-config` with the chosen `--engine`, `--host-key`, optional `--port-key`, `--database-key`, `--user-key`, `--password-key`. Oracle uses exactly one of `--service-key`/`--sid-key` instead of `--database-key`. Alternatively `--url-key` maps a restricted endpoint-only JDBC URL, exclusive with host/port/database/service/SID mappings; user/password remain separate key mappings. Only key names enter argv. Missing, duplicate, invalid or conflicting mappings stop before connecting.
4. Submit a single bounded, classified statement through UTF-8 stdin with the same mappings. Default `--mode read`, 100 rows and a 10-second deadline. A `--mode write` flag does not constitute approval: use the exact-operation mutation boundary first. Larger exports require an explicit request; CLI caps remain finite. Interpret sanitized JSON errors without requesting file values or exposing raw JDBC diagnostics.
5. Report actual transport/transaction/truncation metadata. Never retry a failed query or write automatically, including timeout or unknown commit outcomes. Obtain fresh exact approval for any write retry after separate outcome verification.

Example for PostgreSQL, with nonsecret key names selected from discovery; invoke from the original cwd:

```sh
printf '%s\n' 'SELECT current_database(), current_user;' | java -jar "<absolute-skill-root>/cli/target/data-debug.jar" --engine postgresql --host-key PG_HOST --database-key PG_DATABASE --user-key PG_USER --password-key PG_PASSWORD
```

For MySQL use `SELECT DATABASE(), CURRENT_USER();`, SQL Server `SELECT DB_NAME(), SUSER_SNAME();`, and Oracle `SELECT global_name FROM global_name;` with the corresponding engine and discovered mappings. SQL targets are reached from the host Java process, so Docker host/container routing does not apply to SQL.

Read classification supports conservative SELECT/read CTE, selected SHOW metadata, and nonexecuting EXPLAIN on PostgreSQL/MySQL. Rejects mutating CTE, SELECT INTO, locking reads, EXPLAIN ANALYZE, procedures, multiple statements and ambiguous dialect syntax. It cannot prove arbitrary SQL functions pure: use least-privileged accounts. PostgreSQL/MySQL request server read-only transactions; Oracle uses `SET TRANSACTION READ ONLY`; SQL Server's read-only hint depends on account permissions. Writes commit where transactional; Oracle/MySQL DDL can auto-commit and need manual recovery.

Compatibility targets: Oracle 19c, PostgreSQL 12, MySQL 8.0, SQL Server 2016 through the newer releases documented in [cli/README.md](cli/README.md). Vendor-declared support and synthetic/package tests are separate from real endpoint verification. Older versions may be attempted best-effort, without a version-only rejection or a guarantee; future releases/new data types are not automatically certified.

## Docker Connection Pattern (MongoDB/Redis)

Use:

```sh
docker run --rm --env-file <env-file> db-debug:latest bash -lc '<read-only command>'
```

Network routing:

- For a database on the macOS or Windows Docker host, use `host.docker.internal`.
- For a database on the Linux Docker host, add `--add-host=host.docker.internal:host-gateway`.
- For a database in another container, attach this container to the same explicit Docker network.

Do not expand secret-bearing environment variables in the host shell. Expand them only inside the container's quoted `bash -lc` command.

## Docker Transport Security (MongoDB/Redis)

Verified TLS is preferred but not required. Explicit modes are verified TLS, relaxed encrypted TLS, and plaintext. Do not silently downgrade; state the selected mode and preserve authentication.

- MongoDB: set `tls=false` for plaintext, or set `tls=true`, `tlsAllowInvalidCertificates=true`, and/or `tlsAllowInvalidHostnames=true` in the URI as narrowly as needed.
- Redis: omit `--tls` for plaintext; use `--tls --insecure` for encrypted transport without certificate verification.

Do not disable or bypass authentication unless the user explicitly requests that distinct action and the target is intentionally configured for it.

## Docker Client Selection

- Modern MongoDB: `mongo-connect`
- MongoDB 3.4: `mongo-connect --server-version 3.4`
- Redis: `redis-cli`

Always use `mongo-connect`, not `mongosh` or `mongo-legacy` directly. Do not switch MongoDB clients to work around authentication, DNS, or networking failures. The Dockerfile retains its SQL clients for image compatibility; Codex SQL work uses the Java CLI.

## Docker Read-Only Examples

Modern MongoDB:

```sh
docker run --rm --env-file db.env db-debug:latest bash -lc 'mongo-connect "$MONGODB_URI" --quiet --eval "db.runCommand({ ping: 1 })"'
```

MongoDB 3.4:

```sh
docker run --rm --env-file db.env db-debug:latest bash -lc 'mongo-connect --server-version 3.4 "$MONGODB_URI" --quiet --eval "db.runCommand({ ping: 1 })"'
```

Redis:

```sh
docker run --rm --env-file db.env db-debug:latest bash -lc 'redis-cli -h "$REDIS_HOST" -p "${REDIS_PORT:-6379}" PING'
```

Adapt variable names to the user-provided environment file without exposing their values.

## Mutation Boundary

If the user requests a mutation:

1. Use read-only queries to verify the target and estimate impact.
2. Present the exact mutation and recovery plan.
3. Wait for explicit approval for that exact operation.
4. Execute only the approved SQL statement through the Java CLI with `--mode write`, or the approved MongoDB/Redis command through `db-debug:latest`. Do not replay it automatically.
5. Verify the outcome with a separate read-only query and report it.

If exact approval, target identity, credentials, recovery expectations, or side effects remain unclear, stop and ask the user to decide. Do not use a workaround.
