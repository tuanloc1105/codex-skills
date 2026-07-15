# Hợp đồng CLI `agent-db`

## Cách gọi

Yêu cầu Node.js `>=20.19.0`. Ưu tiên executable global `agent-db`. Nếu chưa cài global, gọi trực tiếp:

```text
node <skill-dir>/scripts/agent-db/bin/agent-db.js <command> [options]
```

Chỉ cài global khi người dùng đã cho phép thay đổi môi trường máy:

```text
npm install -g <skill-dir>/scripts/agent-db
```

Chạy `agent-db doctor` trước để kiểm tra Node, bốn driver database, OS keyring và project hiện tại.

## Đầu ra

Mọi lệnh thông thường ghi đúng một JSON object lên stdout:

```json
{"ok":true,"command":"read","context":{},"data":{},"warnings":[]}
```

Lỗi cũng ở dạng JSON với `ok: false` và `error.code`. Không parse thông báo tự do khi đã có mã lỗi. `credential reveal` là ngoại lệ duy nhất: lệnh chỉ chạy trên local TTY và in secret trực tiếp cho người dùng. `project bind`, `credential set` và `mutation approve` cũng yêu cầu local TTY, nhưng vẫn trả metadata JSON sau khi hoàn tất. Agent không được tự chạy bốn lệnh tương tác này, cấp PTY, capture output hay gọi module nội bộ để lách cổng.

Không ghi credential, vault passphrase hoặc nội dung nhạy cảm vào log chẩn đoán. Không chuyển output của `credential reveal` qua tool, pipe, redirect hay capture.

## Lệnh cấu hình và kiểm tra

```text
agent-db --help
agent-db --version
agent-db doctor

agent-db project init --name <name>
agent-db project list
agent-db project show
agent-db project bind --id <project-uuid>

agent-db target add --id <id> --engine <oracle|mongodb|sqlserver|postgresql> \
  --environment <env> --host <host> --port <port> --database <db-or-service> \
  [--expected-server-identity <value>]
agent-db target list
agent-db target show --target <id>
agent-db target test --target <id> [--mode <read|mutation>] [--timeout-ms <ms>]
```

`target add` còn hỗ trợ:

- `--service <service>` cho Oracle.
- `--namespace <name>` lặp lại hoặc phân cách bằng dấu phẩy; hiện được cưỡng chế cho MongoDB collection.
- `--tls`, `--encrypt`, `--trust-server-certificate` nhận `true|false` hoặc dạng `--no-...`.
- `--auth-source <db>` cho MongoDB.
- `--expected-server-identity <value>` để khóa identity của server/cluster; bắt buộc trước mọi mutation.

TLS mặc định bật cho Oracle, MongoDB và PostgreSQL. SQL Server mặc định `encrypt=true`; mọi engine mặc định `trust-server-certificate=false`. Oracle từ chối hoàn toàn `trust-server-certificate=true`; MongoDB adapter không cung cấp cơ chế bỏ kiểm tra certificate qua flag này. Target ID phải khớp `^[a-z0-9][a-z0-9._-]{0,63}$`.

## Credential và schema

```text
agent-db credential status --target <id> [--mode <read|mutation>]
agent-db credential set --target <id> [--mode <read|mutation>] [--username <name>]
agent-db credential reveal --target <id> [--mode <read|mutation>]

agent-db schema refresh --target <id> [--timeout-ms <ms>]
agent-db schema show --target <id>
```

Mode mặc định là `read`. `credential set` yêu cầu local TTY, nhập secret hai lần, kiểm tra kết nối/identity trước khi mã hóa và lưu. Credential được khóa bằng AAD gồm cả target fingerprint. `schema refresh` luôn dùng credential read; cache schema được mã hóa, khóa theo project binding revision, target fingerprint và read credential ID, rồi hết hạn sau 24 giờ.

## Read

```text
agent-db read --target <id> --file <path> [--max-rows <n>] [--timeout-ms <ms>]
agent-db read --target <id> --text <value> [--max-rows <n>] [--timeout-ms <ms>]
agent-db read --target <id> --stdin [--max-rows <n>] [--timeout-ms <ms>]
```

Chọn đúng một trong `--file`, `--text`, `--stdin`; input UTF-8 tối đa 1 MiB. Mặc định `max-rows=100`, `timeout-ms=15000`; giới hạn hợp lệ lần lượt là `1..10000` và `1000..300000`. Payload kết quả database có budget JSON xấp xỉ 8 MiB; chuỗi/binary trên 64 KiB được tóm tắt, và `truncated` cùng `truncationReason` cho biết giới hạn dòng hay byte. Ưu tiên `--file` cho SQL/JSON dài và trên Windows để tránh lỗi quoting.

`timeout-ms` được adapter áp vào connection, request, statement hoặc call tùy driver; không phải hard wall-clock cho toàn bộ lệnh nhiều pha. MongoDB `schema refresh` là ngoại lệ có deadline tổng xuyên suốt identity/collections/indexes. Khi mutation timeout hoặc lỗi sau khi đã gửi operation, xử lý `MUTATION_OUTCOME_UNKNOWN` bằng truy vấn read-only xác minh trạng thái; không tự retry.

## Mutation và audit

```text
agent-db mutation prepare --target <id> (--file <path>|--text <value>|--stdin) \
  [--transaction <auto|always|never>] [--timeout-ms <ms>]
agent-db mutation show --target <id> --plan <uuid>
agent-db mutation approve --target <id> --plan <uuid>
agent-db mutation cancel --target <id> --plan <uuid>
agent-db mutation execute --target <id> --plan <uuid> [--timeout-ms <ms>]

agent-db audit list [--target <id>] [--limit <n>]
```

`mutation prepare` mặc định `--transaction auto`: PostgreSQL resolve thành `always` hoặc `never` theo statement; ba engine còn lại resolve thành `never`. `always` chỉ được hỗ trợ cho PostgreSQL. Transaction mode đã resolve nằm trong approval hash và không thể đổi lúc execute.

`mutation approve` là cổng người dùng: phải được chính người dùng chạy trong terminal local của đúng project. CLI hiển thị exact preview bằng terminal-safe JSON string encoding, yêu cầu phrase gắn với approval hash, rồi tạo approval receipt AES-GCM riêng. Agent không được gọi lệnh này, cấp pseudo-terminal, gọi module nội bộ hoặc tự tạo receipt. `execute` không nhận phrase/`--confirm`; nó consume one-time plan và receipt còn hạn dưới lock, kiểm hạn lại ngay trước lúc driver gửi operation, rồi chạy đúng một lần. `cancel` khóa plan, atomically rename plan ra khỏi namespace khả dụng và xóa cả plan lẫn receipt.

Plan và receipt dùng chung hạn 5 phút. Audit mặc định trả 50 bản ghi, tối đa 1000, và ghi metadata/hashes thay vì credential hay raw query. Mutation execute vẫn thành công nếu chỉ ghi audit thất bại, nhưng trả warning `AUDIT_WRITE_FAILED`.

## Mã lỗi cần xử lý rõ ràng

- `PROJECT_CONTEXT_REQUIRED`, `PROJECT_BINDING_MISMATCH`, `PROJECT_BINDING_CONFLICT`, `PROJECT_MARKER_CONFLICT`, `PROJECT_MARKER_INVALID`: dừng; để người dùng kiểm tra marker và tự chạy bind local-TTY nếu thật sự cần.
- `TARGET_NOT_FOUND`, `TARGET_IDENTITY_MISMATCH`, `TARGET_IDENTITY_REQUIRED`, `TARGET_BINDING_TAMPERED`: không thử target khác hay sửa fingerprint theo suy đoán.
- `CREDENTIAL_REQUIRED`, `VAULT_LOCKED`, `CREDENTIAL_SCOPE_MISMATCH`: xử lý vault/credential local, không yêu cầu secret qua chat.
- `LOCAL_TTY_REQUIRED`, `USER_CONFIRMATION_REQUIRED`: người dùng phải tự hoàn thành cổng tương tác; Agent không mô phỏng TTY.
- `MUTATION_CONFIRMATION_REQUIRED`, `MUTATION_APPROVAL_REQUIRED`, `READ_ONLY_VIOLATION`: coi input là mutation/thiếu approval hoặc không chắc chắn; không bypass cổng.
- `SECRET_IN_OPERATION`: không preview payload; chuyển phần secret sang workflow database-native chạy local.
- `PLAN_NOT_FOUND`, `PLAN_EXPIRED`, `PLAN_CHANGED`, `PLAN_ALREADY_USED`, `APPROVAL_CHANGED`: prepare lại và xin approval mới.
- `SCHEMA_CACHE_MISSING`, `SCHEMA_CACHE_EXPIRED`, `SCHEMA_CACHE_MISMATCH`: refresh bằng credential read sau khi xác minh target.
- `INPUT_TOO_LARGE`, `INPUT_TOO_COMPLEX`, `OUTPUT_TOO_LARGE`, `NAMESPACE_NOT_ALLOWED`, `UNSUPPORTED_OPERATION`: thu nhỏ input/query/result hoặc sửa target hợp lệ; không bypass guard 1 MiB/8 MiB.
- `LOCK_TIMEOUT`, `STALE_LOCK`: không xóa lock mù quáng; kiểm tra process và trạng thái artifact trước.
- `DATABASE_TIMEOUT`, `DATABASE_ERROR`: báo lỗi đã được redact; không in object lỗi driver thô nếu có nguy cơ chứa secret.
- `MUTATION_OUTCOME_UNKNOWN`: operation đã có thể tới database; không retry, chỉ xác minh bằng credential read và yêu cầu plan/approval mới cho bước tiếp theo.
