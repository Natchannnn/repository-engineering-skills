[CmdletBinding()]
param(
    [Parameter(Mandatory = $false)]
    [string]$SkillsRepo,

    [Parameter(Mandatory = $true)]
    [string]$TargetProject,

    [Parameter(Mandatory = $false)]
    [string]$SkillsSubdir = '.agents\skills',

    [Parameter(Mandatory = $false)]
    [switch]$Update,

    [Parameter(Mandatory = $false)]
    [string]$BackupDir
)

$ErrorActionPreference = 'Stop'

function Get-RelativePath {
    param(
        [Parameter(Mandatory = $true)][string]$BasePath,
        [Parameter(Mandatory = $true)][string]$FullPath
    )
    $cleanBase = $BasePath.TrimEnd('\', '/') + '\'
    if ($FullPath.StartsWith($cleanBase, [System.StringComparison]::OrdinalIgnoreCase)) {
        return $FullPath.Substring($cleanBase.Length).Replace('\', '/')
    }
    return (Split-Path -Leaf $FullPath)
}

function Build-DirectoryManifest {
    param([Parameter(Mandatory = $true)][string]$DirectoryPath)
    $manifest = @{}
    if (-not (Test-Path -LiteralPath $DirectoryPath -PathType Container)) {
        return $manifest
    }
    $files = @(Get-ChildItem -LiteralPath $DirectoryPath -Recurse -File -Force)
    foreach ($file in $files) {
        $rel = Get-RelativePath -BasePath $DirectoryPath -FullPath $file.FullName
        $hash = (Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
        $manifest[$rel] = $hash
    }
    return $manifest
}

# 1. Resolve source repository root
if (-not $SkillsRepo) {
    $scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
    if (-not $scriptDir) {
        $scriptDir = $PSScriptRoot
    }
    $SkillsRepo = Split-Path -Parent $scriptDir
}

if (-not (Test-Path -LiteralPath $SkillsRepo -PathType Container)) {
    throw "Source skills repository not found at literal path: '$SkillsRepo'"
}

$resolvedSource = (Get-Item -LiteralPath $SkillsRepo).FullName

# 2. Pre-flight checks on target project
if (-not (Test-Path -LiteralPath $TargetProject -PathType Container)) {
    throw "Target project directory does not exist at literal path: '$TargetProject'"
}

$resolvedTargetProject = (Get-Item -LiteralPath $TargetProject).FullName
$skillsInstallRoot = Join-Path $resolvedTargetProject $SkillsSubdir
$skillNames = @('repo-foundation', 'repo-native-refactor')

# 3. Pre-flight validation of BOTH source skills before any destination modification
foreach ($skill in $skillNames) {
    $skillSourceDir = Join-Path $resolvedSource $skill
    if (-not (Test-Path -LiteralPath $skillSourceDir -PathType Container)) {
        throw "Source skill directory missing: '$skillSourceDir'"
    }

    $skillDoc = Join-Path $skillSourceDir 'SKILL.md'
    if (-not (Test-Path -LiteralPath $skillDoc -PathType Leaf)) {
        throw "Source SKILL.md missing in: '$skillSourceDir'"
    }

    $skillLicense = Join-Path $skillSourceDir 'LICENSE'
    if (-not (Test-Path -LiteralPath $skillLicense -PathType Leaf)) {
        throw "Source LICENSE missing in: '$skillSourceDir'"
    }

    $refDir = Join-Path $skillSourceDir 'references'
    if (-not (Test-Path -LiteralPath $refDir -PathType Container)) {
        throw "Source references directory missing in: '$skillSourceDir'"
    }

    $refFiles = @(Get-ChildItem -LiteralPath $refDir -Recurse -File -Force)
    if ($refFiles.Count -eq 0) {
        throw "Source references directory is empty in: '$skillSourceDir'"
    }
}

# 4. Pre-flight check on destination: protect existing installations
$existingDestinations = @()
foreach ($skill in $skillNames) {
    $dest = Join-Path $skillsInstallRoot $skill
    if (Test-Path -LiteralPath $dest) {
        $existingDestinations += $dest
    }
}

if ($existingDestinations.Count -gt 0 -and -not $Update) {
    $foundList = $existingDestinations -join ', '
    throw "Destination skill already exists: [$foundList]. To update an existing installation safely without mixing versions, re-run with -Update."
}

# 5. Staging Phase: Prepare payload in installer-owned isolated directory and compute expected manifests
$stagingRoot = Join-Path ([System.IO.Path]::GetTempPath()) ("skills-staging-" + [System.Guid]::NewGuid().ToString())
New-Item -ItemType Directory -Path $stagingRoot -Force | Out-Null

$expectedManifests = @{}

try {
    foreach ($skill in $skillNames) {
        $skillSourceDir = Join-Path $resolvedSource $skill
        $stagedSkill = Join-Path $stagingRoot $skill
        New-Item -ItemType Directory -Path $stagedSkill -Force | Out-Null

        # Copy SKILL.md
        Copy-Item -LiteralPath (Join-Path $skillSourceDir 'SKILL.md') -Destination (Join-Path $stagedSkill 'SKILL.md') -Force

        # Copy LICENSE
        Copy-Item -LiteralPath (Join-Path $skillSourceDir 'LICENSE') -Destination (Join-Path $stagedSkill 'LICENSE') -Force

        # Copy references
        $stagedRef = Join-Path $stagedSkill 'references'
        Copy-Item -LiteralPath (Join-Path $skillSourceDir 'references') -Destination $stagedRef -Recurse -Force

        # Copy optional metadata (e.g. agents/openai.yaml if present)
        $agentsDir = Join-Path $skillSourceDir 'agents'
        if (Test-Path -LiteralPath $agentsDir -PathType Container) {
            $stagedAgents = Join-Path $stagedSkill 'agents'
            Copy-Item -LiteralPath $agentsDir -Destination $stagedAgents -Recurse -Force
        }

        # Build expected manifest from staged payload
        $expectedManifests[$skill] = Build-DirectoryManifest -DirectoryPath $stagedSkill
    }

    # 6. Backup Phase (if updating existing skills)
    $actualBackupPath = $null
    $preUpdateManifests = @{}
    if ($existingDestinations.Count -gt 0 -and $Update) {
        # Capture byte-exact pre-update manifests for all existing destinations
        foreach ($dest in $existingDestinations) {
            $skillName = Split-Path -Leaf $dest
            $preUpdateManifests[$skillName] = Build-DirectoryManifest -DirectoryPath $dest
        }

        if ($BackupDir) {
            # Reject if BackupDir already exists and is not empty to prevent mixing backup contents
            if (Test-Path -LiteralPath $BackupDir) {
                $existingItems = @(Get-ChildItem -LiteralPath $BackupDir -Force)
                if ($existingItems.Count -gt 0) {
                    throw "Specified -BackupDir '$BackupDir' already exists and is not empty. To prevent mixing backup versions, specify an empty or non-existing path, or omit -BackupDir for an automatic timestamped backup."
                }
            }
            $actualBackupPath = $BackupDir
        } else {
            $timestamp = Get-Date -Format 'yyyyMMdd-HHmmss'
            $actualBackupPath = Join-Path $resolvedTargetProject (".agents\skills-backup-" + $timestamp)
            $counter = 1
            while (Test-Path -LiteralPath $actualBackupPath) {
                $actualBackupPath = Join-Path $resolvedTargetProject (".agents\skills-backup-${timestamp}-${counter}")
                $counter++
            }
        }
        New-Item -ItemType Directory -Path $actualBackupPath -Force | Out-Null

        foreach ($dest in $existingDestinations) {
            $skillName = Split-Path -Leaf $dest
            $backupSkillDest = Join-Path $actualBackupPath $skillName
            New-Item -ItemType Directory -Path $backupSkillDest -Force | Out-Null
            Get-ChildItem -LiteralPath $dest -Force | ForEach-Object {
                Copy-Item -LiteralPath $_.FullName -Destination $backupSkillDest -Recurse -Force
            }
        }

        # Verify that backup matches pre-update destination manifests byte-for-byte and has no extra files
        foreach ($skill in $preUpdateManifests.Keys) {
            $backupSkillDest = Join-Path $actualBackupPath $skill
            $expectedPre = $preUpdateManifests[$skill]
            $actualBackupManifest = Build-DirectoryManifest -DirectoryPath $backupSkillDest

            foreach ($rel in $expectedPre.Keys) {
                if (-not $actualBackupManifest.ContainsKey($rel)) {
                    throw "Backup verification failed: '$rel' missing in backup destination '$backupSkillDest'."
                }
                if ($actualBackupManifest[$rel] -ne $expectedPre[$rel]) {
                    throw "Backup verification failed: checksum mismatch on '$rel' in backup destination '$backupSkillDest'."
                }
            }
            foreach ($rel in $actualBackupManifest.Keys) {
                if (-not $expectedPre.ContainsKey($rel)) {
                    throw "Backup verification failed: unmanaged file '$rel' found in backup destination '$backupSkillDest'."
                }
            }
        }
        Write-Output "Backed up existing skills to: '$actualBackupPath'"
    }

    # 7. Deployment with Automatic Rollback on Failure
    New-Item -ItemType Directory -Path $skillsInstallRoot -Force | Out-Null

    try {
        # Clean existing managed skill destinations only when updating
        if ($Update) {
            foreach ($skill in $skillNames) {
                $dest = Join-Path $skillsInstallRoot $skill
                if (Test-Path -LiteralPath $dest) {
                    Remove-Item -LiteralPath $dest -Recurse -Force
                }
            }
        }

        # Copy staged skills to destination
        foreach ($skill in $skillNames) {
            $stagedSkill = Join-Path $stagingRoot $skill
            $dest = Join-Path $skillsInstallRoot $skill
            New-Item -ItemType Directory -Path $dest -Force | Out-Null

            Copy-Item -LiteralPath (Join-Path $stagedSkill 'SKILL.md') -Destination (Join-Path $dest 'SKILL.md') -Force
            Copy-Item -LiteralPath (Join-Path $stagedSkill 'LICENSE') -Destination (Join-Path $dest 'LICENSE') -Force
            Copy-Item -LiteralPath (Join-Path $stagedSkill 'references') -Destination (Join-Path $dest 'references') -Recurse -Force

            $stagedAgents = Join-Path $stagedSkill 'agents'
            if (Test-Path -LiteralPath $stagedAgents -PathType Container) {
                Copy-Item -LiteralPath $stagedAgents -Destination (Join-Path $dest 'agents') -Recurse -Force
            }
        }

        # 8. Post-deploy comprehensive manifest & hash verification
        foreach ($skill in $skillNames) {
            $dest = Join-Path $skillsInstallRoot $skill
            $expected = $expectedManifests[$skill]
            $actual = Build-DirectoryManifest -DirectoryPath $dest

            # Verify all expected files are present with identical SHA-256
            foreach ($relPath in $expected.Keys) {
                if (-not $actual.ContainsKey($relPath)) {
                    throw "Deployed skill '$skill' is missing required file: '$relPath'"
                }
                if ($actual[$relPath] -ne $expected[$relPath]) {
                    throw "Deployed skill '$skill' has checksum mismatch on file: '$relPath' (expected $($expected[$relPath]), got $($actual[$relPath]))"
                }
            }

            # Verify no unmanaged extra files exist in deployed destination
            foreach ($relPath in $actual.Keys) {
                if (-not $expected.ContainsKey($relPath)) {
                    throw "Deployed skill '$skill' contains unexpected unmanaged file: '$relPath'"
                }
            }
        }
    }
    catch {
        $deployError = $_.Exception.Message
        Write-Warning "Deployment failure encountered: $deployError. Initiating automatic rollback..."

        # Rollback logic: Clean any partial deployment and restore from backup if available
        $rollbackSuccess = $true
        $rollbackDetails = ""

        try {
            foreach ($skill in $skillNames) {
                $dest = Join-Path $skillsInstallRoot $skill
                if (Test-Path -LiteralPath $dest) {
                    Remove-Item -LiteralPath $dest -Recurse -Force -ErrorAction SilentlyContinue
                }

                if ($actualBackupPath) {
                    $backupSkill = Join-Path $actualBackupPath $skill
                    if (Test-Path -LiteralPath $backupSkill -PathType Container) {
                        New-Item -ItemType Directory -Path $dest -Force | Out-Null
                        Get-ChildItem -LiteralPath $backupSkill -Force | ForEach-Object {
                            Copy-Item -LiteralPath $_.FullName -Destination $dest -Recurse -Force
                        }
                    }
                }
            }

            # Verify rollback state against pre-update manifests
            if ($actualBackupPath -and $preUpdateManifests.Count -gt 0) {
                foreach ($skill in $preUpdateManifests.Keys) {
                    $dest = Join-Path $skillsInstallRoot $skill
                    $expectedPre = $preUpdateManifests[$skill]
                    $actualRollback = Build-DirectoryManifest -DirectoryPath $dest

                    foreach ($rel in $expectedPre.Keys) {
                        if (-not $actualRollback.ContainsKey($rel)) {
                            $rollbackSuccess = $false
                            $rollbackDetails = "Rollback verification failed: missing file '$rel' in '$dest'"
                            break
                        }
                        if ($actualRollback[$rel] -ne $expectedPre[$rel]) {
                            $rollbackSuccess = $false
                            $rollbackDetails = "Rollback verification failed: checksum mismatch on '$rel' in '$dest'"
                            break
                        }
                    }
                    foreach ($rel in $actualRollback.Keys) {
                        if (-not $expectedPre.ContainsKey($rel)) {
                            $rollbackSuccess = $false
                            $rollbackDetails = "Rollback verification failed: unmanaged file '$rel' in '$dest'"
                            break
                        }
                    }
                    if (-not $rollbackSuccess) { break }
                }
            }
        }
        catch {
            $rollbackSuccess = $false
            $rollbackDetails = $_.Exception.Message
        }

        if ($rollbackSuccess -and $actualBackupPath) {
            throw "Installation failed during deployment: $deployError. Previous installation was safely rolled back and restored from: '$actualBackupPath'"
        } elseif ($actualBackupPath) {
            throw "CRITICAL: Installation failed ($deployError) AND automatic rollback encountered an issue ($rollbackDetails). Your previous installation remains preserved in backup at: '$actualBackupPath'. Please restore manually."
        } else {
            throw "Installation failed during deployment: $deployError. Cleaned partial deployment artifacts from target project."
        }
    }

    $actionVerb = if ($Update) { "Updated" } else { "Installed" }
    $totalFiles = 0
    foreach ($m in $expectedManifests.Values) { $totalFiles += $m.Count }
    Write-Output "$actionVerb skills [repo-foundation, repo-native-refactor] successfully into: '$skillsInstallRoot'"
    Write-Output "Verified byte-exact SHA-256 integrity for all $totalFiles deployed files across both skills."
    if ($actualBackupPath) {
        Write-Output "Previous installation safely preserved at: '$actualBackupPath'"
    }
}
finally {
    if (Test-Path -LiteralPath $stagingRoot) {
        Remove-Item -LiteralPath $stagingRoot -Recurse -Force -ErrorAction SilentlyContinue
    }
}
