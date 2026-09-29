# Skills CLI installation checks

Date: 2026-09-26. These are installation checks, not agent-performance benchmarks.

## Environment and sources

- Windows; Node.js `24.16.0`.
- npm registry reported Skills CLI `1.7.0`, with Node engine requirement `>=22.20.0`.
- CLI invoked as `npx.cmd --yes skills@1.7.0 ...` from temporary project directories. The first `--yes` accepts npm's package download; the CLI's final `-y` accepts its installation/removal prompt.
- Public source: `Natchannnn/repository-engineering-skills`, default branch at `200286cbb7cb67587b9b4131f9cd001203e51745` when checked.
- Local source: that checkout plus the per-skill LICENSE files added with this documentation change. The local additions were tested separately and are not described as already published.
- Project scope only; no global skill installation. Telemetry was disabled for these checks.

## Observed results

| Check | Result |
|---|---|
| GitHub source with `add ... --list` | Exactly two skills discovered: Foundation and Refactor |
| GitHub source with both names, `--agent codex --copy -y` | Exit 0; both directories created under the temporary project's `.agents/skills/` |
| Skill entry files and references | All installed `SKILL.md` and reference files matched the local source bytes |
| Inventory with `list --agent codex` | Both project skills and their source were listed |
| Reinstall over an obsolete reference sentinel | Sentinel inside the selected skill was removed; unrelated project file retained |
| GitHub source with only `--skill repo-native-refactor` | Refactor installed; Foundation absent from that fresh trial directory |
| Local checkout containing per-skill licenses | Both installed LICENSE files matched the root LICENSE bytes |
| Removal with `--agent codex` filter | **Failed the intended effect:** exit 0 and success message, but both SKILL.md files and inventory entries remained |
| Removal without an agent filter | Both selected SKILL.md files absent; inventory reported no project skills; unrelated project file retained |

The documented removal recipe uses the variant without an agent filter. The failed filtered-removal observation is retained here rather than treating exit 0 as proof of success.

## Claude marketplace end-to-end (Batch B follow-up)

Date: 2026-09-28. `claude` CLI on Windows, repo at Batch E commit. All three manifests
pass `claude plugin validate`; this time the full loop ran for real:

- `claude plugin marketplace add Natchannnn/repository-engineering-skills` → exit 0.
- `claude plugin install repo-foundation@repository-engineering-skills` → exit 0, listed.
- `claude plugin install repo-native-refactor@repository-engineering-skills` → exit 0, listed.
- Cleanup: both plugins uninstalled, marketplace removed, `plugin list` shows no trace.
  Note: `~/.claude/plugins/cache/repository-engineering-skills/` lingered on disk after
  removal and was deleted by hand — dormant cache, not a registration.

## Global install (same date, Skills CLI 1.7.0)

- `add <local> --skill repo-foundation -g -a codex --copy -y` → exit 0.
- `remove --global repo-foundation -y` → exit 0, no leftovers found.
- Note: `list -g` hung in this environment (no output within 3 minutes); install and
  removal themselves returned cleanly, so this looks like a CLI display quirk, not a
  repo issue.

## Payload observed from the published source

Before the per-skill license additions:

| Skill | Installed files | Included harness files under `evals/` | Total file bytes |
|---|---:|---:|---:|
| repo-foundation | 34 | 28 | 267,367 |
| repo-native-refactor | 22 | 14 | 192,685 |

The repository-level `evals-suite/` directory was absent from the installed project. Foundation's `agents/openai.yaml` was present; refactor's adapter was added after this check (v0.2.0) and is covered by `scripts/test-package.ps1`. The local-source test added one LICENSE per skill. These counts describe these revisions, not a permanent packaging contract.

The current CLI installs the selected directories including their harness files. It does not execute those harnesses during installation. A smaller runtime-only package remains a separate packaging improvement; these instructions do not claim one exists.

## Boundaries of this check

No model task was launched to claim automatic routing, behavioral improvement, or compatibility across hosts. The examples in the installation guide are tasks users can run after installation. Interactive host selection, global installation, other operating systems, interrupted installs and rollback were not verified here.

Reinstallation replaced the tested skill directories; it is not a promise of transactional recovery on I/O failure. Version `1.7.0` identifies the installer, while the source revision identifies the skill content.

See [installation instructions](installation.md) for the commands and [the upstream CLI](https://github.com/vercel-labs/skills) for its supported options.

## Multi-agent matrix (local source, Batch B)

Date: 2026-09-28. Windows, Node.js `24.16.0`, Skills CLI `1.7.0`, local source at `a905103`.
Each check ran in a fresh temp project: `--list` on the local checkout, then
`add ... --skill repo-foundation repo-native-refactor --agent <name> --copy -y`,
then `list --agent <name>`. Telemetry disabled.

| Agent | `--list` sees 2 skills | `add` exit | Files at expected path | `list` exit |
|---|:---:|:---:|:---:|:---:|
| `claude-code` (`.claude/skills/`) | yes | 0 | both `SKILL.md` present | 0 |
| `cursor` (`.agents/skills/`) | yes | 0 | both `SKILL.md` present | 0 |
| `opencode` (`.agents/skills/`) | yes | 0 | both `SKILL.md` present | 0 |
| `gemini-cli` (`.agents/skills/`) | yes | 0 | both `SKILL.md` present | 0 |

Byte spot-check on `claude-code`: 8 installed files (both `SKILL.md`, both
`shared-contracts.md`, `migration-examples.md`, `refactor-examples.md`, both
`agents/openai.yaml`) match the source bytes exactly via SHA-256.

What this does not claim: no model task was launched on these agents, so routing
quality and behavior parity across hosts remain unverified. Installation success
is file placement, not a behavioral test.
