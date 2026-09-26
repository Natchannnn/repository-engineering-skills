[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
if (-not $scriptDir) { $scriptDir = $PSScriptRoot }
$repoRoot = Split-Path -Parent $scriptDir
$installer = Join-Path $repoRoot 'scripts\install-skills.ps1'

$psExe = if (Get-Command powershell.exe -ErrorAction SilentlyContinue) { "powershell.exe" } elseif (Get-Command pwsh -ErrorAction SilentlyContinue) { "pwsh" } else { "powershell" }

function Invoke-Installer {
    param(
        [Parameter(Mandatory = $true)][string]$ScriptPath,
        [Parameter(Mandatory = $true)][string[]]$Arguments
    )
    $prev = $ErrorActionPreference
    try {
        $ErrorActionPreference = 'Continue'
        $output = & $psExe -NoProfile -ExecutionPolicy Bypass -File $ScriptPath @Arguments 2>&1
        $exitCode = $LASTEXITCODE
        return [PSCustomObject]@{
            ExitCode = $exitCode
            Output = ($output | Out-String)
        }
    } finally {
        $ErrorActionPreference = $prev
        $global:LASTEXITCODE = 0
    }
}

$testRoot = Join-Path ([System.IO.Path]::GetTempPath()) ("test-installer-suite-" + [System.Guid]::NewGuid().ToString())
New-Item -ItemType Directory -Path $testRoot | Out-Null

Write-Host "Running Installer Acceptance Suite in: $testRoot"

try {
    # -------------------------------------------------------------------------
    # Test 1: Fresh install includes LICENSE and passes manifest verification
    # -------------------------------------------------------------------------
    $proj1 = Join-Path $testRoot "proj1"
    New-Item -ItemType Directory -Path $proj1 | Out-Null
    $res1 = Invoke-Installer -ScriptPath $installer -Arguments @("-SkillsRepo", $repoRoot, "-TargetProject", $proj1)
    if ($res1.ExitCode -ne 0) { throw "Test 1 failed with exit code $($res1.ExitCode): $($res1.Output)" }

    $foundLicense = Join-Path $proj1 ".agents\skills\repo-foundation\LICENSE"
    $refLicense = Join-Path $proj1 ".agents\skills\repo-native-refactor\LICENSE"
    if (-not (Test-Path -LiteralPath $foundLicense)) { throw "Test 1: repo-foundation/LICENSE missing" }
    if (-not (Test-Path -LiteralPath $refLicense)) { throw "Test 1: repo-native-refactor/LICENSE missing" }
    Write-Host "[PASS] Test 1: Fresh install succeeded and includes LICENSE files in both skills"

    # -------------------------------------------------------------------------
    # Test 2: Target already exists rejected without -Update
    # -------------------------------------------------------------------------
    $res2 = Invoke-Installer -ScriptPath $installer -Arguments @("-SkillsRepo", $repoRoot, "-TargetProject", $proj1)
    if ($res2.ExitCode -eq 0) { throw "Test 2 failed: expected non-zero exit code when destination exists" }
    Write-Host "[PASS] Test 2: Existing destination rejected without -Update"

    # -------------------------------------------------------------------------
    # Test 3: Normal update removes ghost file, creates backup, keeps other skills
    # -------------------------------------------------------------------------
    $userSkill = Join-Path $proj1 ".agents\skills\custom-unrelated-skill"
    New-Item -ItemType Directory -Path $userSkill | Out-Null
    Set-Content -LiteralPath (Join-Path $userSkill "SKILL.md") -Value "Unrelated user skill"
    $ghostFile = Join-Path $proj1 ".agents\skills\repo-foundation\ghost-old.txt"
    Set-Content -LiteralPath $ghostFile -Value "ghost content"

    $res3 = Invoke-Installer -ScriptPath $installer -Arguments @("-SkillsRepo", $repoRoot, "-TargetProject", $proj1, "-Update")
    if ($res3.ExitCode -ne 0) { throw "Test 3 failed: update exit code $($res3.ExitCode): $($res3.Output)" }
    if (Test-Path -LiteralPath $ghostFile) { throw "Test 3 failed: ghost file was not cleaned up during update" }
    if (-not (Test-Path -LiteralPath (Join-Path $userSkill "SKILL.md"))) { throw "Test 3 failed: unrelated user skill was touched!" }

    $backupDirs = @(Get-ChildItem -LiteralPath (Join-Path $proj1 ".agents") -Filter "skills-backup-*" -Directory)
    if ($backupDirs.Count -eq 0) { throw "Test 3 failed: backup directory was not created" }
    if (-not (Test-Path -LiteralPath (Join-Path $backupDirs[0].FullName "repo-foundation\ghost-old.txt"))) {
        throw "Test 3 failed: backup does not contain previous ghost file"
    }
    Write-Host "[PASS] Test 3: Normal update removes ghost files, preserves backup, and protects unrelated skills"

    # -------------------------------------------------------------------------
    # Test 4: Injected Failure during update triggers automatic ROLLBACK
    # -------------------------------------------------------------------------
    # Set up known state in target project:
    $canaryFoundation = Join-Path $proj1 ".agents\skills\repo-foundation\canary.txt"
    $canaryRefactor = Join-Path $proj1 ".agents\skills\repo-native-refactor\canary.txt"
    Set-Content -LiteralPath $canaryFoundation -Value "foundation canary 123"
    Set-Content -LiteralPath $canaryRefactor -Value "refactor canary 456"

    # Create an installer with failure injected during copy
    $injectedInstaller = Join-Path $testRoot "injected-installer.ps1"
    $installerContent = Get-Content -LiteralPath $installer -Raw
    $targetSnippet = "Copy-Item -LiteralPath (Join-Path `$stagedSkill 'SKILL.md') -Destination (Join-Path `$dest 'SKILL.md') -Force"
    $matchCount = ([regex]::Matches($installerContent, [regex]::Escape($targetSnippet))).Count
    if ($matchCount -ne 1) {
        throw "Test 4 setup failure: target snippet occurs $matchCount times, expected exactly 1"
    }

    $patchedContent = $installerContent.Replace(
        $targetSnippet,
        "if (`$skill -eq 'repo-foundation') { throw 'INJECTED_DEPLOYMENT_FAILURE_DURING_COPY' }; Copy-Item -LiteralPath (Join-Path `$stagedSkill 'SKILL.md') -Destination (Join-Path `$dest 'SKILL.md') -Force"
    )
    Set-Content -LiteralPath $injectedInstaller -Value $patchedContent

    $res4 = Invoke-Installer -ScriptPath $injectedInstaller -Arguments @("-SkillsRepo", $repoRoot, "-TargetProject", $proj1, "-Update")
    if ($res4.ExitCode -eq 0) { throw "Test 4 failed: expected injected failure to exit with non-zero code" }
    if (-not $res4.Output.Contains("INJECTED_DEPLOYMENT_FAILURE_DURING_COPY")) {
        throw "Test 4 failed: output did not contain injected error message. Output:`n$($res4.Output)"
    }

    # VERIFY ROLLBACK: Did rollback restore both skills and their canaries?
    if (-not (Test-Path -LiteralPath $canaryFoundation)) { throw "Test 4 ROLLBACK FAILED: canary.txt in repo-foundation missing!" }
    if (-not (Test-Path -LiteralPath $canaryRefactor)) { throw "Test 4 ROLLBACK FAILED: canary.txt in repo-native-refactor missing!" }
    if (-not (Test-Path -LiteralPath (Join-Path $proj1 ".agents\skills\repo-foundation\SKILL.md"))) { throw "Test 4 ROLLBACK FAILED: repo-foundation/SKILL.md missing!" }
    if (-not (Test-Path -LiteralPath (Join-Path $proj1 ".agents\skills\repo-native-refactor\SKILL.md"))) { throw "Test 4 ROLLBACK FAILED: repo-native-refactor/SKILL.md missing!" }

    $foundCanaryContent = (Get-Content -LiteralPath $canaryFoundation).Trim()
    if ($foundCanaryContent -ne "foundation canary 123") { throw "Test 4 ROLLBACK FAILED: canary content mismatch" }
    Write-Host "[PASS] Test 4: Injected deployment failure was caught and automatic rollback fully restored both skills!"

    # -------------------------------------------------------------------------
    # Test 5: Manifest detects Windows Hidden files and rejects/rolls back
    # -------------------------------------------------------------------------
    $hiddenTestInstaller = Join-Path $testRoot "hidden-test-installer.ps1"
    $refCopySnippet = "Copy-Item -LiteralPath (Join-Path `$stagedSkill 'references') -Destination (Join-Path `$dest 'references') -Recurse -Force"
    $refCopyMatchCount = ([regex]::Matches($installerContent, [regex]::Escape($refCopySnippet))).Count
    if ($refCopyMatchCount -ne 1) {
        throw "Test 5 setup failure: refCopySnippet occurs $refCopyMatchCount times, expected exactly 1"
    }

    # Inject creation of a Windows Hidden file in deployed references right after copy
    $hiddenInjectSnippet = @"
Copy-Item -LiteralPath (Join-Path `$stagedSkill 'references') -Destination (Join-Path `$dest 'references') -Recurse -Force
`$ghostHidden = Join-Path `$dest 'references\hidden-ghost.txt'
Set-Content -LiteralPath `$ghostHidden -Value 'hidden payload content'
(Get-Item -LiteralPath `$ghostHidden -Force).Attributes = 'Hidden'
"@
    $hiddenPatchedContent = $installerContent.Replace($refCopySnippet, $hiddenInjectSnippet)
    Set-Content -LiteralPath $hiddenTestInstaller -Value $hiddenPatchedContent

    $res5 = Invoke-Installer -ScriptPath $hiddenTestInstaller -Arguments @("-SkillsRepo", $repoRoot, "-TargetProject", $proj1, "-Update")
    if ($res5.ExitCode -eq 0) { throw "Test 5 failed: expected unmanaged hidden file to cause non-zero exit code" }
    $normalizedText5 = $res5.Output -replace '\s+', ' '
    if ($normalizedText5 -notmatch "unexpected unmanaged file:\s+'references/hidden-ghost\.txt'") {
        throw "Test 5 failed: installer did not identify unmanaged hidden file in manifest! Output:`n$($res5.Output)"
    }
    # Verify rollback cleaned up the hidden ghost file
    $leakedGhost = Join-Path $proj1 ".agents\skills\repo-foundation\references\hidden-ghost.txt"
    if (Test-Path -LiteralPath $leakedGhost) {
        throw "Test 5 ROLLBACK FAILED: hidden-ghost.txt was not cleaned up during rollback!"
    }
    Write-Host "[PASS] Test 5: Unmanaged Windows Hidden file detected by manifest and rolled back safely!"

    # -------------------------------------------------------------------------
    # Test 6: Reusing non-empty -BackupDir is rejected before mutation
    # -------------------------------------------------------------------------
    $dirtyBackupDir = Join-Path $testRoot "dirty-backup"
    New-Item -ItemType Directory -Path (Join-Path $dirtyBackupDir "repo-foundation") -Force | Out-Null
    $staleBackupFile = Join-Path $dirtyBackupDir "repo-foundation\stale-not-in-current-install.txt"
    Set-Content -LiteralPath $staleBackupFile -Value "stale old version file"

    $res6 = Invoke-Installer -ScriptPath $installer -Arguments @("-SkillsRepo", $repoRoot, "-TargetProject", $proj1, "-BackupDir", $dirtyBackupDir, "-Update")
    if ($res6.ExitCode -eq 0) { throw "Test 6 failed: expected non-empty -BackupDir to be rejected with non-zero exit code" }
    if (-not $res6.Output.Contains("already exists and is not empty")) {
        throw "Test 6 failed: error message did not warn about non-empty -BackupDir! Output:`n$($res6.Output)"
    }

    # Verify target project was completely untouched
    $pollutedDest = Join-Path $proj1 ".agents\skills\repo-foundation\stale-not-in-current-install.txt"
    if (Test-Path -LiteralPath $pollutedDest) {
        throw "Test 6 FAILED: target destination was polluted by stale file from dirty BackupDir!"
    }
    if (-not (Test-Path -LiteralPath $canaryFoundation)) {
        throw "Test 6 FAILED: canary was lost during rejected backup pre-flight!"
    }
    Write-Host "[PASS] Test 6: Non-empty -BackupDir safely rejected before modifying destination!"

    Write-Host "`nALL 6 INSTALLER ACCEPTANCE TESTS PASSED SUCCESSFULLY."
    exit 0
}
finally {
    Remove-Item -LiteralPath $testRoot -Recurse -Force -ErrorAction SilentlyContinue
}
