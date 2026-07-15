# SQL Server

## Target, encryption và identity

Port mặc định là `1433`; `encrypt=true` và `trustServerCertificate=false` theo mặc định.

```text
agent-db target add --id <id> --engine sqlserver --environment <env> \
  --host <host> --database <db> [--port 1433] \
  [--encrypt true] [--trust-server-certificate false] \
  --expected-server-identity <server-name>
```

Ưu tiên `--encrypt`; không dùng `--tls` để thay thế cấu hình SQL Server. Chỉ bật `trustServerCertificate` sau đánh giá rõ ràng, vì nó bỏ kiểm tra trust chain/name của certificate.

Adapter kiểm tra `DB_NAME()`, `SYSTEM_USER`, `SERVERPROPERTY('ServerName')` và product version. Database/expected server identity khớp chính xác; expected identity bắt buộc trước mutation.

## Chỉ đọc, schema và budget

Schema refresh stream tối đa 10.000 dòng từ `sys.tables`, `sys.schemas`, `sys.columns`, `sys.types`; query dùng `TOP (10001)` để phát hiện truncation. Read stream rows và cancel request khi đạt `max-rows` hoặc budget xấp xỉ 8 MiB; `ECANCEL` do chính budget được coi là kết thúc có `truncated=true`, không phải database failure.

`timeout-ms` áp riêng cho connection và từng request. Identity và query là các request nối tiếp nên tổng wall-clock có thể lớn hơn một timeout. SQL Server adapter không mở transaction read-only: account read phải chỉ có `SELECT`/`VIEW DEFINITION` cần thiết, không có DML/DDL/EXECUTE/server role mạnh.

Read guard chặn statement admin, `SELECT INTO`, sequence, multi-statement và locking hints `UPDLOCK`, `XLOCK`, `TABLOCKX`, `HOLDLOCK`. Bộ phân loại vẫn không thay thế least privilege.

## Mutation

Transaction mode resolve thành `never`; `--transaction always` bị từ chối. Adapter không tự mở transaction. Nếu payload tự chứa transaction statements, toàn bộ batch phải xuất hiện trong exact preview nhưng kết quả vẫn báo `transactional:false` vì CLI không quản lý transaction đó.

Mutation stream và discard returned rows, chỉ trả `rowsAffected` tối đa 1.000 entries, `rowsAffectedTruncated` và `returnedRowsDiscarded`. Nó verify lại database/principal/server identity trước khi gửi batch. Lỗi sau khi operation được gửi trả `MUTATION_OUTCOME_UNKNOWN`; không retry hoặc hứa rollback cho DDL/admin.

Không nhúng login password vào SQL preview. Với tạo/đổi login, dùng workflow secret local phù hợp.
