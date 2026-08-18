---
name: interact-with-git-platform
description: Work with GitHub, GitLab, and Gitea through their official command-line clients (`gh`, `glab`, and `tea`), including authentication, host and repository selection, issues, pull or merge requests, reviews, releases, CI, and API fallbacks. Use when Codex must inspect, configure, troubleshoot, or safely mutate a Git platform through these CLIs. Do not use for local-only `git` operations or unrelated hosting providers.
---

# Interact with Git platforms

## Stay within scope

- Use `gh` for GitHub, `glab` for GitLab, and `tea` for Gitea. Do not translate flags between them or substitute a different client without the user's approval.
- Use ordinary `git` for local history, branches, commits, remotes, fetches, and pushes unless the requested platform operation genuinely needs the platform CLI.
- Do not install, upgrade, authenticate, log out, change a default account, register a credential helper, or alter CLI configuration merely because a requested operation cannot run. Explain the condition and obtain authorization for the additional change.
- Prefer a high-level CLI command. Use the client's authenticated API command only when the high-level command lacks the needed capability or cannot preserve the required payload, and keep the request within the original scope.

## Route to the correct client

1. Honor an explicitly requested client or platform. Otherwise inspect `git remote -v` and the working repository without changing them.
2. If one provider is unambiguous, select its client. If multiple remotes map to different providers or multiple hosts/accounts remain plausible, present the resolved candidates and ask the user to choose before accessing private data or mutating anything.
3. Check that the executable exists and discover its capabilities from the applicable root, command-group, and leaf-command help. Record the version only as diagnostic context; never select syntax, refuse a supported operation, or require an upgrade solely from a hardcoded version number.
4. Read exactly the provider reference needed for the task:
   - GitHub and `gh`: [references/github-gh.md](references/github-gh.md)
   - GitLab and `glab`: [references/gitlab-glab.md](references/gitlab-glab.md)
   - Gitea and `tea`: [references/gitea-tea.md](references/gitea-tea.md)
5. For a deliberate cross-platform operation, read each participating provider reference and keep every source and destination explicit.

Treat command examples in this skill as capability illustrations, not a frozen compatibility matrix. If a named flag or alias is absent, use the equivalent advertised by local help, choose another supported high-level command, or use the authenticated API fallback when it remains in scope. Do not make the user reconcile ordinary CLI-version differences.

## Verify context before acting

- Resolve the host, repository owner or namespace, repository name, account identity, and default branch with read-only commands. Never infer a write target solely from the directory name.
- Prefer an explicit per-command repository or host selector over changing a persisted default. When the client infers context from remotes, verify the inferred result before a write.
- For a pull or merge request, resolve the head repository and branch separately from the base repository and branch. Check whether the branch is already published before invoking a command that may push, fork, or create a source branch.
- Do not expose tokens with status flags, debug output, process arguments, logs, or chat. Prefer the client's OAuth/keyring flow, standard input, or a documented environment variable. Treat environment-variable precedence as part of identity verification.
- Do not disable TLS verification or accept a new credential-storage mode unless the user explicitly requests it and understands the target host.

## Classify the operation

### Read-only

Within the requested scope, use version/help/status, list, search, view, diff, checks, pipeline status, and authenticated GET requests after verifying context. Request only the fields and pages needed. Prefer structured output over parsing tables intended for humans.

### Specific writes

A request may authorize a specific create, edit, comment, review, label, close, reopen, workflow run, or release operation. Before executing:

1. Re-read the target when doing so can prevent a wrong-target or lost-update error.
2. Make all material values explicit, including repository, source/base branches, title/body source, state, reviewers, labels, release tag, or pipeline ref.
3. Check whether the command can push, fork, create a branch or tag, enable auto-merge, remove a source branch, trigger CI, or otherwise cause a secondary mutation. Do not accept an implicit secondary mutation outside the request.
4. Execute once, check the native exit status, and re-read the created or updated object.

Do not treat "clean this up," "handle these requests," or a read/review request as authorization for inferred writes.

### High-impact, bulk, or destructive actions

Require an exact target and operation in the user's authorization before merging, deleting, archiving, force-syncing, changing protection or permissions, managing secrets or credentials, publishing or deleting releases, changing repository settings, invoking administration commands, or mutating a set selected by search, file, or query.

When the target set or effect was not already exact, perform a read-only preflight and ask for confirmation with the host, account, repository, object IDs, selector or count, operation, secondary effects, and reversibility. Repeat the preflight if any of those change. Never bypass confirmation with `--yes`, `--force`, or an equivalent flag before this gate is satisfied.

## Preserve inputs and outputs

- Pass user-controlled values as native argument values, not through `eval` or a generated shell command.
- For multiline Markdown, use a documented file or standard-input flag. If the leaf command offers neither, use a shell-native multiline value containing real newline characters or an API request body from a reviewed file; never encode intended line breaks as literal `\n` text.
- After creating or updating a pull or merge request, read its body back and verify that headings, lists, links, and paragraphs retained real line breaks.
- Use JSON or another documented structured format for machine processing. Check the command's exit status before parsing; do not interpret partial output as success.
- Avoid debug or verbose HTTP modes when they may disclose authorization headers or sensitive payloads.

## Handle uncertainty and report

- Do not automatically retry a mutation after a timeout, transport error, interrupted prompt, or partial response. Read the remote object first to determine whether the operation succeeded, then report the observed state and ask for direction if another mutation would be required.
- Adapt when local help exposes equivalent syntax or a safe in-scope fallback. Stop only when identity or target remains ambiguous, authentication or permission is insufficient, no supported route provides the required capability, or completing the task would expand to another tool or provider.
- Report the client and command family used, verified host/account/repository, affected object and URL or ID, observed result, secondary effects, and post-write verification. Redact credentials and unnecessary private data.
