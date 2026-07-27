---
name: interact-with-jira
description: Thao tác Jira Cloud bằng Atlassian CLI chính thức (`acli`), gồm xác thực, tìm kiếm JQL, xem, tạo, sửa, gán, chuyển trạng thái và quản lý work item, project, board, sprint, filter, dashboard, field, comment, attachment, watcher và link. Dùng khi Codex cần chạy, hướng dẫn, tự động hóa hoặc chẩn đoán lệnh `acli jira`; xác minh cú pháp theo phiên bản đang cài và áp dụng cổng an toàn cho thao tác ghi, hàng loạt hoặc phá hủy.
---

# Tương tác với Jira

## Giữ đúng phạm vi

- Chỉ áp dụng cho Jira Cloud qua Atlassian CLI `acli`. Không suy diễn rằng cú pháp này dùng được cho Jira Data Center, Forge CLI, Atlassian MCP hoặc TWG CLI `twg`.
- Nếu người dùng nói “Atlassian CLI” nhưng không nêu binary, kiểm tra executable hoặc hỏi lại khi cả `acli` và `twg` đều khả dụng. Không đổi công cụ ngầm.
- Không gọi Jira REST API để lách thiếu sót của ACLI. Nếu ACLI không hỗ trợ tác vụ, báo giới hạn và xin phép trước khi mở rộng phạm vi sang công cụ khác.

## Xác minh trước khi lập lệnh

1. Chạy `acli --version` và `acli jira --help`.
2. Chạy `acli jira <nhóm> --help`, rồi chạy `--help` trên command lá được định dùng.
3. Dùng cú pháp do binary đang chạy công bố. Không đoán flag từ trí nhớ, ví dụ cũ hoặc tên tương tự của `twg`.
4. Khi cần kiểm tra thay đổi, cài đặt, xác thực hoặc lỗi phiên bản, đọc [nguồn Atlassian chính thức](references/official-sources.md).
5. Trước lần thao tác đầu tiên, đọc [quy trình lệnh và an toàn](references/command-workflows.md). Đọc lại phần liên quan trước thao tác hàng loạt, phá hủy, xác thực hoặc PowerShell.

## Kiểm tra identity và target

- Chạy `acli jira auth status` trước khi truy cập dữ liệu thật. Xác nhận đúng site và tài khoản; che email hoặc site nếu không cần đưa vào chat.
- Dùng `acli jira auth switch --site <site> --email <email>` khi người dùng đã chọn identity khác. Không tự chọn giữa nhiều site/account có khả năng hợp lệ.
- Ưu tiên OAuth qua `acli jira auth login --web` cho phiên tương tác.
- Với API token, chỉ truyền token qua standard input từ secret store, biến môi trường hoặc file local không được commit. Không đặt token vào argument, script, lịch sử shell, log hay chat.
- Không đăng xuất, cài đặt, nâng cấp hoặc thay đổi credential nếu người dùng chỉ yêu cầu thao tác Jira.

## Phân loại hành động

### Chỉ đọc

Cho phép thực hiện trong phạm vi yêu cầu sau khi xác minh target:

- `--version`, `--help`, `jira auth status`.
- Các command `list`, `search`, `view`, `count`, `get` còn được phiên bản hiện tại hỗ trợ.
- Tra cứu work item, project, board, sprint, filter và dashboard.

Giới hạn JQL, field và số lượng kết quả ở mức nhỏ nhất đủ dùng. Ưu tiên `--json` khi cần xử lý bằng máy; không dùng `--paginate` nếu chưa thật sự cần toàn bộ tập kết quả.

### Thay đổi có target rõ ràng

Yêu cầu ban đầu của người dùng có thể cho phép đúng một thay đổi cụ thể như tạo work item, sửa field đã nêu, gán assignee, chuyển trạng thái hoặc thêm comment. Trước khi chạy:

1. Xác minh site/account và command help.
2. Đọc lại work item/project hiện tại nếu điều đó giúp phát hiện target sai hoặc tránh ghi đè.
3. Tóm tắt target và trường sẽ đổi khi lệnh không thể hiện rõ trong yêu cầu.
4. Giữ prompt xác nhận tương tác của ACLI; chỉ thêm `--yes` khi cổng phê duyệt bên dưới đã được đáp ứng.
5. Sau khi chạy, kiểm tra exit code và đọc lại đối tượng quan trọng để xác nhận kết quả.

Không xem yêu cầu chung như “dọn Jira” hoặc “cập nhật các ticket này” là quyền thực hiện mọi thay đổi có thể suy ra.

### Hàng loạt hoặc phá hủy

Luôn thực hiện read-only preflight và xin xác nhận rõ ràng ngay trước khi chạy đối với:

- Mọi mutation chọn target bằng JQL, filter, file hoặc nhiều key.
- Delete, archive/unarchive, restore, thay owner, xóa/reset cấu hình hoặc xóa comment, attachment, watcher, link.
- Xóa/archive project, board, sprint hoặc custom field.
- Bất kỳ hành động nào có thể ảnh hưởng workflow, quyền truy cập, báo cáo hoặc nhiều người dùng.

Preflight phải cho biết site/account, command đầy đủ đã redact secret, selector, số lượng và danh sách key/ID khi khả thi, các field/status sẽ đổi và khả năng hoàn tác. Dừng sau khi xin xác nhận; chỉ thực thi nếu người dùng đồng ý trong chat hiện tại với đúng target và operation đó. Preview lại nếu selector, dữ liệu, identity hoặc command thay đổi.

Không dùng `--ignore-errors` mặc định. Không tự retry mutation khi kết quả không xác định; đọc lại trạng thái trước, báo phần thành công/thất bại và xin quyết định mới.

## Thực thi và báo cáo

- Truyền native arguments dưới dạng argument vector/array, không ghép một chuỗi shell từ dữ liệu Jira hoặc dữ liệu người dùng.
- Dùng file JSON/ADF cho payload phức tạp; xem schema mẫu từ `--generate-json` của đúng phiên bản và rà soát file trước khi gửi.
- Kiểm tra native exit code trước khi parse hoặc lọc output. Không coi output một phần là thành công toàn bộ.
- Redact token, email không cần thiết, nội dung riêng tư và PII trước khi đưa kết quả vào chat.
- Báo command family đã dùng, site đã được xác minh, target, kết quả, phần bị giới hạn và kiểm tra sau ghi. Không lặp lại secret hoặc payload nhạy cảm.

## Dừng an toàn

Dừng và hỏi lại khi site, account, project, work item, selector hoặc mutation còn mơ hồ; khi `--help` không khớp ví dụ; khi quyền/reauthorization bị thiếu; hoặc khi hoàn tất đòi hỏi REST API, browser automation hay CLI khác. Không tạo workaround âm thầm.
