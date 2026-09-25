"""Greenfield byte-preserving snapshot and diff engine for evals-foundation (Phase 2A)."""

from __future__ import annotations

import difflib
import hashlib
import json
import os
import secrets
import shutil
from pathlib import Path, PurePosixPath
from typing import Any

try:
    from .core import (
        HarnessError,
        check_no_links,
        load_json,
        require_sha256,
        safe_path,
        sha256_bytes,
        sha256_file,
        tree_hash,
        utc_now,
        validate_relative_posix_path,
        verify_bundle_dir,
        write_json,
    )
except ImportError:
    from core import (
        HarnessError,
        check_no_links,
        load_json,
        require_sha256,
        safe_path,
        sha256_bytes,
        sha256_file,
        tree_hash,
        utc_now,
        validate_relative_posix_path,
        verify_bundle_dir,
        write_json,
    )

SNAPSHOT_SCHEMA = "repo-foundation-harness/snapshot-v1"
DIFF_SCHEMA = "repo-foundation-harness/diff-v1"


def pattern_match(path: PurePosixPath, pattern: str) -> bool:
    """Match a POSIX relative path against glob patterns including **, **/*, and prefixes."""
    if pattern in ("*", "**", "**/*"):
        return True
    if path.match(pattern):
        return True
    if pattern.startswith("**/") and path.match(pattern[3:]):
        return True
    if pattern.endswith("/**"):
        base_pat = pattern[:-3]
        if path.match(base_pat):
            return True
        for parent in path.parents:
            if parent.match(base_pat):
                return True
    return False


def matches_policy(rel_posix: str, policy: dict[str, list[str]] | None) -> bool:
    """Determine whether a relative POSIX path is included under the snapshot policy."""
    if policy is None:
        return True
    pure = PurePosixPath(rel_posix)
    includes = policy.get("include", ["**/*"])
    excludes = policy.get("exclude", [])

    included = False
    if not includes:
        included = True
    else:
        for pat in includes:
            if pattern_match(pure, pat):
                included = True
                break
    if not included:
        return False

    for pat in excludes:
        if pattern_match(pure, pat):
            return False
    return True


def scan_directory(
    root: Path,
    policy: dict[str, list[str]] | None = None,
) -> list[tuple[str, Path, bool]]:
    """Scan directory recursively, rejecting symlinks/junctions and applying frozen policy."""
    check_no_links(root)
    if not root.is_dir():
        raise HarnessError(f"Expected an ordinary directory: {root}")

    results: list[tuple[str, Path, bool]] = []
    for path in sorted(root.rglob("*")):
        check_no_links(path)
        if path.is_dir():
            continue
        if not path.is_file():
            raise HarnessError(f"Unsupported filesystem entry type: {path}")

        rel_posix = path.relative_to(root).as_posix()
        validate_relative_posix_path(rel_posix)

        if matches_policy(rel_posix, policy):
            safe_path(root, rel_posix)
            is_exec = (os.name != "nt" and bool(path.stat().st_mode & 0o111))
            results.append((rel_posix, path, is_exec))

    return results


def compute_tree_hash_from_entries(entries: list[tuple[str, Path, bool]]) -> str:
    """Compute tree hash deterministically from scanned entries matching core.tree_hash."""
    digest = hashlib.sha256()
    for rel_posix, path, is_exec in entries:
        digest.update(rel_posix.encode("utf-8"))
        digest.update(b"\0")
        digest.update(b"x" if is_exec else b"-")
        digest.update(bytes.fromhex(sha256_file(path)))
    return digest.hexdigest().lower()


def compute_directory_snapshot_hash(root: Path, policy: dict[str, list[str]] | None = None) -> str:
    """Compute tree hash of directory filtered by snapshot policy."""
    entries = scan_directory(root, policy)
    return compute_tree_hash_from_entries(entries)


def create_snapshot(
    source_dir: Path,
    run_root: Path,
    policy: dict[str, list[str]] | None = None,
) -> tuple[str, Path]:
    """Create sealed, byte-preserving snapshot of source_dir in run_root/control/snapshots/<hash>.

    Never overwrites an existing snapshot. If snapshot already exists, verifies its integrity.
    Returns (snapshot_hash, snapshot_dir).
    """
    check_no_links(source_dir)
    check_no_links(run_root)
    entries = scan_directory(source_dir, policy)
    snapshot_hash = compute_tree_hash_from_entries(entries)

    snapshots_root = run_root / "control" / "snapshots"
    snapshots_root.mkdir(parents=True, exist_ok=True)
    snapshot_dir = safe_path(snapshots_root, snapshot_hash)

    if snapshot_dir.exists():
        verify_snapshot_integrity(snapshot_hash, run_root)
        return snapshot_hash, snapshot_dir

    staging_dir = snapshots_root / f".staging_{snapshot_hash}_{secrets.token_hex(4)}"
    staging_files_dir = staging_dir / "files"
    staging_files_dir.mkdir(parents=True, exist_ok=True)

    try:
        files_metadata: dict[str, Any] = {}
        total_bytes = 0

        for rel_posix, abs_path, is_exec in entries:
            validate_relative_posix_path(rel_posix)
            target_path = safe_path(staging_files_dir, rel_posix)
            target_path.parent.mkdir(parents=True, exist_ok=True)

            with abs_path.open("rb") as src, target_path.open("wb") as dst:
                for chunk in iter(lambda: src.read(1024 * 1024), b""):
                    dst.write(chunk)

            f_size = abs_path.stat().st_size
            total_bytes += f_size
            files_metadata[rel_posix] = {
                "sha256": sha256_file(abs_path),
                "size_bytes": f_size,
                "executable": is_exec,
            }

        meta = {
            "schema_version": SNAPSHOT_SCHEMA,
            "snapshot_hash": snapshot_hash,
            "file_count": len(entries),
            "total_bytes": total_bytes,
            "created_at": utc_now(),
            "files": files_metadata,
        }
        meta_file = staging_dir / "snapshot.json"
        meta_file.write_text(json.dumps(meta, indent=2, sort_keys=True) + "\n", encoding="utf-8")

        staged_hash = tree_hash(staging_files_dir)
        if staged_hash != snapshot_hash:
            raise HarnessError(
                f"Staged snapshot hash mismatch: expected {snapshot_hash!r}, got {staged_hash!r}"
            )

        staging_dir.replace(snapshot_dir)
    except Exception:
        if staging_dir.exists():
            shutil.rmtree(staging_dir, ignore_errors=True)
        raise

    return snapshot_hash, snapshot_dir


def verify_snapshot_integrity(snapshot_hash: str, run_root: Path) -> dict[str, Any]:
    """Verify that a sealed snapshot exists and has not been tampered with or corrupted."""
    check_no_links(run_root)
    require_sha256(snapshot_hash, "snapshot_hash")
    snapshot_dir = safe_path(run_root / "control" / "snapshots", snapshot_hash)
    return verify_bundle_dir(snapshot_dir, expected_hash=snapshot_hash)


verify_snapshot_bundle = verify_bundle_dir


def materialize_snapshot(snapshot_hash: str, target_dir: Path, run_root: Path) -> None:
    """Materialize snapshot files into target_dir. Target must be empty or newly created.

    Pre-validates all source and destination paths and their ancestors before creating directories or writing files.
    """
    require_sha256(snapshot_hash, "snapshot_hash")
    check_no_links(run_root)
    check_no_links(target_dir)
    meta = verify_snapshot_integrity(snapshot_hash, run_root)
    source_files_dir = safe_path(run_root / "control" / "snapshots" / snapshot_hash, "files")
    check_no_links(source_files_dir)

    if target_dir.exists():
        check_no_links(target_dir)
        if not target_dir.is_dir():
            raise HarnessError(f"Target directory is not an ordinary directory: {target_dir}")
        if any(target_dir.iterdir()):
            raise HarnessError(f"Target directory is not empty for materialization: {target_dir}")

    files_dict: dict[str, Any] = meta.get("files", {})

    # Pre-validate all source and destination paths BEFORE writing anything
    for rel_posix in files_dict:
        validate_relative_posix_path(rel_posix)
        src_path = safe_path(source_files_dir, rel_posix)
        dst_path = safe_path(target_dir, rel_posix)
        check_no_links(src_path)
        check_no_links(dst_path)

    target_dir.mkdir(parents=True, exist_ok=True)

    for rel_posix, f_meta in files_dict.items():
        src_path = safe_path(source_files_dir, rel_posix)
        dst_path = safe_path(target_dir, rel_posix)
        dst_path.parent.mkdir(parents=True, exist_ok=True)

        with src_path.open("rb") as src, dst_path.open("wb") as dst:
            for chunk in iter(lambda: src.read(1024 * 1024), b""):
                dst.write(chunk)

        if os.name != "nt" and f_meta.get("executable"):
            dst_path.chmod(dst_path.stat().st_mode | 0o111)

    actual_hash = tree_hash(target_dir)
    if actual_hash != snapshot_hash:
        raise HarnessError(
            f"Materialized tree hash mismatch: expected {snapshot_hash!r}, got {actual_hash!r}"
        )


def _analyze_file_bytes(raw: bytes) -> dict[str, Any]:
    """Analyze raw bytes of a file to extract line-ending, size, and encoding characteristics."""
    size = len(raw)
    is_empty = (size == 0)
    if b"\0" in raw:
        return {
            "is_binary": True,
            "size_bytes": size,
            "is_empty": is_empty,
            "eol": None,
            "has_eof_newline": False,
        }
    try:
        raw.decode("utf-8")
    except UnicodeDecodeError:
        return {
            "is_binary": True,
            "size_bytes": size,
            "is_empty": is_empty,
            "eol": None,
            "has_eof_newline": False,
        }

    has_crlf = b"\r\n" in raw
    raw_no_crlf = raw.replace(b"\r\n", b"")
    has_standalone_lf = b"\n" in raw_no_crlf
    has_standalone_cr = b"\r" in raw_no_crlf

    if has_crlf and (has_standalone_lf or has_standalone_cr):
        eol = "MIXED"
    elif has_crlf:
        eol = "CRLF"
    elif has_standalone_lf:
        eol = "LF"
    elif has_standalone_cr:
        eol = "CR"
    else:
        eol = "NONE"

    has_eof_newline = raw.endswith(b"\n") or raw.endswith(b"\r")

    return {
        "is_binary": False,
        "size_bytes": size,
        "is_empty": is_empty,
        "eol": eol,
        "has_eof_newline": has_eof_newline,
    }


def format_unified_diff(
    p_lines: list[str],
    c_lines: list[str],
    fromfile: str,
    tofile: str,
) -> str:
    """Format unified diff preserving exact line endings and appending EOF newline markers."""
    raw_diff = list(difflib.unified_diff(p_lines, c_lines, fromfile=fromfile, tofile=tofile))
    if not raw_diff:
        return ""
    formatted: list[str] = []
    for line in raw_diff:
        if (line.startswith(" ") or line.startswith("+") or line.startswith("-")) and not line.endswith("\n"):
            formatted.append(line + "\n\\ No newline at end of file\n")
        else:
            formatted.append(line)
    return "".join(formatted)


def compute_diff(
    parent_hash: str | None,
    candidate_hash: str,
    run_root: Path,
    diff_type: str = "per_checkpoint",
) -> tuple[str, Path]:
    """Compute structured byte-level diff between parent snapshot and candidate snapshot.

    Verifies snapshot integrity for both candidate and parent (if provided) before checking cache.
    Verifies diff file integrity deterministically on reuse, rejecting tampered or corrupt diffs.
    Returns (diff_sha256, diff_file).
    """
    if diff_type not in ("per_checkpoint", "cumulative"):
        raise HarnessError(f"diff_type must be 'per_checkpoint' or 'cumulative'; got {diff_type!r}")

    check_no_links(run_root)
    require_sha256(candidate_hash, "candidate_hash")
    cand_meta = verify_snapshot_integrity(candidate_hash, run_root)
    cand_files_dir = safe_path(run_root / "control" / "snapshots" / candidate_hash, "files")
    check_no_links(cand_files_dir)

    parent_files: dict[str, Any] = {}
    parent_files_dir: Path | None = None

    if parent_hash is not None:
        require_sha256(parent_hash, "parent_hash")
        parent_meta = verify_snapshot_integrity(parent_hash, run_root)
        parent_files = parent_meta.get("files", {})
        parent_files_dir = safe_path(run_root / "control" / "snapshots" / parent_hash, "files")
        check_no_links(parent_files_dir)

    cand_files: dict[str, Any] = cand_meta.get("files", {})
    cand_set = set(cand_files.keys())
    parent_set = set(parent_files.keys())

    added = sorted(cand_set - parent_set)
    deleted = sorted(parent_set - cand_set)
    common = sorted(cand_set & parent_set)

    modified: list[str] = []
    unchanged: list[str] = []

    for path_str in common:
        p_info = parent_files[path_str]
        c_info = cand_files[path_str]
        if (
            p_info["sha256"] != c_info["sha256"]
            or p_info.get("executable") != c_info.get("executable")
        ):
            modified.append(path_str)
        else:
            unchanged.append(path_str)

    patches: dict[str, Any] = {}

    for path_str in modified:
        assert parent_files_dir is not None
        p_path = safe_path(parent_files_dir, path_str)
        c_path = safe_path(cand_files_dir, path_str)
        p_raw = p_path.read_bytes()
        c_raw = c_path.read_bytes()
        p_analysis = _analyze_file_bytes(p_raw)
        c_analysis = _analyze_file_bytes(c_raw)

        if p_analysis["is_binary"] or c_analysis["is_binary"]:
            patches[path_str] = {
                "type": "binary",
                "parent_sha256": parent_files[path_str]["sha256"],
                "candidate_sha256": cand_files[path_str]["sha256"],
                "parent_size_bytes": p_analysis["size_bytes"],
                "candidate_size_bytes": c_analysis["size_bytes"],
                "size_delta": c_analysis["size_bytes"] - p_analysis["size_bytes"],
                "parent_eol": p_analysis["eol"],
                "candidate_eol": c_analysis["eol"],
                "eol_changed": p_analysis["eol"] != c_analysis["eol"],
                "parent_has_eof_newline": p_analysis["has_eof_newline"],
                "candidate_has_eof_newline": c_analysis["has_eof_newline"],
                "eof_newline_changed": p_analysis["has_eof_newline"] != c_analysis["has_eof_newline"],
                "parent_is_empty": p_analysis["is_empty"],
                "candidate_is_empty": c_analysis["is_empty"],
            }
        else:
            p_text = p_raw.decode("utf-8")
            c_text = c_raw.decode("utf-8")
            p_lines = p_text.splitlines(keepends=True)
            c_lines = c_text.splitlines(keepends=True)
            unified = format_unified_diff(p_lines, c_lines, f"a/{path_str}", f"b/{path_str}")
            patches[path_str] = {
                "type": "text",
                "unified_diff": unified,
                "parent_sha256": parent_files[path_str]["sha256"],
                "candidate_sha256": cand_files[path_str]["sha256"],
                "parent_size_bytes": p_analysis["size_bytes"],
                "candidate_size_bytes": c_analysis["size_bytes"],
                "size_delta": c_analysis["size_bytes"] - p_analysis["size_bytes"],
                "parent_eol": p_analysis["eol"],
                "candidate_eol": c_analysis["eol"],
                "eol_changed": p_analysis["eol"] != c_analysis["eol"],
                "parent_has_eof_newline": p_analysis["has_eof_newline"],
                "candidate_has_eof_newline": c_analysis["has_eof_newline"],
                "eof_newline_changed": p_analysis["has_eof_newline"] != c_analysis["has_eof_newline"],
                "parent_is_empty": p_analysis["is_empty"],
                "candidate_is_empty": c_analysis["is_empty"],
            }

    for path_str in added:
        c_path = safe_path(cand_files_dir, path_str)
        c_raw = c_path.read_bytes()
        c_analysis = _analyze_file_bytes(c_raw)

        if c_analysis["is_binary"]:
            patches[path_str] = {
                "type": "binary",
                "parent_sha256": None,
                "candidate_sha256": cand_files[path_str]["sha256"],
                "parent_size_bytes": None,
                "candidate_size_bytes": c_analysis["size_bytes"],
                "size_delta": c_analysis["size_bytes"],
                "parent_eol": None,
                "candidate_eol": c_analysis["eol"],
                "eol_changed": True,
                "parent_has_eof_newline": None,
                "candidate_has_eof_newline": c_analysis["has_eof_newline"],
                "eof_newline_changed": True,
                "parent_is_empty": None,
                "candidate_is_empty": c_analysis["is_empty"],
            }
        else:
            c_text = c_raw.decode("utf-8")
            c_lines = c_text.splitlines(keepends=True)
            unified = format_unified_diff([], c_lines, "/dev/null", f"b/{path_str}")
            patches[path_str] = {
                "type": "text",
                "unified_diff": unified,
                "parent_sha256": None,
                "candidate_sha256": cand_files[path_str]["sha256"],
                "parent_size_bytes": None,
                "candidate_size_bytes": c_analysis["size_bytes"],
                "size_delta": c_analysis["size_bytes"],
                "parent_eol": None,
                "candidate_eol": c_analysis["eol"],
                "eol_changed": True,
                "parent_has_eof_newline": None,
                "candidate_has_eof_newline": c_analysis["has_eof_newline"],
                "eof_newline_changed": True,
                "parent_is_empty": None,
                "candidate_is_empty": c_analysis["is_empty"],
            }

    for path_str in deleted:
        assert parent_files_dir is not None
        p_path = safe_path(parent_files_dir, path_str)
        p_raw = p_path.read_bytes()
        p_analysis = _analyze_file_bytes(p_raw)

        if p_analysis["is_binary"]:
            patches[path_str] = {
                "type": "binary",
                "parent_sha256": parent_files[path_str]["sha256"],
                "candidate_sha256": None,
                "parent_size_bytes": p_analysis["size_bytes"],
                "candidate_size_bytes": None,
                "size_delta": -p_analysis["size_bytes"],
                "parent_eol": p_analysis["eol"],
                "candidate_eol": None,
                "eol_changed": True,
                "parent_has_eof_newline": p_analysis["has_eof_newline"],
                "candidate_has_eof_newline": None,
                "eof_newline_changed": True,
                "parent_is_empty": p_analysis["is_empty"],
                "candidate_is_empty": None,
            }
        else:
            p_text = p_raw.decode("utf-8")
            p_lines = p_text.splitlines(keepends=True)
            unified = format_unified_diff(p_lines, [], f"a/{path_str}", "/dev/null")
            patches[path_str] = {
                "type": "text",
                "unified_diff": unified,
                "parent_sha256": parent_files[path_str]["sha256"],
                "candidate_sha256": None,
                "parent_size_bytes": p_analysis["size_bytes"],
                "candidate_size_bytes": None,
                "size_delta": -p_analysis["size_bytes"],
                "parent_eol": p_analysis["eol"],
                "candidate_eol": None,
                "eol_changed": True,
                "parent_has_eof_newline": p_analysis["has_eof_newline"],
                "candidate_has_eof_newline": None,
                "eof_newline_changed": True,
                "parent_is_empty": p_analysis["is_empty"],
                "candidate_is_empty": None,
            }

    diff_data = {
        "schema_version": DIFF_SCHEMA,
        "diff_type": diff_type,
        "parent_snapshot_hash": parent_hash,
        "candidate_snapshot_hash": candidate_hash,
        "summary": {
            "added_count": len(added),
            "modified_count": len(modified),
            "deleted_count": len(deleted),
            "unchanged_count": len(unchanged),
            "added": added,
            "modified": modified,
            "deleted": deleted,
            "unchanged": unchanged,
        },
        "patches": patches,
    }

    diff_bytes = (json.dumps(diff_data, indent=2, sort_keys=True) + "\n").encode("utf-8")
    diff_sha = sha256_bytes(diff_bytes)

    diffs_root = run_root / "control" / "diffs"
    diffs_root.mkdir(parents=True, exist_ok=True)
    parent_label = parent_hash or "none"
    diff_file = safe_path(diffs_root, f"{diff_type}_{parent_label}_{candidate_hash}.json")

    if diff_file.exists():
        existing_bytes = diff_file.read_bytes()
        existing_sha = sha256_bytes(existing_bytes)
        if existing_sha != diff_sha:
            raise HarnessError(
                f"Diff integrity violation: diff file {diff_file.name} hash mismatch "
                f"(expected {diff_sha!r}, got {existing_sha!r})"
            )
        return existing_sha, diff_file

    pending_file = diff_file.with_name(diff_file.name + ".pending")
    pending_file.write_bytes(diff_bytes)
    pending_file.replace(diff_file)

    return diff_sha, diff_file
