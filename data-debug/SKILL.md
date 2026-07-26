---
name: data-debug
description: Chẩn đoán và thao tác dữ liệu PostgreSQL, MongoDB, SQL Server, Oracle và Redis bằng CLI Node.js stateless. Dùng khi cần kiểm tra kết nối, xem schema/keyspace, chạy truy vấn chỉ đọc, điều tra dữ liệu, hoặc thực hiện INSERT/UPDATE/DELETE và data mutation đã được người dùng duyệt chính xác trong chat; luôn mặc định READ-ONLY và không thực hiện DDL, cấp quyền hay lệnh quản trị.
---

# Data debug

## Giữ các bất biến

- Chỉ dùng CLI Node.js đi kèm skill. Không dùng Docker image, native database client, driver trực tiếp, module nội bộ hoặc script tự viết để bỏ qua policy.
- Mặc định mọi kết nối và thao tác là READ-ONLY. `doctor`, `test`, `inspect` và `read` không cấp quyền mutation.
- Chỉ mutation sau khi người dùng duyệt đúng plan ID, approval hash, target và exact operation trong chat hiện tại. Không suy diễn approval từ mục tiêu chung, tin nhắn cũ hoặc quyền truy cập database.
- Chỉ cho phép thay đổi dữ liệu: SQL `INSERT`/`UPDATE`/`DELETE`, MongoDB typed insert/update/replace/delete và Redis data commands nằm trong allowlist. Từ chối DDL, schema/index, procedure, quyền, cấu hình, maintenance và lệnh admin.
- Không yêu cầu hoặc lặp lại URI/password trong chat. Chỉ đọc secret từ biến môi trường qua `--connection-env` hoặc `--password-env`; dùng `--env-file` khi cần nạp file local.
- Không ghi connection URI/password vào argument, operation payload, plan, log hoặc kết quả. Mutation payload được hiển thị nguyên vẹn để duyệt, vì vậy chỉ đưa vào đó dữ liệu mà người dùng chấp nhận thấy trong chat.
- Connection có secret đến host ngoài loopback phải mã hóa và xác minh certificate. Không tự thêm `--allow-insecure-credential-transport`; chỉ dùng sau khi giải thích và được người dùng chấp nhận rõ ràng rủi ro của đúng target đó.
- Dùng account quyền tối thiểu. Với read, ưu tiên principal bị database từ chối ghi; với mutation, chỉ cấp đúng quyền data cần thiết. Classifier phía client chỉ là defense-in-depth.
- Không tự retry mutation khi kết quả không xác định. Xác minh trạng thái bằng read, trình bày kết quả và xin approval mới cho hành động khắc phục cụ thể.

## Nạp tham chiếu vừa đủ

- Đọc [hợp đồng CLI](references/cli.md) trước lần gọi đầu tiên hoặc khi cần chọn connection/input flags.
- Đọc [operations](references/operations.md) khi viết SQL/JSON payload hoặc kiểm tra một operation có được hỗ trợ không.
- Đọc [approval qua chat](references/approval.md) trước mọi `mutation preview` và `mutation execute`.

## Dùng CLI

Định nghĩa `<data-debug>` là command vector, không phải chuỗi shell:

```text
node <installed-skill-dir>/scripts/data-debug/bin/data-debug.js
```

1. Chạy `<data-debug> doctor` để kiểm tra Node.js và database driver dependencies.
2. Chuẩn bị connection bằng một biến URI (`--connection-env`) hoặc các flag không bí mật cùng `--password-env`. Chỉ thêm `--env-file` khi file đó là local, không được commit và có quyền truy cập phù hợp.
3. Chạy `test` trước live operation để xác nhận engine, endpoint và database/service. Dừng nếu identity hoặc target không khớp yêu cầu.
4. Dùng `inspect` để khám phá metadata và `read` để đọc dữ liệu. Chọn field, filter, row limit và timeout nhỏ nhất đủ trả lời; không enumerate rộng khi chưa cần.
5. Redact token, payment data, contact details và PII không cần thiết trước khi đưa kết quả vào chat. Nêu rõ truncation, timeout và phạm vi đã đọc.

## Mutation

Chỉ bắt đầu khi người dùng yêu cầu một thay đổi cụ thể:

1. Viết payload data-only và chạy `mutation preview` với đúng target.
2. Hiển thị nguyên vẹn plan ID, approval hash, operation hash, target đã chuẩn hóa, verified identity, exact operation, transaction mode và expiry do CLI trả về. Không diễn giải thay cho exact preview.
3. Hỏi người dùng có đồng ý thực thi **đúng plan/hash/target đó** không rồi dừng. CLI không tự xác thực tin nhắn chat; workflow này là cổng authorization của người dùng.
4. Chỉ sau câu trả lời đồng ý rõ ràng trong chat hiện tại, chạy `mutation execute <cùng connection options> --plan <id> --approved <hash>` đúng một lần.
5. Preview lại và xin approval mới nếu payload, target, plan, hash hoặc connection thay đổi, hay plan hết hạn/đã dùng.

Không coi yêu cầu ban đầu, approval cho plan khác, câu trả lời mơ hồ hoặc sự im lặng là approval. Không tạo approval thay người dùng.

## Dừng an toàn

Dừng và hỏi lại khi engine, endpoint, database/service/index, namespace/key prefix hoặc operation còn mơ hồ. Dừng nếu read classifier trả `unknown`, connection không dùng được mà phải đổi công cụ, hoặc mutation không khớp allowlist. Không tự mở rộng sang MySQL, MongoDB legacy, DDL hay tác vụ DBA.
