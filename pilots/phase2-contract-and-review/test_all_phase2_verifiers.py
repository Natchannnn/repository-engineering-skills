#!/usr/bin/env python3
"""
Unified self-audit runner for all Phase 2 verifiers:
- Task D2 (Contract Migration & Multi-Caller Preservation): 7 tests
- Task R2A (Neutral Review Fixture A - Clean): 4 tests
- Task R2B (Neutral Review Fixture B - Defect): 6 tests
Total: 17 self-audit tests.
"""

from __future__ import annotations

import importlib.util
import pathlib
import sys
import unittest

DIR = pathlib.Path(__file__).parent.resolve()


def load_module_from_file(module_name: str, file_path: pathlib.Path):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load module from {file_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def suite():
    combined_suite = unittest.TestSuite()

    mod_d2 = load_module_from_file("p2_d2_test_verifier", DIR / "D2-contract-migration" / "test_verifier.py")
    mod_r2a = load_module_from_file("p2_r2a_test_verifier", DIR / "R2A-neutral-review" / "test_verifier.py")
    mod_r2b = load_module_from_file("p2_r2b_test_verifier", DIR / "R2B-neutral-review" / "test_verifier.py")

    loader = unittest.defaultTestLoader
    combined_suite.addTests(loader.loadTestsFromModule(mod_d2))
    combined_suite.addTests(loader.loadTestsFromModule(mod_r2a))
    combined_suite.addTests(loader.loadTestsFromModule(mod_r2b))
    return combined_suite


if __name__ == "__main__":
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite())
    sys.exit(0 if result.wasSuccessful() else 1)
