# Credential vault đa nền tảng

## Quy tắc vận hành

- Lưu credential dưới `$HOME/.agent-db`, không lưu trong repository hoặc file `.env` của project.
- Tạo riêng credential `read` và `mutation` cho từng project-target-engine.
- Nhập secret qua prompt local TTY của `credential set`; không truyền secret bằng option CLI.
- Không yêu cầu hoặc lặp lại secret trong chat/tool output.
- Chỉ dùng `credential reveal` khi chính người dùng cần xem lại secret trên terminal local.

## Envelope encryption

Mỗi vault có data-encryption key ngẫu nhiên 32 byte. Credential, schema cache và pending plan được mã hóa bằng AES-256-GCM với:

- IV ngẫu nhiên 12 byte.
- Authentication tag 16 byte.
- Ciphertext, IV và tag mã hóa Base64.
- AAD là JSON của scope đã sắp xếp key, luôn thêm `formatVersion: 1`.

Scope credential gồm `credentialId`, `projectId`, `targetId`, `targetFingerprint`, `engine`, `mode` và `kind: credential`. Vì scope nằm trong AAD và được kiểm tra trước giải mã, không thể tráo credential giữa project, target, cấu hình endpoint, engine hay mode mà không lỗi integrity/scope. Khi target fingerprint đổi, phải thiết lập lại credential cho binding mới.

Schema cache, mutation plan và approval receipt cũng dùng envelope/AAD riêng. Receipt có scope `mutation-approval` gắn `planId`, project, target và `approvalHash`; nó không phải file cờ plaintext có thể tự tạo.

## Bảo vệ vault key

CLI ưu tiên `@napi-rs/keyring`, tức backend OS-native của user đang chạy:

- Windows: Windows Credential Manager/credential vault của hệ điều hành.
- macOS: Keychain.
- Linux: Secret Service/keyring backend mà session desktop cung cấp.

Kiểm tra backend thực tế bằng `agent-db doctor`. Trong `vault-format.json`, protector `os-keyring` ghi:

- service: `codex-agent-db`
- account: `vault:<vaultId>`
- backend đã dùng

Ciphertext trong `$HOME/.agent-db` không đủ để giải mã trên máy khác nếu thiếu entry keyring tương ứng.

Nếu OS keyring không khả dụng hoặc đặt `AGENT_DB_DISABLE_KEYRING=1`, CLI yêu cầu master passphrase tối thiểu 12 ký tự. Nó dẫn xuất wrapping key 32 byte bằng scrypt với salt 16 byte và tham số cố định `N=32768`, `r=8`, `p=3`, `maxmem=67108864`, rồi dùng AES-256-GCM bọc vault key. Salt, tham số và wrapped key nằm trong `vault-format.json`; passphrase không được lưu. CLI từ chối format có cipher/KDF parameters khác thay vì tự hạ cấp.

`AGENT_DB_VAULT_PASSPHRASE` chỉ phù hợp automation có secret manager bảo vệ biến môi trường. Với thao tác người dùng, ưu tiên prompt ẩn để tránh rò rỉ qua process/config/log.

## Thiết lập và thay credential

```text
agent-db credential set --target <id> --mode read [--username <name>]
agent-db credential set --target <id> --mode mutation [--username <name>]
```

CLI yêu cầu secret hai lần, kết nối kiểm tra identity trước khi lưu, cập nhật reference trong manifest rồi xóa record cũ. Việc tạo vault và cập nhật file dùng lock/atomic write để tránh hai process tạo hai key khác nhau. Không tự sao chép credential read sang mutation. Nếu chưa có credential, đưa lệnh để chính người dùng chạy local TTY thay vì đoán, thử giá trị mặc định hoặc để Agent cấp PTY.

## Khôi phục và reveal

Để người dùng xem credential đã quên, yêu cầu họ tự chạy trong terminal local tại đúng project:

```text
agent-db credential reveal --target <id> --mode <read|mutation>
```

CLI hiển thị phrase `REVEAL <target> <mode>`, yêu cầu gõ lại chính xác, và chỉ in username/secret dưới dạng terminal-safe JSON string khi stdin, stderr và stdout đều là TTY phù hợp. Cách biểu diễn này bảo toàn chính xác control character mà không cho chúng điều khiển terminal. Capture, pipe và redirect bị từ chối. Agent không chạy lệnh reveal qua tool rồi chuyển secret vào chat.

Quy trình giải mã mà agent khác cần biết:

1. Đọc `vault-format.json` để lấy `formatVersion`, `vaultId`, cipher và protector.
2. Với `os-keyring`, dùng service/account đã ghi để lấy vault key Base64 từ OS keyring của cùng user/máy.
3. Với `passphrase-scrypt`, yêu cầu người dùng nhập passphrase local, dẫn xuất wrapping key theo salt/tham số đã ghi, rồi giải mã `wrappedKey` với AAD `{formatVersion:1,vaultId,purpose:"vault-key"}`.
4. Giải mã record bằng AES-256-GCM và AAD canonical của đúng scope record; credential bắt buộc có `targetFingerprint` đúng như record/target hiện tại.
5. Ưu tiên để CLI thực hiện toàn bộ qua `credential reveal`; không viết tiện ích xuất hàng loạt secret.

Nếu mất OS keyring entry hoặc quên fallback passphrase thì ciphertext không thể phục hồi. Không có backdoor hoặc escrow. Sao lưu `$HOME/.agent-db` không thay thế việc sao lưu keyring/passphrase an toàn.
