# GitHub CLI (`gh`)

Read this reference only for GitHub operations through `gh`. Discover available capabilities from local leaf-command help and use the official manual at <https://cli.github.com/manual/> when installation, authentication, Enterprise behavior, or an advertised capability needs clarification. Version output is diagnostic metadata, not a compatibility gate.

## Resolve authentication and repository context

- Read the applicable `gh <group> <command> --help` before acting. Use `gh --version` only when reporting or diagnosing behavior; do not choose flags from a numeric version threshold.
- Check authentication with `gh auth status --active --hostname <host>` when the host is known. Do not use `--show-token`.
- Account for token precedence: `GH_TOKEN` and `GITHUB_TOKEN` override stored credentials for GitHub.com; Enterprise tokens and `GH_HOST` can change the selected host. A successful stored login does not prove the command will use that account.
- Verify a repository without changing the persisted default, for example with `gh repo view <host/owner/repo> --json nameWithOwner,url,defaultBranchRef`. For command groups that expose it, prefer the inherited `--repo`/`-R` flag or `GH_REPO` scoped to one command over `gh repo set-default`.
- Do not run `gh auth login`, `auth switch`, `auth refresh`, `auth setup-git`, or `auth logout` unless the user requested or approved that credential/configuration change. For a supplied token, prefer `gh auth login --with-token` through standard input; never place the token directly in a command argument.

## Pull requests and issues

- Before `gh pr create`, make the base repository, base branch, head repository, and head branch explicit. If the current branch is unpublished, inspect local help for possible push or fork behavior. When the advertised head selector suppresses that implicit decision, use it only after verifying that the branch actually exists remotely.
- Inspect the local help for `gh pr create --dry-run`. If it warns that Git changes may still be pushed, do not treat the command as side-effect free; otherwise do not assume stronger guarantees than the help documents.
- Prefer the file/stdin body option advertised by local help for multiline PR bodies. Use the corresponding capability for reviews, comments, releases, or other commands when available.
- `--fill`, `--fill-first`, and `--fill-verbose` derive content from commits. Inspect the resulting title and body before submission when exact wording matters.
- Check `gh pr view <id> --repo <repo> --json ...` before editing, reviewing, closing, reopening, updating a branch, or merging. After a write, read the same object again.
- Treat approval, request-changes, merge, revert, branch update, auto-merge, and removal of a head branch as distinct effects. Use only the effects the user requested and verify the repository's allowed merge method before choosing one.
- Use stable identifiers or full URLs when a branch could match multiple pull requests.

### Issue workflow

- Discover `gh issue list`, `view`, `create`, `edit`, `comment`, `close`, `reopen`, `pin`, `lock`, and related leaf capabilities from local help. Keep title/body edits separate from labels, assignees, milestone, state, pinning, and locking.
- Before creating an issue, search within the verified repository for matching open and recently closed issues when duplicate detection is part of the request. If an issue template applies, preserve its required headings and use a file/stdin body option for multiline Markdown.
- Re-read with `gh issue view <number-or-url> --repo <repo> --json ...` before and after mutation. Treat closing with a reason and adding a closing comment as distinct effects.

### Pull-request review and thread workflow

- Use `gh pr diff`, `gh pr checks`, `gh pr view`, and the files/commits/reviews data exposed by `gh pr view --json` or the API to establish the review context. `gh pr comment` creates a general conversation comment; `gh pr review` submits an overall review. Neither should be assumed to reply to or resolve a line-level review thread.
- Never use `gh pr comment` for a finding tied to a changed line or as a reply to an existing review thread. For an inline finding, create a pull-request review comment with the current commit SHA, path, line and side or supported diff position. For a reply, use the existing review thread node ID or the review-comment reply endpoint advertised by the API.
- For line-level review threads, prefer GraphQL through `gh api graphql` when the installed high-level CLI has no equivalent. Query the pull request's `reviewThreads` connection and paginate it; retain each thread's node ID, `isResolved`, `isOutdated`, path, line information, and comments.
- Reply to an existing thread with the advertised GraphQL review-thread reply mutation when available, passing the stable thread node ID and body. Resolve or unresolve with the corresponding review-thread mutation and the same node ID. Inspect the current GraphQL schema or official manual if mutation names or input fields are not accepted; do not fall back to creating a top-level comment.
- Inline review comments require a commit and diff position or current line/side fields accepted by the GitHub API. Re-read the current head SHA and diff immediately before creation; never reuse a stale position from an earlier diff.
- Draft/pending review comments are not published until the review is submitted. Verify whether an API call creates a pending review, immediately publishes a comment, or submits an approval/request-changes event before using it.
- After creating an inline finding, verify the returned review comment contains the intended path and line/side or position and belongs to the intended pull request. After replying, query the exact thread node and verify the new comment appears in that thread before calling the resolve mutation. Then query it again and verify `isResolved`. For a batch, paginate and verify all affected IDs rather than assuming one successful mutation covered the set.

## Releases, workflows, and repository settings

- Confirm the tag and target commit before creating a release. Distinguish draft creation from publication and inspect whether generated notes or assets add unintended content.
- Workflow dispatch, rerun, cancel, cache deletion, secret or variable changes, repository archive/rename/delete, rulesets, keys, and permission changes are mutations even when invoked from a read-oriented investigation.
- Be careful with commands documented to force synchronization or reset destination state, such as repository sync with a force option. Require the exact source, destination, and branch.

## Structured output and API fallback

- When advertised, prefer a command's `--json <fields>` output, then use `--jq` or `--template` only after selecting supported fields. Use the field-discovery form documented by local help instead of assuming every release accepts the same invocation.
- For `gh api`, use `{owner}`, `{repo}`, and `{branch}` placeholders only after verifying the repository context or explicitly setting `GH_REPO`.
- Adding `--field` or `--raw-field` changes the default method from GET to POST. Always specify `--method` for mutations and for GET requests that carry query parameters.
- Use `--input <file>` or `--input -` for a reviewed JSON body. Use typed `--field` for scalars and documented nested-field syntax only when it remains clearer than a JSON file.
- `--paginate` emits pages sequentially; use `--slurp` when a single combined JSON value is actually required. Avoid fetching all pages without a concrete need.
- REST and GraphQL are capability fallbacks, not authorization fallbacks. Keep the endpoint, fields, method, repository, and expected effect explicit, then re-read state after a mutation.
