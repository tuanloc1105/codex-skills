# Chính sách an toàn

## Mô hình quyền

Với engine hỗ trợ mutation, phân tách hai credential cho mỗi target:

- `read`: account quyền tối thiểu, bị database từ chối mọi ghi/DDL/admin.
- `mutation`: account chỉ có đúng quyền thay đổi cần thiết; không dùng cho khám phá hay truy vấn thường ngày.

Redis v1 chỉ có credential `read`; mode `mutation` bị từ chối ở CLI và adapter.

Không xem bộ phân loại phía client là security boundary. SQL có thể gọi hàm/procedure có side effect; SQL Server không có transaction chỉ đọc ở adapter; MongoDB `command` có phạm vi rất rộng; Redis ACL phải giới hạn account vào đúng command/key prefix. Quyền database là lớp chặn cuối cùng.

## Cổng chỉ đọc cho SQL

Chỉ chấp nhận một statement bắt đầu bằng `SELECT`, `WITH`, `SHOW`, `DESCRIBE`, `DESC` hoặc `EXPLAIN`. Bộ phân loại bỏ qua literal/comment rồi từ chối:

- Nhiều statement phân cách bởi `;`.
- DML, DDL, cấp quyền, procedure, lock, maintenance, backup/restore và lệnh admin.
- `EXPLAIN ANALYZE`, vì nó thực thi statement.
- Oracle `EXPLAIN PLAN`, vì có thể ghi `PLAN_TABLE`.
- Mọi token `INTO`, locking read `FOR UPDATE`/`FOR SHARE`/`FOR NO KEY UPDATE`/`FOR KEY SHARE`.
- SQL Server locking hints `UPDLOCK`, `XLOCK`, `TABLOCKX`, `HOLDLOCK` và `NEXT VALUE FOR`.
- Sequence `NEXTVAL`, các hàm PostgreSQL admin/state-changing đã biết, và Oracle network/filesystem/coordination package đã biết.

Nếu kết quả là mutation hoặc unknown, không chỉnh sửa câu lệnh để lách kiểm tra. Chuyển sang protocol mutation chỉ sau yêu cầu rõ ràng của người dùng.

PostgreSQL chạy read trong `BEGIN READ ONLY`; Oracle dùng `SET TRANSACTION READ ONLY`. SQL Server dựa vào classifier và account read ít quyền, vì vậy phải cấu hình principal read-only ở server.

## Cổng chỉ đọc cho MongoDB

Chỉ nhận JSON operation typed. Read allowlist gồm:

`find`, `findOne`, `aggregate`, `countDocuments`, `estimatedDocumentCount`, `distinct`, `listCollections`, `listIndexes`.

Từ chối pipeline `aggregate` chứa `$out` hoặc `$merge` ở bất kỳ mức lồng nào và các operator server-side `$where`, `$function`, `$accumulator`. Nếu target có `allowedNamespaces`, collection chính và collection tham chiếu qua `$lookup`, `$graphLookup`, `$unionWith` đều phải thuộc allowlist. JSON tree tối đa 128 mức và 100.000 object/array node. Không chuyển arbitrary Mongo command thành read.

## Cổng chỉ đọc cho Redis

Chỉ nhận JSON operation typed và chuyển qua hard allowlist trong [redis.md](redis.md); không nhận raw command, argv tùy ý, Lua, module command, pub/sub, transaction hay command admin. Mọi key phải bắt đầu bằng `keyPrefix` literal đã khóa trong target fingerprint. Command hoặc field không biết bị từ chối fail closed.

`SCAN`, `HSCAN`, `SSCAN` và `ZSCAN` chỉ đọc đúng một page theo cursor do người gọi cung cấp; CLI không tự lặp cursor. `SCAN` chỉ nhận `matchSuffix`, rồi adapter ghép với `keyPrefix`. Nếu cả page vượt `max-rows` hoặc budget output thì bỏ toàn bộ page và trả lỗi, không trả page bị cắt có cursor gây hiểu nhầm. `SLOWLOG GET` loại bỏ argv và client metadata trước khi xuất kết quả; `GET` dùng preview có giới hạn thay vì tải giá trị không giới hạn.

## Scope và identity

Luôn giải quyết project bằng hybrid marker/root/filesystem/Git binding từ thư mục hiện tại, chọn target bằng ID tường minh, rồi kiểm tra identity sau khi kết nối. Database/service/index thực tế phải khớp target; với Redis, authenticated principal, standalone mode và endpoint cấu hình cũng phải khớp, còn mọi key phải nằm dưới `keyPrefix`. `expectedServerIdentity`, nếu có, cũng phải khớp tuyệt đối và là bắt buộc cho mutation. Không tiếp tục khi binding/fingerprint/identity mismatch, kể cả người dùng nói “chắc đúng rồi” mà chưa hoàn tất cổng bind local TTY.

Chỉ coi `local`, `dev`, `development`, `test`, `testing` hoặc `sandbox` là non-production sau khi người dùng xác nhận đúng môi trường. Mọi nhãn còn lại hoặc chưa rõ đều được xử lý như production. Với production read, workflow skill yêu cầu `expectedServerIdentity`; TLS/encryption phải bật, `trustServerCertificate=false`, certificate chain và hostname phải hợp lệ. Thiếu hoặc không rõ bất kỳ điều kiện nào thì fail closed. `target test` chỉ là identity query, nhưng vẫn là kết nối production và chỉ được dùng khi yêu cầu hiện tại thực sự cần kiểm tra dữ liệu live, không phải khi chỉ kiểm tra cấu hình local.

Credential `read` chỉ được xem là ít quyền khi có hồ sơ provision hiện hành ghi đúng credential ID, authenticated principal do `target test` trả về, target fingerprint, namespace/scope và role set/revision. Hồ sơ phải có issuer được xác thực bằng chữ ký hoặc trusted registry, thời điểm phát hành/hết hạn và cơ chế đảm bảo hoặc phát hiện role grant/revoke. Phiên bản này không có dedicated privilege-verification command, vì vậy không dùng generic `read` để tự chứng minh quyền; thiếu hồ sơ đạt yêu cầu thì dừng và yêu cầu provision lại. Coi evidence hết hiệu lực sau thay đổi project binding, target, credential/rotation hoặc role grant/revoke. `credential status` chỉ chứng minh secret record tồn tại, không chứng minh quyền database. Không bao giờ chạy mutation thử để kiểm tra.

Không dò host, scan port, thử database lân cận, đoán credential, hay tự bind sang project/target khác.

## Giới hạn dữ liệu

- Dùng `max-rows` và timeout nhỏ nhất đủ trả lời; bắt đầu với 100 dòng hoặc ít hơn.
- Tránh truy vấn toàn bảng khi có thể lọc, aggregate hoặc dùng metadata.
- Với Redis, dùng key cụ thể trước; chỉ dùng một page SCAN khi thật sự cần và tự quyết định page tiếp theo sau khi xem cursor.
- Dùng allowlist field nghiệp vụ tối thiểu; tránh `SELECT *` hoặc document projection rộng. Redact token, payment, address, contact và PII không cần thiết trước khi đưa vào câu trả lời.
- Input tối đa 1 MiB; payload kết quả database có budget xấp xỉ 8 MiB. Đọc `truncated`, `truncationReason`, `schemaTruncated` và counters bị discard trước khi kết luận dữ liệu đầy đủ.
- Không đưa credential, token, private key hay vault passphrase vào SQL/JSON operation.
- Nếu kết quả chứa dữ liệu nhạy cảm ngoài phạm vi câu hỏi, chỉ tóm tắt tối thiểu và không sao chép thêm.

## Mutation

Mọi INSERT/UPDATE/DELETE, DDL, index, quyền, cấu hình, procedure, command admin, maintenance và thay đổi schema đều là mutation. Không có ngoại lệ cho “thay đổi nhỏ” hay “chỉ ở dev”. Redis v1 không hỗ trợ mutation dưới bất kỳ hình thức nào. Payload mutation bị từ chối nếu có dấu hiệu chứa password/token/private key/credential URI; không đưa secret vào exact preview. Scanner từ khóa chỉ là defense-in-depth và không thể chứng minh một chuỗi generic không phải secret: nếu Agent biết payload có giá trị bí mật dưới bất kỳ tên nào, không được gọi `prepare`; chuyển thao tác sang workflow database-native chạy hoàn toàn local.

Dùng đúng protocol tại [mutation-approval.md](mutation-approval.md). Agent tuyệt đối không chạy `mutation approve`, mô phỏng local TTY, dùng PTY, gọi module nội bộ hay tự viết approval receipt. Timeout sau khi operation đã gửi có thể là `MUTATION_OUTCOME_UNKNOWN`; chỉ xác minh bằng read-only, không retry mutation.
