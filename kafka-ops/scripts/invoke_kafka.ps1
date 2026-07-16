Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$utf8NoBom = [System.Text.UTF8Encoding]::new($false)
[Console]::OutputEncoding = $utf8NoBom
$OutputEncoding = $utf8NoBom

function Stop-WithCode {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Message,

        [int]$Code = 2
    )

    [Console]::Error.WriteLine($Message)
    exit $Code
}

function Test-FullyQualifiedWindowsPath {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Path
    )

    if ($Path -match '^[A-Za-z]:[\\/]') {
        return $true
    }
    if ($Path -match '^\\\\[^\\/]+[\\/][^\\/]+(?:[\\/]|$)') {
        return $true
    }
    return $false
}

function ConvertTo-CmdQuotedToken {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Token
    )

    $escapedToken = [regex]::Replace($Token, '(\\+)$', '$1$1')
    return '"' + $escapedToken + '"'
}

if ([System.Environment]::OSVersion.Platform -ne [System.PlatformID]::Win32NT) {
    Stop-WithCode 'invoke_kafka.ps1 supports native Windows only.'
}
if ($args.Count -lt 1) {
    Stop-WithCode 'Expected an absolute Kafka executable path followed by its exact argument tokens.'
}

$requestedBinary = [string]$args[0]
if (-not (Test-FullyQualifiedWindowsPath -Path $requestedBinary)) {
    Stop-WithCode 'Kafka executable path must be fully qualified; drive-relative and rooted-relative paths are refused.'
}
try {
    $binaryItem = Get-Item -LiteralPath $requestedBinary -ErrorAction Stop
}
catch {
    Stop-WithCode 'Kafka executable does not exist or cannot be resolved.'
}
if ($binaryItem.PSIsContainer) {
    Stop-WithCode 'Kafka executable path resolves to a directory.'
}

$binary = $binaryItem.FullName
$extension = [System.IO.Path]::GetExtension($binary).ToLowerInvariant()
$canonicalName = [System.IO.Path]::GetFileNameWithoutExtension($binary).ToLowerInvariant()
if ($canonicalName -notmatch '^kafka-[a-z0-9-]+$') {
    Stop-WithCode 'Executable is not a recognized Apache Kafka CLI filename.'
}
if ($extension -notin @('.bat', '.cmd', '.exe', '')) {
    Stop-WithCode 'Unsupported native Windows Kafka executable type.'
}

$kafkaArguments = @()
if ($args.Count -gt 1) {
    $kafkaArguments = @($args[1..($args.Count - 1)] | ForEach-Object { [string]$_ })
}
foreach ($argument in $kafkaArguments) {
    if ([string]::IsNullOrEmpty($argument)) {
        Stop-WithCode 'Kafka argv contains an empty token and cannot be transported exactly.'
    }
    if ($argument -match '[\u0000-\u001F\u007F"]') {
        Stop-WithCode 'Kafka argv contains an embedded quote or control character and cannot cross the PowerShell native boundary losslessly.'
    }
}

if ($extension -in @('.bat', '.cmd')) {
    $batchUnsafePattern = '[%!^&|<>"\u0000-\u001F\u007F]'
    if ($binary -match $batchUnsafePattern) {
        Stop-WithCode 'Kafka batch path contains a cmd.exe metacharacter and cannot be executed safely.'
    }
    foreach ($argument in $kafkaArguments) {
        if ($argument -match $batchUnsafePattern) {
            Stop-WithCode 'Kafka batch argv contains a cmd.exe metacharacter and cannot be executed safely.'
        }
    }

    $commandInterpreterPath = Join-Path -Path ([System.Environment]::SystemDirectory) -ChildPath 'cmd.exe'
    try {
        $commandInterpreter = Get-Item -LiteralPath $commandInterpreterPath -ErrorAction Stop
    }
    catch {
        Stop-WithCode 'cmd.exe is required to execute the Apache Kafka Windows batch scripts.'
    }
    if ($commandInterpreter.PSIsContainer) {
        Stop-WithCode 'Trusted Windows cmd.exe path resolves to a directory.'
    }

    $quotedTokens = @(ConvertTo-CmdQuotedToken -Token $binary)
    foreach ($argument in $kafkaArguments) {
        $quotedTokens += ConvertTo-CmdQuotedToken -Token $argument
    }
    $commandLine = '"' + ($quotedTokens -join ' ') + '"'
    $commandInterpreterExecutable = $commandInterpreter.FullName
    $processStartInfo = [System.Diagnostics.ProcessStartInfo]::new()
    $processStartInfo.FileName = $commandInterpreterExecutable
    $processStartInfo.UseShellExecute = $false
    $processStartInfo.Arguments = '/d /s /c ' + $commandLine
    $processStartInfo.EnvironmentVariables['COMSPEC'] = $commandInterpreterExecutable
    $processStartInfo.RedirectStandardInput = $false
    $processStartInfo.RedirectStandardOutput = $false
    $processStartInfo.RedirectStandardError = $false

    $process = [System.Diagnostics.Process]::new()
    try {
        $process.StartInfo = $processStartInfo
        if (-not $process.Start()) {
            Stop-WithCode 'cmd.exe could not be started.'
        }
        $process.WaitForExit()
        $kafkaExitCode = $process.ExitCode
    }
    finally {
        $process.Dispose()
    }
    exit $kafkaExitCode
}

& $binary @kafkaArguments
$kafkaExitCode = $LASTEXITCODE
exit $kafkaExitCode
