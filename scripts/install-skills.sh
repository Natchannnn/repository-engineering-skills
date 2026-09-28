#!/usr/bin/env bash
# Minimal POSIX installer mirror of scripts/install-skills.ps1
# Supports: fresh install + --update with backup + rollback on failure.
# Usage:
#   bash scripts/install-skills.sh --target /path/to/project [--update] [--skills-repo /path/to/skills]
set -euo pipefail

TARGET=""
UPDATE=0
SKILLS_REPO="$(cd "$(dirname "$0")/.." && pwd)"

while [ $# -gt 0 ]; do
  case "$1" in
    --target) TARGET="$2"; shift 2;;
    --update) UPDATE=1; shift 1;;
    --skills-repo) SKILLS_REPO="$2"; shift 2;;
    *) echo "Unknown arg: $1" >&2; exit 2;;
  esac
done

[ -z "$TARGET" ] && { echo "--target is required" >&2; exit 2; }

for s in repo-foundation repo-native-refactor; do
  [ -f "$SKILLS_REPO/$s/SKILL.md" ] || { echo "Missing $s/SKILL.md in $SKILLS_REPO" >&2; exit 1; }
  [ -d "$SKILLS_REPO/$s/references" ] || { echo "Missing $s/references in $SKILLS_REPO" >&2; exit 1; }
done

DEST="$TARGET/.agents/skills"
mkdir -p "$DEST"

if [ "$UPDATE" -eq 0 ]; then
  for s in repo-foundation repo-native-refactor; do
    if [ -e "$DEST/$s" ]; then echo "Exists: $DEST/$s (rerun with --update)" >&2; exit 1; fi
  done
  cp -R "$SKILLS_REPO/repo-foundation" "$DEST/repo-foundation"
  cp -R "$SKILLS_REPO/repo-native-refactor" "$DEST/repo-native-refactor"
  echo "Installed to $DEST"
  exit 0
fi

TS=$(date -u +%Y%m%dT%H%M%SZ)
BACKUP="$TARGET/.agents/skills-backup-$TS"
mkdir -p "$BACKUP"
# backup existing
for s in repo-foundation repo-native-refactor; do
  if [ -e "$DEST/$s" ]; then cp -R "$DEST/$s" "$BACKUP/$s"; fi
done

rollback() {
  echo "Rolling back from $BACKUP" >&2
  rm -rf "$DEST/repo-foundation" "$DEST/repo-native-refactor"
  for s in repo-foundation repo-native-refactor; do
    if [ -e "$BACKUP/$s" ]; then cp -R "$BACKUP/$s" "$DEST/$s"; fi
  done
  exit 1
}
trap rollback ERR

rm -rf "$DEST/repo-foundation" "$DEST/repo-native-refactor"
cp -R "$SKILLS_REPO/repo-foundation" "$DEST/repo-foundation"
cp -R "$SKILLS_REPO/repo-native-refactor" "$DEST/repo-native-refactor"

# verify
for s in repo-foundation repo-native-refactor; do
  [ -f "$DEST/$s/SKILL.md" ] || { echo "Verify failed: $s/SKILL.md" >&2; exit 1; }
done
trap - ERR
echo "Updated (backup at $BACKUP)"
