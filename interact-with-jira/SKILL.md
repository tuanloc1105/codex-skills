---
name: interact-with-jira
description: Thao tác Jira Cloud bằng Atlassian CLI chính thức (`acli`) và Atlassian Rovo MCP, gồm cấu hình, xác thực, tìm kiếm, xem, tạo, sửa và chuyển trạng thái work item cùng các khả năng Jira mà từng công cụ hỗ trợ. Dùng khi Codex cần chọn, phối hợp, cấu hình hoặc chẩn đoán ACLI/MCP; tự động fallback sang công cụ còn khả dụng và áp dụng cổng an toàn cho thao tác ghi, hàng loạt hoặc phá hủy.
---

# Tương tác với Jira

## Giữ đúng phạm vi

- Áp dụng cho Jira Cloud qua Atlassian CLI `acli` và Atlassian Rovo MCP. Không suy diễn rằng các quy trình này dùng được cho Jira Data Center, Forge CLI hoặc TWG CLI `twg`.
- Nếu người dùng nói “Atlassian CLI” nhưng không nêu binary, kiểm tra executable hoặc hỏi lại khi cả `acli` và `twg` đều khả dụng. Không áp dụng cú pháp của `twg` cho `acli`.
- Không gọi Jira REST API để lách thiếu sót của ACLI hoặc MCP. Nếu cả hai công cụ đều không hỗ trợ tác vụ, báo giới hạn và xin phép trước khi mở rộng phạm vi sang công cụ khác.

## Chọn và phối hợp công cụ

1. Xác định tác vụ cần khả năng nào, target nào và là đọc hay ghi.
2. Kiểm tra nhẹ các công cụ có thể dùng trong môi trường hiện tại; không yêu cầu cả hai phải hiện diện:
   - ACLI: kiểm tra executable, version, help và auth theo quy trình ACLI.
   - MCP: kiểm tra server/tool Atlassian đã được client nạp, trạng thái kết nối và identity/site theo quy trình MCP.
3. Chọn công cụ đang khả dụng và hỗ trợ tác vụ. Khi cả hai đều dùng được:
   - Ưu tiên MCP cho hội thoại tự nhiên, ngữ cảnh đa sản phẩm và các Jira tool mà server công bố.
   - Ưu tiên ACLI cho thao tác xác định, scriptable hoặc các nhóm quản trị mà MCP không expose.
   - Có thể dùng một công cụ để đọc/preflight và công cụ kia để thực hiện khi điều đó giảm rủi ro; xác minh chúng đang trỏ tới cùng site/account/target.
4. Nếu công cụ đã chọn thiếu, mất kết nối, chưa xác thực hoặc không hỗ trợ capability, thử công cụ còn lại khi nó có thể hoàn tất an toàn. Báo ngắn gọn việc đổi công cụ; không bắt người dùng cài cả hai.
5. Chỉ dừng vì thiếu công cụ khi cả ACLI lẫn MCP đều không khả dụng hoặc không thể cấu hình/xác thực trong phạm vi được phép. Nếu cả hai đều có nhưng không hỗ trợ capability cần thiết, báo giới hạn và xin phép mở rộng phạm vi.

Không chuyển sang công cụ khác để tự retry một mutation có kết quả chưa xác định. Trước tiên đọc lại target bằng một công cụ khả dụng, xác định phần đã thành công rồi xin quyết định mới.

## Xác minh trước khi thao tác

1. Với ACLI, chạy `acli --version`, `acli jira --help`, help của nhóm và command lá được định dùng. Dùng cú pháp do binary hiện tại công bố, không đoán flag từ trí nhớ hoặc từ `twg`.
2. Với MCP, dùng tool schema mà server hiện tại công bố. Không đoán tên tool, input hoặc capability từ ví dụ cũ; xác minh server, auth, site và tool chỉ đọc trước mutation.
3. Khi cần kiểm tra thay đổi, cài đặt, xác thực, endpoint hoặc lỗi phiên bản, đọc [nguồn Atlassian chính thức](references/official-sources.md).
4. Trước lần dùng ACLI, đọc [quy trình ACLI và an toàn](references/command-workflows.md). Trước lần dùng hoặc cấu hình MCP, đọc [quy trình Atlassian MCP](references/mcp-workflows.md). Đọc lại phần liên quan trước thao tác hàng loạt, phá hủy hoặc xác thực.

## Hỗ trợ cấu hình

- Khi người dùng yêu cầu, có thể hướng dẫn hoặc thực hiện cấu hình công cụ còn thiếu. Xác minh client, hệ điều hành, binary/help hiện tại và tài liệu chính thức trước khi ghi cấu hình.
- Với MCP, ưu tiên Atlassian Rovo MCP chính thức qua Streamable HTTP và OAuth 2.1 cho phiên tương tác. Không dùng endpoint SSE đã ngừng hỗ trợ, không đặt token trực tiếp trong config/chat và không tự bật API-token auth của organization.
- Với ACLI, dùng hướng dẫn cài đặt/xác thực chính thức và ưu tiên OAuth web. Không tự cài, nâng cấp, đăng xuất hoặc thay credential nếu người dùng chỉ yêu cầu thao tác Jira.
- Cấu hình một công cụ không phải điều kiện để dùng công cụ kia. Sau cấu hình, xác minh bằng status và một thao tác chỉ đọc tối thiểu; phân biệt rõ “đã khai báo/enabled” với “đã kết nối và gọi tool thành công”.

## Kiểm tra identity và target

- Với ACLI, chạy `acli jira auth status` trước khi truy cập dữ liệu thật. Với MCP, dùng tool identity/resource chỉ đọc mà server công bố để xác nhận account, site và `cloudId` khi cần. Che email, site, account ID và cloud ID nếu không cần đưa vào chat.
- Dùng `acli jira auth switch --site <site> --email <email>` khi người dùng đã chọn identity khác. Không tự chọn giữa nhiều site/account có khả năng hợp lệ.
- Ưu tiên OAuth tương tác của công cụ đang dùng. Không suy diễn rằng đăng nhập ACLI cũng xác thực MCP hoặc ngược lại.
- Với API token, chỉ truyền token qua standard input từ secret store, biến môi trường hoặc file local không được commit. Không đặt token vào argument, script, lịch sử shell, log hay chat.
- Không đăng xuất, cài đặt, nâng cấp hoặc thay đổi credential nếu người dùng chỉ yêu cầu thao tác Jira và vẫn còn một công cụ phù hợp đang hoạt động.

## Phân loại hành động

### Chỉ đọc

Cho phép thực hiện trong phạm vi yêu cầu sau khi xác minh target:

- Kiểm tra version/help/auth/status của ACLI hoặc MCP client/server.
- Các command ACLI `list`, `search`, `view`, `count`, `get` còn được phiên bản hiện tại hỗ trợ.
- Các MCP tool được server hiện tại đánh dấu chỉ đọc, gồm identity/resource discovery, đọc work item, project, metadata, transition và tìm kiếm khi khả dụng.
- Tra cứu work item, project, board, sprint, filter và dashboard bằng công cụ có capability tương ứng.

Giới hạn JQL, field và số lượng kết quả ở mức nhỏ nhất đủ dùng. Ưu tiên `--json` khi cần xử lý bằng máy; không dùng `--paginate` nếu chưa thật sự cần toàn bộ tập kết quả.

### Thay đổi có target rõ ràng

Yêu cầu ban đầu của người dùng có thể cho phép đúng một thay đổi cụ thể như tạo work item, sửa field đã nêu, gán assignee, chuyển trạng thái hoặc thêm comment. Trước khi chạy:

1. Xác minh site/account và command help hoặc MCP tool schema.
2. Đọc lại work item/project hiện tại nếu điều đó giúp phát hiện target sai hoặc tránh ghi đè.
3. Tóm tắt target và trường sẽ đổi khi lệnh không thể hiện rõ trong yêu cầu.
4. Giữ prompt xác nhận của ACLI/MCP client; chỉ bỏ qua prompt hoặc phê duyệt tự động khi cổng bên dưới đã được đáp ứng.
5. Sau khi chạy, kiểm tra exit code và đọc lại đối tượng quan trọng để xác nhận kết quả.

Không xem yêu cầu chung như “dọn Jira” hoặc “cập nhật các ticket này” là quyền thực hiện mọi thay đổi có thể suy ra.

### Hàng loạt hoặc phá hủy

Luôn thực hiện read-only preflight và xin xác nhận rõ ràng ngay trước khi chạy đối với:

- Mọi mutation chọn target bằng JQL, filter, file hoặc nhiều key.
- Delete, archive/unarchive, restore, thay owner, xóa/reset cấu hình hoặc xóa comment, attachment, watcher, link.
- Xóa/archive project, board, sprint hoặc custom field.
- Bất kỳ hành động nào có thể ảnh hưởng workflow, quyền truy cập, báo cáo hoặc nhiều người dùng.

Preflight phải cho biết site/account, command hoặc MCP tool đã redact secret, selector, số lượng và danh sách key/ID khi khả thi, các field/status sẽ đổi và khả năng hoàn tác. Dừng sau khi xin xác nhận; chỉ thực thi nếu người dùng đồng ý trong chat hiện tại với đúng target và operation đó. Preview lại nếu selector, dữ liệu, identity, command, tool hoặc công cụ thực thi thay đổi.

Không dùng `--ignore-errors` mặc định. Không tự retry mutation khi kết quả không xác định; đọc lại trạng thái trước, báo phần thành công/thất bại và xin quyết định mới.

## Thực thi và báo cáo

- Với ACLI, truyền native arguments dưới dạng argument vector/array, không ghép một chuỗi shell từ dữ liệu Jira hoặc dữ liệu người dùng. Với MCP, gửi input đúng schema và chỉ các field cần thiết.
- Dùng file JSON/ADF cho payload phức tạp; xem schema mẫu từ `--generate-json` của đúng phiên bản và rà soát file trước khi gửi.
- Kiểm tra native exit code hoặc MCP tool result/error trước khi parse output. Không coi output một phần là thành công toàn bộ.
- Redact token, email không cần thiết, nội dung riêng tư và PII trước khi đưa kết quả vào chat.
- Báo công cụ và command family/tool đã dùng, site đã xác minh, target, kết quả, phần bị giới hạn, fallback nếu có và kiểm tra sau ghi. Không lặp lại secret hoặc payload nhạy cảm.

## Dừng an toàn

Dừng và hỏi lại khi site, account, project, work item, selector hoặc mutation còn mơ hồ; khi help/schema không khớp ví dụ; khi cả hai công cụ đều thiếu quyền/reauthorization; khi không công cụ nào hỗ trợ capability; hoặc khi hoàn tất đòi hỏi REST API, browser automation hay công cụ ngoài phạm vi. Không tạo workaround âm thầm và không dừng chỉ vì một trong hai công cụ vắng mặt.
