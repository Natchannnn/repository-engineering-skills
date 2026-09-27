from __future__ import annotations

import unittest
from decimal import Decimal
from src.cart_summary import estimate_cart
from src.checkout import process_checkout
from src.invoice import generate_invoice_line_items


class TestMigrationIntegration(unittest.TestCase):
    def test_checkout_express(self):
        # 50.00 items + 2.0kg * 5.00 domestic + 12.50 express = 72.50
        total = process_checkout(Decimal("50.00"), Decimal("2.0"), "DOMESTIC", express=True)
        self.assertEqual(total, Decimal("72.50"))

    def test_checkout_international(self):
        # 100.00 items + 3.0kg * 15.00 international = 145.00
        total = process_checkout(Decimal("100.00"), Decimal("3.0"), "INTERNATIONAL")
        self.assertEqual(total, Decimal("145.00"))

    def test_cart_summary_express(self):
        items = [
            {"price": Decimal("20.00"), "quantity": 2, "weight_kg": Decimal("1.0")},
        ]
        # subtotal 40.00, weight 2.0kg * 5.00 + 12.50 = 22.50 shipping, total 62.50
        result = estimate_cart(items, "DOMESTIC", express=True)
        self.assertEqual(result["subtotal"], Decimal("40.00"))
        self.assertEqual(result["shipping"], Decimal("22.50"))
        self.assertEqual(result["total"], Decimal("62.50"))

    def test_invoice_express(self):
        items = [{"name": "Item A", "amount": Decimal("15.00")}]
        # weight 1.0kg * 15.00 international + 12.50 express = 27.50
        lines = generate_invoice_line_items(items, Decimal("1.0"), "INTERNATIONAL", express=True)
        self.assertEqual(len(lines), 2)
        self.assertEqual(lines[0]["name"], "Item A")
        self.assertEqual(lines[1]["name"], "Shipping & Handling")
        self.assertEqual(lines[1]["amount"], Decimal("27.50"))


if __name__ == "__main__":
    unittest.main()
