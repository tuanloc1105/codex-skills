Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$utf8NoBom = [System.Text.UTF8Encoding]::new($false)
[Console]::OutputEncoding = $utf8NoBom
$OutputEncoding = $utf8NoBom

if ([System.Environment]::OSVersion.Platform -ne [System.PlatformID]::Win32NT) {
    [Console]::Error.WriteLine('kafka_guard.ps1 supports native Windows only. Use python3 kafka_guard.py on POSIX or WSL.')
    exit 2
}

$guardPath = Join-Path -Path $PSScriptRoot -ChildPath 'kafka_guard.py'
if (-not (Test-Path -LiteralPath $guardPath -PathType Leaf)) {
    [Console]::Error.WriteLine('Kafka guard Python script is missing next to the PowerShell launcher.')
    exit 2
}
$guardPath = (Resolve-Path -LiteralPath $guardPath -ErrorAction Stop).ProviderPath
$guardArguments = @($args)
foreach ($argument in $guardArguments) {
    if ([string]::IsNullOrEmpty([string]$argument) -or ([string]$argument) -match '[\u0000-\u001F\u007F"]') {
        [Console]::Error.WriteLine('Windows guard arguments contain an empty token, embedded quote, or control character that cannot cross the PowerShell native boundary losslessly.')
        exit 2
    }
}

$pythonCandidates = @(
    [PSCustomObject]@{ Name = 'py.exe'; Prefix = @('-3') },
    [PSCustomObject]@{ Name = 'python.exe'; Prefix = @() },
    [PSCustomObject]@{ Name = 'python3.exe'; Prefix = @() }
)

foreach ($candidate in $pythonCandidates) {
    $application = Get-Command -Name $candidate.Name -CommandType Application -ErrorAction SilentlyContinue |
        Select-Object -First 1
    if ($null -eq $application) {
        continue
    }

    $pythonExecutable = $application.Source
    $prefix = @($candidate.Prefix)
    try {
        & $pythonExecutable @prefix -X utf8 -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 9) else 3)'
        $probeExitCode = $LASTEXITCODE
    }
    catch {
        continue
    }
    if ($probeExitCode -ne 0) {
        continue
    }

    & $pythonExecutable @prefix -X utf8 $guardPath @guardArguments
    $guardExitCode = $LASTEXITCODE
    exit $guardExitCode
}

[Console]::Error.WriteLine('Python 3.9 or newer is required. Install it or expose py.exe, python.exe, or python3.exe on PATH.')
exit 2
