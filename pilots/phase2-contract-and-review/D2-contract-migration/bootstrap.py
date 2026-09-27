#!/usr/bin/env python3
"""
Bootstrap script for Task D2 (Contract Migration & Multi-Caller Preservation).
Initializes a clean git repository containing an e-commerce shipping & pricing module,
with multiple internal callers distributed across the codebase.
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


def bootstrap_d2(target_dir: Path) -> Path:
    target_dir.mkdir(parents=True, exist_ok=True)

    run_cmd(["git", "init", "-b", "main"], target_dir)
    run_cmd(["git", "config", "user.name", "Pilot Author"], target_dir)
    run_cmd(["git", "config", "user.email", "author@pilot.test"], target_dir)
    run_cmd(["git", "config", "commit.gpgsign", "false"], target_dir)

    src_dir = target_dir / "src"
    src_dir.mkdir(exist_ok=True)
    tests_dir = target_dir / "tests"
    tests_dir.mkdir(exist_ok=True)

    # 1. src/__init__.py
    (src_dir / "__init__.py").write_text("", encoding="utf-8")

    # 2. src/shipping.py (Legacy contract returning Decimal)
    shipping_code = '''"""Shipping calculation module."""
from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP

DEFAULT_RATE_PER_KG: Decimal = Decimal("5.00")


def get_supported_destinations() -> list[str]:
    """Public API: returns destinations recognized by shipping carriers."""
    return ["DOMESTIC", "INTERNATIONAL", "EXPRESS_ZONE"]


def calculate_shipping(weight_kg: Decimal, destination: str) -> Decimal:
    """Calculate shipping fee. Legacy contract returning raw Decimal."""
    if destination == "DOMESTIC":
        rate = Decimal("5.00")
    elif destination == "INTERNATIONAL":
        rate = Decimal("15.00")
    elif destination == "EXPRESS_ZONE":
        rate = Decimal("25.00")
    else:
        raise ValueError("Unsupported destination")
    return (weight_kg * rate).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
'''
    (src_dir / "shipping.py").write_text(shipping_code, encoding="utf-8")

    # 3. src/checkout.py (Caller 1)
    checkout_code = '''"""Checkout processing module."""
from __future__ import annotations

from decimal import Decimal
from src.shipping import calculate_shipping


def process_checkout(items_total: Decimal, weight_kg: Decimal, destination: str) -> Decimal:
    """Calculates total checkout price including shipping."""
    shipping_fee = calculate_shipping(weight_kg, destination)
    return items_total + shipping_fee
'''
    (src_dir / "checkout.py").write_text(checkout_code, encoding="utf-8")

    # 4. src/cart_summary.py (Caller 2)
    cart_code = '''"""Cart summary and fee estimation module."""
from __future__ import annotations

from decimal import Decimal
from src.shipping import calculate_shipping


def estimate_cart(items: list[dict], destination: str) -> dict[str, Decimal]:
    """Calculates subtotal, shipping fee, and grand total for items in cart."""
    subtotal = sum((item["price"] * item["quantity"] for item in items), Decimal("0.00"))
    total_weight = sum(
        (item.get("weight_kg", Decimal("0.50")) * item["quantity"] for item in items),
        Decimal("0.00"),
    )
    shipping = calculate_shipping(total_weight, destination)
    return {
        "subtotal": subtotal,
        "shipping": shipping,
        "total": subtotal + shipping,
    }
'''
    (src_dir / "cart_summary.py").write_text(cart_code, encoding="utf-8")

    # 5. src/invoice.py (Caller 3)
    invoice_code = '''"""Invoice generation module."""
from __future__ import annotations

from decimal import Decimal
from src.shipping import calculate_shipping


def generate_invoice_line_items(
    items: list[dict], weight_kg: Decimal, destination: str
) -> list[dict]:
    """Generates invoice line items including shipping charges."""
    lines: list[dict] = []
    for item in items:
        lines.append({
            "name": item["name"],
            "amount": item["amount"],
        })
    shipping_cost = calculate_shipping(weight_kg, destination)
    lines.append({
        "name": "Shipping & Handling",
        "amount": shipping_cost,
    })
    return lines
'''
    (src_dir / "invoice.py").write_text(invoice_code, encoding="utf-8")

    # 6. tests/__init__.py
    (tests_dir / "__init__.py").write_text("", encoding="utf-8")

    # 7. tests/test_shipping.py
    test_shipping_code = '''from __future__ import annotations

import unittest
from decimal import Decimal
from src.shipping import calculate_shipping, get_supported_destinations, DEFAULT_RATE_PER_KG


class TestShippingBaseline(unittest.TestCase):
    def test_compatibility_surface(self):
        self.assertEqual(DEFAULT_RATE_PER_KG, Decimal("5.00"))
        self.assertEqual(get_supported_destinations(), ["DOMESTIC", "INTERNATIONAL", "EXPRESS_ZONE"])

    def test_legacy_shipping(self):
        fee = calculate_shipping(Decimal("2.0"), "DOMESTIC")
        # In legacy contract, this was Decimal("10.00")
        # In upgraded contract, candidate will update this test or add new tests
        self.assertIsNotNone(fee)


if __name__ == "__main__":
    unittest.main()
'''
    (tests_dir / "test_shipping.py").write_text(test_shipping_code, encoding="utf-8")

    # 8. tests/test_checkout.py
    test_checkout_code = '''from __future__ import annotations

import unittest
from decimal import Decimal
from src.checkout import process_checkout


class TestCheckout(unittest.TestCase):
    def test_checkout_domestic(self):
        total = process_checkout(Decimal("50.00"), Decimal("2.0"), "DOMESTIC")
        self.assertEqual(total, Decimal("60.00"))


if __name__ == "__main__":
    unittest.main()
'''
    (tests_dir / "test_checkout.py").write_text(test_checkout_code, encoding="utf-8")

    # 9. tests/test_cart_summary.py
    test_cart_code = '''from __future__ import annotations

import unittest
from decimal import Decimal
from src.cart_summary import estimate_cart


class TestCartSummary(unittest.TestCase):
    def test_estimate_cart(self):
        items = [
            {"price": Decimal("20.00"), "quantity": 2, "weight_kg": Decimal("1.0")},
        ]
        result = estimate_cart(items, "DOMESTIC")
        self.assertEqual(result["subtotal"], Decimal("40.00"))
        self.assertEqual(result["shipping"], Decimal("10.00"))
        self.assertEqual(result["total"], Decimal("50.00"))


if __name__ == "__main__":
    unittest.main()
'''
    (tests_dir / "test_cart_summary.py").write_text(test_cart_code, encoding="utf-8")

    # 10. tests/test_invoice.py
    test_invoice_code = '''from __future__ import annotations

import unittest
from decimal import Decimal
from src.invoice import generate_invoice_line_items


class TestInvoice(unittest.TestCase):
    def test_generate_invoice_lines(self):
        items = [{"name": "Item A", "amount": Decimal("15.00")}]
        lines = generate_invoice_line_items(items, Decimal("1.0"), "INTERNATIONAL")
        self.assertEqual(len(lines), 2)
        self.assertEqual(lines[0]["name"], "Item A")
        self.assertEqual(lines[1]["name"], "Shipping & Handling")
        self.assertEqual(lines[1]["amount"], Decimal("15.00"))


if __name__ == "__main__":
    unittest.main()
'''
    (tests_dir / "test_invoice.py").write_text(test_invoice_code, encoding="utf-8")

    # Commit baseline
    run_cmd(["git", "add", "."], target_dir)
    run_cmd(["git", "commit", "-m", "feat: baseline shipping service with distributed callers"], target_dir)

    initial_head = run_cmd(["git", "rev-parse", "HEAD"], target_dir).stdout.strip()

    # Generate baseline snapshot manifest
    manifest: dict[str, dict[str, int | str]] = {}
    for p in target_dir.rglob("*"):
        if p.is_file() and ".git" not in p.parts:
            rel = p.relative_to(target_dir).as_posix()
            manifest[rel] = {
                "sha256": compute_sha256(p),
                "size_bytes": p.stat().st_size,
            }

    snapshot_path = target_dir.parent / f"{target_dir.name}-d2-snapshot.json"
    with open(snapshot_path, "w", encoding="utf-8") as f:
        json.dump({"initial_head": initial_head, "manifest": manifest}, f, indent=2)

    print(f"Successfully bootstrapped D2 fixture at: {target_dir}")
    print(f"INITIAL_HEAD:     {initial_head}")
    print(f"Snapshot file:    {snapshot_path}")
    return target_dir


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Bootstrap Task D2 fixture")
    parser.add_argument("--target-dir", required=True, help="Path to bootstrap target directory")
    args = parser.parse_args()
    bootstrap_d2(Path(args.target_dir).resolve())
