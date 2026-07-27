# Quy trình ACLI cho Jira Cloud

## Mục lục

- Khám phá command
- Xác thực
- Đọc dữ liệu
- Mutation một target
- Mutation hàng loạt hoặc phá hủy
- PowerShell
- Chẩn đoán

## Khám phá command

Luôn đi từ root đến command lá:

```text
acli --version
acli jira --help
acli jira workitem --help
acli jira workitem search --help
```

Các nhóm Jira Cloud thường gặp gồm `auth`, `workitem`, `project`, `board`, `sprint`, `filter`, `dashboard` và `field`. Danh sách này chỉ để định tuyến; output `--help` của binary hiện tại quyết định command và flag thực tế.

Một số command có nhãn `[DEPRECATED]`. Chọn command thay thế mà help hiện tại đề xuất; không tạo automation mới dựa trên alias deprecated.

## Xác thực

Kiểm tra trạng thái trước:

```text
acli jira auth status
```

Trong phiên tương tác, ưu tiên OAuth:

```text
acli jira auth login --web
```

Nếu phải dùng API token, lấy site/email từ người dùng hoặc cấu hình được phép dùng và đưa token qua stdin. Không viết token trực tiếp sau `echo`, trong argument hoặc trong file được theo dõi bởi Git.

Sau khi đổi account, chạy lại `acli jira auth status`. Nếu ACLI báo site admin phải authorize/reauthorize app, dừng và đưa đúng thông báo cho người dùng; không thử né OAuth scope.

## Đọc dữ liệu

Tìm kiếm có giới hạn và chỉ lấy field cần thiết:

```text
acli jira workitem search --jql "project = TEAM AND statusCategory != Done" --fields "key,summary,status,assignee" --limit 50 --json
```

Xem một work item:

```text
acli jira workitem view TEAM-123 --fields "key,summary,status,assignee,description" --json
```

Quy tắc:

- Xác minh JQL với `search` trước khi tái sử dụng nó cho mutation.
- Dùng `--count` khi chỉ cần số lượng.
- Không dùng `*all`, comment, description hoặc attachment nếu câu hỏi không cần dữ liệu đó.
- Parse JSON thay vì dựa vào cột văn bản khi kết quả được dùng cho bước tự động tiếp theo.

## Mutation một target

Quy trình mẫu:

1. Chạy help của command lá.
2. View target hiện tại.
3. Lập argument vector với đúng key/ID và field được người dùng yêu cầu.
4. Chạy mutation một lần.
5. Kiểm tra exit code rồi view lại target.

Ví dụ tạo work item chỉ minh họa cấu trúc; kiểm tra help trước khi dùng:

```text
acli jira workitem create --project TEAM --type Task --summary "Tóm tắt" --json
```

Với description dài, ADF hoặc nhiều custom field, dùng `--generate-json`, chỉnh file cục bộ, kiểm tra nội dung rồi dùng `--from-json`. Không đoán schema JSON.

## Mutation hàng loạt hoặc phá hủy

Không chạy ngay mutation dùng `--jql`, `--filter`, `--from-file` hoặc nhiều key. Thực hiện:

1. Dùng chính selector đó để search/count ở chế độ chỉ đọc.
2. Thu hẹp selector; lấy danh sách key/ID cố định khi khả thi.
3. Trình bày site/account, command, selector, số lượng, target và tác động.
4. Xin xác nhận trong chat và dừng.
5. Sau xác nhận, dựng lại command từ dữ liệu đã duyệt; không tái sử dụng selector đã thay đổi.
6. Chỉ lúc này mới dùng `--yes` nếu cần chạy không tương tác.
7. Không dùng `--ignore-errors`; nếu một phần thất bại, không retry cả batch.
8. Đọc lại các target hoặc search cùng tập key để xác minh.

Delete project, board, sprint, field hoặc work item có thể không cung cấp dry-run hay prompt nhất quán. Không coi việc command thiếu `--yes` là bằng chứng rằng nó an toàn.

## PowerShell

Dùng PowerShell 7 khi có sẵn. Truyền argument bằng array và kiểm tra `$LASTEXITCODE` trước khi xử lý output:

```powershell
$acliArgs = @(
    'jira', 'workitem', 'search',
    '--jql', 'project = TEAM AND statusCategory != Done',
    '--fields', 'key,summary,status',
    '--limit', '50',
    '--json'
)
$jsonText = & acli @acliArgs
$acliExitCode = $LASTEXITCODE
if ($acliExitCode -ne 0) {
    throw "acli failed with exit code $acliExitCode"
}
$items = $jsonText | ConvertFrom-Json
```

Đăng nhập bằng token từ file local được bảo vệ:

```powershell
$loginArgs = @(
    'jira', 'auth', 'login',
    '--site', 'mysite.atlassian.net',
    '--email', 'user@example.com',
    '--token'
)
Get-Content -LiteralPath $tokenFile | & acli @loginArgs
$acliExitCode = $LASTEXITCODE
if ($acliExitCode -ne 0) {
    throw "acli login failed with exit code $acliExitCode"
}
```

Không in `$tokenFile` hoặc nội dung token. Không đặt token trong `$loginArgs`.

## Chẩn đoán

- `command not found`: kiểm tra `Get-Command acli`/`command -v acli` và PATH; không tự tải binary nếu chưa được yêu cầu.
- `unknown command` hoặc `unknown flag`: chạy lại help từ cấp cha đến command lá và kiểm tra changelog.
- `401`, `403` hoặc thiếu scope: xác minh auth status, site, account, quyền Jira và yêu cầu reauthorization hiện hành; không đổi token hay account ngầm.
- Không tìm thấy work item: xác minh site, project key, quyền browse và JQL bằng search nhỏ.
- Batch thành công một phần: giữ output gốc đã redact, đọc lại trạng thái và báo từng target; không tự retry mutation.
- Output parse lỗi: kiểm tra command có hỗ trợ `--json`, exit code và phần stderr trước khi sửa parser.
