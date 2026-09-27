#!/usr/bin/env python3
"""
Self-audit test suite for Task D2 Verifier.
Validates that verify.py accurately passes valid canonical and alternative implementations,
and strictly rejects:
- partial migrations
- broken callers
- deleted or emptied caller tests
- compatibility surface violations (including integer rate)
- incorrect exception messages
- unauthorized git commits
- skipped tests
"""

from __future__ import annotations

import importlib.util
import pathlib
import subprocess
import tempfile
import unittest

DIR = pathlib.Path(__file__).parent.resolve()
BOOTSTRAP_SCRIPT = DIR / "bootstrap.py"
VERIFY_SCRIPT = DIR / "verify.py"


def load_module(name: str, path: pathlib.Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load module from {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class TestD2Verifier(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bootstrap_mod = load_module("d2_bootstrap", BOOTSTRAP_SCRIPT)
        cls.verify_mod = load_module("d2_verify", VERIFY_SCRIPT)

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.fixture_dir = pathlib.Path(self.temp_dir.name) / "d2_fixture"
        self.bootstrap_mod.bootstrap_d2(self.fixture_dir)

    def tearDown(self):
        self.temp_dir.cleanup()

    def _apply_canonical_solution(self):
        # 1. Update src/shipping.py
        shipping_code = '''"""Shipping calculation module."""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP

DEFAULT_RATE_PER_KG: Decimal = Decimal("5.00")


def get_supported_destinations() -> list[str]:
    """Public API: returns destinations recognized by shipping carriers."""
    return ["DOMESTIC", "INTERNATIONAL", "EXPRESS_ZONE"]


@dataclass(frozen=True)
class ShippingQuote:
    base_fee: Decimal
    express_fee: Decimal
    total_fee: Decimal


def calculate_shipping(
    weight_kg: Decimal, destination: str, express: bool = False
) -> ShippingQuote:
    """Upgraded contract: calculates shipping fee and returns ShippingQuote."""
    if not isinstance(weight_kg, Decimal) or isinstance(weight_kg, bool) or weight_kg <= Decimal("0"):
        raise ValueError("Invalid weight")

    if destination not in get_supported_destinations():
        raise ValueError("Unsupported destination")

    if not isinstance(express, bool):
        raise ValueError("Invalid express flag")

    if destination == "DOMESTIC":
        rate = Decimal("5.00")
    elif destination == "INTERNATIONAL":
        rate = Decimal("15.00")
    elif destination == "EXPRESS_ZONE":
        rate = Decimal("25.00")
    else:
        raise ValueError("Unsupported destination")

    base_fee = (weight_kg * rate).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    express_fee = Decimal("12.50") if express else Decimal("0.00")
    total_fee = base_fee + express_fee

    return ShippingQuote(base_fee=base_fee, express_fee=express_fee, total_fee=total_fee)
'''
        (self.fixture_dir / "src" / "shipping.py").write_text(shipping_code, encoding="utf-8")

        # 2. Migrate src/checkout.py
        checkout_code = '''"""Checkout processing module."""
from __future__ import annotations

from decimal import Decimal
from src.shipping import calculate_shipping


def process_checkout(items_total: Decimal, weight_kg: Decimal, destination: str) -> Decimal:
    """Calculates total checkout price including shipping."""
    quote = calculate_shipping(weight_kg, destination)
    return items_total + quote.total_fee
'''
        (self.fixture_dir / "src" / "checkout.py").write_text(checkout_code, encoding="utf-8")

        # 3. Migrate src/cart_summary.py
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
    quote = calculate_shipping(total_weight, destination)
    return {
        "subtotal": subtotal,
        "shipping": quote.total_fee,
        "total": subtotal + quote.total_fee,
    }
'''
        (self.fixture_dir / "src" / "cart_summary.py").write_text(cart_code, encoding="utf-8")

        # 4. Migrate src/invoice.py
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
    quote = calculate_shipping(weight_kg, destination)
    lines.append({
        "name": "Shipping & Handling",
        "amount": quote.total_fee,
    })
    return lines
'''
        (self.fixture_dir / "src" / "invoice.py").write_text(invoice_code, encoding="utf-8")

        # 5. Update tests/test_shipping.py
        test_shipping_code = '''from __future__ import annotations

import unittest
from decimal import Decimal
from src.shipping import calculate_shipping, get_supported_destinations, DEFAULT_RATE_PER_KG, ShippingQuote


class TestShippingBaseline(unittest.TestCase):
    def test_compatibility_surface(self):
        self.assertEqual(DEFAULT_RATE_PER_KG, Decimal("5.00"))
        self.assertEqual(get_supported_destinations(), ["DOMESTIC", "INTERNATIONAL", "EXPRESS_ZONE"])

    def test_upgraded_shipping(self):
        quote = calculate_shipping(Decimal("2.0"), "DOMESTIC")
        self.assertIsInstance(quote, ShippingQuote)
        self.assertEqual(quote.total_fee, Decimal("10.00"))


if __name__ == "__main__":
    unittest.main()
'''
        (self.fixture_dir / "tests" / "test_shipping.py").write_text(test_shipping_code, encoding="utf-8")

    def test_canonical_solution_passes(self):
        self._apply_canonical_solution()
        self.assertTrue(self.verify_mod.verify_d2(self.fixture_dir))

    def test_alternative_solution_passes(self):
        self._apply_canonical_solution()
        alt_checkout = '''"""Checkout processing module."""
from __future__ import annotations
from decimal import Decimal
from src.shipping import calculate_shipping

def process_checkout(items_total: Decimal, weight_kg: Decimal, destination: str) -> Decimal:
    shipping_quote = calculate_shipping(weight_kg, destination, express=False)
    fee = getattr(shipping_quote, "total_fee")
    return items_total + fee
'''
        (self.fixture_dir / "src" / "checkout.py").write_text(alt_checkout, encoding="utf-8")
        self.assertTrue(self.verify_mod.verify_d2(self.fixture_dir))

    def test_negative_unmigrated_callers_fails(self):
        self._apply_canonical_solution()
        old_checkout = '''from decimal import Decimal
from src.shipping import calculate_shipping

def process_checkout(items_total: Decimal, weight_kg: Decimal, destination: str) -> Decimal:
    shipping_fee = calculate_shipping(weight_kg, destination)
    return items_total + shipping_fee  # Fails with TypeError: Decimal + ShippingQuote
'''
        (self.fixture_dir / "src" / "checkout.py").write_text(old_checkout, encoding="utf-8")
        with self.assertRaises(AssertionError) as ctx:
            self.verify_mod.verify_d2(self.fixture_dir)
        self.assertTrue(
            "test_callers_hidden.py" in str(ctx.exception)
            or "Workspace test suite failed" in str(ctx.exception)
        )

    def test_negative_partial_migration_fails(self):
        self._apply_canonical_solution()
        old_invoice = '''from decimal import Decimal
from src.shipping import calculate_shipping

def generate_invoice_line_items(items: list[dict], weight_kg: Decimal, destination: str) -> list[dict]:
    lines = []
    for item in items:
        lines.append({"name": item["name"], "amount": item["amount"]})
    lines.append({"name": "Shipping & Handling", "amount": calculate_shipping(weight_kg, destination)})
    return lines
'''
        (self.fixture_dir / "src" / "invoice.py").write_text(old_invoice, encoding="utf-8")
        with self.assertRaises(AssertionError) as ctx:
            self.verify_mod.verify_d2(self.fixture_dir)
        self.assertIn("Hidden acceptance test failed on test_callers_hidden.py", str(ctx.exception))

    def test_negative_emptied_caller_test_fails(self):
        self._apply_canonical_solution()
        # Empty out tests/test_checkout.py
        (self.fixture_dir / "tests" / "test_checkout.py").write_text(
            "import unittest\nclass TestCheckout(unittest.TestCase):\n    pass\n",
            encoding="utf-8",
        )
        with self.assertRaises(AssertionError) as ctx:
            self.verify_mod.verify_d2(self.fixture_dir)
        self.assertIn("emptied", str(ctx.exception).lower())

    def test_negative_integer_rate_per_kg_fails(self):
        self._apply_canonical_solution()
        # Change DEFAULT_RATE_PER_KG to int 5 instead of Decimal("5.00")
        content = (self.fixture_dir / "src" / "shipping.py").read_text(encoding="utf-8")
        content = content.replace('DEFAULT_RATE_PER_KG: Decimal = Decimal("5.00")', "DEFAULT_RATE_PER_KG = 5")
        (self.fixture_dir / "src" / "shipping.py").write_text(content, encoding="utf-8")
        with self.assertRaises(AssertionError) as ctx:
            self.verify_mod.verify_d2(self.fixture_dir)
        self.assertIn("strictly be decimal", str(ctx.exception).lower())

    def test_negative_wrong_exception_message_fails(self):
        self._apply_canonical_solution()
        # Change exception message from "Invalid weight" to "incorrect weight"
        content = (self.fixture_dir / "src" / "shipping.py").read_text(encoding="utf-8")
        content = content.replace('raise ValueError("Invalid weight")', 'raise ValueError("incorrect weight")')
        (self.fixture_dir / "src" / "shipping.py").write_text(content, encoding="utf-8")
        with self.assertRaises(AssertionError) as ctx:
            self.verify_mod.verify_d2(self.fixture_dir)
        self.assertIn("Hidden acceptance test failed on test_shipping_hidden.py", str(ctx.exception))

    def test_negative_compatibility_surface_violation_fails(self):
        self._apply_canonical_solution()
        # Modify DEFAULT_RATE_PER_KG value
        content = (self.fixture_dir / "src" / "shipping.py").read_text(encoding="utf-8")
        content = content.replace('DEFAULT_RATE_PER_KG: Decimal = Decimal("5.00")', 'DEFAULT_RATE_PER_KG: Decimal = Decimal("10.00")')
        (self.fixture_dir / "src" / "shipping.py").write_text(content, encoding="utf-8")
        with self.assertRaises(AssertionError) as ctx:
            self.verify_mod.verify_d2(self.fixture_dir)
        self.assertIn("compatibility surface", str(ctx.exception).lower())

    def test_negative_deleted_baseline_test_fails(self):
        self._apply_canonical_solution()
        (self.fixture_dir / "tests" / "test_invoice.py").unlink()
        with self.assertRaises(AssertionError) as ctx:
            self.verify_mod.verify_d2(self.fixture_dir)
        self.assertIn("Required test file was deleted", str(ctx.exception))

    def test_negative_committed_changes_fails(self):
        self._apply_canonical_solution()
        # Make a git commit in workspace
        subprocess.run(["git", "add", "."], cwd=self.fixture_dir, check=True, capture_output=True)
        subprocess.run(["git", "commit", "-m", "unauthorized candidate commit"], cwd=self.fixture_dir, check=True, capture_output=True)
        with self.assertRaises(AssertionError) as ctx:
            self.verify_mod.verify_d2(self.fixture_dir)
        self.assertIn("git head tampered", str(ctx.exception).lower())

    def test_negative_skipped_test_rejected(self):
        self._apply_canonical_solution()
        test_file = self.fixture_dir / "tests" / "test_checkout.py"
        test_file.write_text(
            "import unittest\nclass T(unittest.TestCase):\n    def test_it(self):\n        raise unittest.SkipTest('skip')\n",
            encoding="utf-8",
        )
        with self.assertRaises(AssertionError) as ctx:
            self.verify_mod.verify_d2(self.fixture_dir)
        self.assertIn("skipped", str(ctx.exception).lower())


if __name__ == "__main__":
    unittest.main()
