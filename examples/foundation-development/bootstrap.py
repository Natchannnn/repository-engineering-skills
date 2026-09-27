#!/usr/bin/env python3
"""
Bootstraps an isolated Git repository fixture for the Foundation Development Demo.

Scenario:
- 'main' branch contains a data aggregation tool 'metric_hub' with baseline CSV summary CLI and tests.
- Target task for repo-foundation: Implement additive capability 'export-json' to export category metrics
  as formatted JSON to a designated output file.
- Preserves existing summary CLI and core functions, authors proportionate tests, and updates living docs.
"""

import argparse
import pathlib
import subprocess

CORE_PY = '''"""Core data processing and aggregation logic."""

import csv
import pathlib

def parse_csv_file(file_path: str) -> list[dict]:
    """Parses a CSV file into a list of record dictionaries."""
    p = pathlib.Path(file_path)
    if not p.is_file():
        raise FileNotFoundError(f"CSV file not found: {file_path}")

    records = []
    with open(p, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            records.append({
                "id": row.get("id", "").strip(),
                "category": row.get("category", "uncategorized").strip().lower(),
                "amount": float(row.get("amount", 0.0)),
            })
    return records

def compute_category_totals(records: list[dict]) -> dict:
    """Computes record counts and total amounts grouped by category."""
    totals = {}
    for r in records:
        cat = r.get("category", "uncategorized")
        amt = float(r.get("amount", 0.0))
        if cat not in totals:
            totals[cat] = {"count": 0, "total_amount": 0.0}
        totals[cat]["count"] += 1
        totals[cat]["total_amount"] = round(totals[cat]["total_amount"] + amt, 2)
    return totals
'''

CLI_PY = '''"""Command-line interface for metric_hub."""

import argparse
import sys
from src.metric_hub.core import parse_csv_file, compute_category_totals

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="metric_hub", description="Data aggregation utility")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Baseline command: summary
    summary_parser = subparsers.add_parser("summary", help="Display text summary of metrics")
    summary_parser.add_argument("csv_path", help="Path to input CSV file")

    return parser

def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "summary":
        try:
            records = parse_csv_file(args.csv_path)
        except Exception as e:
            print(f"Error reading CSV: {e}", file=sys.stderr)
            sys.exit(1)

        totals = compute_category_totals(records)
        print("=== Metric Hub Summary Report ===")
        print(f"Total Records: {len(records)}")
        for cat, data in sorted(totals.items()):
            print(f"Category: {cat:<15} | Count: {data['count']:<4} | Total: ${data['total_amount']:.2f}")

if __name__ == "__main__":
    main()
'''

TEST_CORE = '''import unittest
from src.metric_hub.core import compute_category_totals

class CoreMetricsTest(unittest.TestCase):
    def test_compute_category_totals(self):
        records = [
            {"category": "books", "amount": 15.00},
            {"category": "books", "amount": 25.50},
            {"category": "groceries", "amount": 50.00},
        ]
        res = compute_category_totals(records)
        self.assertEqual(res["books"]["count"], 2)
        self.assertEqual(res["books"]["total_amount"], 40.50)
        self.assertEqual(res["groceries"]["count"], 1)
        self.assertEqual(res["groceries"]["total_amount"], 50.00)

if __name__ == "__main__":
    unittest.main()
'''

TEST_CLI = '''import unittest
import subprocess
import sys
import pathlib

class CliSummaryTest(unittest.TestCase):
    def test_cli_summary_execution(self):
        root = pathlib.Path(__file__).parent.parent
        sample = root / "samples" / "transactions.csv"
        cmd = [sys.executable, "-m", "src.metric_hub.cli", "summary", str(sample)]
        res = subprocess.run(cmd, cwd=str(root), stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        self.assertEqual(res.returncode, 0)
        self.assertIn("Summary Report", res.stdout)
        self.assertIn("books", res.stdout.lower())

if __name__ == "__main__":
    unittest.main()
'''

SAMPLE_CSV = '''id,category,amount
1,electronics,150.00
2,books,25.00
3,electronics,200.00
4,groceries,45.50
5,books,30.00
6,electronics,100.00
'''

README_MD = '''# Metric Hub

Lightweight data processing tool to summarize financial metrics from CSV datasets.

## Usage

### Summary View
Print a human-readable text table summarizing records by category:

```bash
python -m src.metric_hub.cli summary samples/transactions.csv
```
'''

PYPROJECT_TOML = '''[build-system]
requires = ["setuptools"]
build-backend = "setuptools.build_meta"

[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["."]
'''

GITIGNORE = '''__pycache__/
*.py[cod]
.pytest_cache/
.agents/
'''

def run_git(cwd, args):
    cmd = ["git", "-C", str(cwd)] + args
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if res.returncode != 0:
        raise RuntimeError(f"Git command failed: {' '.join(cmd)}\n{res.stderr.strip()}")
    return res.stdout.strip()

def validate_target_safety(target_dir: pathlib.Path, sidecar_paths: list[pathlib.Path]):
    target_dir = target_dir.resolve()
    if target_dir.exists():
        if not target_dir.is_dir():
            raise FileExistsError(f"Target path '{target_dir}' exists and is not a directory. Aborting to protect data.")
        try:
            next(target_dir.iterdir())
            has_files = True
        except StopIteration:
            has_files = False
        if has_files:
            raise FileExistsError(
                f"Target directory '{target_dir}' already exists and is not empty. "
                "Aborting to avoid overwriting or mixing with existing data."
            )

    for sidecar in sidecar_paths:
        if sidecar.exists():
            raise FileExistsError(
                f"Sidecar file '{sidecar}' already exists. "
                "Aborting to prevent overwriting existing baseline metadata."
            )

def build_fixture(target_dir: pathlib.Path):
    target_dir = target_dir.resolve()
    meta_dir = target_dir.parent
    initial_head_file = meta_dir / f"{target_dir.name}-INITIAL_HEAD"

    # Pre-flight safety check before ANY filesystem mutation
    validate_target_safety(target_dir, [initial_head_file])

    target_dir.mkdir(parents=True, exist_ok=True)

    # 1. Initialize git
    run_git(target_dir, ["init", "-b", "main"])
    run_git(target_dir, ["config", "user.email", "foundation-demo@example.com"])
    run_git(target_dir, ["config", "user.name", "Foundation Demo"])

    # 2. Setup source tree
    src_dir = target_dir / "src" / "metric_hub"
    src_dir.mkdir(parents=True, exist_ok=True)
    (target_dir / "src" / "__init__.py").write_text("", encoding="utf-8")
    (src_dir / "__init__.py").write_text("", encoding="utf-8")
    (src_dir / "core.py").write_text(CORE_PY, encoding="utf-8")
    (src_dir / "cli.py").write_text(CLI_PY, encoding="utf-8")

    tests_dir = target_dir / "tests"
    tests_dir.mkdir(parents=True, exist_ok=True)
    (tests_dir / "__init__.py").write_text("", encoding="utf-8")
    (tests_dir / "test_core.py").write_text(TEST_CORE, encoding="utf-8")
    (tests_dir / "test_cli.py").write_text(TEST_CLI, encoding="utf-8")

    samples_dir = target_dir / "samples"
    samples_dir.mkdir(parents=True, exist_ok=True)
    (samples_dir / "transactions.csv").write_text(SAMPLE_CSV, encoding="utf-8")

    (target_dir / "README.md").write_text(README_MD, encoding="utf-8")
    (target_dir / "pyproject.toml").write_text(PYPROJECT_TOML, encoding="utf-8")
    (target_dir / ".gitignore").write_text(GITIGNORE, encoding="utf-8")

    # 3. Commit initial baseline
    run_git(target_dir, ["add", "."])
    run_git(target_dir, ["commit", "-m", "feat: initial metric hub implementation with summary command"])
    base_commit = run_git(target_dir, ["rev-parse", "HEAD"])

    meta_dir = target_dir.parent
    initial_head_file = meta_dir / f"{target_dir.name}-INITIAL_HEAD"
    initial_head_file.write_text(base_commit, encoding="utf-8")

    print(f"Successfully bootstrapped Foundation Demo fixture at: {target_dir}")
    print(f"Initial Commit (main): {base_commit}")
    print(f"Baseline Head File:    {initial_head_file}")

def main():
    parser = argparse.ArgumentParser(description="Bootstrap Foundation Development Demo Fixture")
    parser.add_argument("target_dir", help="Path to create fixture repository")
    args = parser.parse_args()
    try:
        build_fixture(pathlib.Path(args.target_dir))
    except Exception as e:
        print(f"Error bootstrapping fixture: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
