"""Core data loading, hashing, path safety, and schema validation for evals-foundation."""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import math
import os
import re
import shutil
import sys
from fractions import Fraction
from pathlib import Path
from typing import Any

HARNESS_VERSION = "0.1.0"
JOURNEY_SCHEMA = "repo-foundation-harness/journey-v1"
MANIFEST_SCHEMA = "repo-foundation-harness/manifest-v1"
CHECKPOINT_RECORD_SCHEMA = "repo-foundation-harness/checkpoint-record-v1"
PRE_CHECK_ARTIFACT_SCHEMA = "repo-foundation-harness/pre-check-artifact-v1"
JUDGE_PACKET_SCHEMA = "repo-foundation-harness/judge-packet-v1"
RUBRIC_SCHEMA = "repo-foundation-harness/rubric-v1"
JUDGE_INDEX_SCHEMA = "repo-foundation-harness/judge-index-v1"
JUDGMENT_SCHEMA = "repo-foundation-harness/judgment-v1"
SCORING_POLICY_SCHEMA = "repo-foundation-harness/scoring-policy-v1"
SCORE_REPORT_SCHEMA = "repo-foundation-harness/score-report-v1"

BASE_DIMENSION_IDS = (
    "functional_correctness",
    "change_scope",
    "repository_conformity",
    "ownership_and_complexity",
    "test_quality",
    "wording_and_comments",
)
CP3_EXTRA_DIMENSION_IDS = ("contract_evolution",)
CP4_EXTRA_DIMENSION_IDS = ("takeover_readiness",)
ALL_DIMENSION_IDS = BASE_DIMENSION_IDS + CP3_EXTRA_DIMENSION_IDS + CP4_EXTRA_DIMENSION_IDS
JUDGMENT_VERDICTS = ("pass", "fail", "invalid", "unresolved")

ID_RE = re.compile(r"^[a-z0-9][a-z0-9._-]{0,79}$")
SHA256_RE = re.compile(r"^[a-f0-9]{64}$")
HEX32_RE = re.compile(r"^[a-f0-9]{32}$")
HEX16_RE = re.compile(r"^[a-f0-9]{16}$")
REP_RE = re.compile(r"^rep[0-9]{2}$")

CHECKPOINT_IDS = ("CP1_BOOTSTRAP", "CP2_SLICE", "CP3_EVOLUTION", "CP4_CONTINUITY")
VARIANT_IDS = ("A", "B", "C", "D")
CHECK_TYPES = ("environment", "acceptance", "regression")
CHECK_STATUSES = (
    "PASSED",
    "FAILED",
    "NOT_YET_IMPLEMENTED",
    "ACCEPTANCE_FAILED",
    "ENVIRONMENT_CHECK_FAILED",
    "INFRA_ERROR",
    "TIMEOUT",
)
LIFECYCLE_STATUSES = (
    "PREPARED",
    "EXECUTING",
    "COLLECTED",
    "VERIFIED",
    "JUDGED",
    "SCORED",
    "BLOCKED_BY_PREDECESSOR",
)
EXECUTION_STATUSES = (
    "COMPLETED",
    "TIMEOUT",
    "BUDGET_EXHAUSTED",
    "INFRA_ERROR",
    "BLOCKED_BY_PREDECESSOR",
)
MEASUREMENT_VALIDITIES = (
    "VALID",
    "EVALUATION_INVALID",
    "PENDING_VERIFICATION",
    "UNRESOLVED",
)
OUTPUT_QUALITIES = ("PASS", "FAIL", "HARD_FAILURE", "UNRESOLVED")

WINDOWS_RESERVED_DEVICE_NAMES = {
    "CON", "PRN", "AUX", "NUL",
    "COM1", "COM2", "COM3", "COM4", "COM5", "COM6", "COM7", "COM8", "COM9",
    "LPT1", "LPT2", "LPT3", "LPT4", "LPT5", "LPT6", "LPT7", "LPT8", "LPT9",
}
WINDOWS_FORBIDDEN_CHARS = set('<>:"\\|?*')


def validate_relative_posix_path(rel_posix: str) -> None:
    """Validate that a relative POSIX path is safe, normalized, and valid across OS platforms."""
    if not isinstance(rel_posix, str) or not rel_posix.strip():
        raise HarnessError(f"Invalid relative path: {rel_posix!r}")
    if rel_posix != rel_posix.strip():
        raise HarnessError(f"Path has leading or trailing whitespace: {rel_posix!r}")
    if "\\" in rel_posix:
        raise HarnessError(f"Path must use forward slashes: {rel_posix!r}")
    if rel_posix.startswith("/"):
        raise HarnessError(f"Absolute path not allowed: {rel_posix!r}")
    if ":" in rel_posix:
        raise HarnessError(f"Path contains colon or stream specifier: {rel_posix!r}")

    parts = rel_posix.split("/")
    for part in parts:
        if not part or part in {".", ".."}:
            raise HarnessError(f"Invalid path segment {part!r} in {rel_posix!r}")
        if part != part.strip():
            raise HarnessError(f"Path segment has leading or trailing whitespace {part!r} in {rel_posix!r}")
        if part.endswith("."):
            raise HarnessError(f"Path segment has trailing dot {part!r} in {rel_posix!r}")
        if any(c in WINDOWS_FORBIDDEN_CHARS or ord(c) < 32 for c in part):
            raise HarnessError(f"Path segment contains forbidden character {part!r} in {rel_posix!r}")
        base_name = part.split(".")[0].upper()
        if base_name in WINDOWS_RESERVED_DEVICE_NAMES:
            raise HarnessError(f"Path segment uses reserved Windows device name {part!r} in {rel_posix!r}")


class HarnessError(RuntimeError):
    pass


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z")


def load_json(path: Path) -> dict[str, Any]:
    def pairs(items: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in items:
            if key in result:
                raise HarnessError(f"Duplicate JSON key in {path}: {key}")
            result[key] = value
        return result

    def invalid_constant(value: str) -> None:
        raise HarnessError(f"Non-finite JSON number in {path}: {value}")

    try:
        content = path.read_text(encoding="utf-8")
        value = json.loads(content, object_pairs_hook=pairs, parse_constant=invalid_constant)
    except FileNotFoundError as exc:
        raise HarnessError(f"File not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise HarnessError(f"Invalid JSON in {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise HarnessError(f"Expected a JSON object in {path}")
    return value


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    pending = path.with_name(path.name + ".pending")
    pending.write_text(
        json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    pending.replace(path)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().lower()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().lower()


def tree_hash(root: Path) -> str:
    if not root.is_dir() or root.is_symlink() or getattr(root, "is_junction", lambda: False)():
        raise HarnessError(f"Expected an ordinary directory: {root}")
    digest = hashlib.sha256()
    for path in sorted(root.rglob("*")):
        if path.is_symlink() or getattr(path, "is_junction", lambda: False)():
            raise HarnessError(f"Links are not supported: {path}")
        if path.is_dir():
            continue
        if not path.is_file():
            raise HarnessError(f"Unsupported entry type: {path}")
        rel = path.relative_to(root).as_posix()
        digest.update(rel.encode("utf-8"))
        digest.update(b"\0")
        digest.update(b"x" if os.name != "nt" and path.stat().st_mode & 0o111 else b"-")
        digest.update(bytes.fromhex(sha256_file(path)))
    return digest.hexdigest().lower()


def check_no_links(path: Path) -> None:
    """Ensure that neither path nor any of its existing ancestors is a symlink or junction."""
    chain = [path] + list(path.parents)
    for p in reversed(chain):
        if p.is_symlink() or getattr(p, "is_junction", lambda: False)() or os.path.isjunction(p):
            raise HarnessError(f"Symlinks and junctions are not supported: {p}")


def paths_overlap(p1: Path, p2: Path) -> bool:
    """Return True if p1 and p2 are identical or if one is an ancestor/descendant of the other."""
    try:
        r1 = p1.resolve()
        r2 = p2.resolve()
        s1 = str(r1).lower()
        s2 = str(r2).lower()
        if s1 == s2:
            return True
        p1_parents = [str(p).lower() for p in r1.parents]
        p2_parents = [str(p).lower() for p in r2.parents]
        return s1 in p2_parents or s2 in p1_parents
    except Exception:
        return False


VALID_JSON_SCHEMA_TYPES = {"string", "number", "integer", "boolean", "array", "object", "null"}


def validate_json_schema_definition(schema: dict[str, Any], schema_name: str = "schema") -> None:
    """Validate that a JSON Schema document conforms structurally to JSON Schema Draft 2020-12 / Draft 7 metaschema."""
    if not isinstance(schema, dict):
        raise HarnessError(f"{schema_name} must be a JSON object, got {type(schema).__name__}")

    schema_uri = schema.get("$schema")
    if not isinstance(schema_uri, str) or not schema_uri.startswith("http"):
        raise HarnessError(f"{schema_name} missing or invalid '$schema' URI: {schema_uri!r}")

    def _validate_schema_object(node: Any, path: str) -> None:
        if isinstance(node, bool):
            return
        if not isinstance(node, dict):
            raise HarnessError(f"Schema node at {path} in {schema_name} must be an object or boolean, got {type(node).__name__}")

        # 1. 'type' keyword
        if "type" in node:
            t = node["type"]
            if isinstance(t, str):
                if t not in VALID_JSON_SCHEMA_TYPES:
                    raise HarnessError(
                        f"Invalid JSON Schema type {t!r} at {path}.type in {schema_name}. "
                        f"Valid types: {sorted(VALID_JSON_SCHEMA_TYPES)}"
                    )
            elif isinstance(t, list):
                if len(t) == 0:
                    raise HarnessError(f"Field 'type' at {path}.type in {schema_name} cannot be empty array")
                if len(t) != len(set(t)):
                    raise HarnessError(f"Field 'type' at {path}.type in {schema_name} contains duplicate types: {t}")
                for idx, item in enumerate(t):
                    if not isinstance(item, str) or item not in VALID_JSON_SCHEMA_TYPES:
                        raise HarnessError(
                            f"Invalid JSON Schema type {item!r} at {path}.type[{idx}] in {schema_name}"
                        )
            else:
                raise HarnessError(f"Field 'type' at {path} in {schema_name} must be a string or non-empty list of strings")

        # 2. 'required' keyword
        if "required" in node:
            req = node["required"]
            if not isinstance(req, list) or not all(isinstance(x, str) for x in req):
                raise HarnessError(f"Field 'required' at {path} in {schema_name} must be a list of strings")
            if len(req) != len(set(req)):
                raise HarnessError(f"Field 'required' at {path} in {schema_name} contains duplicate elements: {req}")

        # 3. 'properties' keyword
        if "properties" in node:
            props = node["properties"]
            if not isinstance(props, dict):
                raise HarnessError(f"Field 'properties' at {path} in {schema_name} must be an object, got {type(props).__name__}")
            for prop_name, prop_schema in props.items():
                _validate_schema_object(prop_schema, f"{path}.properties.{prop_name}")

        # 4. 'patternProperties' keyword
        if "patternProperties" in node:
            pat_props = node["patternProperties"]
            if not isinstance(pat_props, dict):
                raise HarnessError(f"Field 'patternProperties' at {path} in {schema_name} must be an object")
            for pat, pat_schema in pat_props.items():
                _validate_schema_object(pat_schema, f"{path}.patternProperties.{pat}")

        # 5. 'items' keyword
        if "items" in node:
            items = node["items"]
            if isinstance(items, (dict, bool)):
                _validate_schema_object(items, f"{path}.items")
            elif isinstance(items, list):
                if len(items) == 0:
                    raise HarnessError(f"Field 'items' at {path} in {schema_name} cannot be empty array")
                for idx, it in enumerate(items):
                    _validate_schema_object(it, f"{path}.items[{idx}]")
            else:
                raise HarnessError(f"Field 'items' at {path} in {schema_name} must be a schema object, boolean, or list, got {type(items).__name__}")

        # 6. 'prefixItems' keyword
        if "prefixItems" in node:
            p_items = node["prefixItems"]
            if not isinstance(p_items, list):
                raise HarnessError(f"Field 'prefixItems' at {path} in {schema_name} must be a list")
            for idx, it in enumerate(p_items):
                _validate_schema_object(it, f"{path}.prefixItems[{idx}]")

        # 7. 'additionalProperties' keyword
        if "additionalProperties" in node:
            add_props = node["additionalProperties"]
            if isinstance(add_props, (dict, bool)):
                _validate_schema_object(add_props, f"{path}.additionalProperties")
            else:
                raise HarnessError(f"Field 'additionalProperties' at {path} in {schema_name} must be a boolean or object")

        # 8. Numeric range keywords
        for num_kw in ("minimum", "maximum", "exclusiveMinimum", "exclusiveMaximum"):
            if num_kw in node:
                val = node[num_kw]
                if isinstance(val, bool) or not isinstance(val, (int, float)):
                    raise HarnessError(f"Field {num_kw!r} at {path} in {schema_name} must be a number, got {val!r}")

        # 9. Combiners: allOf, anyOf, oneOf
        for combiner in ("allOf", "anyOf", "oneOf"):
            if combiner in node:
                comb_val = node[combiner]
                if not isinstance(comb_val, list) or len(comb_val) == 0:
                    raise HarnessError(f"Field {combiner!r} at {path} in {schema_name} must be a non-empty list")
                for idx, sub in enumerate(comb_val):
                    _validate_schema_object(sub, f"{path}.{combiner}[{idx}]")

        # 10. 'not' keyword
        if "not" in node:
            not_val = node["not"]
            if isinstance(not_val, (dict, bool)):
                _validate_schema_object(not_val, f"{path}.not")
            else:
                raise HarnessError(f"Field 'not' at {path} in {schema_name} must be a schema object or boolean")

        # 11. '$defs' / 'definitions'
        for defs_kw in ("$defs", "definitions"):
            if defs_kw in node:
                defs_val = node[defs_kw]
                if not isinstance(defs_val, dict):
                    raise HarnessError(f"Field {defs_kw!r} at {path} in {schema_name} must be an object")
                for def_name, def_schema in defs_val.items():
                    _validate_schema_object(def_schema, f"{path}.{defs_kw}.{def_name}")

        # 12. 'enum' keyword
        if "enum" in node:
            enum_val = node["enum"]
            if not isinstance(enum_val, list) or len(enum_val) == 0:
                raise HarnessError(f"Field 'enum' at {path} in {schema_name} must be a non-empty list")

    _validate_schema_object(schema, "$")


SNAPSHOT_SCHEMA = "repo-foundation-harness/snapshot-v1"


def verify_bundle_dir(bundle_dir: Path, expected_hash: str | None = None) -> dict[str, Any]:
    """Verify that a snapshot bundle directory conforms strictly to specification.

    Exhaustive validation:
    1. Rejects symlinks or junctions in bundle_dir or any of its contents.
    2. Validates top-level bundle scope: only 'snapshot.json', 'files', 'bundle_manifest.json' allowed.
    3. Validates snapshot.json exists, is valid JSON object, schema_version is 'repo-foundation-harness/snapshot-v1'.
    4. Validates snapshot_hash is a 64-char lowercase hex string. If expected_hash is provided, must match.
    5. Validates file_count is a non-negative int.
    6. Validates total_bytes is a non-negative int.
    7. Validates 'files' is a dictionary mapping relative posix paths to file metadata objects.
    8. Validates each file metadata object:
       - path is safe, normalized relative POSIX path (no traversal, no Windows reserved names)
       - sha256 is 64-char lowercase hex
       - size_bytes is non-negative int
       - executable is bool (and on Windows, executable must be False)
    9. Validates files/ directory exists and contains no symlinks.
    10. Bi-directional reconciliation: disk files under files/ must match metadata files exactly (no extra, no missing).
    11. Disk file verification: actual size and sha256 must match metadata; executable must match.
    12. Actual file count must equal file_count; actual total bytes must equal total_bytes.
    13. Overall tree hash of files/ directory must match snapshot_hash.
    """
    check_no_links(bundle_dir)
    if not bundle_dir.is_dir():
        raise HarnessError(f"Snapshot bundle directory not found or not a directory: {bundle_dir}")

    # Top-level containment
    ALLOWED_BUNDLE_ENTRIES = {"snapshot.json", "files", "bundle_manifest.json"}
    for item in bundle_dir.iterdir():
        if item.name not in ALLOWED_BUNDLE_ENTRIES:
            raise HarnessError(
                f"Destination directory contains unmanaged file or directory '{item.name}' "
                "which does not belong to the snapshot bundle. Refusing to mutate."
            )

    meta_file = safe_path(bundle_dir, "snapshot.json")
    check_no_links(meta_file)
    if not meta_file.is_file():
        raise HarnessError(f"Snapshot metadata missing: {meta_file}")

    meta = load_json(meta_file)
    if not isinstance(meta, dict):
        raise HarnessError("Snapshot metadata must be a JSON object")

    if meta.get("schema_version") != SNAPSHOT_SCHEMA:
        raise HarnessError(f"Snapshot schema mismatch: {meta.get('schema_version')!r}")

    snap_hash = meta.get("snapshot_hash")
    if not isinstance(snap_hash, str) or not SHA256_RE.match(snap_hash.lower()):
        raise HarnessError(f"Invalid or missing snapshot_hash in metadata: {snap_hash!r}")
    snap_hash = snap_hash.lower()

    if expected_hash is not None and snap_hash != expected_hash.lower():
        raise HarnessError(
            f"Snapshot hash in metadata ({snap_hash!r}) != expected ({expected_hash.lower()!r})"
        )

    file_count = meta.get("file_count")
    if type(file_count) is not int or file_count < 0:
        raise HarnessError(f"Snapshot file_count must be a non-negative integer; got {file_count!r}")

    total_bytes = meta.get("total_bytes")
    if type(total_bytes) is not int or total_bytes < 0:
        raise HarnessError(f"Snapshot total_bytes must be a non-negative integer; got {total_bytes!r}")

    files = meta.get("files")
    if not isinstance(files, dict):
        raise HarnessError("Snapshot metadata 'files' must be a dictionary")

    # Validate all file metadata objects
    for rel_posix, f_meta in files.items():
        validate_relative_posix_path(rel_posix)
        if not isinstance(f_meta, dict):
            raise HarnessError(f"File metadata for {rel_posix!r} must be a dict")

        f_sha = f_meta.get("sha256")
        if not isinstance(f_sha, str) or not SHA256_RE.match(f_sha.lower()):
            raise HarnessError(f"Invalid sha256 for files[{rel_posix}]: {f_sha!r}")

        f_size = f_meta.get("size_bytes")
        if type(f_size) is not int or f_size < 0:
            raise HarnessError(f"File size_bytes for {rel_posix!r} must be non-negative int; got {f_size!r}")

        f_exec = f_meta.get("executable")
        if type(f_exec) is not bool:
            raise HarnessError(f"File executable for {rel_posix!r} must be bool; got {f_exec!r}")

        if os.name == "nt" and f_exec is not False:
            raise HarnessError(
                f"Snapshot integrity violation: executable metadata on Windows must be false, "
                f"got {f_exec!r} for {rel_posix!r}"
            )

    files_dir = safe_path(bundle_dir, "files")
    check_no_links(files_dir)
    if not files_dir.is_dir():
        raise HarnessError(f"Snapshot files directory missing: {files_dir}")

    # Scan actual disk files under files/
    disk_files: dict[str, Path] = {}
    for p in sorted(files_dir.rglob("*")):
        if p.is_symlink() or getattr(p, "is_junction", lambda: False)():
            raise HarnessError(f"Links are not supported: {p}")
        if p.is_dir():
            continue
        if not p.is_file():
            raise HarnessError(f"Unsupported entry type: {p}")
        rel = p.relative_to(files_dir).as_posix()
        disk_files[rel] = p

    meta_set = set(files.keys())
    disk_set = set(disk_files.keys())

    if meta_set != disk_set:
        extra = disk_set - meta_set
        missing = meta_set - disk_set
        msg_parts = []
        if extra:
            msg_parts.append(f"unmanaged file(s) in 'files/': {sorted(extra)}")
        if missing:
            msg_parts.append(f"missing file(s) declared in manifest: {sorted(missing)}")
        raise HarnessError(
            f"Snapshot integrity violation: file set mismatch ({'; '.join(msg_parts)}): "
            f"in_meta_not_disk={sorted(missing)}, in_disk_not_meta={sorted(extra)}"
        )

    calculated_total_bytes = 0
    for rel, path in disk_files.items():
        f_meta = files[rel]
        st = path.stat()
        if st.st_size != f_meta["size_bytes"]:
            raise HarnessError(
                f"Snapshot integrity violation: file size mismatch for {rel!r}: disk={st.st_size}, meta={f_meta['size_bytes']}"
            )
        calculated_total_bytes += st.st_size

        actual_sha = sha256_file(path)
        if actual_sha != f_meta["sha256"].lower():
            raise HarnessError(
                f"Snapshot integrity violation: file sha256 mismatch for {rel!r}: disk={actual_sha}, meta={f_meta['sha256']}"
            )

        if os.name != "nt":
            is_exec = (st.st_mode & 0o111) != 0
            if is_exec != f_meta["executable"]:
                raise HarnessError(
                    f"Snapshot integrity violation: file executable mismatch for {rel!r}: disk={is_exec}, meta={f_meta['executable']}"
                )

    if len(files) != file_count:
        raise HarnessError(
            f"Snapshot integrity violation: file_count mismatch: meta={file_count}, actual={len(files)}"
        )

    if calculated_total_bytes != total_bytes:
        raise HarnessError(
            f"Snapshot integrity violation: total_bytes mismatch: meta={total_bytes}, calculated={calculated_total_bytes}"
        )

    actual_tree_hash = tree_hash(files_dir)
    if actual_tree_hash != snap_hash:
        raise HarnessError(
            f"Snapshot integrity violation: files in {bundle_dir} have tree hash {actual_tree_hash!r}, expected {snap_hash!r}"
        )

    return meta


def is_valid_snapshot_bundle(bundle_dir: Path) -> tuple[bool, str]:
    """Validate whether an existing directory is a legitimate snapshot bundle conforming to specification."""
    if not bundle_dir.exists():
        return True, "Destination does not exist yet (clean new directory)"
    if not bundle_dir.is_dir():
        return False, f"Destination path is a file, expected directory: {bundle_dir}"

    entries = list(bundle_dir.iterdir())
    if not entries:
        return True, "Destination is an empty directory"

    try:
        verify_bundle_dir(bundle_dir)
        return True, "Valid snapshot bundle"
    except Exception as e:
        return False, str(e)


def safe_path(root: Path, name: str) -> Path:
    check_no_links(root)
    parts = name.split("/")
    if not name or "\\" in name or any(part in {"", ".", ".."} or part.lower() == ".git" or ":" in part for part in parts):
        raise HarnessError(f"Unsupported path: {name!r}")
    current = root
    for part in parts:
        current = current / part
        if current.is_symlink() or getattr(current, "is_junction", lambda: False)() or os.path.isjunction(current):
            raise HarnessError(f"Symlinks and junctions are not supported: {current}")
    if not current.resolve().is_relative_to(root.resolve()):
        raise HarnessError(f"Path escapes root: {name!r}")
    return current


def require_id(value: Any, label: str) -> str:
    if not isinstance(value, str) or not ID_RE.fullmatch(value):
        raise HarnessError(f"{label} must match {ID_RE.pattern!r}; got {value!r}")
    stem = value.split(".")[0].upper()
    if stem in {"CON", "PRN", "AUX", "NUL", *(f"COM{i}" for i in range(1, 10)), *(f"LPT{i}" for i in range(1, 10))} or value.endswith("."):
        raise HarnessError(f"{label} is not a portable filesystem ID: {value}")
    return value


def require_sha256(value: Any, label: str) -> str:
    if not isinstance(value, str) or not SHA256_RE.fullmatch(value):
        raise HarnessError(f"{label} must be a 64-character lowercase hex SHA-256; got {value!r}")
    return value


def fields(data: dict[str, Any], allowed: set[str], required: set[str], label: str) -> None:
    if not isinstance(data, dict):
        raise HarnessError(f"{label} must be an object")
    unknown = set(data) - allowed
    missing = required - set(data)
    if unknown or missing:
        raise HarnessError(f"{label}: unknown fields={sorted(unknown)}, missing fields={sorted(missing)}")


def validate_verifier_command_form(
    argv: list[str],
    verifier_entrypoint: str | None,
    label: str = "check.command.argv",
) -> None:
    """Validate that verifier invocation in argv adheres to supported command forms.

    Supported command form:
    Direct Python script execution using the controller's trusted Python interpreter:
    [<trusted_python>, <verifier_entrypoint | ${VERIFIER}>, ...optional_args]
    where pos == 1.
    All module execution (-m), inline code flags (-c, /c, -e), and non-Python/unverified
    executors are strictly rejected.
    """
    if verifier_entrypoint is None:
        if "${VERIFIER}" in argv:
            raise HarnessError(f"{label} uses '${{VERIFIER}}' placeholder without declaring verifier_entrypoint")
        return

    # verifier_entrypoint is declared
    if len(argv) < 2:
        raise HarnessError(f"{label} must contain at least [executor, verifier_target]")

    # 1. Verify executor at argv[0] is the trusted Python interpreter
    exe = argv[0]
    is_trusted_python = False
    try:
        if Path(exe).resolve() == Path(sys.executable).resolve():
            is_trusted_python = True
        else:
            which_exe = shutil.which(exe)
            if which_exe and Path(which_exe).resolve() == Path(sys.executable).resolve():
                is_trusted_python = True
    except Exception:
        is_trusted_python = False

    if not is_trusted_python:
        raise HarnessError(
            f"{label}: unsupported verifier executor {exe!r}; trusted verifier must be executed directly "
            f"by controller Python interpreter ({sys.executable})"
        )

    # 2. Reject module execution (-m)
    if "-m" in argv:
        raise HarnessError(
            f"{label}: module execution via '-m' is not supported for verifier commands; "
            f"verifier must be executed directly as script target at argv[1]"
        )

    # 3. Reject inline code execution flags
    forbidden_flags = {"-c", "/c", "-e"}
    for arg in argv:
        if arg in forbidden_flags:
            raise HarnessError(f"{label} cannot use inline code execution flag {arg!r} with declared verifier_entrypoint")

    # 4. Check verifier token references and position
    positions = [
        idx for idx, arg in enumerate(argv)
        if arg == verifier_entrypoint or arg == "${VERIFIER}"
    ]
    if len(positions) == 0:
        raise HarnessError(
            f"{label} declared verifier_entrypoint {verifier_entrypoint!r} but it is not referenced in argv via exact token or '${{VERIFIER}}'"
        )
    if len(positions) > 1:
        raise HarnessError(f"{label} contains multiple references to verifier in argv: {argv}")

    pos = positions[0]
    if pos != 1:
        raise HarnessError(
            f"{label} places verifier at invalid position {pos} in argv {argv}; "
            f"verifier must be direct script target at argv[1] ([python, <verifier>])"
        )


def validate_journey_schema(data: dict[str, Any]) -> None:
    fields(
        data,
        {"schema_version", "journey_id", "name", "repetitions", "variants", "checkpoints", "snapshot_policy"},
        {"schema_version", "journey_id", "name", "repetitions", "variants", "checkpoints", "snapshot_policy"},
        "journey",
    )
    if data.get("schema_version") != JOURNEY_SCHEMA:
        raise HarnessError(f"Journey schema_version must be {JOURNEY_SCHEMA!r}")
    require_id(data.get("journey_id"), "journey.journey_id")
    if not isinstance(data.get("name"), str) or not data["name"].strip():
        raise HarnessError("journey.name must be a non-empty string")
    reps = data.get("repetitions")
    if type(reps) is not int or reps < 1 or reps > 20:
        raise HarnessError("journey.repetitions must be an integer between 1 and 20")

    variants = data.get("variants")
    if not isinstance(variants, list) or not variants:
        raise HarnessError("journey.variants must contain at least one variant")
    seen_variants: set[str] = set()
    for idx, variant in enumerate(variants):
        label = f"journey.variants[{idx}]"
        fields(variant, {"id", "skills"}, {"id", "skills"}, label)
        vid = variant.get("id")
        if vid not in VARIANT_IDS or vid in seen_variants:
            raise HarnessError(f"{label}.id must be one of {VARIANT_IDS} and unique; got {vid!r}")
        seen_variants.add(vid)
        skills = variant.get("skills")
        if not isinstance(skills, list):
            raise HarnessError(f"{label}.skills must be an array")
        seen_skill_names: set[str] = set()
        for s_idx, skill in enumerate(skills):
            s_label = f"{label}.skills[{s_idx}]"
            fields(skill, {"name", "path"}, {"name", "path"}, s_label)
            s_name = require_id(skill.get("name"), f"{s_label}.name")
            if s_name in seen_skill_names:
                raise HarnessError(f"Duplicate skill name in {label}: {s_name!r}")
            seen_skill_names.add(s_name)
            if not isinstance(skill.get("path"), str) or not skill["path"].strip():
                raise HarnessError(f"{s_label}.path must be non-empty string")

    checkpoints = data.get("checkpoints")
    if not isinstance(checkpoints, list) or len(checkpoints) != 4:
        raise HarnessError("journey.checkpoints must contain exactly 4 checkpoints")
    for idx, cp in enumerate(checkpoints):
        label = f"journey.checkpoints[{idx}]"
        fields(cp, {"id", "name", "order", "task_ref", "checks"}, {"id", "name", "order", "task_ref", "checks"}, label)
        expected_id = CHECKPOINT_IDS[idx]
        if cp.get("id") != expected_id:
            raise HarnessError(f"{label}.id must be {expected_id!r}")
        order = cp.get("order")
        if type(order) is not int or order != idx + 1:
            raise HarnessError(f"{label}.order must be {idx + 1}")
        if not isinstance(cp.get("name"), str) or not cp["name"].strip():
            raise HarnessError(f"{label}.name must be a non-empty string")
        if not isinstance(cp.get("task_ref"), str) or not cp["task_ref"].strip():
            raise HarnessError(f"{label}.task_ref must be a non-empty string")
        checks = cp.get("checks")
        if not isinstance(checks, list):
            raise HarnessError(f"{label}.checks must be an array")
        check_ids: set[str] = set()
        for c_idx, check in enumerate(checks):
            c_label = f"{label}.checks[{c_idx}]"
            fields(
                check,
                {"id", "type", "validity_scope", "command", "replaces_check_id", "entrypoint", "tool", "verifier_entrypoint"},
                {"id", "type", "validity_scope", "command"},
                c_label,
            )
            cid = require_id(check.get("id"), f"{c_label}.id")
            if cid in check_ids:
                raise HarnessError(f"Duplicate check id in {label}: {cid}")
            check_ids.add(cid)
            ctype = check.get("type")
            if ctype not in CHECK_TYPES:
                raise HarnessError(f"{c_label}.type must be one of {CHECK_TYPES}; got {ctype!r}")
            scope = check.get("validity_scope")
            if not isinstance(scope, list) or not scope or not all(s in CHECKPOINT_IDS for s in scope):
                raise HarnessError(f"{c_label}.validity_scope must be non-empty array of valid checkpoint IDs")
            cmd = check.get("command")
            fields(cmd, {"argv", "timeout_seconds", "cwd", "env"}, {"argv", "timeout_seconds"}, f"{c_label}.command")
            argv = cmd.get("argv")
            if not isinstance(argv, list) or not argv or not all(isinstance(x, str) and x for x in argv):
                raise HarnessError(f"{c_label}.command.argv must be non-empty string array")
            timeout = cmd.get("timeout_seconds")
            if type(timeout) is not int or timeout < 1 or timeout > 86400:
                raise HarnessError(f"{c_label}.command.timeout_seconds must be integer between 1 and 86400")
            if "cwd" in cmd and not isinstance(cmd["cwd"], str):
                raise HarnessError(f"{c_label}.command.cwd must be a string")
            if "env" in cmd:
                env = cmd["env"]
                if not isinstance(env, dict) or not all(isinstance(k, str) and isinstance(v, str) for k, v in env.items()):
                    raise HarnessError(f"{c_label}.command.env must be string-to-string dictionary")
            replaces = check.get("replaces_check_id")
            if replaces is not None:
                require_id(replaces, f"{c_label}.replaces_check_id")
            entrypoint = check.get("entrypoint")
            if entrypoint is not None:
                if not isinstance(entrypoint, str) or not entrypoint.strip():
                    raise HarnessError(f"{c_label}.entrypoint must be a non-empty string or null")
                validate_relative_posix_path(entrypoint)
            tool = check.get("tool")
            if tool is not None:
                if not isinstance(tool, str) or not tool.strip():
                    raise HarnessError(f"{c_label}.tool must be a non-empty string or null")
            verifier = check.get("verifier_entrypoint")
            if verifier is not None:
                if not isinstance(verifier, str) or not verifier.strip():
                    raise HarnessError(f"{c_label}.verifier_entrypoint must be a non-empty string or null")
                validate_relative_posix_path(verifier)
            validate_verifier_command_form(argv, verifier, f"{c_label}.command.argv")

    policy = data.get("snapshot_policy")
    fields(policy, {"include", "exclude"}, {"include", "exclude"}, "journey.snapshot_policy")
    for key in ("include", "exclude"):
        val = policy.get(key)
        if not isinstance(val, list) or not all(isinstance(x, str) and x for x in val):
            raise HarnessError(f"journey.snapshot_policy.{key} must be a string array")


def validate_manifest_schema(data: dict[str, Any]) -> None:
    req = {
        "schema_version",
        "run_id",
        "retry_of_run_id",
        "synthetic",
        "created_at",
        "harness_version",
        "harness_sha256",
        "journey",
        "rubric_sha256",
        "trusted_checks_sha256",
        "initial_snapshot_hash",
        "snapshot_policy",
        "variants",
        "packets",
    }
    fields(data, req, req, "manifest")
    if data.get("schema_version") != MANIFEST_SCHEMA:
        raise HarnessError(f"Manifest schema_version must be {MANIFEST_SCHEMA!r}")
    run_id = data.get("run_id")
    if not isinstance(run_id, str) or not HEX32_RE.fullmatch(run_id):
        raise HarnessError(f"manifest.run_id must be 32 lowercase hex chars; got {run_id!r}")
    retry_of = data.get("retry_of_run_id")
    if retry_of is not None and (not isinstance(retry_of, str) or not HEX32_RE.fullmatch(retry_of)):
        raise HarnessError(f"manifest.retry_of_run_id must be 32 hex chars or null; got {retry_of!r}")
    if type(data.get("synthetic")) is not bool:
        raise HarnessError("manifest.synthetic must be a boolean")
    if not isinstance(data.get("created_at"), str) or not data["created_at"].strip():
        raise HarnessError("manifest.created_at must be non-empty string")
    if not isinstance(data.get("harness_version"), str) or not data["harness_version"].strip():
        raise HarnessError("manifest.harness_version must be non-empty string")
    require_sha256(data.get("harness_sha256"), "manifest.harness_sha256")
    require_sha256(data.get("rubric_sha256"), "manifest.rubric_sha256")
    require_sha256(data.get("trusted_checks_sha256"), "manifest.trusted_checks_sha256")
    require_sha256(data.get("initial_snapshot_hash"), "manifest.initial_snapshot_hash")

    journey = data.get("journey")
    fields(journey, {"id", "sha256", "path"}, {"id", "sha256", "path"}, "manifest.journey")
    require_id(journey.get("id"), "manifest.journey.id")
    require_sha256(journey.get("sha256"), "manifest.journey.sha256")
    if not isinstance(journey.get("path"), str) or not journey["path"].strip():
        raise HarnessError("manifest.journey.path must be non-empty string")

    policy = data.get("snapshot_policy")
    fields(policy, {"include", "exclude"}, {"include", "exclude"}, "manifest.snapshot_policy")
    for key in ("include", "exclude"):
        val = policy.get(key)
        if not isinstance(val, list) or not all(isinstance(x, str) and x for x in val):
            raise HarnessError(f"manifest.snapshot_policy.{key} must be a string array")

    variants = data.get("variants")
    if not isinstance(variants, list) or not variants:
        raise HarnessError("manifest.variants must be a non-empty array")
    for idx, v in enumerate(variants):
        label = f"manifest.variants[{idx}]"
        fields(v, {"id", "skills"}, {"id", "skills"}, label)
        if v.get("id") not in VARIANT_IDS:
            raise HarnessError(f"{label}.id must be in {VARIANT_IDS}")
        skills = v.get("skills")
        if not isinstance(skills, list):
            raise HarnessError(f"{label}.skills must be an array")
        for s_idx, skill in enumerate(skills):
            s_label = f"{label}.skills[{s_idx}]"
            fields(skill, {"name", "path", "sha256"}, {"name", "path", "sha256"}, s_label)
            require_id(skill.get("name"), f"{s_label}.name")
            require_sha256(skill.get("sha256"), f"{s_label}.sha256")

    packets = data.get("packets")
    if not isinstance(packets, list):
        raise HarnessError("manifest.packets must be an array")
    packet_ids: set[str] = set()
    identities: set[tuple[str, str, str, str]] = set()
    for idx, p in enumerate(packets):
        label = f"manifest.packets[{idx}]"
        fields(
            p,
            {"packet_id", "journey_id", "variant_id", "repetition_id", "checkpoint_id", "order", "path"},
            {"packet_id", "journey_id", "variant_id", "repetition_id", "checkpoint_id", "order", "path"},
            label,
        )
        pid = p.get("packet_id")
        if not isinstance(pid, str) or not HEX16_RE.fullmatch(pid) or pid in packet_ids:
            raise HarnessError(f"{label}.packet_id must be unique 16 hex chars; got {pid!r}")
        packet_ids.add(pid)
        jid = require_id(p.get("journey_id"), f"{label}.journey_id")
        vid = p.get("variant_id")
        if vid not in VARIANT_IDS:
            raise HarnessError(f"{label}.variant_id must be in {VARIANT_IDS}")
        rep = p.get("repetition_id")
        if not isinstance(rep, str) or not REP_RE.fullmatch(rep):
            raise HarnessError(f"{label}.repetition_id must match {REP_RE.pattern!r}; got {rep!r}")
        cid = p.get("checkpoint_id")
        if cid not in CHECKPOINT_IDS:
            raise HarnessError(f"{label}.checkpoint_id must be in {CHECKPOINT_IDS}")
        order = p.get("order")
        if type(order) is not int or order not in (1, 2, 3, 4) or CHECKPOINT_IDS[order - 1] != cid:
            raise HarnessError(f"{label}.order must be integer 1..4 corresponding to {cid}")
        identity = (jid, vid, rep, cid)
        if identity in identities:
            raise HarnessError(f"Duplicate packet identity in manifest: {identity}")
        identities.add(identity)
        if not isinstance(p.get("path"), str) or not p["path"].strip():
            raise HarnessError(f"{label}.path must be non-empty string")


def validate_checkpoint_record_schema(data: dict[str, Any]) -> None:
    req = {
        "schema_version",
        "run_id",
        "journey_id",
        "variant_id",
        "repetition_id",
        "checkpoint_id",
        "order",
        "parent_checkpoint_id",
        "parent_snapshot_hash",
        "candidate_snapshot_hash",
        "lifecycle_status",
        "execution_status",
        "measurement_validity",
        "output_quality",
        "synthetic",
    }
    allowed = req | {"per_checkpoint_diff_sha256", "cumulative_diff_sha256", "check_results", "usage"}
    fields(data, allowed, req, "checkpoint_record")

    if data.get("schema_version") != CHECKPOINT_RECORD_SCHEMA:
        raise HarnessError(f"checkpoint_record.schema_version must be {CHECKPOINT_RECORD_SCHEMA!r}")
    run_id = data.get("run_id")
    if not isinstance(run_id, str) or not HEX32_RE.fullmatch(run_id):
        raise HarnessError(f"checkpoint_record.run_id must be 32 hex chars; got {run_id!r}")
    require_id(data.get("journey_id"), "checkpoint_record.journey_id")
    if data.get("variant_id") not in VARIANT_IDS:
        raise HarnessError(f"checkpoint_record.variant_id must be in {VARIANT_IDS}")
    rep = data.get("repetition_id")
    if not isinstance(rep, str) or not REP_RE.fullmatch(rep):
        raise HarnessError(f"checkpoint_record.repetition_id must match {REP_RE.pattern!r}; got {rep!r}")
    cid = data.get("checkpoint_id")
    if cid not in CHECKPOINT_IDS:
        raise HarnessError(f"checkpoint_record.checkpoint_id must be in {CHECKPOINT_IDS}")
    order = data.get("order")
    if type(order) is not int or order not in (1, 2, 3, 4):
        raise HarnessError("checkpoint_record.order must be integer 1..4")
    if CHECKPOINT_IDS[order - 1] != cid:
        raise HarnessError(f"checkpoint_record.order {order} does not match checkpoint_id {cid!r}")

    parent_cid = data.get("parent_checkpoint_id")
    if order == 1:
        if parent_cid is not None:
            raise HarnessError("checkpoint_record CP1 parent_checkpoint_id must be null")
    else:
        expected_parent_cid = CHECKPOINT_IDS[order - 2]
        if parent_cid != expected_parent_cid:
            raise HarnessError(
                f"checkpoint_record CP{order} parent_checkpoint_id must be {expected_parent_cid!r}; got {parent_cid!r}"
            )

    parent_hash = data.get("parent_snapshot_hash")
    if parent_hash is not None:
        require_sha256(parent_hash, "checkpoint_record.parent_snapshot_hash")

    cand_hash = data.get("candidate_snapshot_hash")
    if cand_hash is not None:
        require_sha256(cand_hash, "checkpoint_record.candidate_snapshot_hash")

    l_status = data.get("lifecycle_status")
    if l_status not in LIFECYCLE_STATUSES:
        raise HarnessError(f"checkpoint_record.lifecycle_status must be in {LIFECYCLE_STATUSES}; got {l_status!r}")

    # Consistency checks for lifecycle states
    if l_status == "EXECUTING" and parent_hash is None:
        raise HarnessError("checkpoint_record in EXECUTING status must have parent_snapshot_hash")
    if l_status == "PREPARED":
        if cand_hash is not None:
            raise HarnessError("checkpoint_record in PREPARED status cannot have candidate_snapshot_hash")
        if data.get("execution_status") is not None:
            raise HarnessError("checkpoint_record in PREPARED status cannot have execution_status")
        if data.get("output_quality") is not None:
            raise HarnessError("checkpoint_record in PREPARED status cannot have output_quality")

    e_status = data.get("execution_status")
    if e_status is not None and e_status not in EXECUTION_STATUSES:
        raise HarnessError(f"checkpoint_record.execution_status must be null or in {EXECUTION_STATUSES}; got {e_status!r}")

    m_val = data.get("measurement_validity")
    if m_val is not None and m_val not in MEASUREMENT_VALIDITIES:
        raise HarnessError(f"checkpoint_record.measurement_validity must be null or in {MEASUREMENT_VALIDITIES}; got {m_val!r}")

    o_qual = data.get("output_quality")
    if o_qual is not None and o_qual not in OUTPUT_QUALITIES:
        raise HarnessError(f"checkpoint_record.output_quality must be null or in {OUTPUT_QUALITIES}; got {o_qual!r}")

    # Contradictory states check
    if o_qual == "PASS" and (e_status in ("TIMEOUT", "BUDGET_EXHAUSTED", "INFRA_ERROR", "BLOCKED_BY_PREDECESSOR") or m_val == "EVALUATION_INVALID"):
        raise HarnessError("Contradictory checkpoint record: output_quality cannot be PASS with failed execution or invalid measurement")

    if type(data.get("synthetic")) is not bool:
        raise HarnessError("checkpoint_record.synthetic must be a boolean")

    for diff_field in ("per_checkpoint_diff_sha256", "cumulative_diff_sha256"):
        val = data.get(diff_field)
        if val is not None:
            require_sha256(val, f"checkpoint_record.{diff_field}")

    results = data.get("check_results")
    if results is not None:
        if not isinstance(results, list):
            raise HarnessError("checkpoint_record.check_results must be a list or null")
        for idx, res in enumerate(results):
            label = f"checkpoint_record.check_results[{idx}]"
            fields(
                res,
                {"id", "type", "exit_code", "timed_out", "duration_seconds", "status", "message", "stdout", "stderr"},
                {"id", "type", "exit_code", "timed_out", "duration_seconds"},
                label,
            )
            if not isinstance(res.get("id"), str) or not res["id"].strip():
                raise HarnessError(f"{label}.id must be non-empty string")
            if res.get("type") not in CHECK_TYPES:
                raise HarnessError(f"{label}.type must be in {CHECK_TYPES}")
            code = res.get("exit_code")
            if code is not None and type(code) is not int:
                raise HarnessError(f"{label}.exit_code must be an integer or null")
            if type(res.get("timed_out")) is not bool:
                raise HarnessError(f"{label}.timed_out must be boolean")
            dur = res.get("duration_seconds")
            if not isinstance(dur, (int, float)) or isinstance(dur, bool) or not math.isfinite(dur) or dur < 0:
                raise HarnessError(f"{label}.duration_seconds must be a non-negative finite number")
            st = res.get("status")
            if st is not None and st not in CHECK_STATUSES:
                raise HarnessError(f"{label}.status must be null or in {CHECK_STATUSES}; got {st!r}")
            msg = res.get("message")
            if msg is not None and not isinstance(msg, str):
                raise HarnessError(f"{label}.message must be a string or null")
            for stream_name in ("stdout", "stderr"):
                stream_val = res.get(stream_name)
                if stream_val is not None and not isinstance(stream_val, str):
                    raise HarnessError(f"{label}.{stream_name} must be a string or null")

    usage = data.get("usage")
    if usage is not None:
        fields(usage, {"tokens_input", "tokens_output", "wall_time_seconds", "observed_artifacts"}, set(), "checkpoint_record.usage")
        for int_field in ("tokens_input", "tokens_output", "observed_artifacts"):
            val = usage.get(int_field)
            if val is not None and (type(val) is not int or val < 0):
                raise HarnessError(f"checkpoint_record.usage.{int_field} must be a non-negative integer or null")
        wall = usage.get("wall_time_seconds")
        if wall is not None and (not isinstance(wall, (int, float)) or isinstance(wall, bool) or not math.isfinite(wall) or wall < 0):
            raise HarnessError("checkpoint_record.usage.wall_time_seconds must be a non-negative number or null")


def validate_pre_check_artifact_schema(data: dict[str, Any]) -> None:
    req = {
        "schema_version",
        "run_id",
        "packet_id",
        "journey_id",
        "variant_id",
        "repetition_id",
        "checkpoint_id",
        "order",
        "phase",
        "parent_snapshot_hash",
        "check_results",
        "pre_check_passed",
        "recorded_at",
    }
    fields(data, req, req, "pre_check_artifact")
    if data.get("schema_version") != PRE_CHECK_ARTIFACT_SCHEMA:
        raise HarnessError(f"pre_check_artifact.schema_version must be {PRE_CHECK_ARTIFACT_SCHEMA!r}")
    run_id = data.get("run_id")
    if not isinstance(run_id, str) or not HEX32_RE.fullmatch(run_id):
        raise HarnessError(f"pre_check_artifact.run_id must be 32 hex chars; got {run_id!r}")
    packet_id = data.get("packet_id")
    if not isinstance(packet_id, str) or not HEX16_RE.fullmatch(packet_id):
        raise HarnessError(f"pre_check_artifact.packet_id must be 16 hex chars; got {packet_id!r}")
    require_id(data.get("journey_id"), "pre_check_artifact.journey_id")
    if data.get("variant_id") not in VARIANT_IDS:
        raise HarnessError(f"pre_check_artifact.variant_id must be in {VARIANT_IDS}")
    rep = data.get("repetition_id")
    if not isinstance(rep, str) or not REP_RE.fullmatch(rep):
        raise HarnessError(f"pre_check_artifact.repetition_id must match {REP_RE.pattern!r}; got {rep!r}")
    cid = data.get("checkpoint_id")
    if cid not in CHECKPOINT_IDS:
        raise HarnessError(f"pre_check_artifact.checkpoint_id must be in {CHECKPOINT_IDS}")
    order = data.get("order")
    if type(order) is not int or order not in (1, 2, 3, 4) or CHECKPOINT_IDS[order - 1] != cid:
        raise HarnessError("pre_check_artifact.order must be integer 1..4 matching checkpoint_id")
    if data.get("phase") != "pre":
        raise HarnessError(f"pre_check_artifact.phase must be 'pre'; got {data.get('phase')!r}")
    require_sha256(data.get("parent_snapshot_hash"), "pre_check_artifact.parent_snapshot_hash")
    if type(data.get("pre_check_passed")) is not bool:
        raise HarnessError("pre_check_artifact.pre_check_passed must be boolean")
    if not isinstance(data.get("recorded_at"), str) or not data["recorded_at"].strip():
        raise HarnessError("pre_check_artifact.recorded_at must be non-empty string")

    results = data.get("check_results")
    if not isinstance(results, list):
        raise HarnessError("pre_check_artifact.check_results must be a list")
    for idx, res in enumerate(results):
        label = f"pre_check_artifact.check_results[{idx}]"
        fields(
            res,
            {"id", "type", "exit_code", "timed_out", "duration_seconds", "status", "message", "stdout", "stderr"},
            {"id", "type", "exit_code", "timed_out", "duration_seconds"},
            label,
        )
        if not isinstance(res.get("id"), str) or not res["id"].strip():
            raise HarnessError(f"{label}.id must be non-empty string")
        if res.get("type") not in CHECK_TYPES:
            raise HarnessError(f"{label}.type must be in {CHECK_TYPES}")
        code = res.get("exit_code")
        if code is not None and type(code) is not int:
            raise HarnessError(f"{label}.exit_code must be an integer or null")
        if type(res.get("timed_out")) is not bool:
            raise HarnessError(f"{label}.timed_out must be boolean")
        dur = res.get("duration_seconds")
        if not isinstance(dur, (int, float)) or isinstance(dur, bool) or not math.isfinite(dur) or dur < 0:
            raise HarnessError(f"{label}.duration_seconds must be a non-negative finite number")
        st = res.get("status")
        if st is not None and st not in CHECK_STATUSES:
            raise HarnessError(f"{label}.status must be null or in {CHECK_STATUSES}; got {st!r}")


def scrub_text(
    text: str,
    known_paths: list[str] | None = None,
    known_markers: dict[str, str] | list[str] | None = None,
) -> str:
    r"""Scrub known absolute paths, runner/workspace paths, and secret markers from text.

    Both POSIX and Windows path representations (with either / or \) are matched and replaced.
    """
    if not text:
        return ""

    scrubbed = text

    # 1. Scrub known paths FIRST so full paths are scrubbed before individual tokens
    if known_paths:
        sorted_paths = sorted([p for p in known_paths if p and p.strip()], key=len, reverse=True)
        for p in sorted_paths:
            norm_p_fwd = p.replace("\\", "/")
            norm_p_back = p.replace("/", "\\")
            patterns = {p, norm_p_fwd, norm_p_back}
            for pat in patterns:
                if pat:
                    scrubbed = scrubbed.replace(pat, "[private path]")

    # 2. Scrub custom markers if provided
    if known_markers:
        if isinstance(known_markers, dict):
            sorted_markers = sorted(known_markers.items(), key=lambda x: len(x[0]), reverse=True)
            for marker, replacement in sorted_markers:
                if marker:
                    if re.fullmatch(r"[A-Za-z0-9_]+", marker):
                        scrubbed = re.sub(r"\b" + re.escape(marker) + r"\b", replacement, scrubbed)
                    else:
                        scrubbed = scrubbed.replace(marker, replacement)
        elif isinstance(known_markers, list):
            sorted_markers_list = sorted([m for m in known_markers if m], key=len, reverse=True)
            for marker in sorted_markers_list:
                if re.fullmatch(r"[A-Za-z0-9_]+", marker):
                    scrubbed = re.sub(r"\b" + re.escape(marker) + r"\b", "[REDACTED]", scrubbed)
                else:
                    scrubbed = scrubbed.replace(marker, "[REDACTED]")

    return scrubbed


def applicable_dimensions_for_checkpoint(
    checkpoint_id: str,
    rubric: dict[str, Any] | None = None,
) -> list[str]:
    """Return the list of applicable dimension IDs for a given checkpoint.

    If a frozen rubric is provided, reads from the rubric definition; otherwise defaults
    to the canonical dimensions.
    """
    if rubric is not None:
        dims = []
        for dim in rubric.get("dimensions", []):
            applicable_cps = dim.get("applicable_checkpoints", [])
            if checkpoint_id in applicable_cps:
                dims.append(dim["id"])
        return dims

    dims = list(BASE_DIMENSION_IDS)
    if checkpoint_id == "CP3_EVOLUTION":
        dims.extend(CP3_EXTRA_DIMENSION_IDS)
    elif checkpoint_id == "CP4_CONTINUITY":
        dims.extend(CP4_EXTRA_DIMENSION_IDS)
    return dims


def applicable_bars_for_checkpoint(
    checkpoint_id: str,
    rubric: dict[str, Any] | None = None,
) -> list[str]:
    """Return the list of required bar IDs for a given checkpoint."""
    if rubric is not None:
        bars = []
        for bar in rubric.get("required_bars", []):
            applicable_cps = bar.get("applicable_checkpoints", [])
            if checkpoint_id in applicable_cps:
                bars.append(bar["id"])
        return bars

    common_bars = ["outcome", "no_unauthorized_behavior_change", "scope_bounded", "contract_aligned"]
    if checkpoint_id == "CP3_EVOLUTION":
        common_bars.append("evolution_coherent")
    elif checkpoint_id == "CP4_CONTINUITY":
        common_bars.append("takeover_effective")
    return common_bars


def validate_judge_packet_schema(data: dict[str, Any]) -> None:
    req = {
        "schema_version",
        "artifact_id",
        "created_at",
        "checkpoint_id",
        "order",
        "parent_snapshot_hash",
        "candidate_snapshot_hash",
        "per_checkpoint_diff_sha256",
        "cumulative_diff_sha256",
    }
    fields(data, req, req, "judge_packet")
    if data.get("schema_version") != JUDGE_PACKET_SCHEMA:
        raise HarnessError(f"judge_packet.schema_version must be {JUDGE_PACKET_SCHEMA!r}")
    art_id = data.get("artifact_id")
    if not isinstance(art_id, str) or not HEX16_RE.fullmatch(art_id):
        raise HarnessError(f"judge_packet.artifact_id must be 16 hex chars; got {art_id!r}")
    if not isinstance(data.get("created_at"), str) or not data["created_at"].strip():
        raise HarnessError("judge_packet.created_at must be non-empty string")
    cid = data.get("checkpoint_id")
    if cid not in CHECKPOINT_IDS:
        raise HarnessError(f"judge_packet.checkpoint_id must be in {CHECKPOINT_IDS}; got {cid!r}")
    order = data.get("order")
    if type(order) is not int or order not in (1, 2, 3, 4) or CHECKPOINT_IDS[order - 1] != cid:
        raise HarnessError(f"judge_packet.order must be integer 1..4 matching {cid!r}; got {order!r}")
    require_sha256(data.get("parent_snapshot_hash"), "judge_packet.parent_snapshot_hash")
    require_sha256(data.get("candidate_snapshot_hash"), "judge_packet.candidate_snapshot_hash")
    require_sha256(data.get("per_checkpoint_diff_sha256"), "judge_packet.per_checkpoint_diff_sha256")
    require_sha256(data.get("cumulative_diff_sha256"), "judge_packet.cumulative_diff_sha256")


def validate_judge_index_schema(data: dict[str, Any]) -> None:
    """Validate judge index document matching repo-foundation-harness/judge-index-v1."""
    req = {
        "schema_version",
        "run_id",
        "rubric_sha256",
        "artifacts",
    }
    fields(data, req, req, "judge_index")
    if data.get("schema_version") != JUDGE_INDEX_SCHEMA:
        raise HarnessError(f"judge_index.schema_version must be {JUDGE_INDEX_SCHEMA!r}")
    run_id = data.get("run_id")
    if not isinstance(run_id, str) or not HEX32_RE.fullmatch(run_id):
        raise HarnessError(f"judge_index.run_id must be 32 hex chars; got {run_id!r}")
    require_sha256(data.get("rubric_sha256"), "judge_index.rubric_sha256")

    artifacts = data.get("artifacts")
    if not isinstance(artifacts, list):
        raise HarnessError("judge_index.artifacts must be an array")

    valid_statuses = {"READY", "BLOCKED", "MISSING", "INVALID", "INCOMPLETE"}
    seen_artifact_ids: set[str] = set()
    seen_packet_ids: set[str] = set()
    seen_samples: set[tuple[str, str, int, str]] = set()

    for idx, art in enumerate(artifacts):
        label = f"judge_index.artifacts[{idx}]"
        art_req = {
            "artifact_id",
            "packet_id",
            "journey_id",
            "variant_id",
            "repetition_id",
            "checkpoint_id",
            "order",
            "path",
            "status",
        }
        art_allowed = art_req | {"packet_sha256", "status_reason"}
        fields(art, art_allowed, art_req, label)
        aid = art.get("artifact_id")
        if not isinstance(aid, str) or not HEX16_RE.fullmatch(aid):
            raise HarnessError(f"{label}.artifact_id must be 16 hex chars; got {aid!r}")
        if aid in seen_artifact_ids:
            raise HarnessError(f"Duplicate artifact_id {aid!r} in judge_index")
        seen_artifact_ids.add(aid)

        pid = require_id(art.get("packet_id"), f"{label}.packet_id")
        if pid in seen_packet_ids:
            raise HarnessError(f"Duplicate packet_id {pid!r} in judge_index")
        seen_packet_ids.add(pid)

        jid = require_id(art.get("journey_id"), f"{label}.journey_id")
        vid = art.get("variant_id")
        if vid not in VARIANT_IDS:
            raise HarnessError(f"{label}.variant_id must be in {VARIANT_IDS}; got {vid!r}")
        rep = art.get("repetition_id")
        if type(rep) is not int or rep < 1:
            raise HarnessError(f"{label}.repetition_id must be integer >= 1; got {rep!r}")
        cid = art.get("checkpoint_id")
        if cid not in CHECKPOINT_IDS:
            raise HarnessError(f"{label}.checkpoint_id must be in {CHECKPOINT_IDS}; got {cid!r}")
        order = art.get("order")
        if type(order) is not int or order not in (1, 2, 3, 4) or CHECKPOINT_IDS[order - 1] != cid:
            raise HarnessError(f"{label}.order must be integer 1..4 matching {cid!r}; got {order!r}")

        sample_key = (jid, vid, rep, cid)
        if sample_key in seen_samples:
            raise HarnessError(f"Duplicate sample {sample_key} in judge_index")
        seen_samples.add(sample_key)

        path_val = art.get("path")
        if not isinstance(path_val, str) or not path_val.strip():
            raise HarnessError(f"{label}.path must be non-empty string")

        status = art.get("status")
        if status not in valid_statuses:
            raise HarnessError(f"{label}.status must be in {valid_statuses}; got {status!r}")
        if "packet_sha256" in art and art["packet_sha256"] is not None:
            require_sha256(art["packet_sha256"], f"{label}.packet_sha256")
        if status == "READY" and not art.get("packet_sha256"):
            raise HarnessError(f"{label} with READY status must have packet_sha256")
        if "status_reason" in art and not isinstance(art["status_reason"], str):
            raise HarnessError(f"{label}.status_reason must be string")


def validate_rubric_schema(data: dict[str, Any]) -> None:
    req = {
        "schema_version",
        "rubric_id",
        "dimensions",
        "required_bars",
        "hard_failure_definitions",
    }
    fields(data, req, req, "rubric")
    if data.get("schema_version") != RUBRIC_SCHEMA:
        raise HarnessError(f"rubric.schema_version must be {RUBRIC_SCHEMA!r}")
    require_id(data.get("rubric_id"), "rubric.rubric_id")

    dimensions = data.get("dimensions")
    if not isinstance(dimensions, list) or not dimensions:
        raise HarnessError("rubric.dimensions must be a non-empty array")
    seen_dims: set[str] = set()
    for idx, dim in enumerate(dimensions):
        label = f"rubric.dimensions[{idx}]"
        fields(dim, {"id", "title", "description", "applicable_checkpoints", "anchors"}, {"id", "title", "description", "applicable_checkpoints", "anchors"}, label)
        did = require_id(dim.get("id"), f"{label}.id")
        if did in seen_dims:
            raise HarnessError(f"Duplicate dimension id in rubric: {did!r}")
        seen_dims.add(did)
        for s_key in ("title", "description"):
            if not isinstance(dim.get(s_key), str) or not dim[s_key].strip():
                raise HarnessError(f"{label}.{s_key} must be non-empty string")
        cps = dim.get("applicable_checkpoints")
        if not isinstance(cps, list) or not cps or not all(c in CHECKPOINT_IDS for c in cps):
            raise HarnessError(f"{label}.applicable_checkpoints must be a non-empty array of valid checkpoint IDs")
        anchors = dim.get("anchors")
        fields(anchors, {"0", "1", "2", "3", "4"}, {"0", "1", "2", "3", "4"}, f"{label}.anchors")
        for a_key in ("0", "1", "2", "3", "4"):
            if not isinstance(anchors.get(a_key), str) or not anchors[a_key].strip():
                raise HarnessError(f"{label}.anchors[{a_key!r}] must be non-empty string")

    bars = data.get("required_bars")
    if not isinstance(bars, list) or not bars:
        raise HarnessError("rubric.required_bars must be a non-empty array")
    seen_bars: set[str] = set()
    for idx, bar in enumerate(bars):
        label = f"rubric.required_bars[{idx}]"
        fields(bar, {"id", "title", "description", "applicable_checkpoints"}, {"id", "title", "description", "applicable_checkpoints"}, label)
        bid = require_id(bar.get("id"), f"{label}.id")
        if bid in seen_bars:
            raise HarnessError(f"Duplicate required bar id in rubric: {bid!r}")
        seen_bars.add(bid)
        for s_key in ("title", "description"):
            if not isinstance(bar.get(s_key), str) or not bar[s_key].strip():
                raise HarnessError(f"{label}.{s_key} must be non-empty string")
        cps = bar.get("applicable_checkpoints")
        if not isinstance(cps, list) or not cps or not all(c in CHECKPOINT_IDS for c in cps):
            raise HarnessError(f"{label}.applicable_checkpoints must be a non-empty array of valid checkpoint IDs")

    hard_fails = data.get("hard_failure_definitions")
    if not isinstance(hard_fails, list) or not hard_fails:
        raise HarnessError("rubric.hard_failure_definitions must be a non-empty array")
    seen_hf: set[str] = set()
    hard_id_re = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9._-]{0,79}$")
    for idx, hf in enumerate(hard_fails):
        label = f"rubric.hard_failure_definitions[{idx}]"
        fields(hf, {"id", "description"}, {"id", "description"}, label)
        hfid = hf.get("id")
        if not isinstance(hfid, str) or not hard_id_re.fullmatch(hfid):
            raise HarnessError(f"{label}.id must match {hard_id_re.pattern!r}; got {hfid!r}")
        if hfid.lower() in seen_hf:
            raise HarnessError(f"Duplicate hard failure id in rubric: {hfid!r}")
        seen_hf.add(hfid.lower())
        if not isinstance(hf.get("description"), str) or not hf["description"].strip():
            raise HarnessError(f"{label}.description must be non-empty string")


def validate_judgment_schema(data: dict[str, Any]) -> None:
    req = {
        "schema_version",
        "artifact_id",
        "verdict",
        "bar_evidence",
        "hard_failures",
        "dimensions",
        "confidence",
        "notes",
    }
    fields(data, req | {"invalid_reasons"}, req, "judgment")
    if data.get("schema_version") != JUDGMENT_SCHEMA:
        raise HarnessError(f"judgment.schema_version must be {JUDGMENT_SCHEMA!r}")
    aid = data.get("artifact_id")
    if not isinstance(aid, str) or not HEX16_RE.fullmatch(aid):
        raise HarnessError(f"judgment.artifact_id must be 16 hex chars; got {aid!r}")

    verdict = data.get("verdict")
    if verdict not in JUDGMENT_VERDICTS:
        raise HarnessError(f"judgment.verdict must be one of {JUDGMENT_VERDICTS}; got {verdict!r}")

    bars = data.get("bar_evidence")
    if not isinstance(bars, list):
        raise HarnessError("judgment.bar_evidence must be an array")
    seen_bars: set[str] = set()
    for idx, bar in enumerate(bars):
        label = f"judgment.bar_evidence[{idx}]"
        fields(bar, {"id", "claim", "verdict", "evidence"}, {"id", "claim", "verdict", "evidence"}, label)
        bid = require_id(bar.get("id"), f"{label}.id")
        if bid in seen_bars:
            raise HarnessError(f"Duplicate bar in bar_evidence: {bid!r}")
        seen_bars.add(bid)
        for s_key in ("claim", "evidence"):
            if not isinstance(bar.get(s_key), str) or not bar[s_key].strip():
                raise HarnessError(f"{label}.{s_key} must be non-empty string")
        b_verdict = bar.get("verdict")
        if b_verdict not in ("pass", "fail"):
            raise HarnessError(f"{label}.verdict must be 'pass' or 'fail'; got {b_verdict!r}")

    hard_failures = data.get("hard_failures")
    if not isinstance(hard_failures, list) or not all(isinstance(x, str) and x.strip() for x in hard_failures):
        raise HarnessError("judgment.hard_failures must be a list of non-empty strings")

    dimensions = data.get("dimensions")
    if not isinstance(dimensions, list):
        raise HarnessError("judgment.dimensions must be an array")
    seen_dims: set[str] = set()
    for idx, dim in enumerate(dimensions):
        label = f"judgment.dimensions[{idx}]"
        fields(dim, {"id", "score", "reason", "evidence"}, {"id", "score"}, label)
        did = require_id(dim.get("id"), f"{label}.id")
        if did in seen_dims:
            raise HarnessError(f"Duplicate dimension in judgment.dimensions: {did!r}")
        seen_dims.add(did)
        score = dim.get("score")
        if score is None:
            # Score is undetermined: reason is required
            reason = dim.get("reason")
            if not isinstance(reason, str) or not reason.strip():
                raise HarnessError(f"{label}.reason must be non-empty string when score is null")
        else:
            # Score must be integer 0..4, reject bool, float, NaN, inf
            if type(score) is not int or score < 0 or score > 4:
                raise HarnessError(f"{label}.score must be an integer between 0 and 4 or null; got {score!r}")
            evidence = dim.get("evidence")
            if not isinstance(evidence, list) or not evidence or not all(isinstance(x, str) and x.strip() for x in evidence):
                raise HarnessError(f"{label}.evidence must be a non-empty list of strings when score is present")

    if verdict == "invalid":
        inv_reasons = data.get("invalid_reasons")
        if not isinstance(inv_reasons, list) or not inv_reasons or not all(isinstance(x, str) and x.strip() for x in inv_reasons):
            raise HarnessError("judgment with verdict 'invalid' must provide non-empty invalid_reasons list")

    conf = data.get("confidence")
    if conf not in ("high", "medium", "low"):
        raise HarnessError(f"judgment.confidence must be 'high', 'medium', or 'low'; got {conf!r}")
    if not isinstance(data.get("notes"), str):
        raise HarnessError("judgment.notes must be a string")


def validate_rational_number_schema(data: Any, label: str = "rational") -> None:
    """Validate that data conforms to canonical rational number object encoding."""
    if not isinstance(data, dict):
        raise HarnessError(f"{label} must be an object; got {type(data).__name__}")
    fields(data, {"numerator", "denominator", "display", "decimal_string"}, {"numerator", "denominator", "display", "decimal_string"}, label)
    num = data.get("numerator")
    den = data.get("denominator")
    if type(num) is not int or isinstance(num, bool):
        raise HarnessError(f"{label}.numerator must be an integer (reject bool); got {num!r}")
    if type(den) is not int or isinstance(den, bool) or den <= 0:
        raise HarnessError(f"{label}.denominator must be a strictly positive integer (reject bool); got {den!r}")
    if not isinstance(data.get("display"), str) or not data["display"].strip():
        raise HarnessError(f"{label}.display must be a non-empty string")
    if not isinstance(data.get("decimal_string"), str) or not data["decimal_string"].strip():
        raise HarnessError(f"{label}.decimal_string must be a non-empty string")


def fraction_to_json(f: Fraction, max_decimal_places: int = 6) -> dict[str, Any]:
    """Convert a Fraction to a canonical JSON rational object."""
    if not isinstance(f, Fraction):
        raise HarnessError(f"Expected Fraction, got {type(f).__name__}")
    canonical = Fraction(f.numerator, f.denominator)
    num = canonical.numerator
    den = canonical.denominator
    display = f"{num}" if den == 1 else f"{num}/{den}"

    temp_den = den
    while temp_den % 2 == 0:
        temp_den //= 2
    while temp_den % 5 == 0:
        temp_den //= 5

    sign = "-" if (num < 0) else ""
    abs_num = abs(num)
    int_part = abs_num // den
    rem = abs_num % den

    if temp_den == 1:
        if rem == 0:
            dec_str = f"{sign}{int_part}.0"
        else:
            digits = []
            while rem > 0 and len(digits) < 20:
                rem *= 10
                digits.append(str(rem // den))
                rem %= den
            dec_str = f"{sign}{int_part}.{''.join(digits)}"
    else:
        digits = []
        for _ in range(max_decimal_places):
            rem *= 10
            digits.append(str(rem // den))
            rem %= den
        dec_str = f"~{sign}{int_part}.{''.join(digits)}"

    return {
        "numerator": num,
        "denominator": den,
        "display": display,
        "decimal_string": dec_str,
    }


def json_to_fraction(data: Any, label: str = "rational") -> Fraction:
    """Convert a canonical JSON rational object to a Fraction."""
    if isinstance(data, Fraction):
        return data
    if not isinstance(data, dict):
        raise HarnessError(f"{label} must be an object; got {type(data).__name__}")
    validate_rational_number_schema(data, label)
    return Fraction(data["numerator"], data["denominator"])


def validate_scoring_policy_schema(data: dict[str, Any]) -> None:
    """Validate scoring policy configuration matching repo-foundation-harness/scoring-policy-v1."""
    fields(
        data,
        {"schema_version", "policy_id", "description", "checkpoint_weights", "optional_thresholds", "pricing"},
        {"schema_version", "policy_id", "checkpoint_weights"},
        "scoring_policy",
    )
    if data.get("schema_version") != SCORING_POLICY_SCHEMA:
        raise HarnessError(f"scoring_policy.schema_version must be {SCORING_POLICY_SCHEMA!r}")
    require_id(data.get("policy_id"), "scoring_policy.policy_id")
    if "description" in data and not isinstance(data["description"], str):
        raise HarnessError("scoring_policy.description must be a string")

    weights = data.get("checkpoint_weights")
    if not isinstance(weights, dict):
        raise HarnessError("scoring_policy.checkpoint_weights must be an object")
    fields(weights, set(CHECKPOINT_IDS), set(CHECKPOINT_IDS), "scoring_policy.checkpoint_weights")

    total_weight = Fraction(0, 1)
    for cid in CHECKPOINT_IDS:
        w_obj = weights[cid]
        validate_rational_number_schema(w_obj, f"scoring_policy.checkpoint_weights.{cid}")
        w_frac = json_to_fraction(w_obj, f"scoring_policy.checkpoint_weights.{cid}")
        if w_frac < 0:
            raise HarnessError(f"scoring_policy.checkpoint_weights.{cid} cannot be negative; got {w_frac}")
        total_weight += w_frac

    if total_weight != Fraction(1, 1):
        raise HarnessError(f"scoring_policy.checkpoint_weights must sum exactly to 1; got {total_weight}")

    thresholds = data.get("optional_thresholds")
    if thresholds is not None:
        if not isinstance(thresholds, dict):
            raise HarnessError("scoring_policy.optional_thresholds must be an object or null")
        allowed_thresholds = {"min_checkpoint_pass_rate", "min_trajectory_utility"}
        for k in thresholds:
            if k not in allowed_thresholds:
                raise HarnessError(f"Unsupported threshold in scoring_policy.optional_thresholds: {k!r}; allowed: {allowed_thresholds}")
        for k, v in thresholds.items():
            if v is not None:
                validate_rational_number_schema(v, f"scoring_policy.optional_thresholds.{k}")
                f_val = json_to_fraction(v, f"scoring_policy.optional_thresholds.{k}")
                if k == "min_checkpoint_pass_rate" and (f_val < 0 or f_val > 1):
                    raise HarnessError(f"scoring_policy.optional_thresholds.{k} must be between 0 and 1; got {f_val}")
                if k == "min_trajectory_utility" and (f_val < 0 or f_val > 4):
                    raise HarnessError(f"scoring_policy.optional_thresholds.{k} must be between 0 and 4; got {f_val}")

    pricing = data.get("pricing")
    if pricing is not None:
        if not isinstance(pricing, dict):
            raise HarnessError("scoring_policy.pricing must be an object or null")
        fields(
            pricing,
            {"model_id", "version", "currency", "input_cost_per_million", "output_cost_per_million", "cached_input_cost_per_million"},
            {"model_id", "version", "currency", "input_cost_per_million", "output_cost_per_million"},
            "scoring_policy.pricing",
        )
        for cost_k in ("input_cost_per_million", "output_cost_per_million"):
            validate_rational_number_schema(pricing[cost_k], f"scoring_policy.pricing.{cost_k}")
        if "cached_input_cost_per_million" in pricing and pricing["cached_input_cost_per_million"] is not None:
            validate_rational_number_schema(pricing["cached_input_cost_per_million"], "scoring_policy.pricing.cached_input_cost_per_million")


def validate_score_report_schema(data: dict[str, Any]) -> None:
    """Validate score report document matching repo-foundation-harness/score-report-v1."""
    req = {
        "schema_version",
        "run_id",
        "created_at",
        "synthetic",
        "policy_id",
        "policy_sha256",
        "summary",
        "variants",
        "usage_accounting",
        "limitations",
    }
    allowed = req | {"policy_threshold_met", "policy_threshold_notes"}
    fields(data, allowed, req, "score_report")
    if data.get("schema_version") != SCORE_REPORT_SCHEMA:
        raise HarnessError(f"score_report.schema_version must be {SCORE_REPORT_SCHEMA!r}")
    if not isinstance(data.get("run_id"), str) or not HEX32_RE.fullmatch(data["run_id"]):
        raise HarnessError("score_report.run_id must be 32 hex chars")
    if not isinstance(data.get("created_at"), str) or not data["created_at"].strip():
        raise HarnessError("score_report.created_at must be non-empty string")
    if not isinstance(data.get("synthetic"), bool):
        raise HarnessError("score_report.synthetic must be a boolean")
    require_id(data.get("policy_id"), "score_report.policy_id")
    require_sha256(data.get("policy_sha256"), "score_report.policy_sha256")

    summary = data.get("summary")
    if not isinstance(summary, dict):
        raise HarnessError("score_report.summary must be an object")
    fields(
        summary,
        {"expected_samples", "state_counts", "coverage", "overall_strict_pass_rate", "overall_strict_pass_rate_bounds"},
        {"expected_samples", "state_counts", "coverage", "overall_strict_pass_rate_bounds"},
        "score_report.summary",
    )
    state_counts = summary.get("state_counts")
    if not isinstance(state_counts, dict):
        raise HarnessError("score_report.summary.state_counts must be an object")
    req_states = {"PASS", "FAIL", "HARD_FAILURE", "INCOMPLETE", "BLOCKED", "MISSING", "INVALID", "UNRESOLVED"}
    fields(state_counts, req_states, req_states, "score_report.summary.state_counts")
    for s_name in req_states:
        val = state_counts[s_name]
        if type(val) is not int or val < 0:
            raise HarnessError(f"score_report.summary.state_counts.{s_name} must be non-negative integer")

    cov = summary.get("coverage")
    if not isinstance(cov, dict):
        raise HarnessError("score_report.summary.coverage must be an object")
    fields(cov, {"attempted_coverage", "conclusive_checkpoint_coverage", "judgment_score_coverage"}, {"attempted_coverage", "conclusive_checkpoint_coverage", "judgment_score_coverage"}, "score_report.summary.coverage")
    for c_key in ("attempted_coverage", "conclusive_checkpoint_coverage", "judgment_score_coverage"):
        validate_rational_number_schema(cov[c_key], f"score_report.summary.coverage.{c_key}")

    if summary.get("overall_strict_pass_rate") is not None:
        validate_rational_number_schema(summary["overall_strict_pass_rate"], "score_report.summary.overall_strict_pass_rate")
    bounds = summary.get("overall_strict_pass_rate_bounds")
    if not isinstance(bounds, list) or len(bounds) != 2:
        raise HarnessError("score_report.summary.overall_strict_pass_rate_bounds must be a 2-element array")
    validate_rational_number_schema(bounds[0], "score_report.summary.overall_strict_pass_rate_bounds[0]")
    validate_rational_number_schema(bounds[1], "score_report.summary.overall_strict_pass_rate_bounds[1]")

    if not isinstance(data.get("variants"), list):
        raise HarnessError("score_report.variants must be a list")

    ua = data.get("usage_accounting")
    if not isinstance(ua, dict):
        raise HarnessError("score_report.usage_accounting must be an object")
    ua_req = {"scopes", "derived_estimate_cost_usd"}
    ua_allowed = {
        "scopes",
        "elapsed_wall_time_seconds",
        "elapsed_wall_time_reason",
        "derived_observed_cost_usd",
        "derived_estimated_cost_usd",
        "observed_cost_usd",
        "estimated_cost_usd",
        "derived_estimate_cost_usd",
        "cost_reason",
    }
    fields(ua, ua_allowed, ua_req, "score_report.usage_accounting")
    for c_field in ("derived_observed_cost_usd", "derived_estimated_cost_usd", "observed_cost_usd", "estimated_cost_usd", "derived_estimate_cost_usd"):
        if ua.get(c_field) is not None:
            validate_rational_number_schema(ua[c_field], f"score_report.usage_accounting.{c_field}")
    if ua.get("elapsed_wall_time_seconds") is not None and not isinstance(ua["elapsed_wall_time_seconds"], (int, float)):
        raise HarnessError("score_report.usage_accounting.elapsed_wall_time_seconds must be a number or null")

    scopes = ua.get("scopes")
    if not isinstance(scopes, dict):
        raise HarnessError("score_report.usage_accounting.scopes must be an object")
    for sc_name in ("candidate_work", "verification", "judge"):
        if sc_name in scopes:
            sc_obj = scopes[sc_name]
            sc_req = {
                "input_tokens_observed",
                "output_tokens_observed",
                "input_tokens_estimated",
                "output_tokens_estimated",
                "total_tokens_observed",
                "total_tokens_estimated",
                "summed_duration_seconds",
                "coverage",
                "is_complete",
            }
            sc_extra = {
                "tokens_observed",
                "tokens_estimated",
                "subtotal_derived_cost_usd",
                "subtotal_derived_observed_cost_usd",
                "subtotal_derived_estimated_cost_usd",
                "derived_cost_subtotal_usd",
                "derived_observed_cost_subtotal_usd",
                "derived_estimated_cost_subtotal_usd",
            }
            fields(sc_obj, sc_req | sc_extra, sc_req, f"score_report.usage_accounting.scopes.{sc_name}")
            for sub_k in ("subtotal_derived_cost_usd", "subtotal_derived_observed_cost_usd", "subtotal_derived_estimated_cost_usd",
                          "derived_cost_subtotal_usd", "derived_observed_cost_subtotal_usd", "derived_estimated_cost_subtotal_usd"):
                if sc_obj.get(sub_k) is not None:
                    validate_rational_number_schema(sc_obj[sub_k], f"score_report.usage_accounting.scopes.{sc_name}.{sub_k}")
            cov_sc = sc_obj.get("coverage")
            if isinstance(cov_sc, dict):
                for m_k in ("tokens_input", "tokens_output", "wall_time"):
                    if m_k in cov_sc and cov_sc[m_k] is not None:
                        validate_rational_number_schema(cov_sc[m_k], f"score_report.usage_accounting.scopes.{sc_name}.coverage.{m_k}")

    if not isinstance(data.get("limitations"), list):
        raise HarnessError("score_report.limitations must be a list")



