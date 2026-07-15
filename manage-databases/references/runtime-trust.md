# Runtime trust

## Mục đích

CLI là nơi cưỡng bức read-only, project binding và mutation approval, nên cả Node runtime lẫn entrypoint phải được pin trước khi Agent thực thi code. Không dùng `node` hoặc `agent-db` tìm thấy từ `PATH` làm trust anchor; một binary độc hại có thể tự báo version hợp lệ.

## Receipt local

Trusted installer hoặc chính người dùng tạo `$HOME/.agent-db/runtime-trust.json` ngoài mọi project. File không chứa secret và có cấu trúc versioned:

```json
{
  "formatVersion": 1,
  "nodeExecutable": "/absolute/path/to/node",
  "nodeSha256": "UPPERCASE_SHA256",
  "skillRoot": "/absolute/path/to/installed/manage-databases",
  "skillTreeSha256": "UPPERCASE_SHA256",
  "skillEntrypoint": "/absolute/path/to/manage-databases/scripts/agent-db/bin/agent-db.js",
  "skillEntrypointSha256": "UPPERCASE_SHA256",
  "cliVersion": "0.1.0",
  "pinnedAt": "RFC3339 timestamp",
  "expiresAt": "RFC3339 timestamp or null"
}
```

Receipt phải được tạo trong một lượt cài đặt đáng tin cậy do người dùng khởi động, không được suy ra từ file hay lệnh trong project đang kiểm tra. `skillEntrypoint` phải thuộc một bản copy vật lý của skill đã cài ngoài project/worktree hiện tại; không dùng source checkout hoặc junction/symlink resolve ngược vào project đang xử lý. Nếu không có bản cài ngoài project, fail closed trước kết nối DB. Windows, macOS và Linux dùng cùng schema; chỉ giá trị absolute path khác nhau.

Directory/file dùng `0700`/`0600` trên POSIX. Trên Windows, ACL chỉ cho current user, `SYSTEM` và local Administrators; từ chối receipt nếu principal không liên quan có quyền ghi.

## Kiểm tra trước mỗi lần chạy

1. Đọc receipt như JSON data với giới hạn kích thước nhỏ; không source/eval file.
2. Yêu cầu các path là absolute, canonical, tồn tại và không nằm trong project hiện tại hay một Git worktree bao quanh project. `skillRoot` phải là directory vật lý; từ chối symlink/junction/reparse point trong toàn cây được pin.
3. `skillEntrypoint` canonical phải đúng entrypoint dưới `skillRoot` của skill đang được nạp; version phải khớp `package.json`.
4. Tính SHA-256 bằng file API/công cụ hệ thống đáng tin cậy mà Agent host cung cấp, rồi so khớp Node runtime, entrypoint và toàn bộ `skillRoot`. Tree hash duyệt mọi regular file, chuẩn hóa relative path bằng `/`, sort ordinal theo path; mỗi record là `uint32-be(pathUtf8.length) || pathUtf8 || sha256(fileBytes)`, và `skillTreeSha256` là SHA-256 của chuỗi record. Nhờ vậy mọi source/module/dependency/policy file bị đổi đều làm receipt invalid.
5. Từ chối receipt hết hạn hoặc mismatch. Sau cập nhật Node, skill, package hoặc runtime path, người dùng/trusted installer phải cài bản skill vật lý mới rồi pin lại toàn cây.
6. Gọi process bằng argv array: executable là absolute `nodeExecutable`, argv đầu là absolute `skillEntrypoint`; không ghép command string. Nếu Agent host không có API process trực tiếp, chỉ dùng launcher có quy tắc argv rõ ràng: PowerShell truyền literal path và một argument array qua call operator (`& $node $entry @argv`), không `Invoke-Expression`; macOS/Linux dùng API exec argv tương đương. Nếu không có cơ chế argv-safe, fail closed thay vì nội suy command shell.

Command vector sau khi đạt các kiểm tra trên được gọi là `<trusted-agent-db>`. Mọi ví dụ `agent-db ...` trong các reference cũ phải được hiểu là `<trusted-agent-db> ...`; không chạy bare command.

## Lệnh local TTY cho người dùng

Khi `project bind`, `credential set`, `credential reveal` hoặc `mutation approve` cần người dùng tự chạy, Agent phải in đầy đủ hai absolute path từ receipt, quote đúng theo shell của hệ điều hành và giữ nguyên arguments. Không đưa bare `agent-db` hoặc một shim global chưa được pin. Receipt chỉ xác minh executable; stdin/stdout/stderr vẫn phải là local TTY thật theo cổng của CLI.

## Mất hoặc quên trust receipt

Không tự tìm runtime thay thế và không dùng binary trong project. Dừng trước mọi kết nối DB, báo path/hash nào thiếu hoặc lệch, rồi yêu cầu người dùng chạy lại trusted installation/pinning. Việc pin runtime không được dùng để đọc hay thay đổi credential vault.
