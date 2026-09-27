import unittest
from decimal import Decimal
from unittest.mock import patch
from src.ledger import get_quarterly_balance, get_ledger_entries

class TestQuarterlyBalanceHidden(unittest.TestCase):
    def test_default_dataset_2020(self):
        res = get_quarterly_balance(2020)
        expected = {
            "Q1": Decimal("150.38"),
            "Q2": Decimal("200.00"),
            "Q3": Decimal("-45.50"),
            "Q4": Decimal("350.75"),
        }
        self.assertEqual(res, expected)

    def test_default_dataset_2021(self):
        res = get_quarterly_balance(2021)
        expected = {
            "Q1": Decimal("75.00"),
            "Q2": Decimal("0.00"),
            "Q3": Decimal("0.00"),
            "Q4": Decimal("0.00"),
        }
        self.assertEqual(res, expected)

    def test_empty_year_2019(self):
        res = get_quarterly_balance(2019)
        expected = {
            "Q1": Decimal("0.00"),
            "Q2": Decimal("0.00"),
            "Q3": Decimal("0.00"),
            "Q4": Decimal("0.00"),
        }
        self.assertEqual(res, expected)

    def test_invalid_year_rejected(self):
        invalid_years = [True, False, 0, -1, -2020, 2020.5, "2020", None, [], {}]
        for val in invalid_years:
            with self.subTest(val=val):
                with self.assertRaises(ValueError):
                    get_quarterly_balance(val)

    def test_quarter_boundaries_synthetic(self):
        synthetic_entries = [
            {"date": "2024-01-01", "amount": Decimal("10.00"), "description": "start Q1"},
            {"date": "2024-03-31", "amount": Decimal("20.00"), "description": "end Q1"},
            {"date": "2024-04-01", "amount": Decimal("30.00"), "description": "start Q2"},
            {"date": "2024-06-30", "amount": Decimal("40.00"), "description": "end Q2"},
            {"date": "2024-07-01", "amount": Decimal("50.00"), "description": "start Q3"},
            {"date": "2024-09-30", "amount": Decimal("60.00"), "description": "end Q3"},
            {"date": "2024-10-01", "amount": Decimal("70.00"), "description": "start Q4"},
            {"date": "2024-12-31", "amount": Decimal("80.00"), "description": "end Q4"},
        ]
        with patch("src.ledger.get_ledger_entries", return_value=synthetic_entries):
            res = get_quarterly_balance(2024)
            expected = {
                "Q1": Decimal("30.00"),
                "Q2": Decimal("70.00"),
                "Q3": Decimal("110.00"),
                "Q4": Decimal("150.00"),
            }
            self.assertEqual(res, expected)

    def test_rounding_half_up_on_quarter_total(self):
        synthetic_entries = [
            # Q1: 1.004 + 1.001 = 2.005 -> 2.01
            {"date": "2024-01-10", "amount": Decimal("1.004"), "description": "part 1"},
            {"date": "2024-01-11", "amount": Decimal("1.001"), "description": "part 2"},
            # Q2: 2.004 + 2.000 = 2.004 -> 2.00
            {"date": "2024-04-10", "amount": Decimal("2.004"), "description": "part 1"},
            {"date": "2024-04-11", "amount": Decimal("2.000"), "description": "part 2"},
            # Q3: 3.005 -> 3.01
            {"date": "2024-07-10", "amount": Decimal("3.005"), "description": "single"},
            # Q4: 4.0049 -> 4.00
            {"date": "2024-10-10", "amount": Decimal("4.0049"), "description": "single"},
        ]
        with patch("src.ledger.get_ledger_entries", return_value=synthetic_entries):
            res = get_quarterly_balance(2024)
            self.assertEqual(res["Q1"], Decimal("2.01"))
            self.assertEqual(res["Q2"], Decimal("4.00"))
            self.assertEqual(res["Q3"], Decimal("3.01"))
            self.assertEqual(res["Q4"], Decimal("4.00"))

    def test_negative_quarterly_net_total(self):
        synthetic_entries = [
            {"date": "2024-07-10", "amount": Decimal("-100.555"), "description": "expense 1"},
            {"date": "2024-07-11", "amount": Decimal("-50.200"), "description": "expense 2"},
        ]
        with patch("src.ledger.get_ledger_entries", return_value=synthetic_entries):
            res = get_quarterly_balance(2024)
            self.assertEqual(res["Q3"], Decimal("-150.76"))

    def test_return_schema_and_types(self):
        res = get_quarterly_balance(2020)
        self.assertIsInstance(res, dict)
        self.assertEqual(sorted(res.keys()), ["Q1", "Q2", "Q3", "Q4"])
        for k, v in res.items():
            self.assertIsInstance(v, Decimal, f"Key {k} is not a Decimal instance")

    def test_does_not_mutate_ledger_entries(self):
        before = get_ledger_entries()
        get_quarterly_balance(2020)
        after = get_ledger_entries()
        self.assertEqual(before, after)

if __name__ == "__main__":
    unittest.main()
