# Redis

## Phạm vi v1

Redis v1 chỉ hỗ trợ read/debug trên standalone hoặc managed single endpoint. Không hỗ trợ mutation, Sentinel, Cluster, blocking command, Pub/Sub, transaction, Lua/functions hoặc module command như `JSON.*` và `FT.*`.

Adapter dùng `@redis/client` qua CLI tin cậy, RESP2, không offline queue, không reconnect/retry và có total deadline xuyên connect, identity cùng command. Không gọi `redis-cli`, không dùng raw argv và không dùng metadata `@read` của server để tự mở command mới.

## Target, TLS và identity

Port mặc định là `6379`; TLS mặc định bật. `--database` là logical database index dạng số nguyên không âm canonical. `--key-prefix` là literal prefix bắt buộc, tối đa 256 UTF-8 bytes và không chứa glob metacharacter.

```text
agent-db target add --id <id> --engine redis --environment <env> \
  --host <host> --database 0 [--port 6379] --key-prefix app: \
  [--tls true] --expected-server-identity <host:port>
```

Redis không cho tắt certificate verification bằng `trust-server-certificate`. Chỉ dùng `--no-tls` khi endpoint thật sự không có TLS và rủi ro đã được chấp nhận; production vẫn bắt buộc TLS và expected identity.

Adapter xác minh logical DB và authenticated user bằng `CLIENT INFO`, đối chiếu principal bằng `ACL WHOAMI`, rồi lấy version/mode/run ID bằng `INFO server`. V1 chỉ chấp nhận `redis_mode=standalone`. `serverIdentity` là endpoint cấu hình đã được TLS xác thực, định dạng `host:port` hoặc `[ipv6]:port`; `instanceRunId` là metadata server-reported nhưng không dùng làm identity ổn định vì đổi sau restart/failover.

Credential read phải có provision evidence khớp credential ID, principal, target fingerprint, key prefix và exact wire-command set. Redis ACL phải giới hạn key pattern theo prefix; guard phía CLI chỉ là defense-in-depth. Internal identity cần quyền tối thiểu cho `CLIENT INFO`, `ACL WHOAMI` và `INFO`. Logical `GET` còn gửi `EXISTS`, `STRLEN` và `GETRANGE` để tạo preview có giới hạn, nên ACL/evidence phải cho phép cả ba command đó.

## Read command

Input là JSON typed với schema riêng theo command; ưu tiên file `.json`:

```json
{"operation":"command","command":"GET","arguments":{"key":"app:user:42"}}
```

```json
{"operation":"command","command":"HSCAN","arguments":{"key":"app:user:42","cursor":"0","match":"profile:*","count":50}}
```

Allowlist v1:

- Metadata/keyspace: `PING`, `DBSIZE`, `TIME`, `INFO`, `SCAN`, `EXISTS`, `TYPE`, `TTL`, `PTTL`, `EXPIRETIME`, `PEXPIRETIME`.
- String: `GET`, `GETRANGE`, `STRLEN`.
- Hash: `HGET`, `HMGET`, `HEXISTS`, `HLEN`, `HSTRLEN`, `HSCAN`.
- List/set: `LLEN`, `LINDEX`, `LRANGE`, `SCARD`, `SISMEMBER`, `SMISMEMBER`, `SSCAN`.
- Sorted set: `ZCARD`, `ZCOUNT`, `ZLEXCOUNT`, `ZSCORE`, `ZMSCORE`, `ZRANK`, `ZREVRANK`, `ZRANGE`, `ZSCAN`.
- Stream: `XLEN`, `XRANGE`, `XREVRANGE`, `XINFO STREAM` không `FULL`.
- Diagnostics: `MEMORY USAGE`, `OBJECT ENCODING`, `OBJECT FREQ`, `OBJECT IDLETIME`, `OBJECT REFCOUNT`, `SLOWLOG LEN`, `SLOWLOG GET`.

Command/subcommand không có trong allowlist bị fail closed. Đặc biệt chặn `KEYS`, `RANDOMKEY`, `MONITOR`, blocking reads, mọi write, `CONFIG`, `DEBUG`, `MODULE`, user-supplied `ACL`/`CLIENT`, `SCRIPT`, `FUNCTION`, `EVAL*`, `FCALL*`, `MULTI`/`EXEC`, `SELECT`, `AUTH`, `SORT*`, Pub/Sub và module command.

`GET` chỉ dùng khi `TYPE` là `string`. Với hash/list/set/sorted-set/stream, chọn command type-specific và field/range nhỏ nhất đủ debug. Các call `TYPE`, `TTL` và preview độc lập, không tạo snapshot nguyên tử; key có thể đổi giữa các call.

## Scope và budget

- Mọi exact key và multi-key phải bắt đầu bằng target `keyPrefix`; v1 chỉ hỗ trợ textual UTF-8 keys.
- `SCAN` nhận `matchSuffix`; adapter tự dựng `MATCH <keyPrefix><suffix>`, chạy đúng một page và trả `nextCursor`. Không tự lặp tới cursor `0`.
- `SCAN`/`HSCAN`/`SSCAN`/`ZSCAN` dùng decimal-string cursor và `COUNT <= min(maxRows, 1000)`. Vì `COUNT` chỉ là hint, page vượt row/byte budget bị từ chối toàn bộ thay vì truncate làm mất cursor data.
- `LRANGE`/`ZRANGE` chỉ nhận rank không âm và độ rộng không quá `maxRows`; `XRANGE`/`XREVRANGE` bắt buộc `count <= maxRows`. Payload stream luôn dùng `start` làm biên thấp và `end` làm biên cao; adapter tự đảo thành wire order `end start` cho `XREVRANGE`.
- `GET` dùng `EXISTS` + `STRLEN` + bounded `GETRANGE` để không tải value lớn không giới hạn. `SLOWLOG GET` bỏ toàn bộ argv và client metadata trước khi xuất JSON.
- `INFO` bắt buộc đúng một section allowlisted; `all`, `default`, `everything` và `modules` không được hỗ trợ.
- Command mutation như `DEL` trả `UNSUPPORTED_OPERATION`; không chuyển sang workflow mutation vì Redis v1 không có plan/approval/execute.

## Schema cache

`schema refresh` không `SCAN` và không sample value. Nó chỉ lưu identity, key prefix, capability cùng `INFO keyspace` của logical DB đã chọn. Thống kê keyspace là database-wide, không phải riêng prefix, và phải được trình bày đúng phạm vi này.
