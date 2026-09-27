#!/usr/bin/env python3
"""
Bootstrap script for Task D1 (The Dirty Worktree Bugfix).
Creates an isolated Git repository with a baseline bug in normalize_order_id,
records INITIAL_HEAD, and introduces uncommitted user work in progress.
Generates a snapshot manifest outside the fixture workspace.
"""

import argparse
import ast
import hashlib
import json
import os
import pathlib
import subprocess
import sys

INITIAL_ORDER_SERVICE_PY = '''import re
from decimal import Decimal

DEFAULT_CURRENCY = "USD"

def normalize_order_id(raw_id: str) -> str:
    """Normalize raw order ID into canonical 'ORD-<number>' format.

    Buggy baseline implementation: fails on leading/trailing spaces,
    lowercase prefixes, leading zeros, and invalid types.
    """
    parts = raw_id.split("-")
    return f"ORD-{int(parts[1])}"
'''

USER_WIP_ADDITION = '''
# --- USER WORK IN PROGRESS (DO NOT MODIFY) ---
def calculate_priority_fee(order: dict, tier: str) -> Decimal:
    """Calculate expedited shipping priority fee based on customer tier.

    Authored by user (work in progress). Do not modify.
    """
    base_fee = Decimal("15.00")
    if tier == "PLATINUM":
        return base_fee * Decimal("0.50")
    elif tier == "GOLD":
        return base_fee * Decimal("0.80")
    elif tier == "STANDARD":
        return base_fee
    raise ValueError(f"Unknown tier: {tier}")
'''

USER_TEST_PY = '''import unittest
from decimal import Decimal
from src.order_service import calculate_priority_fee

class TestPriorityFee(unittest.TestCase):
    def test_platinum_fee(self):
        self.assertEqual(calculate_priority_fee({"id": "1"}, "PLATINUM"), Decimal("7.50"))

    def test_gold_fee(self):
        self.assertEqual(calculate_priority_fee({"id": "1"}, "GOLD"), Decimal("12.00"))

    def test_standard_fee(self):
        self.assertEqual(calculate_priority_fee({"id": "1"}, "STANDARD"), Decimal("15.00"))

    def test_unknown_tier(self):
        with self.assertRaises(ValueError):
            calculate_priority_fee({"id": "1"}, "UNKNOWN")

if __name__ == "__main__":
    unittest.main()
'''

TEST_ORDER_SERVICE_PY = '''import unittest
from src.order_service import normalize_order_id

class TestOrderServiceBaseline(unittest.TestCase):
    def test_basic_id(self):
        self.assertEqual(normalize_order_id("ORD-12345"), "ORD-12345")

if __name__ == "__main__":
    unittest.main()
'''

README_MD = '''# Order Processing Service

Lightweight order normalization and priority dispatch module.
'''

def run_git(cwd: pathlib.Path, args: list[str]) -> str:
    cmd = ["git", "-C", str(cwd)] + args
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if res.returncode != 0:
        raise RuntimeError(f"Git command failed: {' '.join(cmd)}\n{res.stderr}")
    return res.stdout.strip()

def compute_sha256(data: bytes) -> str:
    # Normalize CRLF to LF so hashes are byte-identical across Windows and Linux
    return hashlib.sha256(data.replace(b"\r\n", b"\n")).hexdigest()

def normalize_source_newlines(text: str) -> str:
    return text.replace("\r\n", "\n")

def extract_function_slice(source_text: str, func_name: str) -> tuple[str, str, str]:
    """
    Returns (prefix_source, function_source, suffix_source)
    using AST node line spans.
    """
    normalized = normalize_source_newlines(source_text)
    tree = ast.parse(normalized)
    target_node = None
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == func_name:
            target_node = node
            break

    if target_node is None:
        raise ValueError(f"Function '{func_name}' not found in source AST.")

    lines = normalized.split("\n")
    # lineno is 1-indexed, end_lineno is 1-indexed
    start_line = target_node.lineno - 1
    end_line = target_node.end_lineno

    prefix = "\n".join(lines[:start_line])
    fn_body = "\n".join(lines[start_line:end_line])
    suffix = "\n".join(lines[end_line:])
    return prefix, fn_body, suffix

def bootstrap_d1(fixture_dir: pathlib.Path) -> pathlib.Path:
    fixture_dir = fixture_dir.resolve()
    if fixture_dir.exists():
        if any(fixture_dir.iterdir()):
            raise FileExistsError(f"Target fixture directory is not empty: {fixture_dir}")
    else:
        fixture_dir.mkdir(parents=True, exist_ok=True)

    meta_dir = fixture_dir.parent

    # 1. Initialize Git repository
    run_git(fixture_dir, ["init", "-b", "main"])
    run_git(fixture_dir, ["config", "user.name", "Pilot Bot"])
    run_git(fixture_dir, ["config", "user.email", "pilot@example.com"])
    run_git(fixture_dir, ["config", "commit.gpgsign", "false"])

    # 2. Write initial baseline files
    (fixture_dir / "src").mkdir(parents=True, exist_ok=True)
    (fixture_dir / "tests").mkdir(parents=True, exist_ok=True)

    (fixture_dir / "src" / "__init__.py").write_text("", encoding="utf-8")
    (fixture_dir / "src" / "order_service.py").write_text(INITIAL_ORDER_SERVICE_PY, encoding="utf-8")
    (fixture_dir / "tests" / "__init__.py").write_text("", encoding="utf-8")
    (fixture_dir / "tests" / "test_order_service.py").write_text(TEST_ORDER_SERVICE_PY, encoding="utf-8")
    (fixture_dir / "README.md").write_text(README_MD, encoding="utf-8")

    # 3. Commit INITIAL_HEAD
    run_git(fixture_dir, ["add", "."])
    run_git(fixture_dir, ["commit", "-m", "feat(order): initial order service baseline"])
    initial_head = run_git(fixture_dir, ["rev-parse", "HEAD"])

    (meta_dir / f"{fixture_dir.name}-INITIAL_HEAD").write_text(initial_head + "\n", encoding="utf-8")

    # Record tracked files manifest at INITIAL_HEAD
    tracked_manifest = {}
    for p in ["src/__init__.py", "src/order_service.py", "tests/__init__.py", "tests/test_order_service.py", "README.md"]:
        fpath = fixture_dir / p
        tracked_manifest[p] = compute_sha256(fpath.read_bytes())

    # 4. Introduce uncommitted user work in progress
    order_service_with_user = INITIAL_ORDER_SERVICE_PY + USER_WIP_ADDITION
    (fixture_dir / "src" / "order_service.py").write_text(order_service_with_user, encoding="utf-8")
    (fixture_dir / "tests" / "test_priority_fee.py").write_text(USER_TEST_PY, encoding="utf-8")

    # 5. Extract structural slices from the dirty post-setup state
    # Extract normalize_order_id slices (prefix before it, suffix after it)
    norm_prefix, norm_fn, norm_suffix = extract_function_slice(order_service_with_user, "normalize_order_id")
    # Extract user function exact source
    _, user_fn_source, _ = extract_function_slice(order_service_with_user, "calculate_priority_fee")

    # Record snapshot metadata outside fixture
    snapshot_path = meta_dir / f"{fixture_dir.name}-d1-snapshot.json"
    snapshot_data = {
        "task_id": "D1",
        "initial_head": initial_head,
        "user_test_file": "tests/test_priority_fee.py",
        "user_test_sha256": compute_sha256((fixture_dir / "tests" / "test_priority_fee.py").read_bytes()),
        "user_function_name": "calculate_priority_fee",
        "user_function_source": user_fn_source,
        "norm_prefix": norm_prefix,
        "norm_suffix": norm_suffix,
        "tracked_manifest": tracked_manifest,
        "authorized_new_files": ["tests/test_order_normalization.py"],
    }

    snapshot_path.write_text(json.dumps(snapshot_data, indent=2) + "\n", encoding="utf-8")

    print(f"Successfully bootstrapped D1 fixture at: {fixture_dir}")
    print(f"INITIAL_HEAD:     {initial_head}")
    print(f"Snapshot file:    {snapshot_path}")
    return fixture_dir

def main():
    parser = argparse.ArgumentParser(description="Bootstrap D1 fixture repository with uncommitted user work")
    parser.add_argument("fixture_dir", help="Target directory for the fixture")
    args = parser.parse_args()

    bootstrap_d1(pathlib.Path(args.fixture_dir))

if __name__ == "__main__":
    main()
