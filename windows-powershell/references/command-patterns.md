# Command Patterns

Use these snippets as stable starting points. Adjust names and paths to the repo, but keep the shell semantics.

## Probe The Session

```powershell
$PSVersionTable | Select-Object PSVersion, PSEdition, GitCommitId, OS, Platform
Get-Command pwsh,powershell -ErrorAction SilentlyContinue | Select-Object Name, Source, Version
Get-ExecutionPolicy -List
```

PowerShell 7.3+ native argument behavior:

```powershell
Get-Variable PSNativeCommandArgumentPassing -ErrorAction SilentlyContinue |
    Select-Object Name, Value
Get-Variable PSNativeCommandUseErrorActionPreference -ErrorAction SilentlyContinue |
    Select-Object Name, Value
```

## Invoke A Shell Once

From `cmd.exe` or another launcher:

```powershell
pwsh -NoLogo -NoProfile -NonInteractive -ExecutionPolicy Bypass -Command "& { $ErrorActionPreference = 'Stop'; Get-Location }"
```

For Windows PowerShell 5.1:

```powershell
powershell.exe -NoLogo -NoProfile -NonInteractive -ExecutionPolicy Bypass -Command "& { $ErrorActionPreference = 'Stop'; Get-Location }"
```

Prefer `-File` for multi-line scripts:

```powershell
pwsh -NoLogo -NoProfile -NonInteractive -ExecutionPolicy Bypass -File .\build.ps1
```

Use `-EncodedCommand` only when a launcher makes quoting impossible. Encode the command as UTF-16LE before Base64.

## Fail Fast

```powershell
& {
    $ErrorActionPreference = 'Stop'
    $ProgressPreference = 'SilentlyContinue'

    Import-Module Pester -ErrorAction Stop
    Invoke-Pester -CI
}
```

Use `Set-StrictMode -Version Latest` only for scripts you own. Do not inject strict mode into arbitrary project scripts or user profiles.

## Native Commands

Native commands write process exit codes to `$LASTEXITCODE`. For success/failure gates, check it immediately after the command.

```powershell
& git @('status', '--short')
$code = $LASTEXITCODE
if ($code -ne 0) {
    throw "git status failed with exit code $code"
}
```

If a command has non-error nonzero exit codes, handle its contract instead of blindly throwing. `robocopy.exe` is the classic example.

```powershell
& {
    $PSNativeCommandUseErrorActionPreference = $false
    robocopy.exe D:\reports \\server\share *.md
    if ($LASTEXITCODE -gt 8) {
        throw "robocopy failed with exit code $LASTEXITCODE"
    }
}
```

When native quoting becomes fragile, prefer an argument array:

```powershell
$exe = 'C:\Program Files\Git\bin\git.exe'
$arguments = @('-C', 'C:\repo with spaces', 'status', '--short')
& $exe @arguments
if ($LASTEXITCODE -ne 0) { throw "git failed with exit code $LASTEXITCODE" }
```

Use `--%` only on Windows, only for native commands, and only when literal argument passing is more important than PowerShell interpolation or redirection.

```powershell
icacls X:\VMS --% /grant Dom\HVAdmin:(CI)(OI)F
```

## Paths

Use provider-aware path cmdlets rather than manual slash joins.

```powershell
$root = Resolve-Path -LiteralPath '.'
$out = Join-Path -Path $root.Path -ChildPath 'dist'
New-Item -ItemType Directory -Force -Path $out | Out-Null
```

Use `-LiteralPath` when deleting or reading user-provided paths:

```powershell
$target = Resolve-Path -LiteralPath '.\dist' -ErrorAction Stop
Remove-Item -LiteralPath $target.Path -Recurse -Force
```

Add a guard before destructive operations:

```powershell
$target = Resolve-Path -LiteralPath $Path -ErrorAction Stop
$root = [System.IO.Path]::GetPathRoot($target.Path)
if ($target.Path -eq $root) {
    throw "Refusing to remove filesystem root: $($target.Path)"
}
Remove-Item -LiteralPath $target.Path -Recurse -Force
```

## File IO And Encoding

Read whole text files:

```powershell
$text = Get-Content -Raw -LiteralPath .\package.json
```

Write UTF-8 without BOM in both Windows PowerShell 5.1 and PowerShell 7:

```powershell
$utf8NoBom = [System.Text.UTF8Encoding]::new($false)
$out = Join-Path -Path (Resolve-Path -LiteralPath .).Path -ChildPath 'out.txt'
[System.IO.File]::WriteAllText($out, $text, $utf8NoBom)
```

In PowerShell 7, `Set-Content -Encoding utf8NoBOM` is acceptable:

```powershell
Set-Content -LiteralPath .\out.txt -Value $text -Encoding utf8NoBOM
```

JSON:

```powershell
$json = Get-Content -Raw -LiteralPath .\package.json | ConvertFrom-Json
$json | ConvertTo-Json -Depth 100
```

## Environment Variables

Process-scoped:

```powershell
$old = $env:NODE_ENV
try {
    $env:NODE_ENV = 'test'
    npm test
    if ($LASTEXITCODE -ne 0) { throw "npm test failed with exit code $LASTEXITCODE" }
}
finally {
    $env:NODE_ENV = $old
}
```

Persistent user or machine-scoped changes require explicit APIs and should be done only when the user asks:

```powershell
[Environment]::SetEnvironmentVariable('FOO', 'bar', 'User')
```

## Web Requests

Use PowerShell cmdlets for structured web work:

```powershell
$data = Invoke-RestMethod -Uri 'https://example.test/api' -Method Get
Invoke-WebRequest -Uri 'https://example.test/file.zip' -OutFile .\file.zip
```

Use `curl.exe` only when exact curl behavior is required:

```powershell
curl.exe -L -o file.zip https://example.test/file.zip
if ($LASTEXITCODE -ne 0) { throw "curl.exe failed with exit code $LASTEXITCODE" }
```

## Execution Policy

Prefer process-scoped bypass for one command or one script run:

```powershell
pwsh -NoProfile -NonInteractive -ExecutionPolicy Bypass -File .\script.ps1
```

Inside an existing session:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force
```

Do not change `CurrentUser` or `LocalMachine` execution policy unless the user explicitly asks.
