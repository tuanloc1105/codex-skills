# OCB Jira metadata snapshot

The companion [JSON snapshot](wowocb-metadata.json) covers the 31 projects, 44 boards, 17 issue type IDs, 41 status IDs, and 11 issue link types visible to the authenticated account at retrieval time (2026-09-23). Its `scope` is visibility, not an inventory of every object in the company site.

## Read the snapshot

- Find a project by exact `projects[].key` or `id`; use its `workTypes` map for that project's issue type IDs and allowed status IDs. Resolve the names and categories through top-level `issueTypes` and `statuses`.
- A board's `projectKey` is its location, not proof that every board issue belongs to that project. Check the board filter/configuration for board-scoped work.
- For issue links, use the exact `name` and verify direction through `inward` and `outward`.
- Do not infer that a status is reachable from an issue's current state just because it appears in that work type's status set. Read the issue's live transitions.
- This snapshot does not contain create/edit field schemas, field context options, workflow conditions, permission schemes, assignable users, sprint membership, components, or releases. Fetch the narrow live metadata for the exact target when needed to perform an authorized operation.

## Refresh only when needed

Refresh the affected portion when a project, type, status, board, or link is absent from the snapshot; a live Jira response disagrees with it; Jira rejects a snapshot-derived value; or the user explicitly asks to update the snapshot. A normal write does not itself require a site-wide refresh.

1. Verify the authenticated MCP account and accessible resources. Confirm the resource URL is exactly `https://wowocb.atlassian.net`; retain its returned `cloudId` only in the active call context.
2. Identify the smallest affected scope. Discover the exact read operation and schema when it is deferred. Use `listJiraProjects` for project keys/IDs, `listJiraProjectIssueTypesMetadata` for one project's types, `listJiraStatuses` with `mode: project` for one project's statuses, `listJiraBoards` with a project filter for boards, or `listJiraIssueLinkTypes` for link types. Page until the operation reports completion. Do not use JQL issue rows to infer these catalogs.
3. For a failed create/edit/transition, retrieve the exact issue type's create fields, issue edit metadata, or issue transitions rather than refreshing unrelated catalogs. Check required fields and allowed values against the live result. Do not blindly retry a mutation with an uncertain outcome; read its target first.
4. If this is a repository maintenance task that explicitly includes updating the checked-in snapshot, replace only the affected JSON entries with verified MCP data, record a separate `refreshedAt` date on the affected entries, preserve other sections and the original whole-snapshot `retrievedAt`, and validate JSON and project/type/status references. Otherwise use the newly read values for the current task and report that the checked-in snapshot may be stale; do not silently edit the repository.

For all reads and writes, follow the route, identity, bounds, and risk-tier rules in the parent `SKILL.md`.
