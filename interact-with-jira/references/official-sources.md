# Nguồn chính thức và chính sách cập nhật

Đã kiểm tra các nguồn dưới đây vào ngày 2026-07-27. Atlassian cập nhật ACLI độc lập với model và mỗi bản ACLI chỉ được hỗ trợ trong một khoảng thời gian hữu hạn, vì vậy phải kiểm tra lại khi dùng Skill.

## Thứ tự nguồn

1. `acli --version` và `acli ... --help` của binary đang chạy: nguồn quyết định cú pháp có thể thực thi tại máy hiện tại.
2. [ACLI changelog](https://developer.atlassian.com/cloud/acli/changelog/): nguồn chính thức cho release, breaking change và yêu cầu reauthorization.
3. [Jira command reference](https://developer.atlassian.com/cloud/acli/reference/commands/jira/): cây command Jira Cloud và liên kết tới command lá.
4. [Cài đặt ACLI](https://developer.atlassian.com/cloud/acli/guides/install-acli/) và [nâng cấp ACLI](https://developer.atlassian.com/cloud/acli/guides/update-install-guide/): nền tảng hỗ trợ và quy trình cập nhật.
5. [Jira auth login](https://developer.atlassian.com/cloud/acli/reference/commands/jira-auth-login/): OAuth và API token qua standard input.
6. [Troubleshooting](https://developer.atlassian.com/cloud/acli/guides/troubleshooting-guide/): help path và lỗi thường gặp.
7. [ACLI trong CI](https://developer.atlassian.com/cloud/acli/guides/use-acli-on-ci/): bot account, secret variable và token qua stdin.
8. [Command chaining và output](https://developer.atlassian.com/cloud/acli/guides/manage-command-chaining-and-output-redirection/): JSON, pipe và redirect.

## Quy tắc freshness

- Đọc changelog khi phiên bản khác lần dùng trước, auth đột nhiên thiếu scope, hoặc command/flag không khớp Skill.
- Ưu tiên trang `developer.atlassian.com/cloud/acli/`; không lấy blog, gist, diễn đàn hoặc tài liệu Jira CLI bên thứ ba làm nguồn cú pháp.
- Một số trang command reference có thể hiển thị ngày cập nhật cũ hơn binary. Trong xung đột cú pháp, dùng `--help` của binary và ghi nhận chênh lệch.
- Không ghi cứng “phiên bản mới nhất” vào automation. Atlassian yêu cầu cập nhật thường xuyên và changelog có thể bổ sung yêu cầu OAuth mới.

## Phân biệt TWG CLI

Atlassian cũng phát hành TWG CLI `twg`, có cây command và skill dành cho agent riêng. Không trộn `twg jira ...` với `acli jira ...`. Nếu người dùng muốn TWG CLI, dùng [tài liệu TWG CLI](https://developer.atlassian.com/cloud/twg-cli/) và skill chính thức do installer của TWG cung cấp thay vì áp dụng Skill này.
