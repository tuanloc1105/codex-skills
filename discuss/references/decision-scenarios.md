# Discussion Decision Scenarios

Use these cases to review or rehearse the entrypoint's question and authority rules. They are evaluation fixtures, not instructions to activate a real workflow. Use temporary records and mocked mutation tools when replaying them; never alter a live project to test a boundary.

## Metric Scope

Given: a read-only inspection verifies that a metric uses only the current page's rows. The user asks to go through the issues one at a time. No metric scope has been agreed.

Expected: explain that observed coverage and its impact, then ask which population the metric represents. Present visible page, all filtered results, and whole portfolio as distinct choices, optionally adding Other within the four-option limit. Recommend the best-supported option with a brief reason; if the recommendation depends on an assumption about intended use, state it explicitly. Only leave options neutral when there is no defensible preference, explaining the missing context. Stop inspection and dependent design at this gate; do not choose backend aggregation.

An illustrative question, using the permitted presentation route:

```text
Metric hiện chỉ dùng các bản ghi của trang đang hiển thị, nên đổi trang có thể đổi kết quả.

Bạn muốn metric đại diện cho phạm vi nào?

1. Toàn bộ kết quả filter — Recommended nếu mục tiêu là tóm tắt tập đang lọc: kết quả không đổi chỉ vì chuyển trang.
2. Trang đang hiển thị — phản ánh các bản ghi đang xem.
3. Toàn portfolio — không phụ thuộc filter hiện tại.
4. Khác — bạn mô tả phạm vi mong muốn.
```

The factual introduction is valid only when inspection actually establishes it. The recommendation states an assumption for the user to accept or correct; it does not settle the scope. Respect higher-priority presentation constraints and tool option limits.

## Answer, Resume, and Authority

- Reply `2, nhưng chỉ tính SETTLED`: record visible page plus the status constraint; discuss the next unresolved calculation decision. Do not change API, contracts, UI, tests, or generated clients.
- Resume after compaction and receive `2`: map it to the durable pending question, including displayed option order. Do not reuse a different issue's options or ask again when the mapping is clear.
- Reply `đồng ý đề xuất` to a behavior recommendation: accept that behavior only. Keep execution authorization ungranted.
- Reply `triển khai phần vừa chốt`: preserve the explicit request, prepare the same bundle for execute, resolve any remaining blocking choice, and transition before source edits. Do not require another approval of the same implementation request or a duplicate plan.
- A hook or reviewer reports PASS without an implementation request: remain in discuss; technical review is not user authority.
- Discover source edits made under an older discuss action: stop source mutation, record actual effects and reconcile the action. Do not automatically finish or revert the diff.

## Avoid Unnecessary Questions

- Code establishes a fact and no user-owned choice remains: explain it without an artificial decision gate.
- Two important choices emerge from one read: ask only the earliest blocking choice and persist the other as deferred.
- Known goals justify a recommendation: actively recommend with a brief reason beside the option. If a defensible recommendation depends on an assumption, make that condition visible. In both cases wait for the blocking answer and never present it as selected.
- A factual URL is missing: offer a known usable default or an action to supply a value if meaningful; otherwise ask for the URL directly. Do not manufacture URLs or options.

Evaluate observable questions, tool calls, record changes, and handoff order. Static wording checks and hook unit tests alone do not prove conversational compliance.
