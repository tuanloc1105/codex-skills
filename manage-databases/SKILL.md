---
name: manage-databases
description: Tương tác an toàn với Oracle, MongoDB, SQL Server và PostgreSQL qua CLI Node.js project-bound. Dùng khi cần cấu hình kết nối, kiểm tra danh tính database, khám phá schema, chạy truy vấn chỉ đọc, chẩn đoán kết nối, hoặc thực hiện tác vụ DBA/mutation có phê duyệt; luôn mặc định chỉ đọc, tách credential read/mutation, và buộc preview chính xác cùng xác nhận mới cho mọi thay đổi dữ liệu hay cấu hình database.
---

# Quản lý database an toàn

## Giữ các bất biến

- Luôn dùng CLI đi kèm skill qua command vector `<trusted-agent-db>` được pin theo [runtime trust](references/runtime-trust.md). Không bypass policy bằng binary trên `PATH`, driver Node trực tiếp, native DB client, module nội bộ hoặc script tự viết.
- Mặc định mọi thao tác database là chỉ đọc. Không suy diễn quyền ghi từ mục tiêu chung, quyền DBA, tin nhắn cũ, hoặc câu “cứ làm đi”.
- Chỉ làm việc trong project được nhận diện từ thư mục hiện tại và truyền `--target <id>` cho mọi lệnh target/database; `doctor`, `project` và `target list` là các ngoại lệ không nhận target.
- Kiểm tra project, environment, engine, host, database/service và target fingerprint trước khi truy vấn.
- Dùng credential `read` cho khám phá và truy vấn. Chỉ nạp credential `mutation` trong luồng mutation đã được người dùng yêu cầu rõ ràng.
- Không yêu cầu người dùng dán secret vào chat. Nhập credential bằng prompt local TTY của CLI; không đặt password trong command line, file project, log, hay tool output.
- Không xuất credential ra chat. Khi người dùng quên credential, hướng dẫn họ chạy `credential reveal` trực tiếp trong terminal local; lệnh cố ý từ chối stdout bị capture hoặc redirect.
- Không tự chạy `project bind`, `credential set`, `credential reveal` hoặc `mutation approve` qua tool. Đây là các cổng local TTY dành riêng cho người dùng; không cấp pseudo-terminal, không gọi module nội bộ và không tự tạo artifact để lách cổng.
- Không tự `project init` hoặc `target add` từ một yêu cầu mơ hồ như “tự tìm cách”. Đây là thay đổi cấu hình: phải có chỉ dẫn rõ ràng của người dùng và đủ metadata; không dò endpoint, secret hay target lân cận.
- Chỉ coi `local`, `dev`, `development`, `test`, `testing` hoặc `sandbox` là non-production khi người dùng xác nhận đúng môi trường. Mọi nhãn khác (`prod`, `prd`, `live`, `main`, nhãn riêng) hoặc trạng thái chưa rõ đều phải xử lý như production.
- Với read trên production, yêu cầu target có `expectedServerIdentity`; TLS/encryption phải bật, `trustServerCertificate=false`, và kết nối chỉ thành công khi certificate chain cùng hostname hợp lệ. Nếu cấu hình hoặc kết quả kiểm tra thiếu/không rõ, dừng theo fail-closed.
- Xem bộ phân loại câu lệnh là lớp phòng vệ bổ sung, không phải security boundary. Chỉ dùng account read có hồ sơ provision hiện hành khớp credential ID, authenticated principal từ `target test`, target fingerprint, namespace/scope và role set/revision; hồ sơ cần issuer được xác thực, thời hạn và cơ chế phát hiện role đổi. Phiên bản này không cho dùng generic `read` để tự chứng minh quyền; nếu thiếu hồ sơ đạt yêu cầu thì dừng. Evidence vô hiệu sau khi binding, target, credential hoặc role đổi. Tuyệt đối không thử mutation để kiểm tra quyền.

## Nạp tham chiếu vừa đủ

- Đọc [hợp đồng CLI](references/cli-contract.md) trước khi gọi CLI hoặc xử lý JSON trả về.
- Đọc [chính sách an toàn](references/safety-policy.md) trước truy vấn đầu tiên và khi phân loại read/mutation.
- Đọc [ràng buộc project-target](references/project-target-binding.md) khi khởi tạo, bind, thêm target, hoặc gặp lỗi context/identity.
- Đọc [credential vault](references/credential-vault.md) khi thiết lập, khôi phục, di chuyển, hoặc giải thích mã hóa credential.
- Đọc [runtime trust](references/runtime-trust.md) khi receipt runtime thiếu/hết hiệu lực, sau khi Node/skill được cập nhật, hoặc khi chuẩn bị lệnh local TTY cho người dùng.
- Đọc [phê duyệt mutation](references/mutation-approval.md) trước mọi thay đổi dữ liệu, schema, quyền, cấu hình hay tác vụ quản trị.
- Chỉ đọc tham chiếu engine đang dùng: [Oracle](references/oracle.md), [MongoDB](references/mongodb.md), [SQL Server](references/sql-server.md), hoặc [PostgreSQL](references/postgresql.md).

## Thực hiện luồng chuẩn

1. Chỉ dùng bản skill đã cài vật lý ngoài project/worktree hiện tại; nếu canonical skill path nằm trong project đang xử lý thì dừng và yêu cầu cài bản ngoài project. Đọc/kiểm tra `$HOME/.agent-db/runtime-trust.json` theo runtime trust, không chạy binary để nó tự xác minh. Định nghĩa `<trusted-agent-db>` là hai argv tuyệt đối đã pin: `<trusted-node> <entrypoint-trong-skill-đã-cài>`. Nếu receipt thiếu/sai hash/hết hiệu lực, dừng để người dùng pin lại; không tự dò `node`/`agent-db` từ `PATH`. Chạy `<trusted-agent-db> doctor` bằng argv-safe invocation. Bản global chỉ là tiện ích cho người dùng, không phải trust anchor; không tự cài/cập nhật global.
2. Chạy `<trusted-agent-db> project show`. Nếu project mới chưa đăng ký, chỉ `project init` theo yêu cầu người dùng. Nếu cần chuyển binding có sẵn, đưa UUID và command vector tuyệt đối cho `project bind` để chính người dùng chạy trong local TTY; Agent không chạy thay.
3. Chạy `<trusted-agent-db> target list`, lọc theo project, engine/environment/domain mà người dùng nêu và chỉ tự chọn khi có đúng một target khớp. Nếu không có hoặc có nhiều target, hỏi người dùng; không suy target từ tên. Sau đó chạy `<trusted-agent-db> target show --target <id>` và đối chiếu toàn bộ metadata với yêu cầu hiện tại.
4. Chạy `<trusted-agent-db> credential status --target <id> --mode read` cho read; mutation dùng `--mode mutation` chỉ trong workflow mutation. Nếu thiếu, đưa command vector tuyệt đối để người dùng provision/thiết lập qua terminal local TTY. Không nhận hoặc lặp lại secret trong hội thoại.
5. Trước live read, xác định namespace/scope từ yêu cầu người dùng hoặc `schema show` cache local; nếu vẫn thiếu/mơ hồ thì hỏi, không kết nối live để đoán. Sau đó chạy `<trusted-agent-db> target test --target <id> --mode read` rồi xác minh identity, TLS và authenticated principal. Kiểm tra hồ sơ provision quyền read khớp principal/target/scope; hồ sơ phải có credential ID, role-set revision, thời điểm phát hành/hết hạn, chữ ký hoặc trusted registry cho issuer và cơ chế đảm bảo role chưa đổi. Nếu thiếu bất kỳ phần nào thì dừng; không chạy generic `read` để introspect quyền. Chỉ sau khi evidence đạt mới `schema refresh` hoặc business `read`. Chỉ refresh trong scope đã biết hoặc khi người dùng yêu cầu rõ metadata của scope đó; không enumerate toàn bộ schema production để đoán namespace. Một yêu cầu chỉ kiểm tra cấu hình local không cho phép `target test`/refresh/read. Dùng allowlist field nghiệp vụ tối thiểu, tránh `SELECT *`/projection rộng, redact token, payment, address, contact hoặc PII không cần cho câu trả lời; dùng giới hạn dòng và timeout nhỏ nhất đủ dùng.
6. Với mutation, tuân thủ tuyệt đối chuỗi `prepare -> hiển thị preview chính xác -> người dùng tự approve trên local TTY -> kiểm tra receipt mã hóa -> execute một lần`. Không gộp bước và không tự tạo approval thay người dùng.
7. Báo lại đúng project/target, identity đã kiểm chứng, giới hạn/truncation, thời gian chạy và cảnh báo transaction. Không đưa secret vào kết quả.

## Xử lý mutation

Chỉ bắt đầu khi người dùng vừa yêu cầu một thay đổi cụ thể. Target mutation bắt buộc có `expectedServerIdentity`. Chạy `mutation prepare`; bước này kiểm tra lại identity bằng credential mutation và khóa project `bindingRevision`, target fingerprint, credential, exact payload, transaction mode cùng identity vào plan 5 phút. Sau đó trình bày project, environment, target, fingerprint, identity đã kiểm chứng, operation/approval hash, exact preview, transaction mode và thời hạn. Yêu cầu người dùng tự chạy lệnh sau trong terminal local của đúng project:

```text
<trusted-node-tuyệt-đối> <entrypoint-skill-tuyệt-đối> mutation approve --target <id> --plan <uuid>
```

Không chạy lệnh approve thay người dùng, kể cả người dùng gửi phrase trong chat. Không cấp PTY, không capture lệnh và không gọi module nội bộ để tạo receipt. Sau khi người dùng báo đã approve, dùng `mutation show` để thấy `approval.approved=true`; chỉ khi plan còn hạn, payload không đổi và target vẫn khớp mới chạy `mutation execute --target <id> --plan <uuid>`—lệnh không nhận `--confirm`.

Nếu yêu cầu/payload, project binding, target hoặc credential đổi, hay plan hết hạn trước khi gửi DB operation, bỏ plan cũ rồi chỉ prepare lại theo yêu cầu hiện tại. Nếu execute có thể đã gửi operation nhưng không nhận được kết quả xác định, đánh dấu `MUTATION_OUTCOME_UNKNOWN`: tuyệt đối không retry và không prepare lại cùng mutation. Trước tiên chỉ xác minh trạng thái bằng read-only; chỉ sau khi người dùng xem trạng thái thực tế và yêu cầu một hành động khắc phục mới, cụ thể, mới được tạo plan/approval mới. Xem [phê duyệt mutation](references/mutation-approval.md) để xử lý đầy đủ.

## Dừng an toàn

Dừng và hỏi lại khi thiếu project, target, endpoint, database/service, credential hoặc phạm vi namespace. Nếu operation có thể là mutation nhưng người dùng chưa yêu cầu rõ thay đổi cụ thể, không prepare hay execute. Dừng ngay khi identity thực tế không khớp target, khi query read bị phân loại không chắc chắn, hoặc khi dữ liệu đầu vào có chứa secret cần đi qua chat/tool output.
