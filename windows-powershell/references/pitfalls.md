# Pitfalls

## Bash Syntax That Commonly Breaks

Do not assume Bash syntax in PowerShell.

| Bash habit | PowerShell correction |
| --- | --- |
| `export FOO=bar` | `$env:FOO = 'bar'` |
| `FOO=bar npm test` | Set `$env:FOO`, run command, restore it in `finally` |
| `cmd1 && cmd2` | PowerShell 7 supports this; Windows PowerShell 5.1 does not |
| `cmd1 || cmd2` | PowerShell 7 supports this; Windows PowerShell 5.1 does not |
| `/dev/null` | `$null` for PowerShell redirection; `NUL` for some native Windows tools |
| `rm -rf path` | `Remove-Item -LiteralPath path -Recurse -Force` |
| `mkdir -p path` | `New-Item -ItemType Directory -Force -Path path` |
| `which git` | `Get-Command git` or `where.exe git` |
| `grep pattern file` | `Select-String -Pattern pattern -Path file` |
| `chmod +x file` | Usually unnecessary on Windows; do not add unless targeting WSL/Git Bash |
| `sudo command` | Ask for elevated PowerShell or use documented Windows elevation flow |
| `node - <<'NODE'` or `python - <<'PY'` | Use `node -e "..."` / `python -c "..."` for short scripts, or write a temporary script file |

## Quoting

- Single-quoted strings are literal. Use them for paths and regex patterns that do not need interpolation.
- Double-quoted strings expand variables and subexpressions. Use `$($expr)` for member access or calculations.
- Double a single quote inside a single-quoted string: `'don''t'`.
- Escape a double quote inside a double-quoted string with a backtick: `"quoted `"word`""`.
- Avoid smart quotes. PowerShell treats them as quote characters, but they make scripts fragile.
- Avoid building one large command string. Prefer `& $exe @args` with an argument array.
- For regex patterns containing both quote types, backticks, or character classes like `['"]`, assign the pattern to a single-quoted variable first, for example `$pattern = 'from [''"]([^''"]+)[''"]'`, or move the logic into a script file.
- When nesting `pwsh -ExecutionPolicy Bypass -Command` or `powershell.exe -ExecutionPolicy Bypass -Command` inside an outer PowerShell command, the outer shell expands `$...` first. Escape variables with a backtick, for example `` `$_.Name `` or `` `$LASTEXITCODE ``, or avoid nesting by using a `.ps1` file or `-EncodedCommand`.

Common bug:

```powershell
"$HOME: is invalid"
```

Fix with braces:

```powershell
"${HOME}: is valid"
```

## Paths And Wildcards

- Prefer `Join-Path`, `Resolve-Path`, `Split-Path`, and `Test-Path`.
- Use `-LiteralPath` for paths from users, tools, or glob-like names.
- Quote paths with spaces.
- Invoke a quoted path with `&`: `& 'C:\Program Files\App\app.exe'`.
- Do not assume `/` is a path separator for every native Windows command. Many Windows tools interpret `/name` as an option.
- For Windows path filtering, prefer wildcard operators such as `-like '*\node_modules\*'` when regex is unnecessary. If using `-match` or `-notmatch` with a literal path segment, wrap the segment with `[regex]::Escape(...)`; a regex pattern that ends with `\` is invalid.

## Aliases And Command Name Collisions

Generated automation should use canonical names or `.exe` suffixes.

- `where` can resolve as a PowerShell alias/function pattern; use `where.exe` for the Windows executable.
- `curl` and `wget` are aliases in Windows PowerShell 5.1; use `Invoke-WebRequest`, `Invoke-RestMethod`, or `curl.exe`.
- `sort` can mean `Sort-Object`; use `sort.exe` for the native command.
- `sc` can mean `Set-Content`; use `sc.exe` for Service Control.
- `cat`, `ls`, `rm`, `cp`, `mv`, and `sleep` are aliases; prefer `Get-Content`, `Get-ChildItem`, `Remove-Item`, `Copy-Item`, `Move-Item`, and `Start-Sleep`.
- Use `Get-Command name -All` when behavior is surprising.

## Native Argument Passing

PowerShell 7.3 changed native command argument passing. `$PSNativeCommandArgumentPassing` can be `Legacy`, `Standard`, or `Windows`.

- On Windows, PowerShell 7 defaults to `Windows`.
- `Windows` behaves like `Standard` except that known legacy targets use legacy argument passing, including `cmd.exe`, `cscript.exe`, `find.exe`, `sqlcmd.exe`, `wscript.exe`, and files ending in `.bat`, `.cmd`, `.js`, `.vbs`, or `.wsf`.
- Windows PowerShell 5.1 uses legacy behavior.
- When reproducing a Windows PowerShell 5.1 issue in PowerShell 7, set `$PSNativeCommandArgumentPassing = 'Legacy'` inside a local scriptblock.
- For `.bat` and `.cmd`, avoid passing untrusted input as raw arguments; these are interpreted through `cmd.exe`.

The stop-parsing token `--%`:

- Works only on Windows for native commands.
- Makes the rest of the line literal except `%ENVVAR%` expansion.
- Stops at newline or pipeline.
- Does not allow normal PowerShell interpolation after it.
- Cannot be combined with normal PowerShell redirection in the remaining literal text.

Use `Start-Process -ArgumentList` only when a separate process launch is truly needed. For most command-line tools, `& $exe @args` is simpler and easier to inspect.

## Exit Status

- `$?` is the success state of the last command.
- For native executables, `$?` is true when `$LASTEXITCODE` is `0`; false otherwise.
- `$LASTEXITCODE` stores the last native program exit code.
- Check `$LASTEXITCODE` immediately after the native command before running another native command.
- Do not rely on stderr text alone. Many native tools write informational output to stderr.
- In PowerShell 7.3+, `$PSNativeCommandUseErrorActionPreference = $true` makes nonzero native exits issue errors according to `$ErrorActionPreference`; use it deliberately, not blindly.

## Redirection And Streams

PowerShell has six redirectable streams: success `1`, error `2`, warning `3`, verbose `4`, debug `5`, and information `6`. Progress is not redirectable.

Examples:

```powershell
command > out.txt
command 2> err.txt
command 2>&1 > combined.txt
command *> all-streams.txt
command | Out-Null
```

PowerShell can redirect other streams to the success stream, but not arbitrary stream-to-stream combinations. PowerShell 7.4 preserves native stdout byte streams for redirection, but combining stderr with stdout can still turn output into PowerShell objects instead of raw bytes.

## Windows PowerShell 5.1 vs PowerShell 7

PowerShell 7 is installed side-by-side with Windows PowerShell 5.1.

Use compatibility checks before using newer syntax:

```powershell
if ($PSVersionTable.PSVersion.Major -lt 7) {
    throw 'This command requires PowerShell 7+'
}
```

Avoid these in Windows PowerShell 5.1 unless you verified support:

- Pipeline chain operators `&&` and `||`
- Null-coalescing operators `??` and `??=`
- Ternary operator `? :`
- `Set-Content -Encoding utf8NoBOM`
- `$PSNativeCommandArgumentPassing`
- `$PSNativeCommandUseErrorActionPreference`

When targeting both shells, write explicit `if ($?) { ... }` blocks, use .NET for UTF-8 without BOM, and avoid PowerShell 7-only operators.
