# Hợp đồng CLI

## Invocation

Dùng entrypoint của bản skill đã cài:

```text
node <installed-skill-dir>/scripts/data-debug/bin/data-debug.js <command> [options]
```

CLI yêu cầu Node.js 22 trở lên. `doctor` trả `supportedNode` và trạng thái từng driver; không tiếp tục live command nếu runtime không đạt.

Gọi process bằng argv array khi host hỗ trợ; không ghép secret vào command string. Chạy `--help` để xem source of truth cho flags của phiên bản đang cài.

CLI chỉ có các command:

```text
data-debug doctor
data-debug test
data-debug inspect
data-debug read
data-debug mutation preview
data-debug mutation execute <connection-options> --plan <id> --approved <hash>
```

## Connection

Chọn đúng một nguồn connection. Với URI, engine được suy ra từ scheme:

```text
--connection-env <URI_ENV_NAME> [--env-file <path>]
```

Với direct flags, truyền engine tường minh:

```text
--engine <engine> --host <host> [--port <port>] --database <database-or-index> \
--username <username> [--password-env <PASSWORD_ENV_NAME>] [--env-file <path>]
```

`--port` có default theo engine. `--username` là bắt buộc với database SQL/MongoDB và tùy chọn cho Redis; `--password-env` có thể bỏ khi server dùng passwordless/local authentication.

Chỉ truyền **tên** biến qua `--connection-env`/`--password-env`, không truyền giá trị. `--env-file` là file local chứa `KEY=value`; không đưa file này vào repository hoặc tool output.

Khi dùng direct flags, xem `--help` cho option engine-specific như Oracle service, MongoDB auth source, Redis key prefix và TLS/encryption. Connection có secret đến host ngoài loopback phải dùng transport mã hóa và xác minh certificate. Chỉ dùng `--allow-insecure-credential-transport` sau khi người dùng chấp nhận rõ ràng rủi ro lộ credential/data; flag này xuất hiện trong target preview và được bind vào target fingerprint. Không bật cơ chế bỏ kiểm tra certificate chỉ để vượt lỗi kết nối.

CLI stateless về project/credential: không project binding, target registry, vault, schema cache, runtime trust receipt hoặc local-TTY setup. Một plan mutation ngắn hạn là state duy nhất; plan không chứa raw credential. `mutation execute` phải nhận lại cùng connection source để CLI kiểm tra target fingerprint và đọc secret mới từ environment.

## Input và output

`read` và `mutation preview` nhận đúng một input source:

```text
--file <path>
--text <value>
--stdin
```

Ưu tiên `--file` cho SQL/JSON dài và trên Windows. Không đưa credential kết nối vào input source. Payload mutation sẽ xuất hiện nguyên vẹn trong preview, nên cân nhắc dữ liệu nhạy cảm trước khi đưa vào chat.

Dùng `--max-rows` cho `read` và `--timeout-ms` cho live commands. Bắt đầu với giới hạn nhỏ; kiểm tra các field `truncated`, `truncationReason` và counters trước khi kết luận dữ liệu đầy đủ.

Mỗi lệnh trả đúng một JSON object: thành công trên stdout với `ok: true`, lỗi trên stderr với `ok: false` và `error.code`. Parse field JSON thay vì dựa vào message tự do; không để stderr chứa secret.

`mutation preview` còn nhận `--transaction <auto|always|never>`. Giữ mặc định `auto` trừ khi semantics của operation yêu cầu khác; `always` chỉ được hỗ trợ cho PostgreSQL. Transaction mode đã resolve thuộc approval surface và không được đổi lúc execute.

## Ví dụ

```text
data-debug test --connection-env APP_DATABASE_URL --env-file .env.local
data-debug inspect --connection-env APP_MONGODB_URI --timeout-ms 15000
data-debug read --engine sqlserver --host db.internal --port 1433 --database app \
  --username app_reader --password-env APP_DB_PASSWORD --file query.sql --max-rows 100
data-debug mutation preview --connection-env APP_REDIS_URL \
  --file mutation.json
data-debug mutation execute --connection-env APP_REDIS_URL \
  --plan <plan-id> --approved <approval-hash>
```

Các ví dụ dùng `data-debug` như tên ngắn cho command vector Node.js ở trên; không yêu cầu cài global binary.
