# Discuss Record Bundle Reference (Antigravity Edition)

Read this reference completely before creating, explicitly continuing, persisting, or handing off a discussion record bundle.

## Bundle Requirement

Use a version 4 Markdown bundle, never a single tracker file. Resolve every relative destination against the working directory captured at skill entry and never ask a storage-choice question.

- On every new `discuss` invocation, create `./discussion/YYYY-MM-DD-no<N>-<slug>/` by default, including when the request supplies, links, or mentions an existing bundle.
- Adopt and update an existing directory or its `index.md` only when the user explicitly asks to continue, resume, or update that specific bundle. A supplied bundle without that continuation instruction is read-only source context for the newly created bundle and must not be modified. Other file paths are invalid record destinations.
- Use lowercase ASCII slugs. Number new bundles independently within `./discussion/` for each calendar date: inspect sibling directory names matching that date's `YYYY-MM-DD-no<N>-*` form, take the greatest positive integer `N`, and use `N + 1`; start at `no1` when none match. Ignore legacy names and malformed or non-positive sequence values, and never reuse a missing lower number.
- Reserve the selected directory with an atomic create. If it already exists because another writer won the race, recompute from the current siblings and retry with the next sequence number. The sequence belongs only to the containing `discussion/` directory and is independent of the sequence under `plans/`.
- Create missing ancestors automatically. Reject Git metadata locations, path traversal, and symlinks that escape the bundle.
- Freeze the canonical bundle root for the mode lifetime. Tell the user that root and the resume prompt `Use discuss and continue the record bundle at <root>`.

Create these files initially:

```text
<bundle>/
├── index.md
├── context.md
├── decisions.md
├── actions.md
└── evidence.md
```

`index.md` is the control plane. Its manifest lists every bundle-owned Markdown path, beginning with `index.md`. `context.md` holds goal, scope, current state, source-of-truth evidence, baseline, preservation requirements, risks, and constraints. `decisions.md` holds assumptions, decisions, requirements, and open questions. `actions.md` holds scoped-action authorization and results. `evidence.md` holds the log, handoff evidence, amendments, commit records, and execute action markers.

A Direct Execute Handoff may add `plan.md`, `verification.md`, and `phases/P<NN>-<slug>.md`. Add new paths to the manifest in the same coordinated update.

## Index Contract

Use this shape in `index.md`:

```markdown
# Discussion Record

<!-- workflow-record version:4 kind:discuss tracker-id:<stable ID> -->

Tracker ID: <stable non-secret ID>
Created: <timestamp and timezone>
Last updated: <timestamp and timezone>
Mode: discuss
Mode status: <Active | Awaiting decision | Paused | Exited>
Execution readiness: <Not ready | Ready>
Execute mode: <Inactive | Ready | Active | Exited>
Resume instruction: Invoke discuss on <canonical bundle root> (tracker <tracker ID>), read index.md and the manifest files required by the current state, and continue this exact bundle before substantive work.
Workspace: <captured working directory>
Repository: <root, branch, commit>
Mutation boundary: <current boundary>
Active action: <ID and status, or None>

<!-- workflow-active-snapshot:start version:2 -->
## Active Snapshot

Profile: <Lightweight | Durable | Audited>
Required references: <references/tracker.md[, references/response-workflow.md][, references/actions.md]>
Goal: <current goal>
Current state: <current state>
Accepted decisions: <IDs or None>
Open items: <IDs or None>
Next safe action: <one exact action>
<!-- workflow-active-snapshot:end -->

## Resume Checkpoint

- Last completed:
- Current work:
- Blocking decision or dependency:
- Next safe action:
- Deferred work:
- Authorization record:
- Revalidation required:

<!-- workflow-manifest:start -->
index.md
context.md
decisions.md
actions.md
evidence.md
<!-- workflow-manifest:end -->
```

Every declared path must be a relative `.md` path inside the bundle, unique, non-symlinked, and readable. Do not keep record content in undeclared files.

## Persistence and Rereading

- A snapshot reread covers the delimited Active Snapshot in `index.md`; a complete record reread covers `index.md` and every manifest file.
- Apply the entrypoint's coordinated record update contract. Include new Markdown paths in the manifest and verify tracker identity, state, phase links, and evidence markers before completing the update.
- Persist the current checkpoint after material changes. An unchanged turn needs no artificial rewrite.
- If persistence fails, do not present unsaved conclusions as durable state. Report the failed files and stop before further substantive work.

## Cross-Session Handoff

Cross-session continuation requires an explicit instruction to continue, resume, or update the supplied bundle. When that intent is explicit, canonicalize the supplied directory or `index.md`, read the complete bundle, validate its identity and manifest, restore the Active Snapshot and Resume Checkpoint, then compare recorded repository/external revisions with live state when they matter. If the user only supplies or mentions the bundle, create a new bundle and use the old one read-only when relevant. Earlier-session mutation authorization is historical context, never current permission.

If two bundles claim the same tracker ID or the lineage is ambiguous, preserve both, record the conflict, and apply the Immediate Decision Gate.

## Transition Gates

### Settled Discussion Transition Gate

When discussion settles and no blocking question remains, ask the user whether to transition to `plan` or `execute` using `ask_question` (or numbered chat format):
1. `plan`: create a separate structured implementation plan bundle under `./plans/`.
2. `execute`: execute directly using this discussion bundle (Direct Execute Handoff).

### Direct Execute Handoff

When transitioning directly from `discuss` to `execute`:
1. Add `plan.md`, `verification.md`, and initial phase files to the discussion bundle.
2. Verify all deliverables and verification criteria are clearly specified.
3. Update `index.md`: set `Mode status: Exited`, `Execution readiness: Ready`, `Execute mode: Ready`.
4. Hand off the canonical bundle root directly to `execute`.
