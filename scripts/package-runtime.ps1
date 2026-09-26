[CmdletBinding()]
param(
    [Parameter(Mandatory = $false)]
    [string]$OutputDir,

    [Parameter(Mandatory = $false)]
    [switch]$AllowDirty,

    [Parameter(Mandatory = $false)]
    [string]$SourceCommit = "HEAD"
)

$ErrorActionPreference = 'Stop'

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
if (-not $scriptDir) { $scriptDir = $PSScriptRoot }
$repoRoot = (Split-Path -Parent $scriptDir)

# 1. Verify git and resolve source commit SHA
$gitCmd = Get-Command git -ErrorAction SilentlyContinue
if (-not $gitCmd) {
    throw "git executable not found in PATH. A verified source commit is required."
}

$commitSha = (& git -C $repoRoot rev-parse $SourceCommit 2>$null)
if ($LASTEXITCODE -ne 0 -or -not $commitSha) {
    throw "Failed to retrieve source git commit SHA from '$SourceCommit' in '$repoRoot'"
}
$sourceCommitSha = ([string]($commitSha | Out-String)).Trim()

# 2. Inspect git working tree status null-safely
$statusOutput = & git -C $repoRoot status --porcelain
if ($LASTEXITCODE -ne 0) {
    throw "Failed to inspect repository status from: '$repoRoot'"
}
$statusLines = @($statusOutput | Where-Object { [string]::IsNullOrWhiteSpace($_) -eq $false })
$isDirty = ($statusLines.Count -gt 0)

if ($isDirty -and -not $AllowDirty) {
    throw "Working tree is dirty. Runtime packages must be built from a clean, recorded commit revision. (Use -AllowDirty only for local scratch testing)."
}

# 3. Define output destination
if (-not $OutputDir) {
    $OutputDir = Join-Path $repoRoot "dist"
}
New-Item -ItemType Directory -Path $OutputDir -Force | Out-Null
$zipPath = Join-Path $OutputDir "repository-engineering-skills-runtime.zip"

# 4. Create isolated staging workspace
$stagingRoot = Join-Path ([System.IO.Path]::GetTempPath()) ("pkg-runtime-" + [System.Guid]::NewGuid().ToString())
$bundleDir = Join-Path $stagingRoot "repository-engineering-skills-runtime"
$skillsDir = Join-Path $bundleDir "skills"
New-Item -ItemType Directory -Path $skillsDir -Force | Out-Null

try {
    # 5. Extract and stage payload files
    $managedSkills = @("repo-foundation", "repo-native-refactor")

    if (-not $AllowDirty) {
        # RELEASE MODE: Extract bytes directly from Git commit object tree
        $gitQueryPaths = @(
            "LICENSE",
            "repo-foundation/SKILL.md",
            "repo-foundation/LICENSE",
            "repo-foundation/agents/openai.yaml",
            "repo-foundation/references",
            "repo-native-refactor/SKILL.md",
            "repo-native-refactor/LICENSE",
            "repo-native-refactor/agents/openai.yaml",
            "repo-native-refactor/references"
        )

        $treeFiles = @(& git -C $repoRoot ls-tree -r --name-only $sourceCommitSha $gitQueryPaths)
        if ($LASTEXITCODE -ne 0 -or $treeFiles.Count -eq 0) {
            throw "Failed to resolve tracked payload files from commit: $sourceCommitSha"
        }

        # Filter: ensure only permitted paths
        $filteredTreeFiles = @($treeFiles | Where-Object {
            $_ -eq "LICENSE" -or
            $_ -eq "repo-foundation/SKILL.md" -or
            $_ -eq "repo-foundation/LICENSE" -or
            $_ -eq "repo-foundation/agents/openai.yaml" -or
            ($_ -like "repo-foundation/references/*.md") -or
            $_ -eq "repo-native-refactor/SKILL.md" -or
            $_ -eq "repo-native-refactor/LICENSE" -or
            $_ -eq "repo-native-refactor/agents/openai.yaml" -or
            ($_ -like "repo-native-refactor/references/*.md")
        })

        $tarFile = Join-Path $stagingRoot "git-source.tar"
        $tarExtract = Join-Path $stagingRoot "git-source"
        New-Item -ItemType Directory -Path $tarExtract -Force | Out-Null

        & git -C $repoRoot archive --format=tar --output=$tarFile $sourceCommitSha $filteredTreeFiles
        if ($LASTEXITCODE -ne 0) {
            throw "git archive failed for commit $sourceCommitSha"
        }
        tar -xf $tarFile -C $tarExtract

        # Copy root LICENSE
        $extractedRootLicense = Join-Path $tarExtract "LICENSE"
        if (-not (Test-Path -LiteralPath $extractedRootLicense)) {
            throw "LICENSE missing in commit $sourceCommitSha"
        }
        Copy-Item -LiteralPath $extractedRootLicense -Destination (Join-Path $bundleDir "LICENSE") -Force

        # Copy skills into skills/
        foreach ($skill in $managedSkills) {
            $extractedSkillDir = Join-Path $tarExtract $skill
            if (-not (Test-Path -LiteralPath $extractedSkillDir)) {
                throw "Skill directory '$skill' missing in commit $sourceCommitSha"
            }
            $destSkillDir = Join-Path $skillsDir $skill
            New-Item -ItemType Directory -Path $destSkillDir -Force | Out-Null

            # Copy SKILL.md
            Copy-Item -LiteralPath (Join-Path $extractedSkillDir "SKILL.md") -Destination (Join-Path $destSkillDir "SKILL.md") -Force
            # Copy LICENSE
            Copy-Item -LiteralPath (Join-Path $extractedSkillDir "LICENSE") -Destination (Join-Path $destSkillDir "LICENSE") -Force

            # Copy agents/openai.yaml if present
            $agentYaml = Join-Path $extractedSkillDir "agents\openai.yaml"
            if (Test-Path -LiteralPath $agentYaml) {
                $destAgents = Join-Path $destSkillDir "agents"
                New-Item -ItemType Directory -Path $destAgents -Force | Out-Null
                Copy-Item -LiteralPath $agentYaml -Destination (Join-Path $destAgents "openai.yaml") -Force
            }

            # Copy references (*.md)
            $srcRefs = Join-Path $extractedSkillDir "references"
            if (-not (Test-Path -LiteralPath $srcRefs)) {
                throw "Missing references directory for '$skill' in commit $sourceCommitSha"
            }
            $destRefs = Join-Path $destSkillDir "references"
            New-Item -ItemType Directory -Path $destRefs -Force | Out-Null

            $refFiles = @(Get-ChildItem -LiteralPath $srcRefs -File | Where-Object { $_.Extension -eq '.md' })
            if ($refFiles.Count -eq 0) {
                throw "References directory is empty for '$skill' in commit $sourceCommitSha"
            }
            foreach ($rf in $refFiles) {
                Copy-Item -LiteralPath $rf.FullName -Destination (Join-Path $destRefs $rf.Name) -Force
            }
        }
    } else {
        # SCRATCH MODE (-AllowDirty): Stage from working tree with strict whitelist
        $rootLicense = Join-Path $repoRoot "LICENSE"
        if (-not (Test-Path -LiteralPath $rootLicense)) {
            throw "Root LICENSE missing at: '$rootLicense'"
        }
        Copy-Item -LiteralPath $rootLicense -Destination (Join-Path $bundleDir "LICENSE") -Force

        foreach ($skill in $managedSkills) {
            $srcSkillDir = Join-Path $repoRoot $skill
            $destSkillDir = Join-Path $skillsDir $skill
            New-Item -ItemType Directory -Path $destSkillDir -Force | Out-Null

            # Copy SKILL.md
            $skillMd = Join-Path $srcSkillDir "SKILL.md"
            if (-not (Test-Path -LiteralPath $skillMd)) { throw "Missing SKILL.md in: '$srcSkillDir'" }
            Copy-Item -LiteralPath $skillMd -Destination (Join-Path $destSkillDir "SKILL.md") -Force

            # Copy skill-level LICENSE
            $skillLicense = Join-Path $srcSkillDir "LICENSE"
            if (-not (Test-Path -LiteralPath $skillLicense)) { throw "Missing LICENSE in: '$srcSkillDir'" }
            Copy-Item -LiteralPath $skillLicense -Destination (Join-Path $destSkillDir "LICENSE") -Force

            # Copy only agents/openai.yaml if present (strictly openai.yaml, never scratch/tmp files)
            $srcOpenAiYaml = Join-Path $srcSkillDir "agents\openai.yaml"
            if (Test-Path -LiteralPath $srcOpenAiYaml) {
                $destAgents = Join-Path $destSkillDir "agents"
                New-Item -ItemType Directory -Path $destAgents -Force | Out-Null
                Copy-Item -LiteralPath $srcOpenAiYaml -Destination (Join-Path $destAgents "openai.yaml") -Force
            }

            # Copy references (strictly *.md, never *.log, *.tmp or unmanaged files)
            $srcRef = Join-Path $srcSkillDir "references"
            if (-not (Test-Path -LiteralPath $srcRef)) { throw "Missing references directory in: '$srcSkillDir'" }
            $destRef = Join-Path $destSkillDir "references"
            New-Item -ItemType Directory -Path $destRef -Force | Out-Null
            
            $refFiles = @(Get-ChildItem -LiteralPath $srcRef -File | Where-Object { $_.Extension -eq '.md' })
            if ($refFiles.Count -eq 0) { throw "References directory is empty in: '$srcSkillDir'" }
            foreach ($rf in $refFiles) {
                Copy-Item -LiteralPath $rf.FullName -Destination (Join-Path $destRef $rf.Name) -Force
            }
        }
    }

    # 6. Generate manifest.json (excluding manifest.json itself from payload file list)
    $allPayloadFiles = @(Get-ChildItem -LiteralPath $bundleDir -Recurse -File -Force)
    $fileManifest = [ordered]@{}
    foreach ($f in ($allPayloadFiles | Sort-Object FullName)) {
        $relPath = $f.FullName.Substring($bundleDir.Length).TrimStart('\', '/').Replace('\', '/')
        $hash = (Get-FileHash -LiteralPath $f.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
        $fileManifest[$relPath] = $hash
    }

    $manifestData = [ordered]@{
        bundle_name = "repository-engineering-skills-runtime"
        bundle_version = "1.0.0"
        source_commit = $sourceCommitSha
        working_tree_clean = (-not $isDirty)
        generated_at = (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ')
        file_count = $fileManifest.Count
        files = $fileManifest
    }

    $manifestJsonPath = Join-Path $bundleDir "manifest.json"
    $utf8NoBom = New-Object System.Text.UTF8Encoding($false)
    [System.IO.File]::WriteAllText($manifestJsonPath, ($manifestData | ConvertTo-Json -Depth 10), $utf8NoBom)

    # 7. Create ZIP archive
    if (Test-Path -LiteralPath $zipPath) {
        Remove-Item -LiteralPath $zipPath -Force
    }
    Compress-Archive -Path (Join-Path $bundleDir "*") -DestinationPath $zipPath -Force

    # 8. Unpack and self-verify archive integrity
    $verifyRoot = Join-Path ([System.IO.Path]::GetTempPath()) ("pkg-verify-" + [System.Guid]::NewGuid().ToString())
    New-Item -ItemType Directory -Path $verifyRoot -Force | Out-Null

    try {
        Expand-Archive -LiteralPath $zipPath -DestinationPath $verifyRoot -Force
        $unpackedManifestPath = Join-Path $verifyRoot "manifest.json"
        if (-not (Test-Path -LiteralPath $unpackedManifestPath)) {
            throw "Package verification failed: manifest.json missing in unpacked archive"
        }
        $unpackedManifest = Get-Content -LiteralPath $unpackedManifestPath -Raw | ConvertFrom-Json

        if ($unpackedManifest.source_commit -ne $sourceCommitSha) {
            throw "Package verification failed: source_commit mismatch (expected '$sourceCommitSha', got '$($unpackedManifest.source_commit)')"
        }

        if ($unpackedManifest.working_tree_clean -ne (-not $isDirty)) {
            throw "Package verification failed: working_tree_clean mismatch"
        }

        foreach ($entry in $unpackedManifest.files.PSObject.Properties) {
            $relPath = $entry.Name
            $expectedHash = $entry.Value
            $unpackedFile = Join-Path $verifyRoot ($relPath.Replace('/', '\'))
            if (-not (Test-Path -LiteralPath $unpackedFile)) {
                throw "Package verification failed: missing file '$relPath' in unpacked archive"
            }
            $actualHash = (Get-FileHash -LiteralPath $unpackedFile -Algorithm SHA256).Hash.ToLowerInvariant()
            if ($actualHash -ne $expectedHash) {
                throw "Package verification failed: checksum mismatch on '$relPath'"
            }
        }

        # Check for unmanaged extra files in unpacked archive
        $allUnpackedFiles = @(Get-ChildItem -LiteralPath $verifyRoot -Recurse -File -Force)
        foreach ($uf in $allUnpackedFiles) {
            $rel = $uf.FullName.Substring($verifyRoot.Length).TrimStart('\', '/').Replace('\', '/')
            if ($rel -ne "manifest.json" -and -not $unpackedManifest.files.PSObject.Properties[$rel]) {
                throw "Package verification failed: unexpected unmanaged file '$rel' in unpacked archive"
            }
        }
    }
    finally {
        Remove-Item -LiteralPath $verifyRoot -Recurse -Force -ErrorAction SilentlyContinue
    }

    $zipItem = Get-Item -LiteralPath $zipPath
    Write-Output "Successfully built verified runtime package: '$zipPath'"
    Write-Output "Source Commit: $sourceCommitSha"
    Write-Output "Clean Working Tree: $(-not $isDirty)"
    Write-Output "Payload Files: $($fileManifest.Count)"
    Write-Output "Archive Size: $($zipItem.Length) bytes"
    return $zipPath
}
finally {
    Remove-Item -LiteralPath $stagingRoot -Recurse -Force -ErrorAction SilentlyContinue
}
