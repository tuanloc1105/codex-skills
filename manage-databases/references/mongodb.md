# MongoDB

## Target, TLS và identity

Port mặc định là `27017`; TLS mặc định bật. `--database` là namespace làm việc; `--auth-source` mặc định dùng database đó. Dùng `--namespace` để hard-limit collections.

```text
agent-db target add --id <id> --engine mongodb --environment <env> \
  --host <host> --database <db> [--port 27017] [--auth-source admin] \
  [--tls true] [--namespace orders,customers] \
  --expected-server-identity <replica-set-or-server-address>
```

Adapter dùng `hello`: ưu tiên replica-set name, sau đó server-reported `hello.me`, rồi thử `serverStatus.host`; account ít quyền có thể không gọi được `serverStatus`. Database identity là configured namespace, không phải server-reported database. Mutation yêu cầu identity server không rỗng và khớp `expectedServerIdentity` chính xác.

MongoDB adapter không ánh xạ `trust-server-certificate` thành tùy chọn bỏ kiểm tra certificate. Không dựa vào flag đó để chấp nhận certificate không tin cậy. Chỉ dùng `--no-tls` khi endpoint thực sự không có TLS và rủi ro đã được chấp nhận.

## Read operation

Input là một JSON object có `operation`; ưu tiên file `.json`. Read allowlist:

`find`, `findOne`, `aggregate`, `countDocuments`, `estimatedDocumentCount`, `distinct`, `listCollections`, `listIndexes`.

```json
{"operation":"find","collection":"orders","filter":{"status":"open"},"projection":{"_id":1,"status":1},"sort":{"_id":1}}
```

```json
{"operation":"aggregate","collection":"orders","pipeline":[{"$match":{"status":"open"}},{"$group":{"_id":"$region","count":{"$sum":1}}}]}
```

Read guard từ chối `$out`, `$merge`, `$where`, `$function`, `$accumulator`; kiểm tra collection tham chiếu qua `$lookup`, `$graphLookup`, `$unionWith` thuộc allowlist; và giới hạn JSON tree 128 mức/100.000 node. `listCollections` được filter theo allowlist. `distinct` cần `field`; các operation collection-specific cần `collection`.

Cursor dừng ở `max-rows` hoặc budget xấp xỉ 8 MiB và trả `truncationReason`. `findOne`, count và distinct dùng API đơn của driver rồi mới normalize/bound kết quả. `timeout-ms` cấu hình server selection/connect/socket timeout và `maxTimeMS` cho từng operation; read nhiều pha không có deadline tổng cứng.

## Schema

Schema refresh không sample document values. Nó lưu collection info, options/validator và indexes; tối đa 1.000 collection, tối đa 1.000 index mỗi collection và budget 8 MiB tổng. Riêng inspect dùng một deadline tổng `startedAt + timeout-ms` xuyên identity, list collections và list indexes; hết budget trả `DATABASE_TIMEOUT`.

## Mutation

Mutation allowlist:

`command`, `createCollection`, `dropCollection`, `insertOne`, `insertMany`, `updateOne`, `updateMany`, `replaceOne`, `deleteOne`, `deleteMany`, `createIndex`, `dropIndex`.

```json
{"operation":"updateOne","collection":"orders","filter":{"_id":"..."},"update":{"$set":{"status":"closed"}}}
```

Raw `command` chỉ được dùng với target DBA không có namespace allowlist. Exact command vẫn phải preview/approve; không xem nó là read. Adapter không mở transaction và transaction mode luôn `never`; `--transaction always` bị từ chối.

`options` của typed mutation dùng positive allowlist riêng theo operation. CLI từ chối routing/internal options như `dbName`, `authdb`, `session`, `encryptedFields`, view/pipeline/timeseries tạo namespace phụ, timeout do payload tự đặt và `writeConcern`; timeout luôn do CLI cấp. Vì vậy create/drop collection không thể đổi database hoặc tác động auxiliary collection do option ẩn. Raw command có `writeConcern.w=0` cũng bị từ chối; typed write phải trả `acknowledged: true`, nếu không kết quả là `MUTATION_OUTCOME_UNKNOWN`.

Mutation trả metadata tối thiểu: insertMany bỏ danh sách IDs, update/delete trả counts, kết quả khác bị bound/normalize. Connect/socket, identity command và mutation operation dùng timeout/maxTime riêng nên không phải deadline tổng. Nếu lỗi sau khi operation đã gửi, xử lý `MUTATION_OUTCOME_UNKNOWN`; không giả định batch có rollback đa-document và không retry.
