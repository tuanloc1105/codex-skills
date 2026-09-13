---
name: interact-with-git-platform
description: Work with GitHub, GitLab, and Gitea through their official command-line clients (`gh`, `glab`, and `tea`), including authentication, host and repository selection, issues, pull or merge requests, reviews, releases, CI, and API fallbacks. Use when Antigravity must inspect, configure, troubleshoot, or safely mutate a Git platform through these CLIs. Do not use for local-only `git` operations or unrelated hosting providers.
---

# Interact with Git Platforms (Antigravity Edition)

## Stay Within Scope

- Use `gh` for GitHub, `glab` for GitLab, and `tea` for Gitea. Do not translate flags between them or substitute a different client without the user's approval.
- Use ordinary `git` for local history, branches, commits, remotes, fetches, and pushes unless the requested platform operation genuinely needs the platform CLI.
- Execute CLI commands via Antigravity's `run_command` tool.
- Do not install, upgrade, authenticate, log out, change a default account, register a credential helper, or alter CLI configuration merely because a requested operation cannot run. Explain the condition and obtain authorization for the additional change using `ask_question`.
- Prefer a high-level CLI command. Use the client's authenticated API command only when the high-level command lacks the needed capability or cannot preserve the required payload, and keep the request within the original scope.

## Route to the Correct Client

1. Honor an explicitly requested client or platform. Otherwise inspect `git remote -v` and the working repository without changing them.
2. If one provider is unambiguous, select its client. If multiple remotes map to different providers or multiple hosts/accounts remain plausible, present the resolved candidates and ask the user to choose using the `ask_question` tool before accessing private data or mutating anything.
3. Check that the executable exists and discover its capabilities from the applicable root, command-group, and leaf-command help. Record the version only as diagnostic context; never select syntax, refuse a supported operation, or require an upgrade solely from a hardcoded version number.
4. Read exactly the provider reference needed for the task:
   - GitHub and `gh`: [references/github-gh.md](references/github-gh.md)
   - GitLab and `glab`: [references/gitlab-glab.md](references/gitlab-glab.md)
   - Gitea and `tea`: [references/gitea-tea.md](references/gitea-tea.md)
5. For a deliberate cross-platform operation, read each participating provider reference and keep every source and destination explicit.

Treat command examples in this skill as capability illustrations, not a frozen compatibility matrix. If a named flag or alias is absent, use the equivalent advertised by local help, choose another supported high-level command, or use the authenticated API fallback when it remains in scope. Do not make the user reconcile ordinary CLI-version differences.

## Verify Context Before Acting

- Resolve the host, repository owner or namespace, repository name, account identity, and default branch with read-only commands. Never infer a write target solely from the directory name.
- Prefer an explicit per-command repository or host selector over changing a persisted default. When the client infers context from remotes, verify the inferred result before a write.
- For a pull or merge request, resolve the head repository and branch separately from the base repository and branch. Check whether the branch is already published before invoking a command that may push, fork, or create a source branch.
- Do not expose tokens with status flags, debug output, process arguments, logs, or chat. Prefer the client's OAuth/keyring flow, standard input, or a documented environment variable. Treat environment-variable precedence as part of identity verification.
- Do not disable TLS verification or accept a new credential-storage mode unless the user explicitly requests it and understands the target host.

## Classify the Operation

### Read-Only

Within the requested scope, use version/help/status, list, search, view, diff, checks, pipeline status, and authenticated GET requests after verifying context. Request only the fields and pages needed. Prefer structured output (`--json`) over parsing tables intended for humans.

### Specific Writes

A request may authorize a specific create, edit, comment, review, label, close, reopen, workflow run, or release operation. Before executing:

1. Re-read the target when doing so can prevent a wrong-target or lost-update error.
2. Make all material values explicit, including repository, source/base branches, title/body source, state, reviewers, labels, release tag, or pipeline ref.
3. Check whether the command can push, fork, create a branch or tag, enable auto-merge, remove a source branch, trigger CI, or otherwise cause a secondary mutation. Do not accept an implicit secondary mutation outside the request.
4. Execute once with `run_command`, check the native exit status, and re-read the created or updated object.

Do not treat "clean this up," "handle these requests," or a read/review request as authorization for inferred writes.

### High-Impact, Bulk, or Destructive Actions

Require an exact target and operation in the user's authorization before merging, deleting, archiving, force-syncing, changing protection or permissions, managing secrets or credentials, publishing or deleting releases, changing repository settings, invoking administration commands, or mutating a set selected by search, file, or query.

When the target set or effect was not already exact, perform a read-only preflight and ask for confirmation using `ask_question` with the host, account, repository, object IDs, selector or count, operation, secondary effects, and reversibility. Repeat the preflight if any of those change. Never bypass confirmation with `--yes`, `--force`, or an equivalent flag before this gate is satisfied.

## Preserve Inputs and Outputs

- Pass user-controlled values as native argument values, not through `eval` or an unescaped generated shell command.
- For multiline Markdown (such as PR or issue descriptions), create a clean temporary Markdown file using `write_to_file` and pass it via the CLI's body-file parameter (e.g. `gh pr create --body-file <file>`), or use standard input. This avoids shell escaping errors and guarantees exact line break formatting.
- After creating or updating a pull or merge request, read its body back and verify that headings, lists, links, and paragraphs retained real line breaks.
- Use JSON or another documented structured format for machine processing. Check the command's exit status before parsing; do not interpret partial output as success.
- Avoid debug or verbose HTTP modes when they may disclose authorization headers or sensitive payloads.

## Work with Issues, Pull Requests, and Merge Requests

Use the provider reference for exact commands and API shapes. Across providers, follow the same lifecycle:

1. Resolve the repository and stable object identifier, then read the current title, body, state, author, branches, labels, assignees, milestone, and discussion or review state needed for the request.
2. Separate content changes from workflow changes. Creating or editing text, assigning people, changing labels or milestones, closing or reopening, submitting a review, merging, and deleting a source branch are independent mutations.
3. For an issue, check for duplicate or superseding issues when the user asks to create or triage one. Preserve issue templates and make acceptance criteria, reproduction details, and links render as real Markdown.
4. For a pull or merge request, inspect the diff and current checks before reviewing. Distinguish a general conversation comment, an overall review, and a line-level review thread; use the surface matching the user's intent.
5. After every write, re-read the object or returned comment and verify the author, body, state, location, and URL or stable ID.

Treat the requested comment location as part of the write target, not as optional metadata:

- A comment about a specific changed line must be created as an inline diff comment anchored to that file, side, and line or diff position. A top-level PR/MR comment is not an acceptable fallback.
- A response to an existing review comment must be created inside that exact thread or discussion. A new top-level comment, a new inline thread on the same line, or an overall review body is not a reply.
- If the provider, permissions, current diff, or available client/API cannot preserve the requested location or thread identity, stop before writing and report the limitation. Never silently degrade to another comment type.

When asked to "address comments" or "handle review feedback," treat the request as permission to inspect and report unless it explicitly authorizes code changes, replies, review submission, or thread resolution. Do not mark a discussion resolved merely because code changed; verify the concern is addressed and that resolving it is within scope.

## Comment on and Resolve Review Threads

- Inventory unresolved threads before acting. Capture each stable thread/discussion ID, author, path and line or position when present, current resolution state, and enough context to avoid replying to a stale or outdated location.
- Re-read the current diff and the complete thread before replying. A line may have moved, the comment may be outdated, or later replies may already answer it.
- Reply inside the existing thread whenever the request refers to an existing comment. Use a new top-level PR/MR comment only for explicitly cross-cutting information that does not answer a particular thread.
- When the task is to answer and resolve feedback, enforce this sequence for each thread: create the reply using the stable thread/discussion ID, fetch that thread and verify the reply is nested under it, resolve that same thread ID, then fetch it again and verify the resolved state. Do not resolve if the reply was misplaced or cannot be verified.
- Resolve by stable thread/discussion identifier, never by array position, visible ordering, path alone, or comment text. If the high-level CLI lacks thread operations, use the authenticated API described in the provider reference.
- After creating an inline comment, re-read it and verify its path plus line/side or diff position. If the response represents it as a top-level comment or attaches it to a different location, report the mismatch and do not create a duplicate automatically.
- Do not resolve another reviewer's thread when platform policy, repository convention, or the user's request leaves ownership unclear. Report it as addressed and leave resolution to the reviewer.
- For batch work, preflight and present the exact unresolved thread set. After mutation, fetch the set again and report resolved, still-open, outdated, or failed items individually. Do not blindly retry an uncertain mutation.

## Handle Uncertainty and Report

- Do not automatically retry a mutation after a timeout, transport error, interrupted prompt, or partial response. Read the remote object first to determine whether the operation succeeded, then report the observed state and ask for direction if another mutation would be required.
- Adapt when local help exposes equivalent syntax or a safe in-scope fallback. Stop only when identity or target remains ambiguous, authentication or permission is insufficient, no supported route provides the required capability, or completing the task would expand to another tool or provider.
- Report the client and command family used, verified host/account/repository, affected object and URL or ID, observed result, secondary effects, and post-write verification. Redact credentials and unnecessary private data.
