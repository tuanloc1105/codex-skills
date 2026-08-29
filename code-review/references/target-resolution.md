# Target Resolution and Diff Evidence

Resolve the review target before candidate generation. The resolved target is the authoritative scope for every finder, verifier, sweep, fix, comment, and final report. Preserve explicit bases, path filters, exclusions, and staged or unstaged qualifiers instead of silently replacing them with defaults.

## Contents

- Target precedence
- Target semantics
- Working-tree composition
- Evidence normalization
- Review locations and PR commentability
- Failure handling

## Target Precedence

Use the first applicable revision source:

1. the user's explicit pull request, commit, range, branch, tag, base, or working-tree qualifier;
2. the target supplied by an active dedicated review workflow;
3. the current local branch against its upstream;
4. the repository's symbolic default branch, then an existing conventional `main` or `master` branch;
5. `HEAD~1..HEAD` when no usable base exists.

Never mix an explicit historical target with unrelated current working-tree changes unless the user includes both. Paths and exclusions are scope qualifiers applied after choosing the revision source; a file path does not by itself choose a revision range.

## Target Semantics

| Target | Review evidence |
| --- | --- |
| GitHub pull request | The pull request's exact base and head commits. Prefer provider metadata over guessing from local branch names. Record the PR number and head SHA for later comments. |
| Explicit base plus branch or `HEAD` | The merge-base range from the explicit base to the selected tip, unless the user explicitly requests a two-dot range. |
| Branch or tag without an explicit base | Its merge-base range against the resolved default base. Do not assume the branch is checked out. |
| Single commit | That commit against its first parent, equivalent to the commit's own patch. For a root commit, compare against the empty tree. For a merge commit, ask only when parent choice materially changes the requested review; otherwise use the first-parent patch and disclose it. |
| Explicit commit range | Preserve the user's two-dot or three-dot semantics. Do not normalize one form into the other. |
| Local branch bundle | The selected committed branch range, tracked staged and unstaged changes relative to `HEAD`, and non-ignored untracked files. Use this for the implicit current-branch review. |
| Working tree | Tracked staged and unstaged changes relative to `HEAD`, plus non-ignored untracked files. Do not add a committed branch range unless it was also requested. |
| Staged only | The index relative to `HEAD`, plus no unstaged or untracked files unless explicitly requested. |
| Unstaged only | Tracked working-tree changes relative to the index, plus untracked files only when the request includes new working-tree files. |
| File or directory path | Apply the pathspec after resolving the revision or working-tree scope. Include renames whose old or new path matches when the available diff mechanism supports it. |

For a provider pull request, do not substitute the current local branch merely because it has a similar name. Fetch or use provider diff metadata only through an available authorized capability; read-only retrieval does not authorize comments, reviews, pushes, or checkout mutations.

## Working-Tree Composition

Build one logical diff without duplicate hunks:

1. gather the committed range, if any;
2. gather tracked index and working-tree changes relative to `HEAD` as one final-state patch when both staged and unstaged changes are in scope;
3. list non-ignored untracked files and represent each as an addition from the empty file;
4. apply path and exclusion filters consistently to all three sources;
5. key hunks by source, file identity, and final line range so overlapping command output is not reviewed twice.

Low modes may retrieve all applicable sources in one tool call, but the logical scope remains the same. Do not omit an applicable source merely to satisfy the one-call constraint.

## Evidence Normalization

Record a compact scope manifest before reviewing:

```json
{
  "target_kind": "pull-request",
  "base": "base-sha-or-ref",
  "head": "head-sha-or-ref",
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
- If a default base cannot be established, use `HEAD~1` only for an implicit local review and disclose the fallback.
- If a shallow clone prevents merge-base or history inspection, use provider metadata or already-available repository objects; otherwise state the evidence limitation instead of mutating refs to fill the gap.
- If the target is empty, say so and distinguish an empty diff from a clean review with inspected changes.
- Never checkout, reset, merge, rebase, or mutate refs merely to assemble review evidence.
