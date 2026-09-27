from __future__ import annotations

import unittest
from decimal import Decimal
from src.cart_summary import estimate_cart
from src.checkout import process_checkout
from src.invoice import generate_invoice_line_items
from src.shipping import calculate_shipping, ShippingQuote


class TestMigrationIntegration(unittest.TestCase):
    def test_estimate_cart_with_express(self):
        items = [
            {"price": Decimal("25.00"), "quantity": 2, "weight_kg": Decimal("1.5")},
        ]
        # total_weight = 3.0 kg, DOMESTIC, express=True
        # base_fee = 3.0 * 5.00 = 15.00, express_fee = 12.50, total_fee = 27.50
        # subtotal = 50.00, total = 77.50
        result = estimate_cart(items, "DOMESTIC", express=True)
        self.assertEqual(result["subtotal"], Decimal("50.00"))
        self.assertEqual(result["shipping"], Decimal("27.50"))
        self.assertEqual(result["total"], Decimal("77.50"))

    def test_process_checkout_with_express(self):
        # weight 2.0 kg, INTERNATIONAL, express=True
        # base_fee = 2.0 * 15.00 = 30.00, express_fee = 12.50, total_fee = 42.50
        # items_total = 100.00, total = 142.50
        total = process_checkout(
            Decimal("100.00"), Decimal("2.0"), "INTERNATIONAL", express=True
        )
        self.assertEqual(total, Decimal("142.50"))

    def test_generate_invoice_line_items_with_express(self):
        items = [{"name": "Widget", "amount": Decimal("50.00")}]
        # weight 1.0 kg, EXPRESS_ZONE, express=True
        # base_fee = 25.00, express_fee = 12.50, total_fee = 37.50
        lines = generate_invoice_line_items(
            items, Decimal("1.0"), "EXPRESS_ZONE", express=True
        )
        self.assertEqual(len(lines), 2)
        self.assertEqual(lines[0]["name"], "Widget")
        self.assertEqual(lines[0]["amount"], Decimal("50.00"))
        self.assertEqual(lines[1]["name"], "Shipping & Handling")
        self.assertEqual(lines[1]["amount"], Decimal("37.50"))


if __name__ == "__main__":
    unittest.main()
