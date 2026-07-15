# Ràng buộc project và target

## Vị trí trạng thái

CLI lưu trạng thái ngoài repository tại `$HOME/.agent-db` theo mặc định; có thể đổi root bằng `AGENT_DB_HOME` cho test hoặc môi trường biệt lập.

```text
$HOME/.agent-db/
├── registry.json
├── vault-format.json
├── projects/<project-uuid>/manifest.json
├── projects/<project-uuid>/schema/<target-id>.json.enc
├── vault/<credential-uuid>.json.enc
├── pending/<plan-uuid>.json.enc
├── pending/<plan-uuid>.approval.json.enc
└── audit/
```

Registry, manifest và target metadata không nằm trong Git. Credential, schema cache, mutation plan và approval receipt được mã hóa. Dù manifest không chứa password, vẫn xem endpoint metadata là thông tin nội bộ và không đăng vào chat nếu không cần.

## Nhận diện project

Binding là hybrid, không dựa vào một tên thư mục đơn lẻ. Registry lưu project UUID, canonical root, SHA-256 fingerprint của filesystem identity (`device`, `inode`, `birthtime`), fingerprint của normalized `remote.origin.url` nếu có Git, marker path, `bindingMarker` và `bindingRevision` UUID.

Trong Git repository, marker `agent-db-project.json` nằm trong Git directory (thường là `.git/`, không phải worktree). Ngoài Git, marker `.agent-db-project.json` nằm tại project root. Marker chỉ chứa `projectId`, `bindingMarker`, `bindingRevision` và format version; các giá trị phải khớp registry. Writer đặt marker mode `0600` trên POSIX nhưng không thay đổi permission của project root hay Git directory đang tồn tại.

Git remote được normalize, loại username/password/query/fragment trước khi hash. CLI chỉ dùng executable Git tuyệt đối tìm từ `PATH`, bỏ qua binary nằm ở bất kỳ đâu bên trong enclosing Git worktree kể cả khi chạy từ thư mục con, loại toàn bộ biến `AGENT_DB_*` và `GIT_*` khỏi subprocess, tắt prompt Git, và chỉ đọc remote bằng `git config --local`. Khi resolve, root, filesystem fingerprint, marker path/contents và remote fingerprint đều phải khớp. Ngoài Git, thư mục con chỉ tự khớp khi có đúng một project ancestor và marker/fingerprint của root vẫn hợp lệ.

Mỗi `project bind` tạo `bindingRevision` và `bindingMarker` mới, ghi marker ở destination, cập nhật root/fingerprints, rồi xóa marker cũ chỉ khi nó còn khớp. Revision mới làm plan mutation và schema cache cũ không còn hợp lệ.

`project bind` là cổng local TTY. Khi repository được di chuyển/clone, Agent chỉ được chạy `project list`, xác minh UUID với người dùng và đưa lệnh; chính người dùng chạy từ root mới:

```text
agent-db project bind --id <project-uuid>
```

CLI yêu cầu gõ chính xác `BIND <project-name> <project-uuid> TO THIS PROJECT`. Agent không chạy bind qua tool/PTY/module nội bộ và không bind chỉ để bỏ qua mismatch.

## Tạo project và target

```text
agent-db project init --name <name>
agent-db target add --id <id> --engine <engine> --environment <env> \
  --host <host> --port <port> --database <database-or-service> [engine-options]
```

Mỗi target thuộc đúng một project manifest. Luôn dùng ID mô tả rõ environment, ví dụ `dev-orders-ro` hoặc `prod-billing`; không dùng ID mơ hồ như `db1`. Target ID là bất biến trong CLI hiện tại; nếu cấu hình sai, dừng và sửa code/config có kiểm soát thay vì dùng target sai.

Target fingerprint là SHA-256 của JSON canonical gồm toàn bộ `id`, `engine`, `environment`, connection (`host`, `port`, `database`, Oracle `service`, TLS/encrypt/trust policy, MongoDB `authSource`), ordered namespace allowlist và `expectedServerIdentity`. Nó không chứa credential ID hay timestamp. Manifest được recompute khi đọc; mismatch trả `TARGET_BINDING_TAMPERED`.

Credential AAD, mutation plan/receipt và schema cache đều khóa theo target fingerprint. Đổi bất kỳ thành phần binding nào làm credential cũ scope-mismatch, plan/cache cũ invalid; không sửa hash thủ công để tái sử dụng.

## Checklist trước mỗi thao tác

Chạy:

```text
agent-db project show
agent-db target show --target <id>
```

Đối chiếu:

1. Project UUID, tên, root và `bindingRevision`.
2. Target ID và environment, đặc biệt `prod`.
3. Engine, host, port, database hoặc Oracle service.
4. Target fingerprint.
5. Trạng thái credential đúng mode.
6. `expectedServerIdentity`; giá trị này bắt buộc trước mọi mutation.

Sau khi kết nối, adapter kiểm tra database/service thực tế và server identity đã cấu hình. Mutation prepare còn kiểm tra bằng credential mutation, lưu `database`, `principal`, `serverIdentity` đã verified vào approval surface; execute yêu cầu ba giá trị này vẫn khớp. Mismatch là lỗi dừng, không phải cảnh báo.

## Namespace

`--namespace` hiện là hard allowlist cho MongoDB collection và lọc schema MongoDB. Không dựa vào option này để giới hạn SQL schema/table; với Oracle, SQL Server và PostgreSQL, cưỡng chế phạm vi bằng grants/views của account read và câu query cụ thể.

Schema cache có TTL 24 giờ và AAD gồm project ID, `bindingRevision`, target ID/fingerprint và read credential ID. Refresh cache sau khi hết hạn, đổi credential/binding, hoặc trước mutation; execute invalidates cache trước khi gửi mutation nên cả kết quả lỗi cũng cần refresh lại khi muốn đọc schema.
