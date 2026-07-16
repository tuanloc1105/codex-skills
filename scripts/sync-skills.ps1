[CmdletBinding()]
param(
    [Parameter(Position = 0, ValueFromRemainingArguments = $true)]
    [string[]] $Skill
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'

$repoRoot = [System.IO.Path]::GetFullPath((Join-Path -Path $PSScriptRoot -ChildPath '..'))
$homeDirectory = [Environment]::GetFolderPath([Environment+SpecialFolder]::UserProfile)
if ([string]::IsNullOrWhiteSpace($homeDirectory)) {
    throw 'The current user home directory could not be determined.'
}

$robocopy = Get-Command -Name 'robocopy.exe' -CommandType Application -ErrorAction SilentlyContinue |
    Select-Object -First 1
if ($null -eq $robocopy) {
    throw 'robocopy.exe is required but was not found in PATH.'
}

$destinationRoot = Join-Path -Path $homeDirectory -ChildPath '.codex\skills'
$skillNames = @()

if ($null -ne $Skill -and $Skill.Count -gt 0) {
    $skillNames = @($Skill)
}
else {
    $skillNames = @(
        Get-ChildItem -LiteralPath $repoRoot -Directory -Force |
            Where-Object {
                Test-Path -LiteralPath (Join-Path -Path $_.FullName -ChildPath 'SKILL.md') -PathType Leaf
            } |
            Sort-Object -Property Name |
            ForEach-Object { $_.Name }
    )
}

if ($skillNames.Count -eq 0) {
    throw 'No skill directories containing SKILL.md were found.'
}

New-Item -ItemType Directory -Path $destinationRoot -Force | Out-Null

foreach ($skillName in $skillNames) {
    if (
        [string]::IsNullOrWhiteSpace($skillName) -or
        $skillName -in @('.', '..') -or
        $skillName -match '[\\/]'
    ) {
        throw "Skill names must be top-level directory names: $skillName"
    }

    $source = Join-Path -Path $repoRoot -ChildPath $skillName
    $skillFile = Join-Path -Path $source -ChildPath 'SKILL.md'
    if (-not (Test-Path -LiteralPath $skillFile -PathType Leaf)) {
        throw "Skill not found or missing SKILL.md: $skillName"
    }

    $destination = Join-Path -Path $destinationRoot -ChildPath $skillName
    New-Item -ItemType Directory -Path $destination -Force | Out-Null

    $robocopyArguments = @(
        $source
        $destination
        '/E'
        '/COPY:DAT'
        '/DCOPY:DAT'
        '/R:2'
        '/W:1'
        '/NFL'
        '/NDL'
        '/NJH'
        '/NJS'
        '/NP'
        '/XD'
        '.git'
        '.serena'
        '__pycache__'
        '/XF'
        '.git'
        '.serena'
        '.DS_Store'
        '*.pyc'
    )

    $nativeErrorPreference = Get-Variable -Name PSNativeCommandUseErrorActionPreference -ErrorAction SilentlyContinue
    $previousNativeErrorPreference = $null
    if ($null -ne $nativeErrorPreference) {
        $previousNativeErrorPreference = $nativeErrorPreference.Value
        Set-Variable -Name PSNativeCommandUseErrorActionPreference -Value $false
    }

    try {
        & $robocopy.Path @robocopyArguments
        $robocopyExitCode = $LASTEXITCODE
    }
    finally {
        if ($null -ne $nativeErrorPreference) {
            Set-Variable -Name PSNativeCommandUseErrorActionPreference -Value $previousNativeErrorPreference
        }
    }

    if ($robocopyExitCode -ge 8) {
        throw "robocopy failed for '$skillName' with exit code $robocopyExitCode."
    }

    Write-Host "Synced $skillName -> $destination"
}

Write-Host 'Done. Destination-only files were left unchanged.'
