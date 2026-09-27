from __future__ import annotations

import unittest
from decimal import Decimal


class TestShippingHidden(unittest.TestCase):
    def test_compatibility_surface_preserved(self):
        from src.shipping import DEFAULT_RATE_PER_KG, get_supported_destinations

        self.assertEqual(DEFAULT_RATE_PER_KG, Decimal("5.00"))
        self.assertEqual(
            get_supported_destinations(), ["DOMESTIC", "INTERNATIONAL", "EXPRESS_ZONE"]
        )

    def test_upgraded_shipping_quote_structure(self):
        from src.shipping import ShippingQuote, calculate_shipping

        quote = calculate_shipping(Decimal("4.0"), "DOMESTIC", express=False)
        self.assertIsInstance(quote, ShippingQuote)
        self.assertEqual(quote.base_fee, Decimal("20.00"))
        self.assertEqual(quote.express_fee, Decimal("0.00"))
        self.assertEqual(quote.total_fee, Decimal("20.00"))

    def test_shipping_with_express(self):
        from src.shipping import calculate_shipping

        quote = calculate_shipping(Decimal("4.0"), "DOMESTIC", express=True)
        self.assertEqual(quote.base_fee, Decimal("20.00"))
        self.assertEqual(quote.express_fee, Decimal("12.50"))
        self.assertEqual(quote.total_fee, Decimal("32.50"))

    def test_international_and_express_zone(self):
        from src.shipping import calculate_shipping

        quote_intl = calculate_shipping(Decimal("1.5"), "INTERNATIONAL", express=False)
        self.assertEqual(quote_intl.base_fee, Decimal("22.50"))
        self.assertEqual(quote_intl.total_fee, Decimal("22.50"))

        quote_zone = calculate_shipping(Decimal("2.0"), "EXPRESS_ZONE", express=True)
        self.assertEqual(quote_zone.base_fee, Decimal("50.00"))
        self.assertEqual(quote_zone.express_fee, Decimal("12.50"))
        self.assertEqual(quote_zone.total_fee, Decimal("62.50"))

    def test_invalid_weight_validation(self):
        from src.shipping import calculate_shipping

        with self.assertRaises(ValueError):
            calculate_shipping(Decimal("0.0"), "DOMESTIC")

        with self.assertRaises(ValueError):
            calculate_shipping(Decimal("-5.0"), "DOMESTIC")

        with self.assertRaises(ValueError):
            calculate_shipping(5.0, "DOMESTIC")  # type: ignore

        with self.assertRaises(ValueError):
            calculate_shipping("2.0", "DOMESTIC")  # type: ignore

    def test_invalid_destination_validation(self):
        from src.shipping import calculate_shipping

        with self.assertRaises(ValueError):
            calculate_shipping(Decimal("1.0"), "UNKNOWN_COUNTRY")

    def test_invalid_express_flag_validation(self):
        from src.shipping import calculate_shipping

        with self.assertRaises((ValueError, TypeError)):
            calculate_shipping(Decimal("1.0"), "DOMESTIC", express="true")  # type: ignore


if __name__ == "__main__":
    unittest.main()
