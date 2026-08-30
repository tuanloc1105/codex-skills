# Jira Platform issue REST workflows

Prefer exact registry IDs. For other official Jira Platform issue endpoints, first build the dynamic contract required by [REST API workflow](rest-api-workflows.md). Identifiers provide provenance, not write authorization.

## Bounded reads

- Issue detail: request required `fields`/`expand`; avoid rendered content unless necessary.
- Changelog, comments, and worklogs: preserve visibility and page ceilings.
- Link read: require an explicit link ID, or `issue.get` with only `issuelinks` for one issue; never enumerate unrelated issues.
- Watchers: require visibility permission and do not enrich identities beyond the task.
- Versions/releases: use Jira version semantics (`released`, `releaseDate`, `archived`) and explicit project/version provenance.

## Tier B writes

- Comment: one explicit issue and bounded ADF/visibility; require `201`, then GET returned comment ID.
- Create link: pre-read both issues and explicit link type; omit comment unless separately authorized; require `201`, then re-read `issuelinks` on both issues. Duplicate responses make retry unsafe.
- Add watcher: distinguish self/another account; verify account ID/permission; require `204`, then re-read watchers.
- Assign: pre-read assignee and verify account ID; require `204`, then re-read assignee.
- Transition: list available transitions, bind requested state to one returned ID, POST once, require `204`, then re-read status.
- Field edit: fetch edit metadata/current values; allow only requested editable fields, show exact patch, PUT once, require `204`, then re-read changed fields.

An ambiguous write triggers one safe re-read and a report—not another mutation through any tool.

Unregistered single-target create/update operations follow Tier B. Delete/removal, bulk, selector-based, permission, or administrative operations follow Tier C even when the endpoint itself targets one resource.
