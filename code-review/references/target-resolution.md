# Target Resolution and Diff Evidence

Resolve the review target before candidate generation. The resolved target is the authoritative scope for every finder, verifier, sweep, fix, comment, and final report. Preserve explicit bases, path filters, exclusions, and staged or unstaged qualifiers instead of silently replacing them with defaults.

## Contents

- Target precedence
- Target semantics
- Working-tree composition
- Evidence normalization
- Review locations and PR commentability
- Failure handling
- Editable-target correspondence before fixes

## Target Precedence

Use the first applicable revision source:

1. the user's explicit pull request, commit, range, branch, tag, base, or working-tree qualifier;
2. the target supplied by an active dedicated review workflow;
3. applicable PR merge-destination metadata already safely available for the selected branch;
4. the repository's symbolic default branch (for example the known remote's `refs/remotes/origin/HEAD`), then an existing `main` or `master` distinct from the selected tip;
5. the selected tip's first parent when no useful implicit base exists, with an explicit last-commit fallback disclosure; a root uses the empty tree.

An upstream tracking the same feature is not a merge destination. Use `@{upstream}...HEAD` only for an explicit unpushed-only request. Resolve refs to object IDs and require an available merge-base. A default pointing at the selected tip is not useful. Do not mutate refs to discover a default.

Never mix an explicit historical target with unrelated current working-tree changes unless the user includes both. Paths and exclusions are scope qualifiers applied after choosing the revision source; a file path does not by itself choose a revision range.

## Target Semantics

| Target | Review evidence |
| --- | --- |
| GitHub pull request | The pull request's exact base and head commits. Prefer provider metadata over guessing from local branch names. Record the PR number and head SHA for later comments. |
| Explicit base plus branch or `HEAD` | The merge-base range from the explicit base to the selected tip, unless the user explicitly requests a two-dot range. |
| Branch or tag without an explicit base | Its merge-base range against the resolved default base. Do not assume the branch is checked out. |
| Single commit | That commit against its first parent, equivalent to the commit's own patch. For a root commit, compare against the empty tree. For a merge commit, ask only when parent choice materially changes the requested review; otherwise use the first-parent patch and disclose it. |
| Explicit commit range | Preserve the user's two-dot or three-dot semantics. Do not normalize one form into the other. |
| Local branch bundle | The merge-base of the merge destination and `HEAD` against the final tracked worktree, plus eligible non-ignored untracked additions. Use this for the implicit current-branch review. |
| Working tree | Tracked staged and unstaged changes relative to `HEAD`, plus non-ignored untracked files. Do not add a committed branch range unless it was also requested. |
| Staged only | The index relative to `HEAD`, plus no unstaged or untracked files unless explicitly requested. |
| Unstaged only | Tracked working-tree changes relative to the index, plus untracked files only when the request includes new working-tree files. |
| File or directory path | Apply the pathspec after resolving the revision or working-tree scope. Include renames whose old or new path matches when the available diff mechanism supports it. |

For a provider pull request, do not substitute the current local branch merely because it has a similar name. Fetch or use provider diff metadata only through an available authorized capability; read-only retrieval does not authorize comments, reviews, pushes, or checkout mutations.

## Working-Tree Composition

Build evidence by endpoints, not by concatenating temporal patches:

1. For the implicit checked-out branch bundle, resolve `BASE` with `git merge-base <destination> HEAD`; `git diff --binary --find-renames "$BASE" --` compares that tree directly with the final tracked worktree. A committed defect subsequently restored locally disappears.
2. Working-tree-only uses `git diff --binary --find-renames HEAD --`. Staged-only uses `git diff --cached HEAD --`; unstaged-only uses `git diff --`. Historical two-dot uses `git diff A B --`, three-dot uses `git diff A...B --`. Historical targets exclude local edits. A selected branch/tag that is not checked out remains historical unless working-tree inclusion is explicitly requested and correspondence established.
3. List additions with `git ls-files --others --exclude-standard -z`. Apply requested paths/exclusions and mode-specific test/fixture exclusions. For a path absent from the baseline, `git diff --no-index -- /dev/null <path>` supplies an addition (exit 1 means differences). If an untracked path existed in the baseline, reconcile current bytes against that baseline blob instead: staged deletion followed by untracked recreation must not become a stale deletion plus addition. Ignore excluded/ignored untracked content; retain its baseline deletion if in scope. Never stage real files to construct evidence.
4. Preserve old/new identities before path filtering, including renames where either path qualifies. Use `--name-status -z` and `--raw -z` with the same endpoints for metadata. If filtered retrieval loses an endpoint, retrieve metadata first, then filter the normalized evidence. Do not invent lines for mode-only/binary changes.
5. Store committed/index/unstaged provenance separately, with baseline and final coordinates. Review only reconciled final hunks. Capture content identities and recheck if the worktree changes during retrieval.

For a root baseline, derive the repository-format empty-tree ID with `git hash-object -t tree --stdin` on empty input, without `-w`. For implicit last-commit fallback use the parent as baseline and still compare to the final worktree; use empty tree only for a genuine root, not a shallow boundary.

Low modes may retrieve all applicable sources in one tool call. That constraint does not allow dropping additions, reconciliation or metadata. Keep temporary evidence outside the real index/refs and remove only task-owned scratch data.

## Evidence Normalization

Record a compact scope manifest before reviewing:

```json
{
  "target_kind": "pull-request",
  "base": "resolved-baseline-sha",
  "head": "resolved-target-head-sha",
  "repository": "canonical-repository-identity",
  "final_state": "commit-or-index-or-worktree-content-identities",
  "includes_worktree": false,
  "paths": ["optional/pathspec"],
  "exclusions": [],
  "files": ["changed/file.ext"]
}
```

Keep this internal unless the user requests machine-readable scope metadata. Preserve rename and deletion metadata, binary-file status, mode changes, submodule or generated-file markers, and old/new paths even when no textual hunk exists. Review binary or generated changes only through an established source, generator, manifest, or contract; do not invent line findings for opaque content.

## Review Locations and PR Commentability

For every candidate, distinguish the defect location from its reporting location:

- `defect_location`: the smallest changed line that demonstrates the cause;
- `context_location`: an unchanged line needed to explain the cause, when any;
- `comment_location`: a changed line and side accepted by the target PR's current diff, when comments were requested;
- `commentable`: whether a valid inline location exists at the final PR head.

Keep the finding in local or structured output when no inline location exists. Do not move a comment to an unrelated changed line merely to make it postable. Before posting after fixes or a head change, refresh PR metadata and confirm that the finding and comment location still apply to the recorded head.

## Failure Handling

- If an explicit ref, range, path, or PR cannot be resolved, stop rather than reviewing a fallback target.
- If a default base cannot be established, use the selected tip's first parent for an implicit-base review and disclose the fallback; use empty tree for a genuine root. An invalid explicit base never falls back.
- If a shallow clone prevents merge-base or history inspection, use provider metadata or already-available repository objects; otherwise state the evidence limitation instead of mutating refs to fill the gap.
- If the target is empty, say so and distinguish an empty diff from a clean review with inspected changes.
- Never checkout, reset, merge, rebase, or mutate refs merely to assemble review evidence.

## Editable-Target Correspondence Before Fixes

Review evidence is not editing authority for the current checkout. Immediately before each fix:

1. Match the canonical repository identity and the resolved target head to the editable checkout. For a PR, verify its recorded head SHA and repository, not merely branch/file names. For history, ranges or a non-checked-out branch, a current checkout at another head is a mismatch by default.
2. Compare the affected file's current content with the exact reviewed final snapshot, including enclosing behavior and dependencies needed by the fix. For index-only review, compare index and worktree content; a shared HEAD alone proves nothing about staged/unstaged differences. Capture status and patch boundaries before editing.
3. Preserve unrelated edits. If content has changed, re-read and revalidate the same finding against both the requested target and proposed editable content. Proceed only when correspondence and non-overlap are demonstrated; never blindly apply old coordinates or overwrite an overlapping user edit.
4. Skip on mismatch, unknown correspondence or unsafe overlap; retain the still-valid target finding and record a reason in permitted action metadata. Do not automatically checkout, reset, stash or switch branches. An isolated checkout is usable only when already authorized and correspondence is established there.
5. Recheck content immediately before applying the narrow patch; stop that fix if its preimage changed. Reverify the post-fix state and keep target evidence separate from unrelated local state.

A matching path name, clean status, or a patch that applies is insufficient proof. Exact JSON or low output may suppress the action reason; retain it internally without breaking that contract.
