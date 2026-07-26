# Operations

## Mục lục

- [Nguyên tắc chung](#nguyên-tắc-chung)
- [SQL](#sql-postgresql-sql-server-và-oracle)
- [MongoDB](#mongodb)
- [Redis](#redis)

## Nguyên tắc chung

- Dùng đúng một operation cho mỗi `read` hoặc `mutation preview`.
- Giới hạn row/document/key/range và chọn projection nhỏ nhất đủ debug.
- Coi stored function, procedure, dynamic command và server-side code là không an toàn dù tên có vẻ chỉ đọc.
- Không nhét connection password/URI vào SQL/JSON payload; CLI lấy credential kết nối riêng từ environment.
- Dùng read principal cho `test`, `inspect`, `read`; dùng DML-scoped principal cho mutation khi hệ thống có tách account.

## SQL: PostgreSQL, SQL Server và Oracle

Read chỉ nhận một statement thuộc allowlist như `SELECT`, read-only `WITH`, `SHOW`/`DESCRIBE` hoặc safe `EXPLAIN`. Từ chối multi-statement, locking read, `SELECT INTO`, sequence increment, `EXPLAIN ANALYZE`, procedure và hàm có side effect.

PostgreSQL và Oracle chạy read trong read-only transaction khi engine hỗ trợ. SQL Server dựa thêm vào least-privilege account; không xem classifier là security boundary.

Với PostgreSQL mutation, CLI gọi `pg_control_system()` trong lúc preview và ngay trước write để bind approval vào `system_identifier` của cluster. DML principal cần được DBA cấp riêng quyền thực thi function này nếu policy cho phép; CLI không tự cấp quyền và sẽ fail-closed khi không đọc được cluster identity. Read principal không cần quyền này.

Mutation chỉ nhận một data statement:

- `INSERT`
- `UPDATE`
- `DELETE`

Từ chối `MERGE`, DDL, truncate, schema/index, transaction control, procedure, grant/revoke, maintenance, backup/restore, admin command và qualifier cross-database/linked-server/database-link. Ưu tiên predicate cụ thể. Nếu operation cố ý có phạm vi rộng, exact preview và prompt approval phải làm phạm vi đó rõ ràng; không thu nhỏ hoặc mở rộng payload sau khi được duyệt.

Lexer không thể tự chứng minh synonym, foreign table hoặc user-defined function là local và không có side effect. Principal dùng với skill không được có quyền linked server/database link/foreign server, filesystem/network package hay routine quản trị; nếu không bảo đảm được thì dừng thay vì coi classifier là security boundary.

## MongoDB

Dùng typed JSON, không dùng arbitrary database command.

Read operations:

- `find`, `findOne`, `aggregate`
- `countDocuments`, `estimatedDocumentCount`, `distinct`
- `listCollections`, `listIndexes`

`find`/`findOne` dùng `collection` và tùy chọn `filter`, `projection`; `find` còn nhận `sort`, `skip`. `aggregate` dùng `collection`, `pipeline`. `countDocuments` dùng `collection` và tùy chọn `filter`; `estimatedDocumentCount` chỉ dùng `collection`; `distinct` thêm `field`. `listIndexes` dùng `collection`, còn `listCollections` nhận tùy chọn `filter`. Field lạ bị từ chối để typo không biến thành read rộng hơn dự kiến.

Từ chối `$out`, `$merge`, `$where`, `$function`, `$accumulator` và collection ngoài scope.

Mutation operations:

- `insertOne`, `insertMany`
- `updateOne`, `updateMany`, `replaceOne`
- `deleteOne`, `deleteMany`

Từ chối create/drop collection, create/drop index, raw command, server-side JavaScript và option không nằm trong typed schema. Ví dụ:

```json
{
  "operation": "updateOne",
  "collection": "users",
  "filter": { "_id": "user-42" },
  "update": { "$set": { "status": "active" } },
  "options": { "upsert": false }
}
```

## Redis

Dùng typed JSON dạng:

```json
{
  "operation": "command",
  "command": "GET",
  "arguments": { "key": "app:user:42" }
}
```

Read cho phép nhóm command bounded như exact-key GET/type/TTL, hash/list/set/sorted-set/stream reads và một page `SCAN` theo cursor. Không tự lặp toàn keyspace; mọi key phải khớp `--key-prefix` khi prefix được cấu hình.

Các field `arguments` cho read:

| Command | Arguments |
| --- | --- |
| `PING`, `DBSIZE`, `TIME`, `SLOWLOG LEN` | `{}` |
| `INFO` | `section`: một section bounded như `server`, `clients`, `memory`, `stats`, `replication`, `keyspace` |
| `SCAN` | `cursor`, `matchSuffix`; tùy chọn `count`, `type` |
| `TYPE`, `TTL`, `PTTL`, `EXPIRETIME`, `PEXPIRETIME`, `GET`, `STRLEN`, `HLEN`, `LLEN`, `SCARD`, `ZCARD`, `XLEN` | `key` |
| `EXISTS` | `keys: string[]` |
| `GETRANGE` | `key`, `start`, `end` |
| `HGET`, `HEXISTS`, `HSTRLEN` | `key`, `field` |
| `HMGET` | `key`, `fields: string[]` |
| `HSCAN`, `SSCAN`, `ZSCAN` | `key`, `cursor`; tùy chọn `match`, `count` |
| `LINDEX` | `key`, `index` |
| `LRANGE`, `ZRANGE` | `key`, `start`, `stop`; `ZRANGE` nhận thêm `withScores` |
| `SISMEMBER` | `key`, `member` |
| `SMISMEMBER`, `ZMSCORE` | `key`, `members: string[]` |
| `ZCOUNT`, `ZLEXCOUNT` | `key`, `min`, `max` |
| `ZSCORE`, `ZRANK`, `ZREVRANK` | `key`, `member` |
| `XRANGE`, `XREVRANGE` | `key`, `start`, `end`, `count` |
| `XINFO STREAM` | `key` |
| `MEMORY USAGE` | `key`; tùy chọn `samples` |
| `OBJECT ENCODING`, `OBJECT FREQ`, `OBJECT IDLETIME`, `OBJECT REFCOUNT` | `key` |
| `SLOWLOG GET` | `count` |

Read trả scalar trong `value`, tập bounded trong `values`/`entries`, hoặc scan page có `nextCursor` tùy command. Luôn kiểm tra `rowCount`, `truncated`, `truncationReason` và `outputBytes`; tự quyết định có cần gọi page kế tiếp hay không, không tự enumerate toàn bộ keyspace.

Mutation chỉ cho phép data commands typed:

- String/key lifetime: `SET`, `DEL`, `UNLINK`, `EXPIRE`, `PEXPIRE`, `EXPIREAT`, `PEXPIREAT`, `PERSIST`
- Hash/list: `HSET`, `HDEL`, `LPUSH`, `RPUSH`, `LPOP`, `RPOP`, `LTRIM`
- Set/sorted set: `SADD`, `SREM`, `ZADD`, `ZREM`

Các field `arguments` dùng cho mutation:

| Command | Arguments |
| --- | --- |
| `SET` | `key`, `value`; tùy chọn một trong `seconds`, `milliseconds`, `expireAtSeconds`, `expireAtMilliseconds`; tùy chọn `keepTtl`, `condition: "NX"|"XX"`, `get` |
| `DEL`, `UNLINK` | `keys: string[]` |
| `EXPIRE`, `PEXPIRE` | `key` và `seconds` hoặc `milliseconds` |
| `EXPIREAT`, `PEXPIREAT` | `key` và `unixTimeSeconds` hoặc `unixTimeMilliseconds` |
| `PERSIST` | `key` |
| `HSET` | `key`, `entries: { field: value }` |
| `HDEL` | `key`, `fields: string[]` |
| `LPUSH`, `RPUSH` | `key`, `values: string[]` |
| `LPOP`, `RPOP` | `key`, tùy chọn `count` |
| `LTRIM` | `key`, `start`, `stop` |
| `SADD`, `SREM`, `ZREM` | `key`, `members: string[]` |
| `ZADD` | `key`, `entries: [{ "score": 1.5, "member": "name" }]`; tùy chọn `condition: "NX"|"XX"`, `change` |

Từ chối `FLUSHDB`, `FLUSHALL`, `CONFIG`, `ACL`, `SCRIPT`, `FUNCTION`, `MODULE`, `EVAL*`, `FCALL*`, `DEBUG`, `MONITOR`, `KEYS`, auth/select, pub/sub, transaction và command không nằm trong allowlist.

Nếu CLI trả `UNSUPPORTED_OPERATION` hoặc `READ_ONLY_VIOLATION`, không đổi công cụ hay raw command để bypass.
