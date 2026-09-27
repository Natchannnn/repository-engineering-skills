"""
Author's independent acceptance tests for the newly added export-json feature.
Validates behavior, full category coverage, dynamic data parsing, data types, precision,
and error handling independently of agent code.
"""

import json
import pathlib
import subprocess
import sys
import tempfile
import unittest

SYNTHETIC_CSV_CONTENT = """id,category,amount
101,apparel,12.50
102,home_goods,80.00
103,apparel,37.50
104,office,15.25
105,home_goods,20.00
"""

class IndependentFeatureAcceptanceTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture_dir = pathlib.Path.cwd().resolve()
        if str(cls.fixture_dir) not in sys.path:
            sys.path.insert(0, str(cls.fixture_dir))

    def _assert_category_data(self, categories: dict, category_name: str, expected_count: int, expected_amount: float):
        self.assertIn(category_name, categories, f"Missing category '{category_name}' in exported categories")
        cat_data = categories[category_name]
        self.assertIsInstance(cat_data, dict, f"Category '{category_name}' value must be a dictionary")
        self.assertIn("count", cat_data)
        self.assertIn("total_amount", cat_data)

        # Verify strict integer type for count
        self.assertIsInstance(cat_data["count"], int, f"Category '{category_name}' count must be an int")
        self.assertNotIsInstance(cat_data["count"], bool)
        self.assertEqual(cat_data["count"], expected_count)

        # Verify numeric type and value for total_amount
        self.assertTrue(
            isinstance(cat_data["total_amount"], (int, float)) and not isinstance(cat_data["total_amount"], bool),
            f"Category '{category_name}' total_amount must be numeric"
        )
        self.assertAlmostEqual(cat_data["total_amount"], expected_amount, places=2)

    def test_export_json_sample_csv_all_categories_and_types(self):
        sample_csv = self.fixture_dir / "samples" / "transactions.csv"
        self.assertTrue(sample_csv.is_file(), f"Sample CSV missing: {sample_csv}")

        with tempfile.TemporaryDirectory() as td:
            out_json = pathlib.Path(td) / "exported_metrics.json"

            cmd = [
                sys.executable, "-m", "src.metric_hub.cli",
                "export-json", str(sample_csv),
                "--out", str(out_json)
            ]
            res = subprocess.run(cmd, cwd=str(self.fixture_dir), stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            self.assertEqual(res.returncode, 0, f"export-json CLI failed with code {res.returncode}:\n{res.stderr}")
            self.assertTrue(out_json.is_file(), "Target JSON file was not created by export-json")

            data = json.loads(out_json.read_text(encoding="utf-8"))
            self.assertEqual(data.get("status"), "success")

            # Check record_count strict int
            self.assertIn("record_count", data)
            self.assertIsInstance(data["record_count"], int, "record_count must be an integer")
            self.assertNotIsInstance(data["record_count"], bool)
            self.assertEqual(data["record_count"], 6)

            # Check categories completeness
            self.assertIn("categories", data)
            categories = data["categories"]
            expected_categories = {"electronics", "books", "groceries"}
            self.assertEqual(set(categories.keys()), expected_categories, "Exported categories must match all distinct CSV categories")

            # Check exact values for all 3 categories
            self._assert_category_data(categories, "electronics", 3, 450.00)
            self._assert_category_data(categories, "books", 2, 55.00)
            self._assert_category_data(categories, "groceries", 1, 45.50)

    def test_export_json_dynamic_synthetic_dataset(self):
        with tempfile.TemporaryDirectory() as td:
            synth_csv = pathlib.Path(td) / "dynamic_input.csv"
            synth_csv.write_text(SYNTHETIC_CSV_CONTENT, encoding="utf-8")
            out_json = pathlib.Path(td) / "synthetic_metrics.json"

            cmd = [
                sys.executable, "-m", "src.metric_hub.cli",
                "export-json", str(synth_csv),
                "--out", str(out_json)
            ]
            res = subprocess.run(cmd, cwd=str(self.fixture_dir), stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            self.assertEqual(res.returncode, 0, f"export-json CLI failed on synthetic data with code {res.returncode}:\n{res.stderr}")
            self.assertTrue(out_json.is_file(), "Target JSON file was not created for synthetic CSV")

            data = json.loads(out_json.read_text(encoding="utf-8"))
            self.assertEqual(data.get("status"), "success")

            self.assertIn("record_count", data)
            self.assertIsInstance(data["record_count"], int)
            self.assertNotIsInstance(data["record_count"], bool)
            self.assertEqual(data["record_count"], 5)

            categories = data.get("categories", {})
            expected_categories = {"apparel", "home_goods", "office"}
            self.assertEqual(set(categories.keys()), expected_categories, "Categories must be dynamically read from input CSV")

            self._assert_category_data(categories, "apparel", 2, 50.00)
            self._assert_category_data(categories, "home_goods", 2, 100.00)
            self._assert_category_data(categories, "office", 1, 15.25)

    def test_export_json_nonexistent_input_fails_safely(self):
        with tempfile.TemporaryDirectory() as td:
            nonexistent_csv = pathlib.Path(td) / "does_not_exist.csv"
            out_json = pathlib.Path(td) / "should_not_exist.json"

            cmd = [
                sys.executable, "-m", "src.metric_hub.cli",
                "export-json", str(nonexistent_csv),
                "--out", str(out_json)
            ]
            res = subprocess.run(cmd, cwd=str(self.fixture_dir), stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            self.assertNotEqual(res.returncode, 0, "CLI should return non-zero exit code for nonexistent input file")
            self.assertFalse(out_json.is_file(), "Output file must not be created on invalid input")

if __name__ == "__main__":
    unittest.main()
