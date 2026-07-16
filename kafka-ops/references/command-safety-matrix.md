# Ma trận an toàn Apache Kafka CLI

## Cách dùng

Luôn chạy `scripts/kafka_guard.py classify -- <exact-argv>` thay vì tự suy luận từ tên executable. Ma trận này giải thích policy; kết quả guard mới là quyết định áp dụng cho exact argv hiện tại.

Các lớp:

- `LOCAL_READ`: chỉ đọc/thao tác local không đổi Kafka state.
- `READ`: đọc metadata/state, được phép mặc định sau preflight và target check.
- `PREVIEW`: tính hoặc hiển thị thay đổi nhưng không execute.
- `SENSITIVE_READ`: không mutation nhưng có thể lộ payload, ACL, token metadata hoặc deployment details; cần yêu cầu rõ và output tối thiểu.
- `MUTATION`: thay đổi data, offset, metadata, config, quyền, assignment, process hoặc local Kafka state; bắt buộc protocol mutation.
- `UNKNOWN`: không nằm trong allowlist hoặc không chứng minh được read-only; dừng, không chạy.

## Ma trận chính

| CLI | Read/preview được nhận diện | Mutation được nhận diện | Ghi chú |
|---|---|---|---|
| `kafka-topics` | `--list`, `--describe` | `--create`, `--alter`, `--delete` | `--alter` có thể tăng partition và không giảm lại được. |
| `kafka-configs` | `--describe` | `--alter` | Cả add/delete dynamic config đều là mutation. |
| `kafka-consumer-groups` | `--list`, `--describe`; reset không có `--execute` là `PREVIEW` | `--delete`, `--delete-offsets`, reset có `--execute` | Preview offset không phải approval cho execute. |
| `kafka-share-groups` | `--list`, `--describe`; reset không có `--execute` là `PREVIEW` | `--delete`, `--delete-offsets`, reset có `--execute` | Dùng cùng policy offset với consumer group. |
| `kafka-groups` | `--list` | Không allowlist | Action khác là `UNKNOWN` cho đến khi version-specific help được review và guard cập nhật. |
| `kafka-acls` | `--list` là `SENSITIVE_READ` | `--add`, `--remove` | ACL wildcard/prefix có blast radius lớn. |
| `kafka-console-consumer` | Chỉ bounded direct-partition pattern bên dưới | Dùng `--group` hoặc auto-commit có thể đổi group/offset | Mọi pattern khác là `UNKNOWN`. |
| `kafka-console-producer` | Không | Mọi invocation | Risk `high`; exact payload hash/count phải nằm trong approval surface. Custom `--line-reader` là `UNKNOWN`; `--reader-config` phải absolute và được pin. |
| `kafka-get-offsets` | Query | Không allowlist | Vẫn giới hạn topic/partition khi có thể. |
| `kafka-broker-api-versions` | Query | Không allowlist | Dùng để tách lỗi network/protocol khỏi auth. |
| `kafka-log-dirs` | `--describe` | `--alter` | Alter replica placement là high risk. |
| `kafka-reassign-partitions` | `--generate` là `PREVIEW` | `--execute`, `--cancel`, `--verify` | `--verify` có thể xóa throttle khi reassignment hoàn tất nên không phải pure read. |
| `kafka-leader-election` | Không | Mọi invocation | Unclean election có thể gây mất dữ liệu. |
| `kafka-delete-records` | Không | Mọi invocation | Data deletion, high risk. |
| `kafka-delegation-tokens` | `--describe` là `SENSITIVE_READ` | `--create`, `--renew`, `--expire` | Không in token/secret material. |
| `kafka-transactions` | `--list`, `--describe` là `SENSITIVE_READ` | `--abort` | Transactional IDs có thể nhạy cảm. |
| `kafka-features` | `--describe` | `--upgrade`, `--downgrade`, `--disable` | Feature-level change là cluster-wide. |
| `kafka-client-metrics` | `--describe` | `--alter`, `--delete` | Cả hai mutation có risk `high`; selector rộng phải coi là production blast radius. |
| `kafka-metadata-quorum` | `--describe` | add/remove controller flags | Quorum membership mutation là high risk. |
| `kafka-cluster` | `cluster-id` | `unregister` | Dùng cluster ID làm identity cho approval. |
| `kafka-streams-application-reset` | Chỉ explicit `--dry-run` | Invocation không có `--dry-run` | Reset có thể đổi offsets và internal topics. |
| `kafka-storage` | `random-uuid` local; `info` là `SENSITIVE_READ` | `format` | Không format storage như một bước “sửa nhanh”. |
| broker start/stop tools | Không | Mọi invocation, kể cả help/version | Một số script lifecycle có thể bỏ qua flag và đổi process state. |
| producer perf/verifiable tools | Không | Mọi invocation | Tạo records/load. |
| consumer perf/verifiable/share tools | Không allowlist | Không tự nâng thành mutation | `UNKNOWN` vì khó đảm bảo group/offset và bounds. |

## Bounded console consumer

Chỉ phân loại `SENSITIVE_READ` khi exact argv có đủ:

- `--topic`, `--partition`, `--offset` để direct-assign phạm vi cụ thể.
- `--max-messages` từ 1 đến 100.
- `--timeout-ms` từ 1 đến 60000.
- `--consumer-property enable.auto.commit=false`.
- `--consumer-property allow.auto.create.topics=false`.
- Không `--group`, `--group-id` hay `--from-beginning`.

Nếu cần đọc nhiều hơn, thực hiện nhiều đợt nhỏ sau khi báo kết quả đợt trước; không nới guard bằng một lệnh rộng.

## Quy tắc version và flag

- `--help`/`--version` chỉ là `LOCAL_READ` cho explicit allowlist hiện hành: `kafka-acls`, `kafka-broker-api-versions`, `kafka-client-metrics`, `kafka-cluster`, `kafka-configs`, `kafka-consumer-groups`, `kafka-features`, `kafka-get-offsets`, `kafka-groups`, `kafka-log-dirs`, `kafka-metadata-quorum`, `kafka-reassign-partitions`, `kafka-share-groups`, `kafka-storage`, `kafka-topics` và `kafka-transactions`.
- Các tool luôn mutation — `kafka-console-producer`, `kafka-delete-records`, `kafka-leader-election`, `kafka-producer-perf-test`, `kafka-server-start`, `kafka-server-stop`, `kafka-verifiable-producer` — vẫn là `MUTATION` khi argv chứa `--help` hoặc `--version`.
- Với known tool còn lại (`kafka-console-consumer`, `kafka-console-share-consumer`, `kafka-consumer-perf-test`, `kafka-delegation-tokens`, `kafka-streams-application-reset`, `kafka-verifiable-consumer`), help/version là `UNKNOWN` vì guard chưa chứng minh invocation local và bounded. Tool không được nhận diện hoặc tổ hợp action/flag không allowlist cũng là `UNKNOWN`.
- Dùng version từ preflight và local help/version đã được allowlist để kiểm tra cú pháp; help không cấp quyền chạy action khác chưa có trong allowlist.
- Nếu Kafka thêm action mới, đổi semantics hoặc CLI vendor dùng cùng tên, giữ `UNKNOWN` cho đến khi cập nhật guard và tests.
- Nếu một lệnh có đồng thời read và mutation flag, mutation thắng.
- Không dùng shell pipeline/redirection để làm lệnh “trông giống read”; classifier chỉ bảo vệ exact argv được truyền vào.
- Trên native Windows, empty token, embedded quote/control hoặc shape không đi qua PowerShell native boundary một cách lossless phải là `UNKNOWN`. Với `.bat`/`.cmd`, guard còn chặn metacharacter có thể bị `cmd.exe` diễn giải. Không escape để lách; xem `windows.md`.

## Nguồn chính thức

- Apache Kafka Quickstart: <https://kafka.apache.org/quickstart/>
- Basic Kafka Operations: <https://kafka.apache.org/operations/basic-kafka-operations/>
- Authorization and ACLs: <https://kafka.apache.org/security/authorization-and-acls/>
