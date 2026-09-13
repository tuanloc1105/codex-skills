# Gitea CLI (`tea`)

Read this reference only for Gitea operations through `tea`. Client and server capabilities can differ across installations, so discover the client surface from local help and verify server behavior with read-only requests. Use the official Tea project page at <https://about.gitea.com/products/tea/> and the maintained source at <https://gitea.com/gitea/tea> when an advertised capability needs clarification. Version output is diagnostic metadata, not a compatibility gate.

## Resolve login, instance, and repository context

- Read `tea --help` and the applicable group/leaf help to discover command names and aliases; installations may expose plural groups or shorter aliases. Use `tea --version` only when reporting or diagnosing behavior, not to choose syntax.
- Inspect configured login names only when needed and use the login selector advertised by the target command. Check whether `tea whoami` accepts that selector; if it does not, do not use it to prove the identity of a non-default login. Instead, use a selector-bound authenticated GET supported by local API help, then verify the repository separately with the same login and an explicit repository selector. Do not display or inspect stored token values.
- Resolve repository context with an explicit `--repo`, or use `--remote` to select the remote from which Tea discovers the login. When Tea infers context from the current directory, verify the inferred instance and owner/repository before accessing private data or writing.
- Tea is designed around local repository context and may assume that relevant Git state is already published. Check remotes, tracking branches, and the remote head before creating or checking out a pull request; do not let a platform operation imply an unauthorized push.
- Do not run `tea login add`, edit/delete/default, `logout`, or credential-helper setup unless requested or approved. Prefer OAuth or documented environment variables over literal token, username/password, or OTP arguments. Registering Tea as a Git credential helper changes Git authentication behavior and is a separate configuration action.
- Never use `--insecure` merely to overcome a certificate error. Stop and report the instance and certificate condition unless the user explicitly authorizes disabling TLS verification for that host.

## Pull requests and issues

- Before creating a Tea pull request, use the selectors advertised by local help to verify the repository, login or remote, head, and base. For a fork, use the supported head form and confirm the source branch exists remotely.
- Tea may implement draft pull requests by applying a WIP-style title convention. Verify the resulting title and draft state on the server rather than assuming native draft semantics.
- Inspect high-level issue and pull-create help for a description file or standard-input mode. If only a description string is available, preserve multiline Markdown with a shell-native multiline argument or use the API's advertised file/stdin payload mode with reviewed JSON.
- Treat assignees, labels, milestones, deadlines, maintainer edits, and referenced versions as distinct changes. Use only those requested and verify that names resolve on the selected instance.
- Re-read an issue or pull request by numeric index after create, edit, comment, close, reopen, review, or merge. Do not confuse an issue/PR index with a repository or database ID.
- `tea pulls merge` can perform the merge directly without a confirmation flag. Resolve the repository, pull index, mergeability, checks, approvals, and merge style before invoking it.

### Issue workflow

- Discover the installed `tea issues` list/view/create/edit/comment/close/reopen capabilities and aliases from leaf help. Treat title/body, labels, assignees, milestone, deadline, and state as independent changes.
- Search the verified repository for plausible duplicates when requested before creating an issue. Preserve repository templates, and use a supported description file/stdin option or a reviewed API payload for multiline Markdown.
- Re-read by repository plus issue index before and after mutation. Gitea pull requests share issue-style conversation facilities, so verify whether a command is operating on an issue or pull request with that index.

### Pull-request review and comment workflow

- Distinguish issue-style PR comments, submitted reviews, and inline review comments. Inspect `tea pulls`, review-related help, and the selected Gitea server's API before deciding which surface matches the request.
- Never substitute an issue-style PR comment for a requested inline finding or thread reply. Use a supported inline review-comment endpoint with the exact diff location, or a supported reply endpoint with the existing review/comment ID. If the selected server exposes neither operation, stop without commenting and report the unsupported capability.
- If Tea lacks a high-level reply or resolution command, use `tea api` only for endpoints advertised by the selected server. Inventory the pull's reviews and review comments with explicit repository and pull index, retaining review/comment IDs, paths, line context, commit IDs, and resolved or outdated fields when the server exposes them.
- Gitea versions may not expose a GitHub/GitLab-style resolvable thread model. Do not claim that a reply, review submission, or issue-style comment resolves a thread. If the server exposes no resolution mutation, reply with the requested status when authorized and report that resolution must remain open or be completed in the web UI.
- Inline comments depend on the current diff and commit context. Re-fetch the pull head and changed files immediately before posting and use only the position fields documented by that server.
- After creating an inline comment, verify its path and line or diff position. After replying, verify the reply is associated with the intended review/comment thread before resolving when supported, then verify the resolved state separately. If Gitea exposes comments without stable thread nesting, do not represent a new comment as a reply or resolve substitute.

## Releases, actions, and administration

- Before creating a Tea release, confirm the tag and target and inspect documented missing-tag behavior. If the server may create a missing tag at the requested target or default branch, treat that as a secondary mutation. Prefer the advertised note-file or stdin capability for multiline release notes.
- Action runs, reruns, cancellation, secrets or variables, webhooks, deploy keys, repository migration, archive/delete, organization changes, and branch changes are mutations. Confirm leaf help and verify the selected server's capability with read-only requests where practical.
- Treat `tea admin` as out of scope unless the user explicitly requests an administrative operation and the exact instance, object, and effect are verified.
- Avoid `--force` on delete operations until the destructive-action gate is satisfied. A client-side prompt is not a substitute for resolving the correct server and repository.

## Structured output and API fallback

- Prefer `--output json` with a minimal `--fields` selection when the command supports them. Tea also exposes table, CSV, TSV, YAML, and simple output; do not parse decorated tables when structured output is available.
- List commands default to finite page and limit values. Request the page range needed and do not assume the first page is complete.
- `tea api` prefixes ordinary endpoints with `/api/v1/`. It can replace context placeholders such as `{owner}` and `{repo}`; use them only after verifying or explicitly setting repository context.
- Quote endpoints containing `?` or `&` so the shell cannot reinterpret them.
- Supplying string fields, typed fields, or raw data can change the default request method to POST. Specify `--method` for every mutation and for GET requests that include parameters.
- Prefer the API's advertised file/stdin data mode for a complete reviewed JSON payload. Use typed fields for small scalar values and locally documented arrays or objects; do not combine raw data with field flags.
- `tea api --output` may name an output file rather than a serialization format, unlike entity commands. Read leaf help before assuming flag semantics.
- After an API mutation, use a GET or the corresponding high-level view command to verify remote state before reporting success.
