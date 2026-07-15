# Oracle

## Target, TLS và identity

Port mặc định là `1521`; TLS/TCPS mặc định bật. `--database` bắt buộc và có thể chứa service; nếu có `--service`, adapter ưu tiên nó cho connect string và identity.

```text
agent-db target add --id <id> --engine oracle --environment <env> \
  --host <host> --database <service> [--service <service>] [--port 1521] \
  [--tls true] --expected-server-identity <server-host>
```

TLS tạo connect string `tcps://host:port/service?ssl_server_dn_match=on`. Oracle từ chối `--trust-server-certificate true`; CLI không cho tắt certificate DN matching. Chỉ dùng `--no-tls` khi endpoint thực sự không hỗ trợ TCPS và người dùng chấp nhận transport không mã hóa.

Adapter kiểm tra `SERVICE_NAME`, `CURRENT_USER`, `SERVER_HOST` và server version. Service khớp không phân biệt hoa thường; expected server identity khớp chính xác. `expectedServerIdentity` có thể thiếu cho read nhưng bắt buộc trước mutation.

## Chỉ đọc, schema và budget

Read/inspect chạy `SET TRANSACTION READ ONLY`, verify identity rồi rollback trước khi đóng connection. Schema refresh stream `ALL_TAB_COLUMNS`, tối đa 10.000 row metadata và budget xấp xỉ 8 MiB.

Read dùng result set `fetchArraySize=1`, dừng/đóng cursor khi đạt `max-rows` hoặc `max-output-bytes`. LOB không được đọc vào output: adapter trả type, length nếu biết và `contentOmitted=true`, rồi đóng LOB. Vì vậy không kết luận nội dung LOB từ summary.

`timeout-ms` đặt connect timeout và `connection.callTimeout` cho từng call/round-trip; chuỗi connect + identity + nhiều fetch không có deadline tổng cứng. Không giả định wall-clock luôn nhỏ hơn đúng một `timeout-ms`.

Cấp account read quyền connect/select đúng object/view; không cấp DML, DDL, procedure hay system privilege không cần thiết. Không dùng `NEXTVAL`, locking read, `EXPLAIN PLAN`, hoặc package network/filesystem/coordination trong read mode.

## Mutation

Oracle resolve transaction mode thành `never`; `--transaction always` bị từ chối. Adapter verify lại database/principal/server identity, execute exact SQL với `autoCommit:false`, đóng và đếm mọi returned/implicit result set thay vì xuất dữ liệu, rồi gọi commit. Kết quả chỉ báo `rowsAffected`, `returnedResultSetsDiscarded`, `transactional:false` và cảnh báo implicit commit.

DDL và nhiều lệnh admin Oracle có thể commit ngầm trước/sau statement; không hứa rollback. Nếu driver lỗi sau khi SQL đã gửi, xử lý `MUTATION_OUTCOME_UNKNOWN` bằng truy vấn read-only, không retry. Không nhúng password/user secret trong SQL; dùng workflow secret local của Oracle.
