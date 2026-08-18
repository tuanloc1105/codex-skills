# GitLab CLI (`glab`)

Read this reference only for GitLab operations through `glab`, including GitLab.com, GitLab Self-Managed, and GitLab Dedicated. Discover capabilities from local leaf-command help and use the official CLI documentation at <https://docs.gitlab.com/cli/> when authentication, host behavior, or an advertised capability needs clarification. Version output is diagnostic metadata, not a compatibility gate.

## Resolve authentication and repository context

- Read the applicable `glab <group> <command> --help` for the exact operation. Use `glab --version` only when reporting or diagnosing behavior. Output flags and prompt behavior are not uniform across command groups or installations.
- Check the intended instance with `glab auth status --hostname <host>`. Use `--all` only when inventorying configured hosts is necessary, and never use `--show-token`.
- Git remotes, `GITLAB_HOST` or `GL_HOST`, token environment variables, and stored configuration can all affect host/account selection. `GITLAB_TOKEN`, `GITLAB_ACCESS_TOKEN`, and `OAUTH_TOKEN` can override stored credentials, so verify the effective identity rather than merely confirming that a login exists.
- Verify the project with the explicit repository selector advertised by local help. It may accept a namespace/project path, nested group path, full URL, or Git URL; verify the resolved project before writing.
- Do not run `glab auth login`, switch accounts, change configuration, or log out unless requested or approved. Prefer the web OAuth/keyring flow. If a token must be supplied, use `glab auth login --stdin`; do not pass a literal token in the command line or accept plaintext storage without authorization.

## Merge requests and issues

- Before `glab mr create`, specify and verify `--repo`, `--source-branch`, `--target-branch`, and `--head` when the source project differs from the target project.
- Inspect local `glab mr create --help` for the effects of `--fill`, `--push`, and source-branch creation. When help says `--fill` enables a push, treat it as publishing the current branch. Do not allow any of these secondary Git mutations unless publication is in scope.
- `--auto-merge`, `--squash-before-merge`, `--remove-source-branch`, collaboration settings, and draft state are separate effects. Do not inherit interactive or project defaults when the user requires a specific outcome.
- Determine the meaning of `--description -` from local help; do not assume `-` means standard input, because some installations use it to open an editor. Confirm where merge request templates are loaded from. For exact multiline content, use a reviewed local template when appropriate, a shell-native multiline argument, or an API input file when the advertised high-level command cannot preserve the payload.
- `--yes` skips submission confirmation but does not resolve ambiguous inputs. Use it only after the skill's write gate is satisfied and all relevant fields are explicit.
- Re-read an MR by stable IID or URL before edit, review, checkout, close, reopen, branch update, or merge, and again after a write. Keep project ID and MR IID distinct when using the API.

## Pipelines, releases, and project settings

- Pipeline run, retry, cancel, delete, schedule, variable update, and manual job play are mutations. Confirm the project, ref, variables or inputs, and whether protected or production resources can be affected.
- Distinguish pipeline status/watch commands from commands that create or retry a pipeline. A wait or live status mode may block and may be incompatible with JSON output; inspect local help.
- Before creating a release, confirm whether the tag already exists and inspect help or official documentation for missing-tag behavior. If the command would create a tag from the target or default branch, treat that as a secondary mutation and set the target ref explicitly when needed.
- Repository prune, mirror configuration, archive/delete/transfer, protected branch or environment changes, access-token operations, runners, deploy keys, variables, and secrets require the exact target and effect. Use a documented dry run when available and verify what it covers.

## Structured output and API fallback

- Prefer the structured-output format exposed by the leaf command. Flag names vary and some commands expose only text; never assume GitHub-style `--json` or a shared short flag exists.
- List commands are paginated. Set page and per-page limits deliberately instead of assuming the first page is complete or fetching every page automatically.
- `glab api` infers the host from the current repository, otherwise it can default to GitLab.com. Set `--hostname` or verify repository context before accessing a Self-Managed or Dedicated instance.
- Repository placeholders such as `:fullpath`, `:id`, and `:branch` depend on local context. Use them only after verifying that context.
- Adding `--field`, `--raw-field`, or form data changes the default method to POST. Specify `--method` explicitly for mutations and for GET requests with parameters.
- Prefer the advertised file/stdin input mode for complex JSON arrays and objects. Use typed-field parsing only as documented by local help, and do not combine multipart form input with incompatible field/input modes.
- Use `--output ndjson` with pagination when streaming large result sets is genuinely necessary. For GraphQL pagination, ensure the query exposes the required cursor and page information.
- After any API mutation, re-read the project object through a GET or the relevant high-level view command before reporting success.
