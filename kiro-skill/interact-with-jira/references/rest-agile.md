# Jira Software REST workflows

All registered Agile capabilities are Tier A. Unregistered Agile capabilities require a dynamic contract; every Agile mutation is Tier C.

- Establish board provenance from explicit ID or bounded project/location/name filter. Board listing requires narrowing.
- Request required issue fields and narrow JQL. Respect permissions and page ceilings.
- For registered reads, use only their exact enhanced backlog/sprint-issue paths. For dynamic capabilities, require the exact current official endpoint page; do not substitute deprecated neighbors or synthesize routes.
- Treat `nextPageToken` as opaque; do not mix pagination models or exceed ceilings.
- Bind sprint IDs to an explicit board/task sprint; validate `originBoardId` when returned and constrain state filters.
- Versions are releases in Jira semantics. Correlate board versions to project/version IDs; never infer mutation authorization from read access.

For Agile mutations, pre-read the board/sprint/version and affected issues, disclose the exact state change and impact, and obtain Tier C confirmation immediately before execution. Report provenance, filters/JQL/fields, pages consumed, truncation at the ceiling, and mutation verification.
