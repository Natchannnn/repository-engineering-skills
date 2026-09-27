#!/usr/bin/env python3
"""
Setup Finalizer and Setup Metadata Validator for Demo Fixtures.

Defines the explicit 3-stage lifecycle for demo execution:
1. Bootstrap fixture: generates git fixture repository, INITIAL_HEAD, and baseline manifest.
2. Skill installation & setup finalization: operator installs skills (via CLI or copy),
   then runs this finalizer to verify source is pristine and snapshot lockfile state.
3. Agent task execution & independent verification: agent executes task, and author verifier
   validates both task output and strict preservation of setup baseline and scope.
"""

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
import pathlib
import subprocess
import sys

def run_git(cwd: pathlib.Path, args: list[str]) -> str:
    cmd = ["git", "-C", str(cwd)] + args
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if res.returncode != 0:
        raise RuntimeError(f"Git command failed: {' '.join(cmd)}\n{res.stderr.strip()}")
    return res.stdout.strip()

def get_git_paths(cwd: pathlib.Path, args: list[str]) -> list[str]:
    cmd = ["git", "-C", str(cwd)] + args
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if res.returncode != 0:
        err = res.stderr.decode("utf-8", errors="replace").strip()
        raise RuntimeError(f"Git command failed: {' '.join(cmd)}\n{err}")
    return [p.decode("utf-8", errors="replace") for p in res.stdout.split(b"\0") if len(p) > 0]

def validate_pristine_source(fixture_dir: pathlib.Path) -> None:
    """
    Verifies that the fixture repository source code is completely pristine
    before setup finalization. No agent edits, no dirty working tree,
    no unauthorized extra files are permitted.
    """
    fixture_dir = fixture_dir.resolve()
    if not fixture_dir.is_dir():
        raise FileNotFoundError(f"Fixture directory does not exist: {fixture_dir}")

    git_dir = fixture_dir / ".git"
    if not git_dir.exists():
        raise AssertionError(f"Target directory is not a Git repository: {fixture_dir}")

    meta_dir = fixture_dir.parent
    head_file = meta_dir / f"{fixture_dir.name}-INITIAL_HEAD"
    if not head_file.is_file():
        raise FileNotFoundError(f"Missing INITIAL_HEAD reference file at: {head_file}. Ensure fixture was bootstrapped.")

    expected_head = head_file.read_text(encoding="utf-8").strip()
    current_head = run_git(fixture_dir, ["rev-parse", "HEAD"])
    if current_head != expected_head:
        raise AssertionError(f"Pristine source check failed: HEAD advanced from {expected_head} to {current_head}")

    res_diff = subprocess.run(["git", "-C", str(fixture_dir), "diff", "--quiet", "HEAD"], check=False)
    if res_diff.returncode != 0:
        raise AssertionError("Pristine source check failed: uncommitted modifications detected in working tree.")

    res_cached = subprocess.run(["git", "-C", str(fixture_dir), "diff", "--cached", "--quiet"], check=False)
    if res_cached.returncode != 0:
        raise AssertionError("Pristine source check failed: staged changes detected in index.")

    # Check Demo 1 external baseline manifest if present
    manifest_file = meta_dir / f"{fixture_dir.name}-baseline-manifest.json"
    if manifest_file.is_file():
        baseline = json.loads(manifest_file.read_text(encoding="utf-8"))
        for rel_path, expected_hash in baseline.items():
            p = fixture_dir / rel_path
            if not p.is_file():
                raise AssertionError(f"Pristine source check failed: protected baseline file missing: '{rel_path}'")
            actual_hash = hashlib.sha256(p.read_bytes()).hexdigest()
            if actual_hash != expected_hash:
                raise AssertionError(f"Pristine source check failed: protected baseline file modified: '{rel_path}'")

    # Check untracked files: only tooling (.agents/) and exact root skills-lock.json allowed
    untracked = get_git_paths(fixture_dir, ["ls-files", "-z", "--others", "--exclude-standard"])
    for u in untracked:
        p = u.replace("\\", "/")
        parts = p.split("/")
        if any(part in {".agents", "__pycache__", ".pytest_cache"} for part in parts):
            continue
        if p == "skills-lock.json":
            continue
        raise AssertionError(
            f"Pristine source check failed: unauthorized untracked file detected before setup finalization: '{u}'. "
            "Only installed skills tooling (.agents/) and exact root 'skills-lock.json' are permitted."
        )

    # Validate lockfile JSON structure if present
    lockfile = fixture_dir / "skills-lock.json"
    if lockfile.is_file():
        try:
            json.loads(lockfile.read_text(encoding="utf-8"))
        except Exception as e:
            raise AssertionError(f"Pristine source check failed: 'skills-lock.json' is not valid JSON: {e}")

def finalize_setup(fixture_dir: pathlib.Path) -> pathlib.Path:
    """
    Finalizes setup for a demo fixture repository:
    1. Validates that source tree is completely pristine and matches INITIAL_HEAD.
    2. Snapshots the presence and SHA-256 hash of skills-lock.json.
    3. Persists setup metadata to <fixture-name>-setup-metadata.json in fixture parent directory.
    4. Refuses to overwrite existing setup metadata to preserve audit trail.
    """
    fixture_dir = fixture_dir.resolve()
    meta_dir = fixture_dir.parent
    metadata_path = meta_dir / f"{fixture_dir.name}-setup-metadata.json"

    if metadata_path.exists():
        raise FileExistsError(
            f"Setup metadata already exists at: {metadata_path}\n"
            "Setup cannot be re-finalized on an existing session. "
            "To conduct a new trial, bootstrap a fresh fixture directory."
        )

    validate_pristine_source(fixture_dir)

    head_file = meta_dir / f"{fixture_dir.name}-INITIAL_HEAD"
    initial_head = head_file.read_text(encoding="utf-8").strip()

    lockfile = fixture_dir / "skills-lock.json"
    if lockfile.is_file():
        lockfile_status = "present"
        lockfile_sha256 = hashlib.sha256(lockfile.read_bytes()).hexdigest()
    else:
        lockfile_status = "absent"
        lockfile_sha256 = None

    metadata = {
        "schema_version": "1.0",
        "initial_head": initial_head,
        "lockfile_status": lockfile_status,
        "lockfile_sha256": lockfile_sha256,
        "setup_finalized_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }

    try:
        with metadata_path.open("x", encoding="utf-8") as stream:
            stream.write(json.dumps(metadata, indent=2) + "\n")
    except FileExistsError:
        raise FileExistsError(
            f"Setup metadata already exists at: {metadata_path}\n"
            "Setup cannot be re-finalized on an existing session. "
            "To conduct a new trial, bootstrap a fresh fixture directory."
        )
    return metadata_path

def verify_setup_metadata(fixture_dir: pathlib.Path) -> dict:
    """
    Validates that setup metadata exists and enforces strict lockfile integrity:
    - If skills-lock.json was present at setup, it must exist and match recorded SHA-256 byte hash.
    - If skills-lock.json was absent at setup, it must NOT exist post-setup.
    - Setup metadata initial_head must match INITIAL_HEAD.
    """
    fixture_dir = fixture_dir.resolve()
    meta_dir = fixture_dir.parent
    metadata_path = meta_dir / f"{fixture_dir.name}-setup-metadata.json"

    if not metadata_path.is_file():
        raise FileNotFoundError(
            f"Missing setup metadata file: {metadata_path}\n"
            "Setup finalization is mandatory before running verification.\n"
            f"Please run 'python examples/finalize_setup.py \"{fixture_dir}\"' after skill installation and before agent execution."
        )

    try:
        meta = json.loads(metadata_path.read_text(encoding="utf-8"))
    except Exception as e:
        raise AssertionError(f"Corrupted setup metadata file at '{metadata_path}': {e}")

    for k in ("schema_version", "initial_head", "lockfile_status"):
        if k not in meta:
            raise AssertionError(f"Malformed setup metadata: missing required field '{k}' in {metadata_path}")

    head_file = meta_dir / f"{fixture_dir.name}-INITIAL_HEAD"
    if head_file.is_file():
        expected_head = head_file.read_text(encoding="utf-8").strip()
        if meta.get("initial_head") != expected_head:
            raise AssertionError(
                f"Setup metadata initial_head '{meta.get('initial_head')}' does not match INITIAL_HEAD file '{expected_head}'"
            )

    lockfile = fixture_dir / "skills-lock.json"
    status = meta.get("lockfile_status")
    expected_sha = meta.get("lockfile_sha256")

    if status == "present":
        if not lockfile.is_file():
            raise AssertionError(
                f"Lockfile integrity violation: 'skills-lock.json' was present at setup finalization "
                f"({expected_sha[:12] if expected_sha else ''}...), but is now missing."
            )
        curr_sha = hashlib.sha256(lockfile.read_bytes()).hexdigest()
        if curr_sha != expected_sha:
            raise AssertionError(
                f"Lockfile integrity violation: 'skills-lock.json' was modified post-setup.\n"
                f"  Setup SHA-256:   {expected_sha}\n"
                f"  Current SHA-256: {curr_sha}"
            )
    elif status == "absent":
        if lockfile.is_file():
            raise AssertionError(
                "Lockfile state violation: 'skills-lock.json' was absent at setup finalization, "
                "but appeared during or after agent task execution."
            )
    else:
        raise ValueError(f"Invalid lockfile_status in setup metadata: '{status}'")

    return meta

def main():
    parser = argparse.ArgumentParser(description="Finalize setup for demo fixture before agent execution")
    parser.add_argument("fixture_dir", help="Path to bootstrapped fixture repository")
    args = parser.parse_args()

    fixture_dir = pathlib.Path(args.fixture_dir).resolve()
    print("=== Finalizing Demo Setup ===")
    print(f"Fixture: {fixture_dir}")
    try:
        metadata_path = finalize_setup(fixture_dir)
        meta = json.loads(metadata_path.read_text(encoding="utf-8"))
        print("    [PASS] Setup successfully finalized.")
        print(f"           INITIAL_HEAD:    {meta['initial_head']}")
        print(f"           Lockfile status: {meta['lockfile_status']}")
        if meta["lockfile_status"] == "present":
            print(f"           Lockfile SHA256: {meta['lockfile_sha256']}")
        print(f"           Metadata file:   {metadata_path}")
    except Exception as e:
        print(f"    [FAIL] Setup finalization failed: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
