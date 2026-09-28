# Installation & Maintenance

Use the [Skills CLI](https://github.com/vercel-labs/skills) to install directly from GitHub. These skills do not need their own npm package.

## Requirements

- Git available on PATH.
- Node.js 22.20.0 or newer with npm/npx for Skills CLI 1.7.0.
- A coding agent host that supports the selected skill location.

Python is only needed to run the included evaluation harness and repo tooling (`pip install -r requirements-test.txt` for `jsonschema`, plus `python scripts/sync-shared.py --check` and `python scripts/classify-risk.py`), not to load the Markdown instructions. Examples pin the installer to 1.7.0; this does not pin the repository content to a release.

## Preview and install

Open a terminal in your target project. To see the two available skills without installing:

```sh
npx skills@1.7.0 add Natchannnn/repository-engineering-skills --list
```

Install both for Codex in that project:

```sh
npx skills@1.7.0 add Natchannnn/repository-engineering-skills --skill repo-foundation repo-native-refactor --agent codex --copy -y
```

`--copy` selects copying instead of symlinking. `-y` accepts the installation, including replacement of existing selected skills. The command writes `.agents/skills/<skill-name>/` and `skills-lock.json`; it does not install globally. Back up any personal edits inside those skill directories before reinstalling.

Install only Refactor:

```sh
npx skills@1.7.0 add Natchannnn/repository-engineering-skills --skill repo-native-refactor --agent codex --copy -y
```

For Foundation alone, replace the skill name with `repo-foundation`.

To choose a host and installation options interactively:

```sh
npx skills@1.7.0 add Natchannnn/repository-engineering-skills --skill repo-foundation repo-native-refactor
```

The tested recipe is the explicit Codex copy command. The CLI offers other agents, but successful file placement does not establish equivalent skill behavior on every host. Global installation is optional via the CLI's `--global` flag and has not been tested here.

## What gets installed

The CLI copies each selected skill directory. With the current source layout, this includes `SKILL.md`, `references/`, each skill's `evals/` harness directory, the per-skill `LICENSE`, and each skill's `agents/openai.yaml` metadata.

The repository-level `evals-suite/` archive is not installed. The included harness files are not executed by the install command. This is currently a full skill-directory installation, not a runtime-only bundle.

References must stay beside `SKILL.md`. Do not move only the entry file after installation. The CLI may download the whole source repository to discover skills even though only selected directories are installed.

## Try the skills in a separate project

Create an empty folder, open it in your host and run the install command there. This keeps the trial separate from a working application.

First check the installed inventory:

```sh
npx skills@1.7.0 list --agent codex
```

Expect `repo-foundation` and `repo-native-refactor` with paths inside the trial project. Start a new Codex session in that folder and use:

```text
Use $repo-foundation to create a small Python CLI that reads a CSV with category and amount columns and prints totals by category. Include a sample CSV, a meaningful test and instructions for running it. Keep the implementation small. Do not commit or publish.
```

After implementation, try a review that does not permit edits:

```text
Use $repo-native-refactor to review the implementation you just created. Report only findings supported by the code and requirements. Do not edit files. If no actionable issue is established, say so.
```

Check that the host actually read the installed skill, the CLI produces the expected totals, the checks exercised the required behavior, and the review did not modify files. Confirm the path if another copy of the skill exists at user or plugin scope. Inventory listing alone is not a behavioral test.

These are suggested trial tasks, not reported benchmark results. The installation checks performed for this change are recorded in [npx-install-verification.md](npx-install-verification.md).

## Reinstall or update

From the same project, rerun the explicit `add` command to replace the selected installed copies with content from the repository's current default branch. In the recorded test, a stale reference file inside a selected skill was removed and an unrelated project file was preserved.

This replaces local edits inside the selected skill directories. It is not a merge, and no rollback or interruption-durability guarantee is claimed for the third-party installer. Keep personal customizations separately or back them up first.

`skills-lock.json` records source information; the `skills@1.7.0` version in the command identifies the installer, not a version of Foundation or Refactor. Record the actual source revision when comparing behavior.

## Remove from the project

From the project where the skills were installed:

```sh
npx skills@1.7.0 remove --skill repo-foundation repo-native-refactor -y
```

This removes the selected skills from project agent installations without a per-agent filter. Omit `-y` if you want the CLI's confirmation flow. Removal does not undo source-code changes previously made by an agent using a skill.

For CLI 1.7.0, the tested `remove ... --agent codex -y` variant reported success but left the shared `.agents/skills/` copies installed. The command above, without that filter, removed them in the test. Run `npx skills@1.7.0 list --agent codex` afterwards and verify that the selected project skills are absent. If you need to keep the same skills available to another project agent, review the CLI's selection behavior before removing them.

## Test local changes before publishing

From a separate trial project, replace the GitHub source with your checkout path:

```powershell
npx skills@1.7.0 add 'C:\path\to\repository-engineering-skills' --skill repo-foundation repo-native-refactor --agent codex --copy -y
```

Use an absolute path. Do not install into the source checkout just to test packaging. Local-source installation tests your uncommitted files; GitHub-source installation reads the published repository.

## Install or update from local clone (PowerShell)

If installing from a local clone of this repository without Node.js or `npx`:

### Fresh installation
```powershell
pwsh -NoProfile -File ./scripts/install-skills.ps1 -TargetProject "C:\path\to\my-project"
```
The script performs pre-flight validation on both source skills (`SKILL.md`, `references/`, and metadata). If either skill already exists at the destination `.agents/skills/`, the script aborts before making any modifications to prevent accidental overwrites.

### Safe update with automatic backup
```powershell
pwsh -NoProfile -File ./scripts/install-skills.ps1 -TargetProject "C:\path\to\my-project" -Update
```
When `-Update` is specified:
1. Validates the source repository (`SKILL.md`, `LICENSE`, `references/`, and metadata for both skills).
2. Stages the new version in an isolated temporary directory and computes a SHA-256 directory manifest.
3. Automatically backs up existing skill copies to `<project>/.agents/skills-backup-<timestamp>/`.
4. Replaces the destination skill directories cleanly, eliminating stale ghost files from older versions while leaving unrelated skills in `.agents/skills/` untouched.
5. Performs bi-directional manifest and SHA-256 verification on all deployed files. If any error occurs during copy or verification, the installer automatically rolls back and restores the previous installation from the backup.

## Standalone Runtime ZIP Distribution

For offline environments, air-gapped systems, or teams that do not use Node.js or `npx`, pre-built runtime packages are generated using `scripts/package-runtime.ps1` (or downloaded as `repository-engineering-skills-runtime.zip` from repository releases).

### Package structure

The runtime archive excludes evaluation harnesses, tests, and authoring tools, containing strictly the 22 payload files required for agent execution:

```text
repository-engineering-skills-runtime/
├── LICENSE
├── manifest.json
└── skills/
    ├── repo-foundation/
    │   ├── LICENSE
    │   ├── SKILL.md
    │   ├── agents/
    │   │   └── openai.yaml
    │   └── references/
    │       ├── bootstrap.md
    │       ├── continuity.md
    │       ├── evolution.md
    │       ├── migration-examples.md
    │       ├── shared-contracts.md
    │       └── verification.md
    └── repo-native-refactor/
        ├── LICENSE
        ├── SKILL.md
        ├── agents/
        │   └── openai.yaml
        └── references/
            ├── deterministic-tooling.md
            ├── error-reliability.md
            ├── finding-taxonomy.md
            ├── refactor-examples.md
            ├── repository-prose.md
            ├── repository-rehabilitation.md
            ├── semantic-risk.md
            ├── shared-contracts.md
            └── testing-integrity.md
```

### Integrity verification

Before deploying, verify all payload files against `manifest.json`:

#### PowerShell
```powershell
$manifest = Get-Content .\manifest.json -Raw | ConvertFrom-Json
$failed = 0
foreach ($entry in $manifest.files.PSObject.Properties) {
    $path = $entry.Name
    $expected = $entry.Value
    if (-not (Test-Path -LiteralPath $path)) {
        Write-Error "Missing payload file: $path"
        $failed++
        continue
    }
    $actual = (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($actual -ne $expected) {
        Write-Error "SHA-256 mismatch on $path"
        $failed++
    }
}
if ($failed -eq 0) {
    Write-Host "Verification PASSED: All $($manifest.file_count) payload files match SHA-256 manifest."
} else {
    throw "Verification FAILED: $failed file(s) mismatched or missing."
}
```

#### Python
```python
import json, hashlib, pathlib, sys

manifest = json.loads(pathlib.Path("manifest.json").read_text(encoding="utf-8"))
failed = 0
for rel_path, expected_hash in manifest["files"].items():
    file_path = pathlib.Path(rel_path)
    if not file_path.is_file():
        print(f"Missing: {rel_path}", file=sys.stderr)
        failed += 1
        continue
    actual_hash = hashlib.sha256(file_path.read_bytes()).hexdigest()
    if actual_hash != expected_hash:
        print(f"Mismatch: {rel_path} (expected {expected_hash}, got {actual_hash})", file=sys.stderr)
        failed += 1

if failed == 0:
    print(f"Verification PASSED: All {manifest['file_count']} files match SHA-256 manifest.")
else:
    sys.exit(f"Verification FAILED: {failed} error(s) detected.")
```

### Manual deployment into a target project

Because the standalone ZIP does not include the repository's PowerShell installer script, manual deployment is performed directly:

1. Extract `repository-engineering-skills-runtime.zip`.
2. In your target project root, create `.agents/skills/` (or your host agent's configured skills path, e.g. `.claude/skills/`).
3. Copy the two skill folders:
   - Copy `skills/repo-foundation/` to `<target-project>/.agents/skills/repo-foundation/`
   - Copy `skills/repo-native-refactor/` to `<target-project>/.agents/skills/repo-native-refactor/`

Alternatively, if you have cloned the source repository, you can pass the unpacked `skills/` path to the installer:
```powershell
pwsh -NoProfile -File ./scripts/install-skills.ps1 -SkillsRepo "C:\path\to\unpacked\skills" -TargetProject "C:\path\to\my-project"
```

## Troubleshooting

- **`npx` is not found:** install a supported Node.js version, then reopen the terminal.
- **PowerShell blocks the npm wrapper:** use `npx.cmd` in place of `npx`; the arguments stay the same. No execution-policy change is needed for that workaround.
- **Skill is not visible:** inspect the installation path, current project, host support and duplicate copies; then start a new session.
- **GitHub installation still shows old content:** confirm the intended changes have been committed and pushed to the source branch.
- **Installation succeeds but behavior is wrong:** report the source revision, host/model, prompt and observed result. Installation success does not establish task success.
