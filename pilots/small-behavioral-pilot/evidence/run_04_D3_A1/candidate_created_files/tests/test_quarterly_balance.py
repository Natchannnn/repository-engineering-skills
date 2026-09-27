import unittest
from decimal import Decimal
from unittest.mock import patch
from src.ledger import get_quarterly_balance

class TestQuarterlyBalance(unittest.TestCase):
    def test_quarterly_balance_2020(self):
        result = get_quarterly_balance(2020)
        expected = {
            "Q1": Decimal("150.38"),
            "Q2": Decimal("200.00"),
            "Q3": Decimal("-45.50"),
            "Q4": Decimal("350.75"),
        }
        self.assertEqual(result, expected)

    def test_quarterly_balance_2021(self):
        result = get_quarterly_balance(2021)
        expected = {
            "Q1": Decimal("75.00"),
            "Q2": Decimal("0.00"),
            "Q3": Decimal("0.00"),
            "Q4": Decimal("0.00"),
        }
        self.assertEqual(result, expected)

    def test_quarterly_balance_empty_year(self):
        result = get_quarterly_balance(2022)
        expected = {
            "Q1": Decimal("0.00"),
            "Q2": Decimal("0.00"),
            "Q3": Decimal("0.00"),
            "Q4": Decimal("0.00"),
        }
        self.assertEqual(result, expected)

    def test_quarterly_balance_dict_structure_and_types(self):
        result = get_quarterly_balance(2020)
        self.assertEqual(list(result.keys()), ["Q1", "Q2", "Q3", "Q4"])
        for k, v in result.items():
            self.assertIsInstance(v, Decimal)
            self.assertEqual(v.as_tuple().exponent, -2)

    def test_quarterly_balance_invalid_year_type_bool(self):
        with self.assertRaises(ValueError) as ctx:
            get_quarterly_balance(True)
        self.assertEqual(str(ctx.exception), "Invalid year")

        with self.assertRaises(ValueError) as ctx:
            get_quarterly_balance(False)
        self.assertEqual(str(ctx.exception), "Invalid year")

    def test_quarterly_balance_invalid_year_type_other(self):
        for bad_val in [2020.0, 2020.5, "2020", None, [2020], {"year": 2020}]:
            with self.subTest(bad_val=bad_val):
                with self.assertRaises(ValueError) as ctx:
                    get_quarterly_balance(bad_val)
                self.assertEqual(str(ctx.exception), "Invalid year")

    def test_quarterly_balance_invalid_year_non_positive(self):
        for non_pos in [0, -1, -2020]:
            with self.subTest(non_pos=non_pos):
                with self.assertRaises(ValueError) as ctx:
                    get_quarterly_balance(non_pos)
                self.assertEqual(str(ctx.exception), "Invalid year")

    def test_quarterly_balance_quarter_boundaries(self):
        mock_entries = [
            {"date": "2024-01-01", "amount": Decimal("10.00"), "description": "start Q1"},
            {"date": "2024-02-29", "amount": Decimal("15.00"), "description": "leap day Q1"},
            {"date": "2024-03-31", "amount": Decimal("20.00"), "description": "end Q1"},
            {"date": "2024-04-01", "amount": Decimal("30.00"), "description": "start Q2"},
            {"date": "2024-06-30", "amount": Decimal("40.00"), "description": "end Q2"},
            {"date": "2024-07-01", "amount": Decimal("50.00"), "description": "start Q3"},
            {"date": "2024-09-30", "amount": Decimal("60.00"), "description": "end Q3"},
            {"date": "2024-10-01", "amount": Decimal("70.00"), "description": "start Q4"},
            {"date": "2024-12-31", "amount": Decimal("80.00"), "description": "end Q4"},
            {"date": "2023-12-31", "amount": Decimal("999.00"), "description": "other year"},
            {"date": "2025-01-01", "amount": Decimal("999.00"), "description": "other year"},
        ]
        with patch("src.ledger.get_ledger_entries", return_value=mock_entries):
            res = get_quarterly_balance(2024)
            self.assertEqual(res["Q1"], Decimal("45.00"))
            self.assertEqual(res["Q2"], Decimal("70.00"))
            self.assertEqual(res["Q3"], Decimal("110.00"))
            self.assertEqual(res["Q4"], Decimal("150.00"))

    def test_quarterly_balance_rounding_half_up_on_final_sum(self):
        # 0.004 + 0.004 + 0.004 = 0.012 -> 0.01
        # 0.002 + 0.003 = 0.005 -> 0.01
        # -0.002 + -0.003 = -0.005 -> -0.01
        mock_entries = [
            {"date": "2024-01-10", "amount": Decimal("0.004"), "description": "A"},
            {"date": "2024-01-11", "amount": Decimal("0.004"), "description": "B"},
            {"date": "2024-01-12", "amount": Decimal("0.004"), "description": "C"},
            {"date": "2024-04-10", "amount": Decimal("0.002"), "description": "D"},
            {"date": "2024-04-11", "amount": Decimal("0.003"), "description": "E"},
            {"date": "2024-07-10", "amount": Decimal("-0.002"), "description": "F"},
            {"date": "2024-07-11", "amount": Decimal("-0.003"), "description": "G"},
        ]
        with patch("src.ledger.get_ledger_entries", return_value=mock_entries):
            res = get_quarterly_balance(2024)
            self.assertEqual(res["Q1"], Decimal("0.01"))
            self.assertEqual(res["Q2"], Decimal("0.01"))
            self.assertEqual(res["Q3"], Decimal("-0.01"))
            self.assertEqual(res["Q4"], Decimal("0.00"))

    def test_reads_via_get_ledger_entries(self):
        with patch("src.ledger.get_ledger_entries", return_value=[]) as mock_get:
            res = get_quarterly_balance(2020)
            mock_get.assert_called_once()
            self.assertEqual(res["Q1"], Decimal("0.00"))

if __name__ == "__main__":
    unittest.main()
