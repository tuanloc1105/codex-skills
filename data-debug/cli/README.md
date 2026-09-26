# Data Debug SQL CLI

Bundled Java 17+ CLI for Oracle, PostgreSQL, MySQL and SQL Server. MongoDB/Redis remain on `db-debug:latest`. Build needs JDK 17+, Maven and first-resolution network access; runtime needs Java 17+ only. No native SQL clients or Docker required. Pins and build plugins live in [pom.xml](pom.xml).

```sh
mvn -f data-debug/cli/pom.xml clean verify
java -jar /absolute/skill-root/cli/target/data-debug.jar --help
java -jar /absolute/skill-root/cli/target/data-debug.jar --drivers
```

The skill automatically builds a missing JAR from its loaded skill root, then invokes the absolute JAR while keeping the original terminal cwd for queries. Repository maintenance never changes installed skill copies. `target/` is generated/ignored; do not commit or distribute accidental build output as source.

## Configuration privacy

Only the CLI reads `cwd/.env.db`. The agent must never inspect, source, copy or print this file or values. No parent/home/skill-root search; symlink and nonregular configs are rejected. `--list-keys` emits key/duplicate names only; `--check-config` validates mappings and endpoint format without any connection. Help/version/driver discovery need no config.

Dotenv is bounded UTF-8 literal `NAME=value`, optional `export`, surrounding single/double quotes, blank lines and comments. Unquoted `#` starts a comment only after whitespace or at the start; quoted values retain `#`. No interpolation, shell execution or escape expansion. Quotes must close on the same line. Duplicate mapped names fail even when their values agree; unmapped duplicates are reported during discovery. Key names follow `[A-Za-z_][A-Za-z0-9_]{0,127}`. Empty passwords are accepted as supplied; other mapped fields must be nonempty. Config/SQL input caps are each 1 MiB; malformed input produces a code without its contents.

Only key names, engine/mode and bounded limits enter argv. Never pass credential values/URLs as arguments. Arbitrary field names can be mapped:

```sh
java -jar /absolute/skill-root/cli/target/data-debug.jar --list-keys
java -jar /absolute/skill-root/cli/target/data-debug.jar --check-config --engine postgresql --host-key TARGET_HOST --database-key TARGET_DB --user-key TARGET_USER --password-key TARGET_PASSWORD
printf '%s\n' 'SELECT current_database(), current_user;' | java -jar /absolute/skill-root/cli/target/data-debug.jar --engine postgresql --host-key TARGET_HOST --database-key TARGET_DB --user-key TARGET_USER --password-key TARGET_PASSWORD
```

Choose mappings from key names and user context; ask when ambiguous. `--port-key` optional, otherwise 5432/3306/1433/1521 by engine. Oracle requires `--service-key` or `--sid-key` instead of `--database-key`. `--url-key` is exclusive with endpoint field keys; `--user-key`/`--password-key` still required. URLs are restricted to these endpoint-only shapes (port required), reconstructed with enforced policy:

- `jdbc:postgresql://host:port/database`
- `jdbc:mysql://host:port/database`
- `jdbc:sqlserver://host:port;databaseName=database`
- `jdbc:oracle:thin:@[tcp://|tcps://|//]host:port/service` (choose one prefix, not literal brackets).

IPv6 hosts use brackets. Host names/IPs and database/service/SID identifiers are conservative; complex names, descriptors, URL parameters, encoded options, inline credentials, instance names and multi-host URLs fail `TARGET_FORMAT`/`URL_POLICY` rather than silently overriding TLS/auth/timeouts. URL transport is normalized by `--tls`; no URL option overrides. This CLI does not support wallets, external/integrated authentication, SSH tunnels setup or arbitrary vendor connection properties. An externally prepared tunnel can be addressed as a normal host/port.

## SQL and transaction contract

SQL arrives only through stdin. One statement/invocation; optional trailing semicolon/comments. Conservative dialect-aware lexer handles standard quotes, doubled delimiters, SQL Server brackets, MySQL backticks, PostgreSQL dollar quotes and Oracle q quotes. Rejects executable/optimizer comments, nested comments, ambiguous backslash escapes, client batches, procedural statements and unsupported syntax clearly. Default read mode admits SELECT/read CTE, selected SHOW on PostgreSQL/MySQL and nonexecuting EXPLAIN on those engines. Mutating CTE, SELECT INTO, locking reads, EXPLAIN ANALYZE, calls and known unsafe operations are refused. It cannot prove arbitrary function purity; read-only accounts are required for a meaningful security boundary.

PostgreSQL/MySQL use driver-propagated read-only transactions. Oracle executes an internal `SET TRANSACTION READ ONLY`; SQL Server only provides a hint/application intent, so account privileges remain essential. Session controls are separate from the exactly-one user SQL execution. No version-only rejection or newer-server-specific session syntax.

`--mode write` is a capability, not approval. The skill must obtain approval for the exact target/SQL/effect/recovery. DML commits once; failure requests rollback, which does not prove reversal of nontransactional tables or side effects. Oracle/MySQL DDL may auto-commit. Commit failures/timeouts report unknown outcomes. Never automatically reconnect/replay SQL or writes. Verify the actual outcome separately before approving any retry. Procedure calls, transaction-control statements and administration are intentionally unsupported.

## TLS and deadlines

Default `--tls verified` requires encrypted transport and server certificate/identity validation. A certificate/hostname failure permits one automatic `relaxed` encrypted connection retry with the same target/authentication, before user execution only. Auth/network failures do not trigger a downgrade. `--tls relaxed` starts encrypted with certificate/identity validation relaxed. No automatic plaintext fallback or authentication bypass. `--tls plaintext` explicitly disables encryption requirement; SQL Server may still negotiate encryption when required by the server, reported as `plaintext-requested-server-may-encrypt` rather than claiming verified plaintext.

PostgreSQL uses verify-full/require/disable; MySQL VERIFY_IDENTITY/REQUIRED/DISABLED; SQL Server encrypt plus trustServerCertificate. Oracle uses TCPS with per-datasource SSLContext for relaxed trust, never a global JVM trust override. Relaxed connections lose server identity assurance. Verification uses driver-enforced transport properties; no extra server permission/query is required to inspect transport. Server versions are inspected internally without publishing target values.

`--timeout 1..300` (default 10 seconds) bounds the overall JDBC connection/fallback/execution/result/commit lifecycle after input validation. Driver login/socket/query timeouts are also set. Timeout cancels/aborts best-effort; it cannot prove that server work stopped or a write did not commit. SQL is never sent after an interrupted late connection. OS/stdin I/O and server-side work may outlive their client deadlines; there is no promise of bounded server cost.

## Output

UTF-8 JSON stdout: engine, mode, transport, transaction, ddlRecovery, columns (`label`, vendor `type`), row arrays (text representation or null), rowCount and truncated; non-result statements return updateCount. Duplicate labels remain distinct columns. Text cells capped at 4 KiB; rows default100, adjustable `--max-rows 1..10000`; 256 columns maximum; total output at most1 MiB with envelope reservation. Results are streamed from JDBC into a bounded response so errors never leave partially written JSON. Binary and unsupported object/array/XML values are omitted with a marker and `truncated=true`; LOBs are not materialized wholesale. Output caps do not limit server scan cost. Query results may contain sensitive information: summarize minimally; exports require an explicit request.

Errors go to stderr as stable JSON codes with sanitized transaction/transport state; exit2. No raw exception, URL, stacktrace, password or config contents. Missing/nonregular config uses `CONFIG_FILE`; IO/service errors use `IO_OR_DRIVER`; argument/mapping/syntax failures have distinct codes. Duplicate/missing key errors deliberately do not echo names/values. Success exit0. Query values and column names are result data, not credential redaction; avoid selecting secrets.

## Driver compatibility and evidence

Pins were checked against official sources on 2026-09-26. One driver per engine; no runtime dependency download, driver fallback/class collision or legacy duplicate. Selection favors the agreed server range over blindly newest. Java source is compiled with release17.

| Engine | Pinned artifact | Minimum / newer target | Vendor evidence | Real endpoints |
|---|---|---|---|---|
| PostgreSQL | org.postgresql:postgresql:42.7.13 | 12 / 18 | [Download policy](https://jdbc.postgresql.org/download/) says Java8+; releases since42.7.4 do not guarantee servers below9.1 | Not run |
| MySQL | com.mysql:mysql-connector-j:9.7.0 | 8.0 / 9.7 | [Exact9.7 release](https://dev.mysql.com/doc/relnotes/connector-j/en/news-9-7-0.html) explicitly8.0+; Java8+ platform.26.7 generic overview conflicts with [compatibility page](https://dev.mysql.com/doc/connector-j/en/connector-j-versions.html), so9.7 selected for8.0 | Not run |
| SQL Server | com.microsoft.sqlserver:mssql-jdbc:13.4.0.jre11 | 2016 / 2025 | [13.4 release](https://learn.microsoft.com/en-us/sql/connect/jdbc/release-notes-for-the-jdbc-driver) Java17; [support matrix](https://learn.microsoft.com/en-us/sql/connect/jdbc/microsoft-jdbc-driver-for-sql-server-support-matrix?view=sql-server-ver17) supported drivers cover supported SQL releases;2016 remains the agreed compatibility target; standard [extended support ended July2026](https://learn.microsoft.com/en-us/lifecycle/products/sql-server-2016) (ESU separate), so current driver matrix alone does not certify it | Not run |
| Oracle | com.oracle.database.jdbc:ojdbc17:23.26.3.0.0 | 19c / 26ai | [Exact26ai23.26.3 download](https://www.oracle.com/database/technologies/appdev/jdbc-downloads.html) lists19c/21c/23ai/26ai and JDK17 | Not run |

Minimum targets are implementation goals, not a fabricated real-server certification. SQL Server2016's lifecycle is distinct from protocol compatibility; no promise of current vendor support for an expired server. Package service discovery and fake adapter tests exercise four drivers/policies, not real auth/TLS/writes. Older targets may be tried best-effort without a minimum-version check; future releases/new syntax/data types not automatically supported. Oracle TLS especially needs real endpoint verification. Driver licenses/notices are copied into artifact-specific `META-INF/dependency-notices/` before shading (including Microsoft MIT from its13.4 source tag); dependencies retain their own licensing (MySQL GPLv2 with Universal FOSS Exception, PostgreSQL BSD, Microsoft MIT, Oracle FUTC).

## Verification

```sh
mvn -f data-debug/cli/pom.xml clean verify
python3 ~/.codex/skills/.system/skill-creator/scripts/quick_validate.py ./data-debug
git diff --check
```

Core/JDBC unit tests use literal temporary fixtures and injected JDBC proxies. Packaged tests run the actual shaded JAR from a different cwd, check privacy/error JSON, four driver services and Java17 bytecode. No agent reads a real `.env.db`; no live database writes, Docker pull/build or production connection is part of repository checks.
