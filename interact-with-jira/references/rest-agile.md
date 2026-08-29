# Jira Software read-only REST workflows

All registered Agile capabilities are Tier A. Board, backlog, sprint, and version mutations are prohibited.

- Establish board provenance from explicit ID or bounded project/location/name filter. Board listing requires narrowing.
- Request required issue fields and narrow JQL. Respect permissions and page ceilings.
- Use only exact enhanced backlog/sprint-issue paths in the registry. Do not substitute deprecated `/rest/agile/1.0/...` neighbors or synthesize `/rest/software/1.0/...` routes.
- Treat `nextPageToken` as opaque; do not mix pagination models or exceed ceilings.
- Bind sprint IDs to an explicit board/task sprint; validate `originBoardId` when returned and constrain state filters.
- Versions are releases in Jira semantics. Correlate board versions to project/version IDs; never infer mutations from read access.

Report provenance, filters/JQL/fields, pages consumed, and truncation at the ceiling.
