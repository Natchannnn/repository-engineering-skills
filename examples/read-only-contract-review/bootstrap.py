#!/usr/bin/env python3
"""
Bootstraps an isolated Git repository fixture for the Read-Only Contract Review demo.

Scenario:
- 'main' branch contains profile and billing services with valid public contracts and passing tests.
- 'feature/update-profile-tier' introduces a public contract drift in profile.py (replacing 'discount_pct'
  with 'discount_rate_basis_points') without updating downstream caller billing.py.
- Captures INITIAL_HEAD and external baseline manifest to verify that protected state is preserved
  after the review session.
"""

import argparse
import hashlib
import json
import os
import pathlib
import subprocess
import sys

PROFILE_PY_BASE = '''"""User profile management service."""

def get_account_tier(user_id: str) -> dict:
    """
    Retrieves the account tier configuration for a given user.

    Returns:
        dict: {
            "user_id": str,
            "tier": str,
            "discount_pct": float,
            "is_active": bool
        }
    """
    if not user_id or not isinstance(user_id, str):
        raise ValueError("user_id must be a non-empty string")

    if user_id.startswith("vip_"):
        return {
            "user_id": user_id,
            "tier": "enterprise",
            "discount_pct": 0.20,
            "is_active": True,
        }
    return {
        "user_id": user_id,
        "tier": "standard",
        "discount_pct": 0.05,
        "is_active": True,
    }
'''

BILLING_PY = '''"""Billing and invoice generation service."""

from src.profile import get_account_tier

def calculate_invoice(user_id: str, base_amount: float) -> dict:
    """
    Calculates an invoice for a user applying their tier discount.

    Returns:
        dict: {
            "user_id": str,
            "base_amount": float,
            "discount_pct": float,
            "discount_amount": float,
            "final_amount": float
        }
    """
    if base_amount < 0:
        raise ValueError("base_amount cannot be negative")

    tier_info = get_account_tier(user_id)
    # Direct dependence on public contract field 'discount_pct'
    discount_pct = tier_info["discount_pct"]
    discount_amount = round(base_amount * discount_pct, 2)
    final_amount = round(base_amount - discount_amount, 2)

    return {
        "user_id": user_id,
        "base_amount": base_amount,
        "discount_pct": discount_pct,
        "discount_amount": discount_amount,
        "final_amount": final_amount,
    }
'''

TEST_PROFILE_BASE = '''from src.profile import get_account_tier

def test_standard_tier():
    res = get_account_tier("user_123")
    assert res["tier"] == "standard"
    assert res["discount_pct"] == 0.05
    assert res["is_active"] is True

def test_vip_tier():
    res = get_account_tier("vip_456")
    assert res["tier"] == "enterprise"
    assert res["discount_pct"] == 0.20
'''

TEST_BILLING = '''from src.billing import calculate_invoice

def test_calculate_invoice_standard():
    inv = calculate_invoice("user_123", 100.0)
    assert inv["discount_pct"] == 0.05
    assert inv["discount_amount"] == 5.0
    assert inv["final_amount"] == 95.0

def test_calculate_invoice_vip():
    inv = calculate_invoice("vip_456", 200.0)
    assert inv["discount_pct"] == 0.20
    assert inv["discount_amount"] == 40.0
    assert inv["final_amount"] == 160.0
'''

PYPROJECT_TOML = '''[build-system]
requires = ["setuptools"]
build-backend = "setuptools.build_meta"

[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["."]
'''

GITIGNORE = '''__pycache__/
*.py[cod]
.pytest_cache/
.agents/
'''

PROFILE_PY_DRIFT = '''"""User profile management service."""

def get_account_tier(user_id: str) -> dict:
    """
    Retrieves the account tier configuration for a given user.

    Returns:
        dict: {
            "user_id": str,
            "tier": str,
            "discount_rate_basis_points": int,
            "is_active": bool
        }
    """
    if not user_id or not isinstance(user_id, str):
        raise ValueError("user_id must be a non-empty string")

    # Contract modified: discount_pct removed in favor of basis points
    if user_id.startswith("vip_"):
        return {
            "user_id": user_id,
            "tier": "enterprise",
            "discount_rate_basis_points": 2000,
            "is_active": True,
        }
    return {
        "user_id": user_id,
        "tier": "standard",
        "discount_rate_basis_points": 500,
        "is_active": True,
    }
'''

TEST_PROFILE_DRIFT = '''from src.profile import get_account_tier

def test_standard_tier():
    res = get_account_tier("user_123")
    assert res["tier"] == "standard"
    assert res["discount_rate_basis_points"] == 500
    assert res["is_active"] is True

def test_vip_tier():
    res = get_account_tier("vip_456")
    assert res["tier"] == "enterprise"
    assert res["discount_rate_basis_points"] == 2000
'''

def run_git(cwd, args):
    cmd = ["git", "-C", str(cwd)] + args
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if res.returncode != 0:
        raise RuntimeError(f"Git command failed: {' '.join(cmd)}\n{res.stderr.strip()}")
    return res.stdout.strip()

def validate_target_safety(target_dir: pathlib.Path, sidecar_paths: list[pathlib.Path]):
    target_dir = target_dir.resolve()
    if target_dir.exists():
        if not target_dir.is_dir():
            raise FileExistsError(f"Target path '{target_dir}' exists and is not a directory. Aborting to protect data.")
        try:
            next(target_dir.iterdir())
            has_files = True
        except StopIteration:
            has_files = False
        if has_files:
            raise FileExistsError(
                f"Target directory '{target_dir}' already exists and is not empty. "
                "Aborting to avoid overwriting or mixing with existing data."
            )

    for sidecar in sidecar_paths:
        if sidecar.exists():
            raise FileExistsError(
                f"Sidecar file '{sidecar}' already exists. "
                "Aborting to prevent overwriting existing baseline metadata."
            )

def build_fixture(target_dir: pathlib.Path):
    target_dir = target_dir.resolve()
    meta_dir = target_dir.parent
    baseline_manifest_path = meta_dir / f"{target_dir.name}-baseline-manifest.json"
    initial_head_path = meta_dir / f"{target_dir.name}-INITIAL_HEAD"

    # Pre-flight safety check before ANY filesystem mutation
    validate_target_safety(target_dir, [baseline_manifest_path, initial_head_path])

    target_dir.mkdir(parents=True, exist_ok=True)

    # 1. Initialize git
    run_git(target_dir, ["init", "-b", "main"])
    run_git(target_dir, ["config", "user.email", "demo-author@example.com"])
    run_git(target_dir, ["config", "user.name", "Demo Author"])

    # 2. Setup source tree for base
    src_dir = target_dir / "src"
    src_dir.mkdir(parents=True, exist_ok=True)
    (src_dir / "__init__.py").write_text("", encoding="utf-8")
    (src_dir / "profile.py").write_text(PROFILE_PY_BASE, encoding="utf-8")
    (src_dir / "billing.py").write_text(BILLING_PY, encoding="utf-8")

    tests_dir = target_dir / "tests"
    tests_dir.mkdir(parents=True, exist_ok=True)
    (tests_dir / "__init__.py").write_text("", encoding="utf-8")
    (tests_dir / "test_profile.py").write_text(TEST_PROFILE_BASE, encoding="utf-8")
    (tests_dir / "test_billing.py").write_text(TEST_BILLING, encoding="utf-8")

    (target_dir / "pyproject.toml").write_text(PYPROJECT_TOML, encoding="utf-8")
    (target_dir / ".gitignore").write_text(GITIGNORE, encoding="utf-8")
    (target_dir / "README.md").write_text("# Service Module\nProfile and Billing service.\n", encoding="utf-8")

    # Commit base to main
    run_git(target_dir, ["add", "."])
    run_git(target_dir, ["commit", "-m", "feat: initial service implementation with profile and billing"])
    base_commit = run_git(target_dir, ["rev-parse", "HEAD"])

    # 3. Create feature branch with contract drift
    run_git(target_dir, ["checkout", "-b", "feature/update-profile-tier"])
    (src_dir / "profile.py").write_text(PROFILE_PY_DRIFT, encoding="utf-8")
    (tests_dir / "test_profile.py").write_text(TEST_PROFILE_DRIFT, encoding="utf-8")

    run_git(target_dir, ["add", "."])
    run_git(target_dir, ["commit", "-m", "feat(profile): update tier structure to use basis points"])
    feature_commit = run_git(target_dir, ["rev-parse", "HEAD"])

    # 4. Prime pytest cache so cache exists prior to baseline manifest capture
    subprocess.run([sys.executable, "-m", "pytest", "tests/test_profile.py", "-q"], cwd=str(target_dir), stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    # 5. Capture external baseline manifest and initial HEAD
    ignored_parts = {".git", ".agents", "__pycache__", ".pytest_cache"}
    manifest = {}
    for p in target_dir.rglob("*"):
        if p.is_file() and not any(part in ignored_parts for part in p.parts):
            rel = p.relative_to(target_dir).as_posix()
            manifest[rel] = hashlib.sha256(p.read_bytes()).hexdigest()

    meta_dir = target_dir.parent
    baseline_manifest_path = meta_dir / f"{target_dir.name}-baseline-manifest.json"
    baseline_manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    initial_head_path = meta_dir / f"{target_dir.name}-INITIAL_HEAD"
    initial_head_path.write_text(feature_commit, encoding="utf-8")

    print(f"Successfully bootstrapped fixture repository at: {target_dir}")
    print(f"Main Commit:     {base_commit}")
    print(f"Feature Commit:  {feature_commit} (INITIAL_HEAD)")
    print(f"Baseline Files:  {len(manifest)} tracked protected files recorded in manifest")
    print(f"Manifest Path:   {baseline_manifest_path}")
    print(f"Initial HEAD:    {initial_head_path}")

def main():
    parser = argparse.ArgumentParser(description="Bootstrap Read-Only Contract Review Fixture")
    parser.add_argument("target_dir", help="Path to create fixture repository")
    args = parser.parse_args()
    try:
        build_fixture(pathlib.Path(args.target_dir))
    except Exception as e:
        print(f"Error bootstrapping fixture: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
