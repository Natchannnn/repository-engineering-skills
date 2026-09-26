[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
if (-not $scriptDir) {
    $scriptDir = $PSScriptRoot
}
$repoRoot = Split-Path -Parent $scriptDir
$archiveRoot = Join-Path $repoRoot 'evals-suite'

if (-not (Test-Path -LiteralPath $archiveRoot -PathType Container)) {
    throw "Archive root directory not found at: $archiveRoot"
}

$verifiers = @(Get-ChildItem -LiteralPath $archiveRoot -Recurse -Filter verify_hashes.py -File | Sort-Object FullName)

if ($verifiers.Count -ne 31) {
    throw "Expected 31 archive verifiers; found $($verifiers.Count). Review inventory."
}

Get-Command python -ErrorAction Stop | Out-Null

foreach ($verifier in $verifiers) {
    & python -B $verifier.FullName
    if ($LASTEXITCODE -ne 0) {
        throw "Archive verification failed: $($verifier.FullName)"
    }
}

Write-Output "Verified $($verifiers.Count)/31 archive packets successfully."
