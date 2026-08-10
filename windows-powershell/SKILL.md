---
name: windows-powershell
description: Reliable Windows PowerShell 5.1 and PowerShell 7+ command authoring, execution, troubleshooting, and Bash-to-PowerShell translation for Codex on Windows. Use when working in Windows terminals, `powershell.exe`, `pwsh`, PowerShell scripts (`.ps1`, `.psm1`, `.psd1`), Windows paths, native `.exe`/`.bat`/`.cmd` commands, Windows CI jobs, or when a user reports command failures caused by shell syntax, quoting, paths, aliases, redirection, execution policy, native argument passing, or exit-code handling.
---

# Windows PowerShell

## Overview

Use this skill to make Windows shell work predictable. Treat PowerShell as its own shell, not as Bash with different slashes.

## Self-Maintenance

When a Windows command failure exposes a reusable gap and the active `AGENTS.md` authorizes updating this skill:

1. Reproduce and diagnose the failure before changing guidance. Add only a general rule or example that prevents the same class of failure.
2. Edit the authoritative repository directory at `D:\usually-use-script\codex-skills\windows-powershell\`. Do not edit only `~\.codex\skills\windows-powershell\`; it is the installed mirror.
3. Read `D:\usually-use-script\codex-skills\docs\agent\skill-maintenance.md`, validate the repository copy, sync the complete skill directory to `~\.codex\skills\windows-powershell\`, validate the mirror, and verify all non-excluded paths and contents match.
4. If the repository source is unavailable, report the proposed update instead of mutating the installed mirror.

## Core Workflow

1. Identify the active shell before writing non-trivial commands:

```powershell
$PSVersionTable | Select-Object PSVersion, PSEdition, GitCommitId, OS, Platform
Get-Command pwsh,powershell -ErrorAction SilentlyContinue | Select-Object Name, Source, Version
```

2. Choose the shell deliberately:

- Prefer `pwsh` for new automation, cross-platform projects, PowerShell 7 operators, and improved native argument handling.
- Use `powershell.exe` only when the task needs Windows PowerShell 5.1, Desktop-only modules, legacy snap-ins, or exact user reproduction.
- If the user explicitly says PowerShell 7, use `pwsh`. If they explicitly say Windows PowerShell, use `powershell.exe`.

3. Whenever starting a new PowerShell process, always pass `-ExecutionPolicy Bypass` immediately after the executable. Apply this to interactive and non-interactive launches of both PowerShell 7 (`pwsh`) and Windows PowerShell (`powershell.exe`), including `-Command`, `-File`, `-EncodedCommand`, and nested-shell calls. This changes policy only for that process; never replace it with a persistent `CurrentUser` or `LocalMachine` policy change.

```powershell
pwsh -ExecutionPolicy Bypass
powershell.exe -ExecutionPolicy Bypass
```

4. Use a fail-fast wrapper for PowerShell cmdlets and scripts:

```powershell
& {
    $ErrorActionPreference = 'Stop'
    $ProgressPreference = 'SilentlyContinue'

    # commands here
}
```

5. Check native command exit codes explicitly. `$ErrorActionPreference` handles PowerShell errors, not all native `.exe` failures in every version and preference state.

```powershell
git status --short
if ($LASTEXITCODE -ne 0) { throw "git failed with exit code $LASTEXITCODE" }
```

6. For complex multi-line logic, create or edit a `.ps1` file with the available file-editing tool, then run it with `-File`. Do not cram fragile scripts into one heavily escaped command string.

```powershell
pwsh -ExecutionPolicy Bypass -NoLogo -NonInteractive -File .\script.ps1
```

## Command Authoring Rules

- Use full cmdlet names in generated commands. Avoid aliases such as `ls`, `cat`, `rm`, `curl`, `wget`, `where`, `sort`, and `sc` unless verifying an interactive user habit.
- Keep whitespace between a cmdlet/function name and its first argument even in compact scripts. For example, write `Write-Output $value`, not `Write-Output$value`; PowerShell parses the latter as a different command name.
- Give helper functions distinctive verb-noun names. Avoid single-letter names such as `g` or `h` in profile-loading shells because an existing alias can take precedence over the function and invoke an unrelated command.
- A same-volume atomic move preserves the DACL already applied to a temporary file. Validate the moved file with `Get-Acl`; do not reapply the same `FileSecurity` object, because reusing it can make `Set-Acl` request `SeSecurityPrivilege` unnecessarily.
- Do not add `-NoProfile` by default. Let the selected shell load its normal profiles; use `-NoProfile` only when the user explicitly requests a profile-free session or when isolating a problem caused by profile configuration.
- Use `-LiteralPath` for user-provided paths and any path containing `[]`, wildcard characters, leading dashes, or unusual punctuation.
- `-LiteralPath` never expands `*` or `?`. To copy the contents of a trusted directory while retaining literal-path safety, enumerate its children first and call `Copy-Item -LiteralPath $_.FullName` for each item; do not write `Copy-Item -LiteralPath (Join-Path $source '*')`.
- Do not rely on PowerShell or Windows to expand wildcard path arguments for native tools such as `rg`. Search a real directory and pass the wildcard through the tool's filter option, for example `rg pattern references -g '*.md'` or `rg pattern node_modules -g '*.d.ts'`. Never pass `references/*.md` or `references\*.md` as a path argument; both can reach `rg` literally and fail on Windows.
- If using `rg --` to end option parsing for a pattern that begins with `-`, put options such as `-g` before `--`; every token after `--` is a pattern or path, not an option.
- Quote paths with spaces. Invoke quoted executables with the call operator: `& 'C:\Program Files\Git\bin\git.exe' status`.
- When using a native launcher or wrapper command, do not pass PowerShell cmdlets such as `Get-Content` or `Test-Path` as the executable. Invoke PowerShell explicitly instead, for example `pwsh -ExecutionPolicy Bypass -NoLogo -Command "Get-Content -Raw -LiteralPath 'C:\path\file.txt'"`.
- Do not assume every command-batch or sandbox runner uses the interactive session's shell. If diagnostics show that the runner writes a POSIX shell script or prefixes assignments such as `NAME=value`, PowerShell-only syntax (`&`, script blocks, cmdlets, and `$...` variables) will fail before `pwsh.exe` starts. Use a tool whose contract explicitly runs PowerShell, or invoke the absolute `pwsh.exe` path using POSIX-compatible launcher syntax and pass non-trivial logic through `-File`/`-EncodedCommand`; do not send a PowerShell call operator or inline script block through that runner.
- When policy requires an absolute `pwsh.exe` path while the tool host is already PowerShell, treat this as a nested-shell call. A child script containing variables or loops must use `-File` or `-EncodedCommand`; do not place it in an outer double-quoted `-Command` payload, because the host expands child `$...` expressions before launch.
- For short read-only batches in a PowerShell host, keep the child `-Command` payload outer-single-quoted and use doubled single quotes for child literals. If the batch needs arrays, loops, or mixed quoting, switch immediately to `-File` or `-EncodedCommand` instead of adding another escaping layer.
- When a nested `ssh` remote command contains its own single-quoted `awk`, `sed`, or shell program, do not embed it inside another single-quoted `pwsh -ExecutionPolicy Bypass -Command` payload. Use `-EncodedCommand` for the child PowerShell and assign the remote program with a literal here-string before passing it as one SSH argument.
- Use single quotes for literal strings and double quotes only when interpolation is needed.
- Use `${name}` or `$($expr)` inside expandable strings when characters follow a variable, especially before `:`.
- For regex patterns containing both quote types, backticks, or character classes like `['"]`, assign the pattern to a single-quoted variable first, for example `$pattern = 'from [''"]([^''"]+)[''"]'`, or move the logic into a script file. Avoid packing such regex directly into a long one-liner pipeline. In particular, never inline backtick-escaped double quotes inside a regex carried through a nested `-Command`; use a `.ps1` file, `-EncodedCommand`, or a simpler quote-free pattern followed by post-processing.
- When invoking `pwsh -ExecutionPolicy Bypass -Command` or `powershell.exe -ExecutionPolicy Bypass -Command` from an outer PowerShell command, avoid fragile nested quoting for scripts containing variables such as `$_`, `$null`, `$p`, or `$LASTEXITCODE`, single-quoted literals, or regex pipes (`|`). The outer shell expands `$...` first, so unescaped variables can disappear before the child shell runs. Prefer a temporary `.ps1` file or `-EncodedCommand`; otherwise escape `$` with a backtick, for example `` `$_.Name ``, or avoid nesting.
- If a short nested command must stay inline and its body can avoid single-quoted literals, wrap the entire child `-Command` payload in outer single quotes and use double quotes inside it. This preserves child variables such as `$_`; never put that payload in outer double quotes unless every `$` is escaped.
- In particular, keep child-owned `$...` expressions literal when PowerShell launches another PowerShell. For example, use `& powershell.exe -ExecutionPolicy Bypass -NoLogo -NoProfile -NonInteractive -Command '$PSVersionTable.PSVersion.ToString()'`; the outer single quotes preserve `$PSVersionTable` for the child. A double-quoted payload can expand it in the outer host into a type-name string that the child cannot parse. Use `-File` or `-EncodedCommand` once the child body needs its own single-quoted strings or non-trivial logic.
- To send a multiline here-string to a child PowerShell stdin, pipe it: `@'... '@ | & pwsh -ExecutionPolicy Bypass -Command -`. Do not use Bash-style input redirection such as `pwsh -ExecutionPolicy Bypass -Command - <@'... '@`; `<` is not a PowerShell stdin redirection operator.
- Do not pipe exact text formats such as unified diffs through the ordinary PowerShell object pipeline when byte-for-byte line endings matter; native stdin may receive CRLF and cause whitespace errors. Create an LF patch file with the available file-editing tool and pass its path to the native command instead.
- This also applies to tool wrappers and MCP commands whose host shell may already be PowerShell. If the command needs loops, variables, pipelines, or quoting-sensitive arguments, invoke PowerShell with `-File`/`-EncodedCommand` or use a non-shell runner such as `execFile` with an argument array; do not rely on a single-quoted `-Command` payload surviving every layer.
- From JSON tool calls, a command string such as `pwsh -ExecutionPolicy Bypass -Command "... $i ..."` is still first parsed by the host shell. The same rule applies when the executable is invoked through an absolute path such as `& 'C:\tools\pwsh.exe' -ExecutionPolicy Bypass -Command "... $i ..."`; the call operator does not protect the child payload from outer-shell expansion. Treat every `$variable` inside the child payload as unsafe unless escaped for the host shell, encoded, or moved into a script file.
- In particular, an outer PowerShell invocation using a double-quoted `-Command` payload will expand child variables even when the child script later uses arrays or `foreach`. A command like `pwsh -ExecutionPolicy Bypass -Command "$files = ...; foreach ($f in $files) { ... }"` can reach the child as `foreach ( in )`. Use `-File`, `-EncodedCommand`, or escape every child `$` for the outer shell.
- For a short fixed batch that only reads several known files, avoid a child loop entirely: keep the child payload outer-single-quoted and write separate `Get-Content -LiteralPath ''C:\path\one'' -Raw` statements. If iteration is genuinely needed, use `-File` or `-EncodedCommand`; do not change the outer payload to double quotes.
- This rule also applies to command strings sent through batch/MCP runners on Windows: assume their host shell parses the string before launching the explicitly named `pwsh.exe`. For any child script with `$variables`, `foreach`, or `$_`, generate UTF-16LE Base64 and invoke `pwsh.exe -ExecutionPolicy Bypass -EncodedCommand <value>`, or use a checked-in/temporary `.ps1` file; an absolute executable path alone does not make an outer double-quoted `-Command` safe.
- When a tool already exposes a native PowerShell command surface (for example `shell_command` on a Windows session), run the script directly in that host. If the available runner uses another shell, invoke PowerShell with an encoded child script or use a non-shell process API that accepts an argument array; otherwise `$...` can be consumed by the intermediate shell before PowerShell parses it.
- Use arrays for native command arguments when constructing them programmatically: `$args = @('status', '--short'); & git @args`.
- When native output must be piped, truncated, or otherwise processed by PowerShell, capture the native output and `$LASTEXITCODE` separately before starting the PowerShell pipeline. A mixed pipeline such as `& $exe @args 2>&1 | Select-Object -First 3` can leave `$LASTEXITCODE` unset; use `$nativeOutput = & $exe @args 2>&1; $nativeExitCode = $LASTEXITCODE; $nativeOutput | Select-Object -First 3` and validate `$nativeExitCode`.
- Do not reuse PowerShell automatic variables as ordinary accumulators. In particular, `$Matches` is replaced with a hashtable after every successful `-match`; use a task-specific name such as `$metadataMatches` for result collections. The same caution applies to `$Host`, `$Error`, `$Input`, `$Args`, and other automatic variables.
- Do not assume a normal native argv array is lossless for a nested `.bat`/`.cmd` launch that requires `cmd.exe /s /c`. For a validated, deliberately narrow token domain, use `System.Diagnostics.ProcessStartInfo` with trusted absolute `cmd.exe` in `FileName`, `UseShellExecute = $false`, and the complete raw `/d /s /c <payload>` in `.Arguments`; pin `COMSPEC` to the same executable. Reject empty tokens, embedded quotes/control characters and relevant cmd metacharacters before payload construction. See `references/command-patterns.md` for the quoting contract and trailing-backslash rule.
- Pass Java/JVM system properties with dots, such as `-Dfile.encoding=UTF-8`, as quoted strings or array elements. Unquoted native arguments can be reparsed incorrectly and become a class name such as `.encoding=UTF-8`. This applies especially to Maven `.cmd` launchers: put every `-D...=...` token in an argument array and splat the array into `mvn.cmd`; a directly written `-Djavax.net.ssl.trustStore=...` can be split and interpreted as a Maven plugin prefix.
- Treat PowerShell pipelines as object pipelines. Use text parsing only after confirming the command produces plain text.
- Do not assume `Invoke-WebRequest.Content` is always a string in PowerShell 7. For JSON responses it can be a `byte[]`; inspect the value type and decode bytes with the response encoding or UTF-8 before `ConvertFrom-Json`, or use `Invoke-RestMethod` when status/header access is not required.
- In PowerShell 7, parse JSON that may contain an empty property name (for example `package-lock.json` has `packages[""]`) with `ConvertFrom-Json -AsHashtable`, then index `$json.packages['']`. Normal `ConvertFrom-Json` rejects empty property names; Windows PowerShell 5.1 lacks `-AsHashtable`, so use a .NET/Node JSON parser there.
- A `foreach (...) { ... }` language statement cannot be followed directly by a pipeline operator. Wrap its output in an array/subexpression first, for example `$results = @(foreach ($item in $items) { [pscustomobject]@{ Name = $item } }); $results | ConvertTo-Json`, or assign the loop output to a variable before piping; otherwise PowerShell reports `An empty pipe element is not allowed`. This includes short Git inventory loops: use `$rows = @(foreach ($repo in $repos) { [pscustomobject]@{ Repo = $repo } }); $rows | Format-Table`, never `foreach (...) { ... } | Format-Table`. It also applies inside nested `-Command` payloads: never write `foreach (...) { ... } | ConvertTo-Json`.
- Avoid Bashisms in Windows PowerShell 5.1: no `&&`, `||`, `??`, `?:`, process substitution, here-docs, `export`, `VAR=value cmd`, `/dev/null`, `chmod`, or `sudo`.
- Do not use Bash heredoc forms such as `node - <<'NODE'` for inline Node/Python scripts. In PowerShell, pass short scripts with `node -e "..."` or put multi-line scripts in a temporary `.js`, `.py`, or `.ps1` file and execute that file.
- For Windows path filtering, prefer wildcard operators such as `-like '*\node_modules\*'` or `-notlike '*\node_modules\*'` when regex is not needed. If using `-match` or `-notmatch` with a literal path segment, wrap the segment with `[regex]::Escape(...)`; a regex pattern that ends with `\` is invalid.
- Avoid local variable names that collide case-insensitively with automatic variables. For example, `$matches` aliases `$Matches` and is repopulated by regex `-match`, while `$host` aliases the read-only `$Host` variable and cannot be assigned. Prefer task-specific names such as `$matchResult` or `$repositoryHost`.

## Common Translations

| Intent | PowerShell |
| --- | --- |
| Current directory | `Get-Location` |
| List files including hidden | `Get-ChildItem -Force` |
| Read a text file as one string | `Get-Content -Raw -LiteralPath .\file.txt` |
| Search file text | `Select-String -Path .\*.ts -Pattern 'TODO'` |
| Find a command | `Get-Command git` or `where.exe git` |
| Create directory like `mkdir -p` | `New-Item -ItemType Directory -Force -Path .\dist` |
| Remove recursively | `Remove-Item -LiteralPath .\dist -Recurse -Force` |
| Copy recursively | `Copy-Item -LiteralPath .\src -Destination .\dst -Recurse -Force` |
| Set process env var | `$env:NODE_ENV = 'test'` |
| Discard output | `> $null`, `2> $null`, or `*> $null` |

## Reference Loading

Read only the reference needed for the immediate task:

- `references/command-patterns.md`: canonical snippets for shell probing, one-shot execution, paths, file IO, env vars, native commands, execution policy, and safe deletes.
- `references/pitfalls.md`: Bash-to-PowerShell pitfalls, quoting traps, aliases, native argument passing, redirection streams, and Windows PowerShell 5.1 vs PowerShell 7 differences.
- `references/official-docs.md`: Microsoft Learn sources used to build this skill; load when a precise documentation citation or deeper lookup is needed.
