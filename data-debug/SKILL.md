---
name: data-debug
description: Safely inspect and troubleshoot Oracle, PostgreSQL, MySQL, MongoDB, Redis, or Microsoft SQL Server through the db-debug:latest Docker image. Use for database connectivity checks, metadata inspection, read-only queries, query-plan analysis, or database incident debugging. All database work is read-only by default; mutations require explicit approval for the exact operation.
---

# Data Debug

Use only the `db-debug:latest` image for supported database work. Treat the database, its credentials, and returned data as sensitive.

## Workflow

1. Confirm the target engine, environment, database, and diagnostic question. Resolve ambiguity before connecting to production or another sensitive environment.
2. Verify Docker and the required local image before using any database client:

   ```sh
   docker version
   docker image inspect db-debug:latest
   ```

   If either command fails, stop and report the blocker. Do not pull, build, retag, or substitute an image unless the user explicitly asks for that exact action.
3. If client availability is uncertain, run:

   ```sh
   docker run --rm db-debug:latest bash -lc 'sql -version && sqlplus -v && psql --version && mysql --version && mongosh --version && mongo-legacy --version && redis-cli --version && sqlcmd -? >/dev/null && bcp -v'
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
- Never place connection URIs, passwords, tokens, certificates, or other secrets in chat, source files, shell command arguments, or captured logs. Pass connection settings through a user-provided environment file with `docker run --env-file`.
- Keep environment files outside the repository, restrict their permissions, never print them, and delete temporary credential files after use when their lifecycle is owned by the task.
- Never disable TLS, certificate verification, hostname verification, or authentication checks. Stop and report certificate or network failures instead of bypassing them.
- Always use `--rm`. Do not mount the Docker socket, mount database data directories, use `--privileged`, or add capabilities. Avoid host filesystem mounts unless a user-requested import or export requires a specific path.
- Prefer explicit timeouts supported by the selected client or server. Avoid unbounded scans, full collection reads, keyspace-wide Redis commands, and production query-plan execution that could create material load.
- Do not switch MongoDB clients to work around TLS, authentication, DNS, or networking failures.
- Report the database identity and scope before substantive diagnostics when a wrong-target connection would be risky.

## Connection Pattern

Use:

```sh
docker run --rm --env-file <env-file> db-debug:latest bash -lc '<read-only command>'
```

Network routing:

- For a database on the macOS or Windows Docker host, use `host.docker.internal`.
- For a database on the Linux Docker host, add `--add-host=host.docker.internal:host-gateway`.
- For a database in another container, attach this container to the same explicit Docker network.

Do not expand secret-bearing environment variables in the host shell. Expand them only inside the container's quoted `bash -lc` command.

## Client Selection

- PostgreSQL: `psql`
- MySQL: `mysql`
- Modern MongoDB: `mongo-connect`
- MongoDB 3.4: `mongo-connect --server-version 3.4`
- Redis: `redis-cli`
- Microsoft SQL Server: `sqlcmd`; use `bcp` only for an explicitly requested bulk transfer
- Oracle: prefer `sqlplus`; use `sql` only when SQLcl features are required

Always use `mongo-connect`, not `mongosh` or `mongo-legacy` directly.

## Read-Only Examples

PostgreSQL:

```sh
docker run --rm --env-file db.env db-debug:latest bash -lc 'psql --set ON_ERROR_STOP=1 --command "BEGIN READ ONLY; SELECT current_database(), current_user; COMMIT;"'
```

MySQL:

```sh
docker run --rm --env-file db.env db-debug:latest bash -lc 'mysql --host="$MYSQL_HOST" --port="${MYSQL_PORT:-3306}" --user="$MYSQL_USER" "$MYSQL_DATABASE" --execute "START TRANSACTION READ ONLY; SELECT DATABASE(), CURRENT_USER(); COMMIT;"'
```

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

Microsoft SQL Server:

```sh
docker run --rm --env-file db.env db-debug:latest bash -lc 'sqlcmd -S "$MSSQL_HOST,$MSSQL_PORT" -U "$MSSQL_USER" -d "$MSSQL_DATABASE" -K ReadOnly -Q "SELECT DB_NAME(), SUSER_SNAME();"'
```

Oracle:

```sh
docker run --rm --env-file db.env db-debug:latest bash -lc 'printf "connect %s/%s@%s\nSET TRANSACTION READ ONLY;\nSELECT global_name FROM global_name;\nCOMMIT;\nexit\n" "$ORACLE_USER" "$ORACLE_PASSWORD" "$ORACLE_DSN" | sqlplus -s /nolog'
```

Adapt variable names to the user-provided environment file without exposing their values.

## Mutation Boundary

If the user requests a mutation:

1. Use read-only queries to verify the target and estimate impact.
2. Present the exact mutation and recovery plan.
3. Wait for explicit approval for that exact operation.
4. Execute only the approved operation through `db-debug:latest`.
5. Verify the outcome with a separate read-only query and report it.

If exact approval, target identity, credentials, recovery expectations, or side effects remain unclear, stop and ask the user to decide. Do not use a workaround.
