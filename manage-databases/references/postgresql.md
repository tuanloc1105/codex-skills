# PostgreSQL

## Target, TLS và identity

Port mặc định là `5432`; TLS mặc định bật và certificate verification bật mặc định.

```text
agent-db target add --id <id> --engine postgresql --environment <env> \
  --host <host> --database <db> [--port 5432] \
  [--tls true] [--trust-server-certificate false] \
  --expected-server-identity <server-address>
```

Adapter kiểm tra `current_database()`, `current_user`, `inet_server_addr()` (hoặc `local`) và `version()`. Database/expected server address khớp chính xác; expected identity bắt buộc trước mutation. Không bật `trust-server-certificate` cho production vì nó đặt `rejectUnauthorized=false`.

## Chỉ đọc, schema và budget

Read mở `BEGIN READ ONLY`, đặt `SET LOCAL statement_timeout`, verify identity, đọc cursor từng row rồi rollback. Cursor dừng/đóng khi đạt `max-rows` hoặc budget xấp xỉ 8 MiB và trả `truncationReason`.

Schema refresh đọc `information_schema.columns`, đánh dấu primary-key columns, bỏ `pg_catalog`/`information_schema`, lấy tối đa 10.001 rows và xuất tối đa 10.000 để phát hiện truncation.

Connection có `connectionTimeoutMillis`; statement timeout bảo vệ schema/read query sau khi được đặt. Connect, identity và query là nhiều pha nên `timeout-ms` không phải deadline wall-clock tổng. Account read vẫn phải chỉ có CONNECT/USAGE/SELECT/VIEW cần thiết; `BEGIN READ ONLY` không thay thế least privilege.

Read guard chặn `nextval`, locking reads, hàm PostgreSQL admin/state-changing đã biết và `EXPLAIN ANALYZE`. Không chạy function chưa chứng minh không side effect bằng credential có quyền ghi.

## Mutation và transaction mode

- `auto` resolve thành `never` cho `CREATE/DROP DATABASE`, `CREATE/DROP TABLESPACE`, `ALTER SYSTEM`, `VACUUM`, thao tác `CONCURRENTLY`, `CALL`, `DO` và SQL điều khiển transaction; các mutation khác thành `always`.
- `always` mở transaction, đặt `SET LOCAL statement_timeout`, commit khi thành công và rollback nếu lỗi trước khi bắt đầu commit.
- `never` không mở transaction và đặt session `statement_timeout` trước exact SQL.

Mode đã resolve nằm trong approval hash. Adapter verify lại database/principal/server identity trước operation. Mutation stream nhưng discard mọi returned row; nó báo metadata tối đa 1.000 statements, `statementCount`, `statementsTruncated` và `returnedRowsDiscarded`, không dump `RETURNING` data.

Khi operation đã gửi hoặc commit đã bắt đầu, driver error được nâng thành `MUTATION_OUTCOME_UNKNOWN`; không retry. Dù mode `always` báo `transactional:true`, lỗi kết nối quanh commit vẫn cần xác minh read-only. Không nhúng role password/secret vào SQL preview.
