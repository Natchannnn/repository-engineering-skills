# Installation & Maintenance Guide

This document explains how to install, update, and remove `repo-foundation` and `repo-native-refactor`.

---

## 1. What to Install

Only two directories contain runtime instructions for coding agents:
- `repo-foundation/` (specifically `SKILL.md` and `references/`)
- `repo-native-refactor/` (specifically `SKILL.md` and `references/`)

> [!CAUTION]
> Do **not** install or copy `evals-suite/` into your project. That directory contains evaluation harnesses and sealed historical test artifacts, which are not runtime instructions.

---

## 2. Installing into OpenAI Codex / Agent SDK

OpenAI Codex and the Agent SDK discover skills stored under `.agents/skills/<skill-name>/` at the root of a project.

### PowerShell (Windows)

```powershell
# Set your paths:
$skillsRepo = "C:\path\to\cloned\repository-engineering-skills"
$projectRoot = "C:\path\to\your\project"

$skillsDest = Join-Path $projectRoot ".agents\skills"

foreach ($skill in @("repo-foundation", "repo-native-refactor")) {
    $targetDir = Join-Path $skillsDest $skill
    if (Test-Path -LiteralPath $targetDir) {
        Write-Warning "Skill already exists at $targetDir. Remove or backup before reinstalling."
        continue
    }
    New-Item -ItemType Directory -Path $targetDir -Force | Out-Null
    Copy-Item -LiteralPath (Join-Path $skillsRepo "$skill\SKILL.md") -Destination $targetDir -Force
    Copy-Item -LiteralPath (Join-Path $skillsRepo "$skill\references") -Destination $targetDir -Recurse -Force
    Write-Host "Installed $skill to $targetDir"
}
```

### Bash (POSIX)

```bash
SKILLS_REPO="/path/to/cloned/repository-engineering-skills"
PROJECT_ROOT="/path/to/your/project"
SKILLS_DEST="$PROJECT_ROOT/.agents/skills"

for skill in repo-foundation repo-native-refactor; do
  target="$SKILLS_DEST/$skill"
  if [ -d "$target" ]; then
    echo "Warning: $target already exists."
    continue
  fi
  mkdir -p "$target"
  cp "$SKILLS_REPO/$skill/SKILL.md" "$target/"
  cp -r "$SKILLS_REPO/$skill/references" "$target/"
  echo "Installed $skill to $target"
done
```

---

## 3. Installing for Other Hosts (Claude Code, Cursor, Antigravity)

Different agent environments load skills from different locations:

- **Antigravity / Gemini CLI:** Global skills reside in `~/.gemini/antigravity/skills/<skill-name>/` or workspace `.gemini/skills/<skill-name>/`.
- **Generic Markdown Hosts:** Any host that reads instruction files from a prompt or system context can point to `SKILL.md` directly.

Ensure that the sibling `references/` directory is copied alongside `SKILL.md` so that contextual links remain valid.

---

## 4. Updating Skills

To update to a new version:
1. Pull the latest release of `repository-engineering-skills`.
2. Delete the old skill directories in your project's `.agents/skills/`.
3. Copy the updated `SKILL.md` and `references/` folders.
4. Verify by starting a new agent session and prompting:
   ```text
   What skills do you have available? Summarize repo-foundation.
   ```

---

## 5. Uninstallation

To remove the skills from a project, delete the corresponding subdirectories:

```powershell
Remove-Item -Recurse -Force "path\to\project\.agents\skills\repo-foundation"
Remove-Item -Recurse -Force "path\to\project\.agents\skills\repo-native-refactor"
```
