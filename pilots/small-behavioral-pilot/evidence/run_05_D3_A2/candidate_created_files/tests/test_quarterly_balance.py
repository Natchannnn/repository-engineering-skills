import unittest
from decimal import Decimal
from unittest.mock import patch

from src.ledger import get_quarterly_balance


class TestQuarterlyBalance(unittest.TestCase):
    def test_quarterly_balance_2020_default_data(self):
        result = get_quarterly_balance(2020)
        expected = {
            "Q1": Decimal("150.38"),
            "Q2": Decimal("200.00"),
            "Q3": Decimal("-45.50"),
            "Q4": Decimal("350.75"),
        }
        self.assertEqual(result, expected)

    def test_quarterly_balance_2021_default_data(self):
        result = get_quarterly_balance(2021)
        expected = {
            "Q1": Decimal("75.00"),
            "Q2": Decimal("0.00"),
            "Q3": Decimal("0.00"),
            "Q4": Decimal("0.00"),
        }
        self.assertEqual(result, expected)

    def test_quarterly_balance_year_with_no_entries(self):
        result = get_quarterly_balance(2022)
        expected = {
            "Q1": Decimal("0.00"),
            "Q2": Decimal("0.00"),
            "Q3": Decimal("0.00"),
            "Q4": Decimal("0.00"),
        }
        self.assertEqual(result, expected)
        self.assertEqual(list(result.keys()), ["Q1", "Q2", "Q3", "Q4"])

    def test_return_dict_keys_and_types(self):
        result = get_quarterly_balance(2020)
        self.assertEqual(set(result.keys()), {"Q1", "Q2", "Q3", "Q4"})
        for k, v in result.items():
            self.assertIsInstance(v, Decimal)

    def test_invalid_year_validation(self):
        invalid_years = [
            0,
            -1,
            -2020,
            True,
            False,
            2020.0,
            2020.5,
            "2020",
            None,
            [2020],
            {"year": 2020},
        ]
        for year in invalid_years:
            with self.subTest(year=year):
                with self.assertRaises(ValueError) as cm:
                    get_quarterly_balance(year)
                self.assertEqual(str(cm.exception), "Invalid year")

    def test_rounding_on_final_total_round_half_up(self):
        mock_entries = [
            {"date": "2024-01-10", "amount": Decimal("10.004"), "description": "Part A"},
            {"date": "2024-02-10", "amount": Decimal("10.002"), "description": "Part B"},
        ]
        # Sum is 20.006 -> rounded half up to 20.01.
        # If rounded individually first: 10.00 + 10.00 = 20.00.
        with patch("src.ledger.get_ledger_entries", return_value=mock_entries):
            result = get_quarterly_balance(2024)
            self.assertEqual(result["Q1"], Decimal("20.01"))

    def test_quarter_boundary_dates(self):
        mock_entries = [
            # Q1 boundaries
            {"date": "2024-01-01", "amount": Decimal("10.00"), "description": "Q1 start"},
            {"date": "2024-02-29", "amount": Decimal("15.00"), "description": "Q1 leap day"},
            {"date": "2024-03-31", "amount": Decimal("20.00"), "description": "Q1 end"},
            # Q2 boundaries
            {"date": "2024-04-01", "amount": Decimal("30.00"), "description": "Q2 start"},
            {"date": "2024-06-30", "amount": Decimal("40.00"), "description": "Q2 end"},
            # Q3 boundaries
            {"date": "2024-07-01", "amount": Decimal("50.00"), "description": "Q3 start"},
            {"date": "2024-09-30", "amount": Decimal("60.00"), "description": "Q3 end"},
            # Q4 boundaries
            {"date": "2024-10-01", "amount": Decimal("70.00"), "description": "Q4 start"},
            {"date": "2024-12-31", "amount": Decimal("80.00"), "description": "Q4 end"},
            # Out of year
            {"date": "2023-12-31", "amount": Decimal("999.00"), "description": "Previous year"},
            {"date": "2025-01-01", "amount": Decimal("999.00"), "description": "Next year"},
        ]
        with patch("src.ledger.get_ledger_entries", return_value=mock_entries):
            result = get_quarterly_balance(2024)
            self.assertEqual(result["Q1"], Decimal("45.00"))
            self.assertEqual(result["Q2"], Decimal("70.00"))
            self.assertEqual(result["Q3"], Decimal("110.00"))
            self.assertEqual(result["Q4"], Decimal("150.00"))


if __name__ == "__main__":
    unittest.main()
