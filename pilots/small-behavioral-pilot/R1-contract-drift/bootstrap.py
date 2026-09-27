#!/usr/bin/env python3
"""
Bootstrap script for Task R1 (Contract Drift Review).
Creates an isolated Git repository with a baseline 'main' branch and a feature branch
'refactor/tax-id-standardization' where a schema field was renamed (tax_identifier -> tax_id),
billing service was updated, but notification service was left broken.
The repository is delivered in a clean read-only state on the feature branch.
"""

import argparse
import hashlib
import json
import os
import pathlib
import subprocess
import sys

MAIN_SCHEMA_PY = '''from dataclasses import dataclass

@dataclass
class AccountProfile:
    account_id: str
    legal_name: str
    tax_identifier: str
    email: str
'''

MAIN_BILLING_PY = '''from src.schema import AccountProfile

def generate_billing_receipt(profile: AccountProfile, amount_cents: int) -> dict:
    return {
        "account_id": profile.account_id,
        "tax_ref": profile.tax_identifier,
        "amount_cents": amount_cents,
        "status": "billed",
    }
'''

MAIN_NOTIFICATION_PY = '''from src.schema import AccountProfile

def send_tax_invoice(profile: AccountProfile, invoice_number: str) -> dict:
    return {
        "recipient_email": profile.email,
        "tax_id_on_file": profile.tax_identifier,
        "invoice_number": invoice_number,
        "delivery_status": "queued",
    }
'''

MAIN_TEST_BILLING_PY = '''import unittest
from src.schema import AccountProfile
from src.billing_service import generate_billing_receipt

class TestBillingService(unittest.TestCase):
    def test_generate_receipt(self):
        profile = AccountProfile("acc_1", "Acme Corp", "US-123456789", "billing@acme.com")
        res = generate_billing_receipt(profile, 5000)
        self.assertEqual(res["tax_ref"], "US-123456789")

if __name__ == "__main__":
    unittest.main()
'''

MAIN_TEST_NOTIFICATION_PY = '''import unittest
from src.schema import AccountProfile
from src.notification_service import send_tax_invoice

class TestNotificationService(unittest.TestCase):
    def test_send_invoice(self):
        profile = AccountProfile("acc_1", "Acme Corp", "US-123456789", "billing@acme.com")
        res = send_tax_invoice(profile, "INV-2026-001")
        self.assertEqual(res["tax_id_on_file"], "US-123456789")

if __name__ == "__main__":
    unittest.main()
'''

BRANCH_SCHEMA_PY = '''from dataclasses import dataclass

@dataclass
class AccountProfile:
    account_id: str
    legal_name: str
    tax_id: str
    email: str
'''

BRANCH_BILLING_PY = '''from src.schema import AccountProfile

def generate_billing_receipt(profile: AccountProfile, amount_cents: int) -> dict:
    return {
        "account_id": profile.account_id,
        "tax_ref": profile.tax_id,
        "amount_cents": amount_cents,
        "status": "billed",
    }
'''

README_MD = '''# Account & Billing Services

Microservices for managing account schemas, billing receipts, and tax invoice notifications.
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

def bootstrap_r1(fixture_dir: pathlib.Path) -> pathlib.Path:
    fixture_dir = fixture_dir.resolve()
    if fixture_dir.exists():
        if any(fixture_dir.iterdir()):
            raise FileExistsError(f"Target fixture directory is not empty: {fixture_dir}")
    else:
        fixture_dir.mkdir(parents=True, exist_ok=True)

    meta_dir = fixture_dir.parent

    # 1. Initialize Git repository on main branch
    run_git(fixture_dir, ["init", "-b", "main"])
    run_git(fixture_dir, ["config", "user.name", "Pilot Bot"])
    run_git(fixture_dir, ["config", "user.email", "pilot@example.com"])
    run_git(fixture_dir, ["config", "commit.gpgsign", "false"])

    # 2. Write initial baseline files on main
    (fixture_dir / "src").mkdir(parents=True, exist_ok=True)
    (fixture_dir / "tests").mkdir(parents=True, exist_ok=True)

    (fixture_dir / "src" / "__init__.py").write_text("", encoding="utf-8")
    (fixture_dir / "src" / "schema.py").write_text(MAIN_SCHEMA_PY, encoding="utf-8")
    (fixture_dir / "src" / "billing_service.py").write_text(MAIN_BILLING_PY, encoding="utf-8")
    (fixture_dir / "src" / "notification_service.py").write_text(MAIN_NOTIFICATION_PY, encoding="utf-8")

    (fixture_dir / "tests" / "__init__.py").write_text("", encoding="utf-8")
    (fixture_dir / "tests" / "test_billing.py").write_text(MAIN_TEST_BILLING_PY, encoding="utf-8")
    (fixture_dir / "tests" / "test_notification.py").write_text(MAIN_TEST_NOTIFICATION_PY, encoding="utf-8")
    (fixture_dir / "README.md").write_text(README_MD, encoding="utf-8")

    run_git(fixture_dir, ["add", "."])
    run_git(fixture_dir, ["commit", "-m", "feat(schema): initial account schema and service implementations"])
    main_head = run_git(fixture_dir, ["rev-parse", "HEAD"])

    # 3. Create and switch to feature branch
    branch_name = "refactor/tax-id-standardization"
    run_git(fixture_dir, ["checkout", "-b", branch_name])

    # 4. Apply schema change and update billing, but leave notification broken
    (fixture_dir / "src" / "schema.py").write_text(BRANCH_SCHEMA_PY, encoding="utf-8")
    (fixture_dir / "src" / "billing_service.py").write_text(BRANCH_BILLING_PY, encoding="utf-8")

    run_git(fixture_dir, ["add", "src/schema.py", "src/billing_service.py"])
    run_git(fixture_dir, ["commit", "-m", "feat(schema): standardize tax identifier field to tax_id"])
    branch_head = run_git(fixture_dir, ["rev-parse", "HEAD"])

    # Record tracked files manifest at initial feature branch HEAD
    tracked_manifest = {}
    tracked_files = [
        "src/__init__.py",
        "src/schema.py",
        "src/billing_service.py",
        "src/notification_service.py",
        "tests/__init__.py",
        "tests/test_billing.py",
        "tests/test_notification.py",
        "README.md",
    ]
    for p in tracked_files:
        fpath = fixture_dir / p
        tracked_manifest[p] = compute_sha256(fpath.read_bytes())

    # Record snapshot metadata outside fixture
    snapshot_path = meta_dir / f"{fixture_dir.name}-r1-snapshot.json"
    snapshot_data = {
        "task_id": "R1",
        "main_head": main_head,
        "initial_head": branch_head,
        "branch_name": branch_name,
        "tracked_manifest": tracked_manifest,
        "ground_truth_finding": {
            "verdict": "defect",
            "source_file": "src/schema.py",
            "source_symbol": "AccountProfile.tax_identifier",
            "source_symbol_aliases": ["AccountProfile.tax_identifier", "AccountProfile.tax_id"],
            "broken_caller_file": "src/notification_service.py",
            "broken_caller_symbol": "send_tax_invoice",
            "breakage_type_allowed": ["contract_drift", "removed_symbol"],
        }
    }

    snapshot_path.write_text(json.dumps(snapshot_data, indent=2) + "\n", encoding="utf-8")

    print(f"Successfully bootstrapped R1 fixture at: {fixture_dir}")
    print(f"MAIN_HEAD:        {main_head}")
    print(f"INITIAL_HEAD:     {branch_head} ({branch_name})")
    print(f"Snapshot file:    {snapshot_path}")
    return fixture_dir

def main():
    parser = argparse.ArgumentParser(description="Bootstrap R1 fixture repository for contract drift review")
    parser.add_argument("fixture_dir", help="Target directory for the fixture")
    args = parser.parse_args()

    bootstrap_r1(pathlib.Path(args.fixture_dir))

if __name__ == "__main__":
    main()
