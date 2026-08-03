# Nguồn chính thức và chính sách cập nhật

Đã kiểm tra các nguồn dưới đây vào ngày 2026-08-03. Atlassian cập nhật ACLI và Rovo MCP độc lập với model/client, vì vậy phải kiểm tra lại khi dùng Skill.

## Thứ tự nguồn

1. `acli --version` và `acli ... --help` của binary đang chạy: nguồn quyết định cú pháp có thể thực thi tại máy hiện tại.
2. [ACLI changelog](https://developer.atlassian.com/cloud/acli/changelog/): nguồn chính thức cho release, breaking change và yêu cầu reauthorization.
3. [Jira command reference](https://developer.atlassian.com/cloud/acli/reference/commands/jira/): cây command Jira Cloud và liên kết tới command lá.
4. [Cài đặt ACLI](https://developer.atlassian.com/cloud/acli/guides/install-acli/) và [nâng cấp ACLI](https://developer.atlassian.com/cloud/acli/guides/update-install-guide/): nền tảng hỗ trợ và quy trình cập nhật.
5. [Jira auth login](https://developer.atlassian.com/cloud/acli/reference/commands/jira-auth-login/): OAuth và API token qua standard input.
6. [Troubleshooting](https://developer.atlassian.com/cloud/acli/guides/troubleshooting-guide/): help path và lỗi thường gặp.
7. [ACLI trong CI](https://developer.atlassian.com/cloud/acli/guides/use-acli-on-ci/): bot account, secret variable và token qua stdin.
8. [Command chaining và output](https://developer.atlassian.com/cloud/acli/guides/manage-command-chaining-and-output-redirection/): JSON, pipe và redirect.

## Atlassian Rovo MCP

1. [Getting started](https://support.atlassian.com/atlassian-rovo-mcp-server/docs/getting-started-with-the-atlassian-remote-mcp-server/): endpoint hiện hành, Codex setup và OAuth.
2. [Supported tools](https://support.atlassian.com/atlassian-rovo-mcp-server/docs/supported-tools/): tool, permission group và scope hiện được expose.
3. [Authentication and authorization](https://support.atlassian.com/atlassian-rovo-mcp-server/docs/authentication-and-authorization/): chọn OAuth 2.1 hoặc API token.
4. [Configuring OAuth 2.1](https://support.atlassian.com/atlassian-rovo-mcp-server/docs/configuring-oauth-2-1/): endpoint Streamable HTTP, consent, cloud ID và lỗi auth.
5. [Setting up clients](https://support.atlassian.com/atlassian-rovo-mcp-server/docs/setting-up-clients/): điều kiện môi trường và client.
6. [Permissions](https://support.atlassian.com/security-and-access-policies/docs/Configure-Atlassian-Rovo-MCP-server-permission/): quyền Read, Write và Search do organization admin kiểm soát.
7. [Domain, authentication và IP controls](https://support.atlassian.com/security-and-access-policies/docs/control-atlassian-rovo-mcp-server-settings/): domain allowlist, API-token policy và IP allowlist.

## Quy tắc freshness

- Đọc changelog khi phiên bản khác lần dùng trước, auth đột nhiên thiếu scope, hoặc command/flag không khớp Skill.
- Ưu tiên trang `developer.atlassian.com/cloud/acli/`; không lấy blog, gist, diễn đàn hoặc tài liệu Jira CLI bên thứ ba làm nguồn cú pháp.
- Một số trang command reference có thể hiển thị ngày cập nhật cũ hơn binary. Trong xung đột cú pháp, dùng `--help` của binary và ghi nhận chênh lệch.
- Không ghi cứng “phiên bản mới nhất” vào automation. Atlassian yêu cầu cập nhật thường xuyên và changelog có thể bổ sung yêu cầu OAuth mới.
- Với MCP, tool schema/list mà server đang expose quyết định input thực thi. Trang Supported tools dùng để xác minh capability và scope, không thay thế schema runtime.
- Dùng endpoint Streamable HTTP mà Getting started hiện công bố. Không quay lại endpoint SSE cũ.

## Phân biệt TWG CLI

Atlassian cũng phát hành TWG CLI `twg`, có cây command và skill dành cho agent riêng. Không trộn `twg jira ...` với `acli jira ...`. Nếu người dùng muốn TWG CLI, dùng [tài liệu TWG CLI](https://developer.atlassian.com/cloud/twg-cli/) và skill chính thức do installer của TWG cung cấp thay vì áp dụng Skill này.
