# ACLI workflow for Jira Cloud

## Contents

- Discover commands
- Authenticate
- Read data
- Mutate one target
- Bulk or destructive mutations
- PowerShell
- Troubleshoot

## Discover commands

Always navigate from the root to the leaf command:

```text
acli --version
acli jira --help
acli jira workitem --help
acli jira workitem search --help
```

Common Jira Cloud groups include `auth`, `workitem`, `project`, `board`, `sprint`, `filter`, `dashboard`, and `field`. This list is only for routing; the current binary's `--help` output determines the actual commands and flags.

Some commands are marked `[DEPRECATED]`. Use the replacement recommended by current help; do not build new automation on a deprecated alias.

## Authenticate

Check status first:

```text
acli jira auth status
```

Prefer OAuth in an interactive session:

```text
acli jira auth login --web
```

If an API token is required, obtain the site/email from the user or approved configuration and provide the token through stdin. Do not put the token directly after `echo`, in an argument, or in a Git-tracked file.

After switching accounts, run `acli jira auth status` again. If ACLI reports that a site administrator must authorize or reauthorize the app, stop and relay the exact message to the user; do not try to bypass OAuth scopes.

## Read data

Use a bounded search and request only the required fields:

```text
acli jira workitem search --jql "project = TEAM AND statusCategory != Done" --fields "key,summary,status,assignee" --limit 50 --json
```

View one work item:

```text
acli jira workitem view TEAM-123 --fields "key,summary,status,assignee,description" --json
```

Rules:

- Validate JQL with `search` before reusing it for a mutation.
- Use `--count` when only the count is needed.
- Do not request `*all`, comments, descriptions, or attachments unless the task needs that data.
- Parse JSON instead of relying on text columns when the result feeds a later automated step.

## Mutate one target

Example workflow:

1. Run help for the leaf command.
2. View the current target.
3. Build an argument vector with the exact key/ID and fields requested by the user.
4. Run the mutation once.
5. Check the exit code, then view the target again.

This create-work-item example only illustrates the structure; check help before using it:

```text
acli jira workitem create --project TEAM --type Task --summary "Summary" --json
```

For a long description, ADF, or multiple custom fields, use `--generate-json`, edit a local file, review its contents, and then use `--from-json`. Do not guess the JSON schema.

## Bulk or destructive mutations

Do not immediately run a mutation that uses `--jql`, `--filter`, `--from-file`, or multiple keys. Instead:

1. Use the same selector to search/count in read-only mode.
2. Narrow the selector; obtain a fixed key/ID list when practical.
3. Present the site/account, command, selector, count, targets, and impact.
4. Request confirmation in chat and stop.
5. After confirmation, rebuild the command from the approved data; do not reuse a changed selector.
6. Only then use `--yes` when non-interactive execution is required.
7. Do not use `--ignore-errors`; if part of the operation fails, do not retry the whole batch.
8. Re-read the targets or search the same key set to verify the result.

Deleting a project, board, sprint, field, or work item may not offer a dry run or consistent prompt. Do not treat the absence of `--yes` as evidence that a command is safe.

## PowerShell

Use PowerShell 7 when available. Pass arguments through an array and check `$LASTEXITCODE` before processing output:

```powershell
$acliArgs = @(
    'jira', 'workitem', 'search',
    '--jql', 'project = TEAM AND statusCategory != Done',
    '--fields', 'key,summary,status',
    '--limit', '50',
    '--json'
)
$jsonText = & acli @acliArgs
$acliExitCode = $LASTEXITCODE
if ($acliExitCode -ne 0) {
    throw "acli failed with exit code $acliExitCode"
}
$items = $jsonText | ConvertFrom-Json
```

Log in with a token from a protected local file:

```powershell
$loginArgs = @(
    'jira', 'auth', 'login',
    '--site', 'mysite.atlassian.net',
    '--email', 'user@example.com',
    '--token'
)
Get-Content -LiteralPath $tokenFile | & acli @loginArgs
$acliExitCode = $LASTEXITCODE
if ($acliExitCode -ne 0) {
    throw "acli login failed with exit code $acliExitCode"
}
```

Do not print `$tokenFile` or the token contents. Do not place the token in `$loginArgs`.

## Troubleshoot

- `command not found`: check `Get-Command acli`/`command -v acli` and PATH; do not download the binary unless requested.
- `unknown command` or `unknown flag`: rerun help from the parent group through the leaf command and check the changelog.
- `401`, `403`, or missing scope: verify authentication status, site, account, Jira permissions, and current reauthorization requirements; do not silently switch tokens or accounts.
- Work item not found: verify the site, project key, browse permission, and JQL with a small search.
- Partially successful batch: preserve the redacted original output, re-read state, and report each target; do not retry automatically.
- Output parse failure: check whether the command supports `--json`, its exit code, and stderr before changing the parser.
