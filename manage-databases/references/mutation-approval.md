# Protocol phê duyệt mutation

## Điều kiện bắt đầu

Chỉ chuẩn bị mutation khi yêu cầu hiện tại của người dùng mô tả thay đổi cụ thể trên target cụ thể. Quyền DBA, blanket approval, câu “cứ làm đi”, hoặc phrase gửi trong chat không thay thế cổng local TTY.

Redis v1 chỉ hỗ trợ read/debug; không tạo plan, approval hay execute mutation cho Redis.

Mutation bao gồm mọi thay đổi data, schema, index, user/role/grant, cấu hình, procedure, job, maintenance và administrative command. Target phải có `expectedServerIdentity` và credential mutation riêng. Payload có dấu hiệu chứa secret bị chặn bằng `SECRET_IN_OPERATION`; không preview password/token/private key qua chat/tool output.

## Bước 1: Prepare

Agent được chạy:

```text
agent-db mutation prepare --target <id> (--file <path>|--text <value>|--stdin) \
  [--transaction <auto|always|never>] [--timeout-ms <ms>]
```

Prepare kết nối bằng credential mutation, xác minh database/principal/server identity, phân loại operation và resolve transaction mode trước khi tạo plan. Plan AES-GCM có TTL 5 phút và khóa:

- Project ID cùng `bindingRevision`.
- Target ID, đầy đủ target fingerprint, engine và environment.
- Mutation credential ID.
- Exact raw payload cùng SHA-256 operation hash.
- Verified `database`, `principal`, `serverIdentity` và metadata identity.
- Operation type, transaction mode, created/expiry time.

`approvalHash` bao phủ toàn bộ approval surface trên; confirmation phrase dùng 12 ký tự đầu của approval hash, không chỉ operation hash.

## Bước 2: Trình bày preview

Trước khi yêu cầu approval, Agent trình bày:

- Project ID/name, `bindingRevision`, environment, target ID/fingerprint và engine.
- Verified database, principal và server identity.
- Operation type/hash, approval hash và `operationPreview.exact` nguyên văn.
- Transaction mode đã resolve, `expiresAt` và cảnh báo implicit commit/outcome phù hợp engine.
- Lệnh local `mutation approve` với đúng target/plan.

Không tóm tắt thay exact preview. Nếu payload cần secret, cancel plan và chuyển phần secret sang workflow database-native chạy hoàn toàn local.

## Bước 3: Người dùng approve trên local TTY

Chính người dùng chạy từ terminal local tại đúng project:

```text
agent-db mutation approve --target <id> --plan <uuid>
```

CLI yêu cầu stdin, stderr và stdout TTY; in exact payload cùng metadata dưới dạng terminal-safe JSON string encoding; sau đó người dùng gõ phrase `MUTATE <target-id> <approval-hash-prefix>`. Phrase chỉ chứa target ID đã validate và hash, không chứa project/environment metadata tự do.

Agent tuyệt đối không:

- Chạy `mutation approve` qua tool hoặc subagent.
- Cấp/mô phỏng pseudo-terminal.
- Capture hay redirect output approval.
- Gọi trực tiếp `PendingStore`/module nội bộ.
- Tự tạo hoặc chỉnh approval artifact.
- Coi phrase người dùng gửi trong chat là approval.

Approval tạo receipt AES-GCM riêng, scope theo plan/project/target/approval hash và chứa binding revision, target fingerprint, credential ID, thời điểm approve cùng expiry đúng bằng plan. Receipt plaintext giả hoặc receipt của plan khác không hợp lệ.

Sau khi người dùng báo hoàn tất, Agent chạy:

```text
agent-db mutation show --target <id> --plan <uuid>
```

Chỉ tiếp tục khi `approval.approved=true`, plan/receipt còn hạn và mọi preview field vẫn khớp.

## Bước 4: Execute đúng một lần

Agent chạy, không có `--confirm`:

```text
agent-db mutation execute --target <id> --plan <uuid> [--timeout-ms <ms>]
```

Execute giữ registry/manifest/plan locks, kiểm tra lại binding revision, target fingerprint, mutation credential, payload/approval hashes và receipt. Plan cùng receipt được consume one-time trước database call. Adapter kết nối lại, yêu cầu `database`, `principal`, `serverIdentity` khớp identity đã preview, rồi kiểm expiry thêm lần cuối ngay trước khi gửi operation.

Schema cache bị invalid trước khi gửi mutation, kể cả lần execute sau đó lỗi. Sau thành công hoặc khi cần xác minh lỗi, refresh cache bằng credential read.

Không retry execute. Nếu driver lỗi sau khi operation có thể đã được gửi, CLI trả `MUTATION_OUTCOME_UNKNOWN`; plan/receipt đã bị consume. Tuyệt đối không prepare lại cùng mutation. Dùng truy vấn read-only để xác minh trạng thái và báo sự không chắc chắn. Chỉ tạo plan mới sau khi người dùng đã xem trạng thái thực tế và yêu cầu một hành động khắc phục mới, cụ thể; hành động mới cần approval mới.

## Cancel và thay đổi

Với active plan còn hợp lệ, chạy:

```text
agent-db mutation cancel --target <id> --plan <uuid>
```

Cancel giữ plan lock, atomically rename plan ra khỏi namespace khả dụng rồi xóa cả plan và approval receipt. Plan đã cancel không execute được. Không xóa/chỉnh file pending thủ công.

Cancel và prepare lại khi payload, target, identity, transaction mode hoặc yêu cầu đổi dù chỉ một ký tự. Project rebind, target/credential đổi, plan hết 5 phút, receipt mismatch hay plan đã consume đều cần plan và approval mới.

## Transaction mode

- `auto`: PostgreSQL chọn `never` cho `CREATE/DROP DATABASE`, `CREATE/DROP TABLESPACE`, `ALTER SYSTEM`, `VACUUM`, thao tác `CONCURRENTLY`, `CALL`, `DO` và SQL điều khiển transaction; các PostgreSQL mutation khác chọn `always`. Oracle, SQL Server và MongoDB chọn `never`.
- `always`: chỉ hỗ trợ PostgreSQL; adapter mở transaction, đặt `SET LOCAL statement_timeout`, commit khi thành công và rollback khi lỗi trước commit.
- `never`: không mở transaction do adapter; PostgreSQL đặt session `statement_timeout`. Oracle, SQL Server và MongoDB luôn execute theo mode này.

Transaction mode nằm trong approval hash và không thể đổi ở execute. Dù PostgreSQL trả `transactional: true`, lỗi kết nối lúc/ sau commit vẫn có thể làm outcome không chắc chắn. Oracle DDL/admin có implicit commit; SQL Server không tự bọc transaction; MongoDB adapter không mở multi-document transaction.
