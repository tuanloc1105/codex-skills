# Target, Scope, and Ownership

Resolve the exact code being simplified before candidate generation. The resolved target remains authoritative through review, edits, verification, and reporting.

## Target Precedence

Use the first applicable revision source:

1. the user's explicit commit, range, branch, tag, pull or merge request, staged/unstaged qualifier, or named files from the current conversation;
2. an execution record's explicit session or commit range;
3. the current local branch bundle against its upstream;
4. the repository's symbolic default branch, then an existing conventional `main` or `master` branch;
5. the working-tree changes alone when no committed comparison can be established;
6. files the user named or the assistant edited earlier in the conversation when no Git diff exists.

Paths and exclusions narrow the selected revision source; they do not choose a revision range. Never add current working-tree changes to an explicit historical target unless the user includes both.

## Target Semantics

| Target | Simplification scope |
| --- | --- |
| Explicit commit range | Preserve the user's two-dot or three-dot semantics and inspect the complete range. |
| Single commit | That commit's own patch against its first parent; use the empty tree for a root commit. |
| Branch or tag | Its merge-base range against the explicit or resolved base. Do not assume it is checked out. |
| Pull or merge request | The provider's exact base and head commits when available through an authorized read capability. |
| Local branch bundle | The committed branch range plus tracked staged and unstaged changes and non-ignored untracked additions. |
| Working tree | Tracked staged and unstaged changes relative to `HEAD`, plus non-ignored untracked additions; no committed range unless requested. |
| Staged only | The index relative to `HEAD`; exclude unstaged and untracked files unless requested. |
| Unstaged only | Tracked changes relative to the index; include untracked files only when requested. |
| Named files without a diff | The current contents plus conversation evidence that places them in scope. |

For a multi-commit session range, inspect the full diff and ordered commit history. Do not reduce it to the last commit. Compose committed, tracked working-tree, and untracked evidence into one logical diff without reviewing overlapping hunks twice.

## Scope Manifest

Record this internal manifest before review:

```json
{
  "target_kind": "local-branch-bundle",
  "base": "base-ref-or-sha",
  "head": "head-ref-or-sha",
  "includes_worktree": true,
  "paths": [],
  "exclusions": [],
  "files": [
    {"path": "src/file.ext", "domain": "shared/library", "ownership": "in-scope"}
  ]
}
```

Classify files or hunks as frontend/UI, backend/service, shared/library, infrastructure/configuration, test-only, or mixed. Record uncertainty instead of selecting a convenient domain. Preserve rename, deletion, binary, generated-file, mode-change, and submodule metadata even when no textual hunk exists.

## Working-Tree Baseline

Before editing, capture enough read-only evidence to distinguish simplification edits from pre-existing work:

- `git status --short`;
- the resolved target diff and changed-file list;
- staged, unstaged, and untracked ownership within that target;
- hashes or exact starting contents of files that may be edited;
- user changes outside the target.

Do not stage, revert, overwrite, or reformat pre-existing user changes. If an authorized simplification must overlap a changed hunk, preserve the user's current final state and make only the smallest attributable edit. Stop when ownership cannot be determined safely.

## Scope Boundaries

An adjacent edit is allowed only when it is necessary to compile, preserve the contract, update a directly affected caller, or remove dead code created by the simplification. Record it in the edit ledger with that reason.

Do not:

- clean pre-existing dead code;
- migrate unrelated callers to a new abstraction;
- change dependency versions merely to enable cleanup;
- alter a public API, persisted data, wire format, configuration key, or user-visible behavior without explicit intent;
- checkout, reset, merge, rebase, or mutate refs to assemble evidence.

If an explicit target cannot be resolved, stop instead of substituting a fallback. Distinguish an empty target from a reviewed target with no simplification opportunities.
