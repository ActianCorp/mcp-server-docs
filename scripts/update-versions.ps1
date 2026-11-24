<#
.SYNOPSIS
    Registers a released doc version in versions.json and refreshes the
    "latest" folder on the aws-docserver.

.DESCRIPTION
    Called by the "Publish to aws-docserver" stage of the Jenkinsfile after the
    version folder (for example, D:\Sites\mcp-server\1.2) is in place.

    - Adds the version to versions.json if it is missing.
    - Gives the "latest" alias only to the highest version in the file, so a
      rebuild of an older release (for example, 1.1) never takes over "latest".
    - If this version is the highest, replaces the "latest" folder with a copy
      of the version folder. The old "latest" folder is moved to the backup
      directory first.
    - Backs up versions.json before writing, and writes only when the content
      changes. Safe to run more than once.

    Use -DryRun to log what would change without touching anything.

.EXAMPLE
    powershell -NoProfile -ExecutionPolicy Bypass -File update-versions.ps1 `
        -SiteRoot D:\Sites\mcp-server -Version 1.2 -BuildNumber 42 -DryRun
#>
param(
    [Parameter(Mandatory = $true)][string]$SiteRoot,
    [Parameter(Mandatory = $true)][string]$Version,
    [Parameter(Mandatory = $true)][string]$BuildNumber,
    [string]$BackupRoot = 'D:\backups',
    [switch]$DryRun
)

$ErrorActionPreference = 'Stop'

function Write-Log([string]$Message) { Write-Output "[update-versions] $Message" }

# Validate input before touching anything.
$parsed = $null
if (-not [System.Version]::TryParse($Version, [ref]$parsed)) {
    throw "Version '$Version' is not a numeric version such as 1.2."
}
$versionDir  = Join-Path $SiteRoot $Version
$latestDir   = Join-Path $SiteRoot 'latest'
$versionsFile = Join-Path $SiteRoot 'versions.json'

if (-not (Test-Path $versionDir)) {
    throw "Version folder not found: $versionDir"
}

# Read the current list. A missing file starts an empty list.
$entries = @()
if (Test-Path $versionsFile) {
    $raw = Get-Content -Raw -Path $versionsFile
    if ($raw -and $raw.Trim()) {
        $entries = @(ConvertFrom-Json -InputObject $raw)
    }
}

# Add this version if it is not listed yet.
$known = @($entries | ForEach-Object { $_.version })
if ($known -notcontains $Version) {
    Write-Log "Adding version $Version to the list."
    $entries += [pscustomobject]@{ version = $Version; title = $Version; aliases = @() }
}

# Sort numerically, highest first. Entries that are not numeric versions are dropped from sorting
# and kept at the end, unchanged.
$numeric = @($entries | Where-Object { $v = $null; [System.Version]::TryParse($_.version, [ref]$v) })
$other   = @($entries | Where-Object { $v = $null; -not [System.Version]::TryParse($_.version, [ref]$v) })
$numeric = @($numeric | Sort-Object -Property @{ Expression = { [System.Version]$_.version }; Descending = $true })
$highest = $numeric[0].version

# Only the highest version carries the "latest" alias.
$result = @()
foreach ($e in $numeric) {
    $aliases = @()
    if ($e.version -eq $highest) { $aliases = @('latest') }
    $result += [ordered]@{ version = [string]$e.version; title = [string]$e.title; aliases = $aliases }
}
foreach ($e in $other) {
    $result += [ordered]@{ version = [string]$e.version; title = [string]$e.title; aliases = @($e.aliases) }
}

# ConvertTo-Json (Windows PowerShell) indents with 4 spaces. Reformat to 2 spaces to match the repo.
$json = ConvertTo-Json -InputObject $result -Depth 5
$json = [regex]::Replace($json, '(?m)^( +)', { param($m) ' ' * ([int]($m.Groups[1].Length / 2)) })

$current = ''
if (Test-Path $versionsFile) { $current = (Get-Content -Raw -Path $versionsFile) }
$changed = ($current.Trim() -ne $json.Trim())

Write-Log "Highest version: $highest. This build: $Version."
if ($changed) {
    Write-Log 'versions.json will change to:'
    Write-Output $json
} else {
    Write-Log 'versions.json is already up to date.'
}

$refreshLatest = ($Version -eq $highest)
if ($refreshLatest) {
    Write-Log "The 'latest' folder will be replaced with a copy of $Version."
} else {
    Write-Log "$Version is not the highest version. Leaving 'latest' unchanged."
}

if ($DryRun) {
    Write-Log 'Dry run: no files were changed.'
    return
}

if (-not (Test-Path $BackupRoot)) { New-Item -ItemType Directory -Path $BackupRoot | Out-Null }

if ($changed) {
    if (Test-Path $versionsFile) {
        Copy-Item -Path $versionsFile -Destination (Join-Path $BackupRoot "mcp-server-versions-$BuildNumber.json")
    }
    # UTF-8 without a byte order mark, so the browser parses the file cleanly.
    [System.IO.File]::WriteAllText($versionsFile, $json + "`n", (New-Object System.Text.UTF8Encoding($false)))
    Write-Log 'versions.json updated.'
}

if ($refreshLatest) {
    if (Test-Path $latestDir) {
        Move-Item -Path $latestDir -Destination (Join-Path $BackupRoot "mcp-server-latest-$BuildNumber.backup")
    }
    Copy-Item -Path $versionDir -Destination $latestDir -Recurse
    Write-Log "'latest' now matches $Version."
}
