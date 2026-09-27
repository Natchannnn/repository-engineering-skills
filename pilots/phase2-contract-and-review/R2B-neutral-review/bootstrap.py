#!/usr/bin/env python3
"""
Bootstrap script for Task R2B (Neutral Review Fixture B).
Initializes a git repository with main branch and checkout on review/auth-token-v2.
This fixture contains a real breaking contract drift where src/auth_service.py
altered generate_session_token's signature, breaking the caller in src/api_gateway.py.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path


def run_cmd(cmd: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    res = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, check=False)
    if res.returncode != 0:
        raise RuntimeError(f"Command failed ({cmd}):\nSTDOUT: {res.stdout}\nSTDERR: {res.stderr}")
    return res


def compute_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def bootstrap_r2b(target_dir: Path) -> Path:
    target_dir.mkdir(parents=True, exist_ok=True)

    run_cmd(["git", "init", "-b", "main"], target_dir)
    run_cmd(["git", "config", "user.name", "Review Author"], target_dir)
    run_cmd(["git", "config", "user.email", "review-author@pilot.test"], target_dir)
    run_cmd(["git", "config", "commit.gpgsign", "false"], target_dir)

    src_dir = target_dir / "src"
    src_dir.mkdir(exist_ok=True)
    tests_dir = target_dir / "tests"
    tests_dir.mkdir(exist_ok=True)

    # 1. src/__init__.py
    (src_dir / "__init__.py").write_text("", encoding="utf-8")

    # 2. src/auth_service.py on main
    auth_service_v1 = '''"""Authentication and session token service."""
from __future__ import annotations


class AuthService:
    def generate_session_token(self, user_id: str, role: str) -> str:
        """Generates a session token string for user and role."""
        if not user_id or not role:
            raise ValueError("user_id and role cannot be empty")
        return f"sess_{user_id}_{role}_valid"
'''
    (src_dir / "auth_service.py").write_text(auth_service_v1, encoding="utf-8")

    # 3. src/api_gateway.py on main (Caller 1)
    api_gateway_v1 = '''"""API Gateway authentication middleware."""
from __future__ import annotations

from src.auth_service import AuthService


def handle_login(auth: AuthService, user_id: str, role: str) -> dict[str, str]:
    """Handles login request and creates user session."""
    token = auth.generate_session_token(user_id, role)
    return {
        "status": "authenticated",
        "user_id": user_id,
        "token": token,
    }
'''
    (src_dir / "api_gateway.py").write_text(api_gateway_v1, encoding="utf-8")

    # 4. src/web_controller.py on main (Caller 2)
    web_controller_v1 = '''"""Web frontend controller."""
from __future__ import annotations

from src.auth_service import AuthService


def login_web_user(auth: AuthService, user_id: str, role: str) -> str:
    """Logs in user via web session."""
    return auth.generate_session_token(user_id, role)
'''
    (src_dir / "web_controller.py").write_text(web_controller_v1, encoding="utf-8")

    # 5. tests/__init__.py
    (tests_dir / "__init__.py").write_text("", encoding="utf-8")

    # 6. tests/test_auth.py
    test_auth = '''import unittest
from src.auth_service import AuthService
from src.api_gateway import handle_login
from src.web_controller import login_web_user


class TestAuth(unittest.TestCase):
    def test_auth_workflow(self):
        auth = AuthService()
        res = handle_login(auth, "u123", "admin")
        self.assertEqual(res["status"], "authenticated")
        self.assertEqual(login_web_user(auth, "u123", "admin"), "sess_u123_admin_valid")


if __name__ == "__main__":
    unittest.main()
'''
    (tests_dir / "test_auth.py").write_text(test_auth, encoding="utf-8")

    # Commit main
    run_cmd(["git", "add", "."], target_dir)
    run_cmd(["git", "commit", "-m", "feat: baseline authentication and gateway service"], target_dir)
    main_head = run_cmd(["git", "rev-parse", "HEAD"], target_dir).stdout.strip()

    # Create feature branch: review/auth-token-v2
    run_cmd(["git", "checkout", "-b", "review/auth-token-v2"], target_dir)

    # In feature branch: Refactor AuthService.generate_session_token with tenant_id parameter
    auth_service_v2 = '''"""Authentication and session token service."""
from __future__ import annotations


class AuthService:
    def generate_session_token(self, user_id: str, tenant_id: str, role: str) -> str:
        """Generates a tenant-scoped session token string."""
        if not user_id or not tenant_id or not role:
            raise ValueError("user_id, tenant_id, and role cannot be empty")
        return f"sess_{tenant_id}_{user_id}_{role}_valid"
'''
    (src_dir / "auth_service.py").write_text(auth_service_v2, encoding="utf-8")

    # Update Caller 2 (web_controller.py)
    web_controller_v2 = '''"""Web frontend controller."""
from __future__ import annotations

from src.auth_service import AuthService


def login_web_user(auth: AuthService, user_id: str, role: str) -> str:
    """Logs in user via web session with default tenant."""
    return auth.generate_session_token(user_id, "default_tenant", role)
'''
    (src_dir / "web_controller.py").write_text(web_controller_v2, encoding="utf-8")

    # DEFECT INJECTION: Caller 1 (src/api_gateway.py) was NOT updated!
    # It still calls: auth.generate_session_token(user_id, role) with only 2 args.
    # At runtime, calling handle_login raises:
    # TypeError: AuthService.generate_session_token() missing 1 required positional argument: 'role'

    run_cmd(["git", "add", "."], target_dir)
    run_cmd(["git", "commit", "-m", "refactor: scope session token by tenant_id"], target_dir)
    feature_head = run_cmd(["git", "rev-parse", "HEAD"], target_dir).stdout.strip()

    # Snapshot manifest of review branch
    manifest: dict[str, dict[str, int | str]] = {}
    for p in target_dir.rglob("*"):
        if p.is_file() and ".git" not in p.parts:
            rel = p.relative_to(target_dir).as_posix()
            manifest[rel] = {
                "sha256": compute_sha256(p),
                "size_bytes": p.stat().st_size,
            }

    snapshot_path = target_dir.parent / f"{target_dir.name}-r2b-snapshot.json"
    with open(snapshot_path, "w", encoding="utf-8") as f:
        json.dump(
            {
                "main_head": main_head,
                "feature_head": feature_head,
                "branch": "review/auth-token-v2",
                "manifest": manifest,
            },
            f,
            indent=2,
        )

    print(f"Successfully bootstrapped R2B fixture at: {target_dir}")
    print(f"MAIN_HEAD:        {main_head}")
    print(f"FEATURE_HEAD:     {feature_head} (review/auth-token-v2)")
    print(f"Snapshot file:    {snapshot_path}")
    return target_dir


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Bootstrap Task R2B fixture")
    parser.add_argument("--target-dir", required=True, help="Path to bootstrap target directory")
    args = parser.parse_args()
    bootstrap_r2b(Path(args.target_dir).resolve())
