[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
if (-not $scriptDir) { $scriptDir = $PSScriptRoot }
$repoRoot = Split-Path -Parent $scriptDir
$packager = Join-Path $scriptDir "package-runtime.ps1"
$installer = Join-Path $scriptDir "install-skills.ps1"
$verifyPayloadPy = Join-Path $scriptDir "verify-package-payload.py"

$testRoot = Join-Path ([System.IO.Path]::GetTempPath()) ("pkg-acceptance-" + [System.Guid]::NewGuid().ToString())
New-Item -ItemType Directory -Path $testRoot | Out-Null

Write-Host "Running Runtime Package Acceptance Suite in: $testRoot"

try {
    # -------------------------------------------------------------
    # Setup: Create an isolated Git repository fixture with clean history
    # -------------------------------------------------------------
    Write-Host "--> Setting up isolated clean Git fixture..."
    $fixtureRoot = Join-Path $testRoot "git-fixture"
    New-Item -ItemType Directory -Path $fixtureRoot | Out-Null

    # Copy tracked skills, licenses, .gitignore, .gitattributes, and scripts
    Copy-Item -LiteralPath (Join-Path $repoRoot "LICENSE") -Destination $fixtureRoot -Force
    Copy-Item -LiteralPath (Join-Path $repoRoot ".gitignore") -Destination $fixtureRoot -Force
    Copy-Item -LiteralPath (Join-Path $repoRoot ".gitattributes") -Destination $fixtureRoot -Force
    Copy-Item -LiteralPath (Join-Path $repoRoot "repo-foundation") -Destination (Join-Path $fixtureRoot "repo-foundation") -Recurse -Force
    Copy-Item -LiteralPath (Join-Path $repoRoot "repo-native-refactor") -Destination (Join-Path $fixtureRoot "repo-native-refactor") -Recurse -Force
    
    $fixtureScripts = Join-Path $fixtureRoot "scripts"
    New-Item -ItemType Directory -Path $fixtureScripts | Out-Null
    Copy-Item -LiteralPath $packager -Destination (Join-Path $fixtureScripts "package-runtime.ps1") -Force
    Copy-Item -LiteralPath $installer -Destination (Join-Path $fixtureScripts "install-skills.ps1") -Force
    Copy-Item -LiteralPath $verifyPayloadPy -Destination (Join-Path $fixtureScripts "verify-package-payload.py") -Force

    # Initialize Git fixture and make clean initial commit
    & git -C $fixtureRoot init -b main | Out-Null
    & git -C $fixtureRoot config user.email "auditor@example.com"
    & git -C $fixtureRoot config user.name "Auditor"
    & git -C $fixtureRoot add .
    & git -C $fixtureRoot commit -m "feat: initial clean commit for package test" | Out-Null
    
    $fixtureCommit = ([string](& git -C $fixtureRoot rev-parse HEAD)).Trim()
    if (-not $fixtureCommit) { throw "Failed to initialize test git fixture." }

    $fixturePackager = Join-Path $fixtureScripts "package-runtime.ps1"
    $fixtureVerifyPy = Join-Path $fixtureScripts "verify-package-payload.py"
    $fixtureDist = Join-Path $fixtureRoot "dist"

    # -------------------------------------------------------------
    # Test 1: Clean build without -AllowDirty (R1)
    # -------------------------------------------------------------
    Write-Host "--> Test 1: Verifying clean repository release build (without -AllowDirty)..."
    $utcStart = [DateTime]::UtcNow
    & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $fixturePackager -OutputDir $fixtureDist
    if ($LASTEXITCODE -ne 0) { throw "Test 1 FAILED: Packager failed on clean repository without -AllowDirty" }
    $utcEnd = [DateTime]::UtcNow

    $zipPath = Join-Path $fixtureDist "repository-engineering-skills-runtime.zip"
    if (-not (Test-Path -LiteralPath $zipPath)) { throw "Test 1 FAILED: Zip not produced at $zipPath" }

    $unpackedDir = Join-Path $testRoot "unpacked-clean"
    Expand-Archive -LiteralPath $zipPath -DestinationPath $unpackedDir -Force

    $manifestPath = Join-Path $unpackedDir "manifest.json"
    if (-not (Test-Path -LiteralPath $manifestPath)) { throw "Test 1 FAILED: manifest.json missing" }
    $manifest = Get-Content -LiteralPath $manifestPath -Raw | ConvertFrom-Json

    if ($manifest.working_tree_clean -ne $true) { throw "Test 1 FAILED: expected working_tree_clean to be true" }
    if ($manifest.source_commit -ne $fixtureCommit) { throw "Test 1 FAILED: source_commit mismatch" }
    if ($manifest.file_count -ne 17) { throw "Test 1 FAILED: expected exactly 17 payload files, got $($manifest.file_count)" }
    Write-Host "    [PASS] Clean repo build succeeded with 17 verified payload files."

    # -------------------------------------------------------------
    # Test 2: Timestamp UTC format and window check (R3 & T1)
    # -------------------------------------------------------------
    Write-Host "--> Test 2: Verifying UTC timestamp compliance across PowerShell engines (T1)..."
    $rawJson = Get-Content -LiteralPath $manifestPath -Raw
    if ($rawJson -notmatch '"generated_at"\s*:\s*"(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z)"') {
        throw "Test 2 FAILED: manifest.json does not contain valid UTC ISO 8601 timestamp string ending in 'Z'"
    }
    $rawIsoString = $Matches[1]
    $parsedUtc = [DateTime]::Parse($rawIsoString, [System.Globalization.CultureInfo]::InvariantCulture, [System.Globalization.DateTimeStyles]::AdjustToUniversal)
    if ($parsedUtc -lt $utcStart.AddSeconds(-5) -or $parsedUtc -gt $utcEnd.AddSeconds(5)) {
        throw "Test 2 FAILED: Timestamp '$rawIsoString' is out of bounds with respect to UTC execution window."
    }
    Write-Host "    [PASS] Timestamp '$rawIsoString' is strictly UTC-compliant and matches execution window."

    # -------------------------------------------------------------
    # Test 3: Direct byte-for-byte comparison with Git commit objects (R2 & T2)
    # -------------------------------------------------------------
    Write-Host "--> Test 3: Cryptographic byte-for-byte comparison of payload with Git commit objects..."
    $verifyOutput = & python -B $fixtureVerifyPy --repo $fixtureRoot --commit $fixtureCommit --unpacked $unpackedDir 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "Test 3 FAILED: Byte-for-byte comparison against Git commit failed:`n$verifyOutput"
    }
    Write-Host "    [PASS] All 17 payload files match Git commit objects byte-for-byte."

    # -------------------------------------------------------------
    # Test 3b: Negative control - mutated payload must FAIL Git comparison (T2)
    # -------------------------------------------------------------
    Write-Host "--> Test 3b: Verifying negative control (mutated payload must FAIL even if manifest matches)..."
    $tamperDir = Join-Path $testRoot "unpacked-tampered"
    New-Item -ItemType Directory -Path $tamperDir | Out-Null
    Copy-Item -Path (Join-Path $unpackedDir "*") -Destination $tamperDir -Recurse -Force

    # Tamper with repo-foundation/SKILL.md
    $tamperedSkill = Join-Path $tamperDir "skills\repo-foundation\SKILL.md"
    [System.IO.File]::AppendAllText($tamperedSkill, "`nNEGATIVE_CONTROL_NOT_IN_SOURCE_COMMIT`n")

    # Recompute manifest.json so manifest matches the tampered file perfectly
    $tamperedManifest = Get-Content -LiteralPath (Join-Path $tamperDir "manifest.json") -Raw | ConvertFrom-Json
    $newHash = (Get-FileHash -LiteralPath $tamperedSkill -Algorithm SHA256).Hash.ToLowerInvariant()
    $tamperedManifest.files."skills/repo-foundation/SKILL.md" = $newHash
    $utf8NoBom = New-Object System.Text.UTF8Encoding($false)
    [System.IO.File]::WriteAllText((Join-Path $tamperDir "manifest.json"), ($tamperedManifest | ConvertTo-Json -Depth 10), $utf8NoBom)

    # Run verify-package-payload.py against the tampered package
    $prevEap = $ErrorActionPreference
    $negControlCaught = $false
    try {
        $ErrorActionPreference = 'Continue'
        & python -B $fixtureVerifyPy --repo $fixtureRoot --commit $fixtureCommit --unpacked $tamperDir 2>&1 | Out-Null
        if ($LASTEXITCODE -ne 0) {
            $negControlCaught = $true
        }
    }
    catch {
        $negControlCaught = $true
    }
    finally {
        $ErrorActionPreference = $prevEap
        $global:LASTEXITCODE = 0
        Remove-Item -LiteralPath $tamperDir -Recurse -Force -ErrorAction SilentlyContinue
    }

    if (-not $negControlCaught) {
        throw "Test 3b FAILED: Mutated payload was NOT caught by Git object verification!"
    }
    Write-Host "    [PASS] Mutated payload was strictly caught and rejected by Git commit comparison."

    # -------------------------------------------------------------
    # Test 4: Dirty repository rejection without -AllowDirty (R1)
    # -------------------------------------------------------------
    Write-Host "--> Test 4: Verifying rejection of dirty working tree without -AllowDirty..."
    $dirtyTrackedFile = Join-Path $fixtureRoot "repo-foundation\SKILL.md"
    $originalSkillContent = [System.IO.File]::ReadAllText($dirtyTrackedFile)
    [System.IO.File]::AppendAllText($dirtyTrackedFile, "`n<!-- dirty uncommitted edit -->`n")

    $dirtyFailed = $false
    $prevEap = $ErrorActionPreference
    try {
        $ErrorActionPreference = 'Continue'
        $dirtyOutput = & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $fixturePackager -OutputDir (Join-Path $testRoot "dist-dirty") 2>&1
        if ($LASTEXITCODE -ne 0) {
            $dirtyFailed = $true
        }
    }
    catch {
        $dirtyFailed = $true
    }
    finally {
        $ErrorActionPreference = $prevEap
        $global:LASTEXITCODE = 0
        [System.IO.File]::WriteAllText($dirtyTrackedFile, $originalSkillContent)
    }

    if (-not $dirtyFailed) {
        throw "Test 4 FAILED: Packager should have failed on dirty repository without -AllowDirty"
    }
    Write-Host "    [PASS] Dirty repository was rejected as expected."

    # -------------------------------------------------------------
    # Test 5: Ignored files isolation in release and scratch mode (R2)
    # -------------------------------------------------------------
    Write-Host "--> Test 5: Verifying ignored files isolation (R2)..."
    # Inject ignored files matching Astra's audit probe
    $ignoredLog = Join-Path $fixtureRoot "repo-foundation\references\internal-notes.log"
    $ignoredTmp = Join-Path $fixtureRoot "repo-native-refactor\agents\scratch.tmp"
    $agentsDir = Split-Path -Parent $ignoredTmp
    if (-not (Test-Path -LiteralPath $agentsDir)) { New-Item -ItemType Directory -Path $agentsDir -Force | Out-Null }
    [System.IO.File]::WriteAllText($ignoredLog, "internal confidential notes")
    [System.IO.File]::WriteAllText($ignoredTmp, "temporary scratch state")

    # Confirm git status considers repo clean because these extensions are ignored by .gitignore
    $gitStatus = @(& git -C $fixtureRoot status --porcelain)
    if ($gitStatus.Count -ne 0) {
        throw "Test 5 setup error: injected files are not ignored by .gitignore"
    }

    # Run release packaging (clean mode) with ignored files present on disk
    $releaseDistIgnored = Join-Path $testRoot "dist-release-ignored"
    & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $fixturePackager -OutputDir $releaseDistIgnored
    if ($LASTEXITCODE -ne 0) { throw "Test 5 FAILED: Packager failed in release mode with ignored files present" }

    $unpackedIgnoredRelease = Join-Path $testRoot "unpacked-ignored-release"
    Expand-Archive -LiteralPath (Join-Path $releaseDistIgnored "repository-engineering-skills-runtime.zip") -DestinationPath $unpackedIgnoredRelease -Force

    # Direct byte-for-byte check on release with ignored files present on disk
    & python -B $fixtureVerifyPy --repo $fixtureRoot --commit $fixtureCommit --unpacked $unpackedIgnoredRelease
    if ($LASTEXITCODE -ne 0) { throw "Test 5 FAILED: Release package with ignored files present failed Git byte verification" }

    $manifestRelease = Get-Content -LiteralPath (Join-Path $unpackedIgnoredRelease "manifest.json") -Raw | ConvertFrom-Json
    if ($manifestRelease.files.PSObject.Properties['skills/repo-foundation/references/internal-notes.log'] -or
        $manifestRelease.files.PSObject.Properties['skills/repo-native-refactor/agents/scratch.tmp'] -or
        (Test-Path -LiteralPath (Join-Path $unpackedIgnoredRelease "skills\repo-foundation\references\internal-notes.log")) -or
        (Test-Path -LiteralPath (Join-Path $unpackedIgnoredRelease "skills\repo-native-refactor\agents\scratch.tmp"))) {
        throw "Test 5 FAILED: Ignored files leaked into release package!"
    }
    if ($manifestRelease.file_count -ne 17) {
        throw "Test 5 FAILED: Expected 17 files in release manifest, found $($manifestRelease.file_count)"
    }
    Write-Host "    [PASS] Release mode extracted directly from Git commit tree, completely excluding ignored files."

    # Run scratch packaging with -AllowDirty
    $scratchDistIgnored = Join-Path $testRoot "dist-scratch-ignored"
    & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $fixturePackager -OutputDir $scratchDistIgnored -AllowDirty
    if ($LASTEXITCODE -ne 0) { throw "Test 5 FAILED: Packager failed with -AllowDirty" }

    $unpackedIgnoredScratch = Join-Path $testRoot "unpacked-ignored-scratch"
    Expand-Archive -LiteralPath (Join-Path $scratchDistIgnored "repository-engineering-skills-runtime.zip") -DestinationPath $unpackedIgnoredScratch -Force

    $manifestScratch = Get-Content -LiteralPath (Join-Path $unpackedIgnoredScratch "manifest.json") -Raw | ConvertFrom-Json
    if ($manifestScratch.files.PSObject.Properties['skills/repo-foundation/references/internal-notes.log'] -or
        $manifestScratch.files.PSObject.Properties['skills/repo-native-refactor/agents/scratch.tmp'] -or
        (Test-Path -LiteralPath (Join-Path $unpackedIgnoredScratch "skills\repo-foundation\references\internal-notes.log")) -or
        (Test-Path -LiteralPath (Join-Path $unpackedIgnoredScratch "skills\repo-native-refactor\agents\scratch.tmp"))) {
        throw "Test 5 FAILED: Ignored files leaked into scratch package!"
    }
    if ($manifestScratch.file_count -ne 17) {
        throw "Test 5 FAILED: Expected 17 files in scratch manifest, found $($manifestScratch.file_count)"
    }
    Write-Host "    [PASS] Scratch mode strictly bounded payload to whitelisted files, completely excluding ignored files."

    Remove-Item -LiteralPath $ignoredLog -Force
    Remove-Item -LiteralPath $ignoredTmp -Force

    # -------------------------------------------------------------
    # Test 6: Standalone ZIP consumer experience (manual placement)
    # -------------------------------------------------------------
    Write-Host "--> Test 6: Verifying standalone consumer experience without repo installer..."
    $manualProject = Join-Path $testRoot "consumer-manual-project"
    New-Item -ItemType Directory -Path $manualProject | Out-Null
    
    # Standalone verification using manifest.json in unzipped archive
    $unpackedSkills = Join-Path $unpackedDir "skills"
    $consumerAgentsSkills = Join-Path $manualProject ".agents\skills"
    New-Item -ItemType Directory -Path $consumerAgentsSkills | Out-Null

    Copy-Item -LiteralPath (Join-Path $unpackedSkills "repo-foundation") -Destination (Join-Path $consumerAgentsSkills "repo-foundation") -Recurse -Force
    Copy-Item -LiteralPath (Join-Path $unpackedSkills "repo-native-refactor") -Destination (Join-Path $consumerAgentsSkills "repo-native-refactor") -Recurse -Force

    if (-not (Test-Path -LiteralPath (Join-Path $consumerAgentsSkills "repo-foundation\SKILL.md")) -or
        -not (Test-Path -LiteralPath (Join-Path $consumerAgentsSkills "repo-foundation\LICENSE")) -or
        -not (Test-Path -LiteralPath (Join-Path $consumerAgentsSkills "repo-native-refactor\SKILL.md")) -or
        -not (Test-Path -LiteralPath (Join-Path $consumerAgentsSkills "repo-native-refactor\LICENSE"))) {
        throw "Test 6 FAILED: Manual placement failed to produce complete skills layout"
    }
    Write-Host "    [PASS] Standalone manual placement successfully configured consumer project."

    # -------------------------------------------------------------
    # Test 7: Source repo installer compatibility with unzipped bundle
    # -------------------------------------------------------------
    Write-Host "--> Test 7: Verifying installer script compatibility with unpacked skills..."
    $installerProject = Join-Path $testRoot "consumer-installer-project"
    New-Item -ItemType Directory -Path $installerProject | Out-Null

    & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $installer -SkillsRepo $unpackedSkills -TargetProject $installerProject
    if ($LASTEXITCODE -ne 0) { throw "Test 7 FAILED: install-skills.ps1 failed against unpacked bundle" }

    if (-not (Test-Path -LiteralPath (Join-Path $installerProject ".agents\skills\repo-foundation\SKILL.md")) -or
        -not (Test-Path -LiteralPath (Join-Path $installerProject ".agents\skills\repo-native-refactor\SKILL.md"))) {
        throw "Test 7 FAILED: installer failed to install skills from unpacked bundle"
    }
    Write-Host "    [PASS] install-skills.ps1 successfully installed skills from unpacked bundle."

    Write-Host "`nAll 8 Runtime Package Acceptance Tests (including negative control) PASSED successfully!" -ForegroundColor Green
    exit 0
}
finally {
    Remove-Item -LiteralPath $testRoot -Recurse -Force -ErrorAction SilentlyContinue
}
