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

Start an interactive PowerShell process with process-scoped execution-policy bypass:

```powershell
pwsh -ExecutionPolicy Bypass
powershell.exe -ExecutionPolicy Bypass
```

From `cmd.exe` or another launcher:

```powershell
pwsh -ExecutionPolicy Bypass -NoLogo -NonInteractive -Command "& { $ErrorActionPreference = 'Stop'; Get-Location }"
```

For Windows PowerShell 5.1:

```powershell
powershell.exe -ExecutionPolicy Bypass -NoLogo -NonInteractive -Command "& { $ErrorActionPreference = 'Stop'; Get-Location }"
```

Prefer `-File` for multi-line scripts:

```powershell
pwsh -ExecutionPolicy Bypass -NoLogo -NonInteractive -File .\build.ps1
```

Use `-EncodedCommand` only when a launcher makes quoting impossible. Encode the command as UTF-16LE before Base64.

### PowerShell launching PowerShell

When the parent process is already PowerShell and the child command is a short inline script, pass a script block directly to avoid another layer of string quoting:

```powershell
& 'D:\dev-kit\PS7\pwsh.exe' -ExecutionPolicy Bypass -NoLogo -NoProfile -Command {
    Get-Content -LiteralPath 'C:\path\file.txt' -Raw
    Write-Output '--- next file ---'
}
```

Do not wrap that script block in an outer double-quoted string; embedded quotes and child-owned expressions can be parsed or expanded by the parent before launch. Use `-File` for non-trivial or reusable scripts.

This is especially important for loops and collections. An outer double-quoted payload can erase child variables and turn `foreach ($item in $items)` into the invalid `foreach ( in )` before PowerShell 7 starts:

```powershell
& 'D:\dev-kit\PS7\pwsh.exe' -ExecutionPolicy Bypass -NoLogo -NoProfile -Command {
    $candidates = @('C:\Java\jdk-21\bin\java.exe', 'C:\Java\jdk-17\bin\java.exe')
    foreach ($candidate in $candidates) {
        if (Test-Path -LiteralPath $candidate) { & $candidate -version }
    }
}
```

Keep child-owned variables literal at the outer boundary. Outer single quotes preserve `$PSVersionTable` for the child process:

```powershell
& powershell.exe -ExecutionPolicy Bypass -NoLogo -NoProfile -NonInteractive `
    -Command '$PSVersionTable.PSVersion.ToString()'
if ($LASTEXITCODE -ne 0) { throw "child PowerShell failed with exit code $LASTEXITCODE" }
```

Do not put that child payload in outer double quotes: the outer host can expand `$PSVersionTable` first and pass an invalid type-name expression to the child. Prefer `-File` when the child command needs single-quoted literals, loops, pipelines, or other non-trivial logic; use `-EncodedCommand` only when a launcher prevents `-File`.

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

### Validated `.bat`/`.cmd` through raw `cmd.exe` arguments

A nested batch launch under `cmd.exe /s /c` is not a normal argv-array problem. When an existing runner has a narrow validated token contract, use `ProcessStartInfo` to keep the raw payload intact on both Windows PowerShell 5.1 and PowerShell 7:

```powershell
function ConvertTo-CmdQuotedToken {
    param([Parameter(Mandatory = $true)][string]$Token)

    # Double only the final run of backslashes before the closing quote.
    $escapedToken = [regex]::Replace($Token, '(\\+)$', '$1$1')
    return '"' + $escapedToken + '"'
}

$batch = 'C:\Program Files\Kafka\bin\windows\kafka-topics.bat'
$batchArgs = @('--version')
$tokens = @($batch) + $batchArgs
$unsafe = '[%!^&|<>"\u0000-\u001F\u007F]'
foreach ($token in $tokens) {
    if ([string]::IsNullOrEmpty($token) -or $token -match $unsafe) {
        throw 'Batch token cannot be transported by this cmd.exe contract.'
    }
}

$cmd = (Get-Item -LiteralPath (
    Join-Path -Path ([Environment]::SystemDirectory) -ChildPath 'cmd.exe'
) -ErrorAction Stop).FullName
$quotedTokens = @($tokens | ForEach-Object { ConvertTo-CmdQuotedToken -Token $_ })
$payload = '"' + ($quotedTokens -join ' ') + '"'

$startInfo = [System.Diagnostics.ProcessStartInfo]::new()
$startInfo.FileName = $cmd
$startInfo.UseShellExecute = $false
$startInfo.Arguments = '/d /s /c ' + $payload
$startInfo.EnvironmentVariables['COMSPEC'] = $cmd
$startInfo.RedirectStandardInput = $false
$startInfo.RedirectStandardOutput = $false
$startInfo.RedirectStandardError = $false

$process = [System.Diagnostics.Process]::new()
try {
    $process.StartInfo = $startInfo
    if (-not $process.Start()) { throw 'cmd.exe could not be started.' }
    $process.WaitForExit()
    $exitCode = $process.ExitCode
}
finally {
    $process.Dispose()
}
if ($exitCode -ne 0) { throw "batch command failed with exit code $exitCode" }
```

The metacharacter rejection and trailing-backslash rule are part of this specific contract, not a general-purpose Windows argument encoder. Do not use this pattern to bypass a runner that rejected a token, and keep native `.exe` launches on argument arrays when possible.

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

Always pass process-scoped bypass whenever starting PowerShell 7 or Windows PowerShell, including interactive sessions, one-shot commands, scripts, encoded commands, and nested shells:

```powershell
pwsh -ExecutionPolicy Bypass -NonInteractive -File .\script.ps1
powershell.exe -ExecutionPolicy Bypass -NonInteractive -File .\script.ps1
```

Inside an existing session:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force
```

Do not change `CurrentUser` or `LocalMachine` execution policy unless the user explicitly asks.
