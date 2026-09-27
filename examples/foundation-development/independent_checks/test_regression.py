"""
Author's independent regression tests for existing contracts.
Ensures that existing baseline functionality and public API signatures are preserved.
"""

import subprocess
import sys
import unittest
import pathlib

class BaselineContractRegressionTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture_dir = pathlib.Path.cwd().resolve()
        if str(cls.fixture_dir) not in sys.path:
            sys.path.insert(0, str(cls.fixture_dir))

    def test_public_core_contract_preserved(self):
        # Dynamically import from src in target workspace
        sys.path.insert(0, str(self.fixture_dir))
        try:
            from src.metric_hub.core import compute_category_totals, parse_csv_file

            # Verify signature and return type contract
            sample_records = [
                {"category": "hardware", "amount": 120.50},
                {"category": "software", "amount": 80.00},
                {"category": "hardware", "amount": 29.50},
            ]
            res = compute_category_totals(sample_records)
            self.assertIn("hardware", res)
            self.assertIn("software", res)
            self.assertEqual(res["hardware"]["count"], 2)
            self.assertEqual(res["hardware"]["total_amount"], 150.00)
            self.assertEqual(res["software"]["count"], 1)
            self.assertEqual(res["software"]["total_amount"], 80.00)
        finally:
            if str(self.fixture_dir) in sys.path:
                sys.path.remove(str(self.fixture_dir))

    def test_baseline_summary_cli_preserved(self):
        sample_csv = self.fixture_dir / "samples" / "transactions.csv"
        self.assertTrue(sample_csv.is_file(), f"Sample CSV missing: {sample_csv}")

        cmd = [sys.executable, "-m", "src.metric_hub.cli", "summary", str(sample_csv)]
        res = subprocess.run(cmd, cwd=str(self.fixture_dir), stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        self.assertEqual(res.returncode, 0, f"Baseline CLI failed: {res.stderr}")
        self.assertIn("Summary Report", res.stdout)
        self.assertIn("electronics", res.stdout.lower())

if __name__ == "__main__":
    unittest.main()
