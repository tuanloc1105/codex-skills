---
name: windows-powershell
description: Reliable Windows PowerShell 5.1 and PowerShell 7+ command authoring, execution, troubleshooting, and Bash-to-PowerShell translation for Codex on Windows. Use when working in Windows terminals, `powershell.exe`, `pwsh`, PowerShell scripts (`.ps1`, `.psm1`, `.psd1`), Windows paths, native `.exe`/`.bat`/`.cmd` commands, Windows CI jobs, or when a user reports command failures caused by shell syntax, quoting, paths, aliases, redirection, execution policy, native argument passing, or exit-code handling.
---

# Windows PowerShell

## Overview

Use this skill to make Windows shell work predictable. Treat PowerShell as its own shell, not as Bash with different slashes.

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

3. Use a fail-fast wrapper for PowerShell cmdlets and scripts:

```powershell
& {
    $ErrorActionPreference = 'Stop'
    $ProgressPreference = 'SilentlyContinue'

    # commands here
}
```

4. Check native command exit codes explicitly. `$ErrorActionPreference` handles PowerShell errors, not all native `.exe` failures in every version and preference state.

```powershell
git status --short
if ($LASTEXITCODE -ne 0) { throw "git failed with exit code $LASTEXITCODE" }
```

5. For complex multi-line logic, create or edit a `.ps1` file with the available file-editing tool, then run it with `-File`. Do not cram fragile scripts into one heavily escaped command string.

```powershell
pwsh -NoLogo -NoProfile -NonInteractive -ExecutionPolicy Bypass -File .\script.ps1
```

## Command Authoring Rules

- Use full cmdlet names in generated commands. Avoid aliases such as `ls`, `cat`, `rm`, `curl`, `wget`, `where`, `sort`, and `sc` unless verifying an interactive user habit.
- Use `-LiteralPath` for user-provided paths and any path containing `[]`, wildcard characters, leading dashes, or unusual punctuation.
- Quote paths with spaces. Invoke quoted executables with the call operator: `& 'C:\Program Files\Git\bin\git.exe' status`.
- When using a native launcher or wrapper command, do not pass PowerShell cmdlets such as `Get-Content` or `Test-Path` as the executable. Invoke PowerShell explicitly instead, for example `pwsh -NoLogo -NoProfile -Command "Get-Content -Raw -LiteralPath 'C:\path\file.txt'"`.
- Use single quotes for literal strings and double quotes only when interpolation is needed.
- Use `${name}` or `$($expr)` inside expandable strings when characters follow a variable, especially before `:`.
- For regex patterns containing both quote types, backticks, or character classes like `['"]`, assign the pattern to a single-quoted variable first, for example `$pattern = 'from [''"]([^''"]+)[''"]'`, or move the logic into a script file. Avoid packing such regex directly into a long one-liner pipeline.
- When invoking `pwsh -Command` or `powershell.exe -Command` from an outer PowerShell command, avoid fragile nested quoting for scripts containing variables such as `$_`, `$null`, `$p`, or `$LASTEXITCODE`, single-quoted literals, or regex pipes (`|`). The outer shell expands `$...` first, so unescaped variables can disappear before the child shell runs. Prefer a temporary `.ps1` file or `-EncodedCommand`; otherwise escape `$` with a backtick, for example `` `$_.Name ``, or avoid nesting.
- This also applies to tool wrappers and MCP commands whose host shell may already be PowerShell. If the command needs loops, variables, pipelines, or quoting-sensitive arguments, invoke PowerShell with `-File`/`-EncodedCommand` or use a non-shell runner such as `execFile` with an argument array; do not rely on a single-quoted `-Command` payload surviving every layer.
- From JSON tool calls, a command string such as `pwsh -Command "... $i ..."` is still first parsed by the host shell. Treat every `$variable` inside the child payload as unsafe unless escaped for the host shell, encoded, or moved into a script file.
- In particular, an outer PowerShell invocation using a double-quoted `-Command` payload will expand child variables even when the child script later uses arrays or `foreach`. A command like `pwsh -Command "$files = ...; foreach ($f in $files) { ... }"` can reach the child as `foreach ( in )`. Use `-File`, `-EncodedCommand`, or escape every child `$` for the outer shell.
- Use arrays for native command arguments when constructing them programmatically: `$args = @('status', '--short'); & git @args`.
- Pass Java/JVM system properties with dots, such as `-Dfile.encoding=UTF-8`, as quoted strings or array elements. Unquoted native arguments can be reparsed incorrectly and become a class name such as `.encoding=UTF-8`.
- Treat PowerShell pipelines as object pipelines. Use text parsing only after confirming the command produces plain text.
- Avoid Bashisms in Windows PowerShell 5.1: no `&&`, `||`, `??`, `?:`, process substitution, here-docs, `export`, `VAR=value cmd`, `/dev/null`, `chmod`, or `sudo`.
- Do not use Bash heredoc forms such as `node - <<'NODE'` for inline Node/Python scripts. In PowerShell, pass short scripts with `node -e "..."` or put multi-line scripts in a temporary `.js`, `.py`, or `.ps1` file and execute that file.
- For Windows path filtering, prefer wildcard operators such as `-like '*\node_modules\*'` or `-notlike '*\node_modules\*'` when regex is not needed. If using `-match` or `-notmatch` with a literal path segment, wrap the segment with `[regex]::Escape(...)`; a regex pattern that ends with `\` is invalid.
- Avoid local variable names that differ only by case from automatic variables, such as `$matches` versus `$Matches`; PowerShell variables are case-insensitive, and regex `-match` repopulates `$Matches`.

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
