# Quy trình Atlassian Rovo MCP cho Jira Cloud

## Mục lục

- Khám phá và chọn MCP client
- Cấu hình trên Codex
- Xác thực và target
- Đọc dữ liệu
- Mutation
- Fallback với ACLI
- Chẩn đoán

## Khám phá và chọn MCP client

Atlassian Rovo MCP là remote Streamable HTTP server. Trước khi cấu hình, xác định MCP client người dùng đang dùng và kiểm tra help/tài liệu hiện hành của client đó; không sao chép cú pháp Codex sang client khác.

Endpoint chính thức hiện hành:

```text
https://mcp.atlassian.com/v1/mcp/authv2
```

Không cấu hình endpoint `/v1/sse`. Không thay Atlassian Rovo MCP chính thức bằng package MCP Jira bên thứ ba nếu người dùng chưa yêu cầu và chưa đánh giá rủi ro.

## Cấu hình trên Codex

Xác minh CLI trước:

```text
codex --version
codex mcp --help
codex mcp add --help
codex mcp login --help
```

Khi người dùng đã yêu cầu cấu hình, thêm server:

```text
codex mcp add atlassian --url https://mcp.atlassian.com/v1/mcp/authv2
codex mcp login atlassian
```

OAuth mở trình duyệt để người dùng đăng nhập và consent. Không tự chọn account/site khi có nhiều lựa chọn. Không đưa access token vào command, config hoặc chat.

Cấu hình an toàn đề xuất trong `~/.codex/config.toml` hoặc project config được người dùng chọn:

```toml
[mcp_servers.atlassian]
url = "https://mcp.atlassian.com/v1/mcp/authv2"
auth = "oauth"
default_tools_approval_mode = "writes"
enabled = true
```

Không ghi đè table đã có. Đọc cấu hình hiện tại, giữ nguyên field không liên quan và chỉ thêm/sửa giá trị người dùng yêu cầu. Sau thay đổi, chạy:

```text
codex mcp list
codex mcp get atlassian
```

`enabled` và `OAuth` chỉ xác nhận cấu hình đã được nhận. Mở phiên Codex mới khi cần, kiểm tra `/mcp`, rồi gọi đúng một tool chỉ đọc tối thiểu để xác nhận server đã kết nối và OAuth thực sự hoạt động.

## Xác thực và target

- Ưu tiên OAuth 2.1 cho phiên tương tác. API token dành cho non-interactive/M2M và chỉ dùng khi organization cho phép cùng người dùng yêu cầu.
- Dùng `atlassianUserInfo` và `getAccessibleAtlassianResources`, hoặc tool tương đương mà server hiện tại công bố, để xác minh identity và site/cloud ID.
- Nếu có nhiều site, không tự chọn chỉ từ tên gần giống. Xin người dùng chọn hoặc đối chiếu target đã nêu.
- Quyền MCP không vượt quyền Jira của user. Organization admin còn có thể chặn riêng nhóm Read, Write hoặc Search, domain OAuth và IP.

## Đọc dữ liệu

Chỉ gọi tool server hiện tại expose và dùng schema được công bố. Các capability Jira thường có gồm đọc work item, project/type metadata, transition, remote link, tìm account và tìm kiếm JQL.

Giữ truy vấn hẹp:

- Chỉ yêu cầu field cần thiết.
- Giới hạn JQL/result count.
- Không lấy description, comment, attachment hoặc dữ liệu người dùng nếu tác vụ không cần.
- Redact email, account ID, cloud ID, site và nội dung riêng tư trước khi báo cáo.

## Mutation

Các capability ghi thường gặp gồm tạo/sửa work item, comment, worklog và transition. Trước mỗi mutation:

1. Xác minh identity/site và tool schema.
2. Đọc target hoặc metadata/transition cần thiết.
3. Giữ approval cho write tools.
4. Với hàng loạt hoặc phá hủy, thực hiện preflight và xin xác nhận theo `SKILL.md`.
5. Sau tool result thành công, đọc lại target quan trọng.

Nếu tool timeout hoặc trả kết quả không rõ, không gọi lại bằng MCP hay ACLI ngay. Đọc lại target trước để tránh mutation trùng.

## Fallback với ACLI

- Nếu MCP chưa cấu hình, chưa xác thực, bị policy chặn hoặc không expose capability, dùng ACLI khi ACLI khả dụng và hỗ trợ tác vụ.
- Nếu ACLI thiếu command/capability nhưng MCP có tool phù hợp, dùng MCP.
- Một công cụ đang hoạt động là đủ; không yêu cầu cấu hình công cụ còn lại chỉ để hoàn tất tác vụ.
- Khi đổi công cụ giữa preflight và mutation, xác minh lại site/account/target và preview lại nếu command/tool hoặc tác động thay đổi.

## Chẩn đoán

- Server không xuất hiện: kiểm tra config scope, `codex mcp list`, client restart/new session và `/mcp`.
- `enabled` nhưng không gọi được tool: chạy live check chỉ đọc; kiểm tra OAuth, token hết hạn, organization permission, domain/IP allowlist và network.
- OAuth không mở hoặc callback lỗi: chạy lại login sau khi kiểm tra browser/callback và domain allowlist; không tự chuyển sang token.
- `Access denied`: xác minh quyền Jira của user và nhóm Read/Write/Search trong Atlassian Administration.
- Không có tool mong đợi: kiểm tra danh sách tool chính thức và tool schema hiện tại; dùng ACLI nếu có capability tương ứng.
- Nhiều site hoặc sai `cloudId`: gọi lại resource discovery và yêu cầu người dùng chọn target.
