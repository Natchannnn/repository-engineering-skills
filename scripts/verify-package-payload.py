#!/usr/bin/env python3
"""
Verifies unpacked runtime package payload against Git commit object tree.

Ensures:
1. Every tracked payload file in the source commit is present in the unpacked package.
2. Every payload file in the unpacked package matches byte-for-byte with Git's object database (git cat-file blob).
3. SHA-256 hashes in manifest.json match both the disk files and the Git commit objects.
4. No unmanaged extra files exist in the package.
"""

import argparse
import hashlib
import json
import pathlib
import subprocess
import sys

ALLOWED_QUERY_PREFIXES = [
    "LICENSE",
    "repo-foundation/SKILL.md",
    "repo-foundation/LICENSE",
    "repo-foundation/agents/openai.yaml",
    "repo-foundation/references",
    "repo-native-refactor/SKILL.md",
    "repo-native-refactor/LICENSE",
    "repo-native-refactor/agents/openai.yaml",
    "repo-native-refactor/references",
]

def git_cmd(repo_path, args, binary=False):
    cmd = ["git", "-C", str(repo_path)] + args
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    if res.returncode != 0:
        err = res.stderr.decode("utf-8", errors="replace").strip()
        raise RuntimeError(f"Git command failed: {' '.join(cmd)}\n{err}")
    return res.stdout if binary else res.stdout.decode("utf-8", errors="replace")

def get_expected_tracked_files(repo_path, commit_sha):
    output = git_cmd(repo_path, ["ls-tree", "-r", "--name-only", commit_sha] + ALLOWED_QUERY_PREFIXES)
    lines = [line.strip().replace("\\", "/") for line in output.splitlines() if line.strip()]
    
    allowed = []
    for path in lines:
        if path == "LICENSE":
            allowed.append(path)
        elif path in ("repo-foundation/SKILL.md", "repo-foundation/LICENSE", "repo-foundation/agents/openai.yaml"):
            allowed.append(path)
        elif path.startswith("repo-foundation/references/") and path.endswith(".md"):
            allowed.append(path)
        elif path in ("repo-native-refactor/SKILL.md", "repo-native-refactor/LICENSE", "repo-native-refactor/agents/openai.yaml"):
            allowed.append(path)
        elif path.startswith("repo-native-refactor/references/") and path.endswith(".md"):
            allowed.append(path)
    return sorted(allowed)

def verify_package(repo_path, commit_sha, unpacked_dir):
    repo_path = pathlib.Path(repo_path).resolve()
    unpacked_dir = pathlib.Path(unpacked_dir).resolve()
    
    manifest_file = unpacked_dir / "manifest.json"
    if not manifest_file.is_file():
        raise ValueError(f"manifest.json missing at: {manifest_file}")
    
    manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
    if manifest.get("source_commit") != commit_sha:
        raise ValueError(f"source_commit mismatch: expected {commit_sha}, got {manifest.get('source_commit')}")
    
    manifest_files = manifest.get("files", {})
    expected_tracked = get_expected_tracked_files(repo_path, commit_sha)
    
    expected_pkg_map = {}
    for gp in expected_tracked:
        if gp == "LICENSE":
            rel_pkg = "LICENSE"
        else:
            rel_pkg = f"skills/{gp}"
        expected_pkg_map[rel_pkg] = gp
    
    # 1. Check inventory exact match
    manifest_pkg_paths = sorted(manifest_files.keys())
    expected_pkg_paths = sorted(expected_pkg_map.keys())
    
    if manifest_pkg_paths != expected_pkg_paths:
        missing = set(expected_pkg_paths) - set(manifest_pkg_paths)
        extra = set(manifest_pkg_paths) - set(expected_pkg_paths)
        raise ValueError(f"Inventory mismatch between commit and manifest! Missing: {missing}, Extra: {extra}")
    
    # 2. Check each file byte-for-byte against git object database
    for rel_pkg, git_path in expected_pkg_map.items():
        disk_file = unpacked_dir / pathlib.Path(rel_pkg)
        if not disk_file.is_file():
            raise FileNotFoundError(f"Payload file missing on disk: {disk_file}")
        
        # Read git blob raw bytes
        git_blob = git_cmd(repo_path, ["cat-file", "blob", f"{commit_sha}:{git_path}"], binary=True)
        disk_bytes = disk_file.read_bytes()
        
        # Exact byte-for-byte assertion
        if disk_bytes != git_blob:
            raise ValueError(
                f"BYTE MISMATCH on '{rel_pkg}': disk content does NOT match Git commit object '{commit_sha}:{git_path}'! "
                f"(disk size: {len(disk_bytes)} bytes, git blob size: {len(git_blob)} bytes)"
            )
        
        # Check SHA-256 against manifest
        disk_sha = hashlib.sha256(disk_bytes).hexdigest().lower()
        manifest_sha = manifest_files[rel_pkg].lower()
        if disk_sha != manifest_sha:
            raise ValueError(f"Hash mismatch on '{rel_pkg}': disk {disk_sha} != manifest {manifest_sha}")
    
    # 3. Check for any unexpected files in unpacked directory (other than root manifest.json)
    disk_all = [
        p.relative_to(unpacked_dir).as_posix()
        for p in unpacked_dir.rglob("*")
        if p.is_file() and p.relative_to(unpacked_dir).as_posix() != "manifest.json"
    ]
    disk_all_sorted = sorted(disk_all)
    if disk_all_sorted != expected_pkg_paths:
        extra_on_disk = set(disk_all_sorted) - set(expected_pkg_paths)
        raise ValueError(f"Unexpected extra files on disk in unpacked package: {extra_on_disk}")
    
    return len(expected_pkg_paths)

def main():
    parser = argparse.ArgumentParser(description="Verify unpacked package against Git commit tree")
    parser.add_argument("--repo", required=True, help="Path to git repository")
    parser.add_argument("--commit", required=True, help="Commit SHA to verify against")
    parser.add_argument("--unpacked", required=True, help="Path to unpacked package directory")
    args = parser.parse_args()
    
    try:
        count = verify_package(args.repo, args.commit, args.unpacked)
        print(f"PASS: Verified {count}/{count} payload files byte-for-byte against Git commit {args.commit}")
        sys.exit(0)
    except Exception as e:
        print(f"FAIL: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
