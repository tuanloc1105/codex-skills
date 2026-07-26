# Approval mutation qua chat

## Điều kiện tạo preview

Chỉ chạy `mutation preview` sau khi người dùng yêu cầu một thay đổi dữ liệu cụ thể và target đã rõ. Preview không phải approval và không gửi mutation tới database.

Không preview DDL/admin/permission, thao tác ngoài allowlist hoặc payload chứa connection credential. Dùng đúng connection source và input sẽ được dùng khi execute.

## Nội dung phải hiển thị

Sau preview, trình bày nguyên vẹn các field CLI trả về:

```text
Plan: <plan-id>
Approval hash: <hash>
Operation hash: <hash>
Expires: <timestamp>
Target: <exact public target, including target fingerprint>
Verified identity: <identity returned by preview>
Operation type: <typed operation name>
Operation: <exact SQL/JSON payload returned by preview>
Transaction mode: <resolved mode>
```

Sau đó hỏi một câu rõ ràng, ví dụ:

```text
Bạn có đồng ý thực thi đúng plan <plan-id>, hash <hash>, trên target này không?
```

Dừng và chờ câu trả lời. Không chạy `mutation execute` trong cùng lượt tạo preview.

## Approval hợp lệ

Chỉ chấp nhận câu trả lời đồng ý rõ ràng của người dùng trong chat hiện tại, gửi sau exact preview và gắn được với đúng plan/hash/target. Câu “đồng ý”, “OK, chạy plan đó” hoặc tương đương là hợp lệ khi chỉ có một prompt approval đang chờ.

Không chấp nhận:

- Yêu cầu mutation ban đầu hoặc quyền chung như “cứ sửa giúp mình”.
- Approval trước khi preview, từ chat khác, cho plan/hash/target khác hoặc đã bị chỉnh sửa.
- Câu trả lời mơ hồ, sự im lặng hoặc suy luận từ ngữ cảnh.
- Approval do Agent tự tạo, local TTY giả lập hoặc sửa plan store.

## Execute

Sau approval hợp lệ, chạy đúng một lần:

```text
data-debug mutation execute <same-connection-options> \
  --plan <plan-id> --approved <approval-hash>
```

CLI phải từ chối plan sai hash, hết hạn, đã dùng, bị thay đổi hoặc target fingerprint không khớp connection options. `--approved` chứng minh execute khớp preview; nó không tự chứng minh người dùng đã nhắn approval, vì vậy Agent vẫn phải tuân thủ cổng chat ở trên.

Nếu payload, target hoặc connection thay đổi, tạo preview mới và xin approval mới. Nếu execute lỗi trước khi gửi operation, báo lỗi và chỉ preview lại khi còn đúng yêu cầu. Nếu outcome có thể không xác định sau khi gửi operation, không retry; dùng read-only để xác minh trạng thái rồi xin approval mới cho một hành động khắc phục cụ thể.
