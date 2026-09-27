from __future__ import annotations

import unittest
from decimal import Decimal


class TestCallersHidden(unittest.TestCase):
    def test_caller_checkout_migrated(self):
        from src.checkout import process_checkout

        total = process_checkout(Decimal("100.00"), Decimal("3.0"), "DOMESTIC")
        # 100.00 + (3.0 * 5.00) = 115.00
        self.assertEqual(total, Decimal("115.00"))

    def test_caller_cart_summary_migrated(self):
        from src.cart_summary import estimate_cart

        items = [
            {"price": Decimal("10.00"), "quantity": 3, "weight_kg": Decimal("2.0")},
        ]
        result = estimate_cart(items, "INTERNATIONAL")
        # Subtotal: 30.00, weight: 6.0kg * 15.00 = 90.00, total: 120.00
        self.assertEqual(result["subtotal"], Decimal("30.00"))
        # Accepts either Decimal total_fee or ShippingQuote object, but total must equal Decimal("120.00")
        self.assertEqual(result["total"], Decimal("120.00"))

    def test_caller_invoice_migrated(self):
        from src.invoice import generate_invoice_line_items

        items = [{"name": "Widget", "amount": Decimal("50.00")}]
        lines = generate_invoice_line_items(items, Decimal("1.0"), "DOMESTIC")
        self.assertEqual(len(lines), 2)
        self.assertEqual(lines[0]["name"], "Widget")
        self.assertEqual(lines[0]["amount"], Decimal("50.00"))
        self.assertEqual(lines[1]["name"], "Shipping & Handling")
        # Shipping fee must be Decimal("5.00")
        self.assertEqual(lines[1]["amount"], Decimal("5.00"))


if __name__ == "__main__":
    unittest.main()
