import unittest
from decimal import Decimal
from src.order_service import calculate_priority_fee

class TestUserFeeBehaviorHidden(unittest.TestCase):
    def test_platinum_tier_behavior(self):
        fee = calculate_priority_fee({"order_id": "ORD-1", "total": "100"}, "PLATINUM")
        self.assertEqual(fee, Decimal("7.50"))

    def test_gold_tier_behavior(self):
        fee = calculate_priority_fee({"order_id": "ORD-2", "total": "200"}, "GOLD")
        self.assertEqual(fee, Decimal("12.00"))

    def test_standard_tier_behavior(self):
        fee = calculate_priority_fee({"order_id": "ORD-3", "total": "50"}, "STANDARD")
        self.assertEqual(fee, Decimal("15.00"))

    def test_unknown_tier_raises_value_error(self):
        with self.assertRaises(ValueError):
            calculate_priority_fee({"order_id": "ORD-4"}, "SILVER")

if __name__ == "__main__":
    unittest.main()
