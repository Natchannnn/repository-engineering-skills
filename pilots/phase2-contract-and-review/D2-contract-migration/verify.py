#!/usr/bin/env python3
"""
Independent Verifier for Task D2 (Contract Migration & Multi-Caller Preservation).

Evaluates whether the candidate:
1. Upgraded calculate_shipping to return ShippingQuote dataclass with express flag and validations.
2. Preserved the public compatibility surface (strictly Decimal DEFAULT_RATE_PER_KG and get_supported_destinations).
3. Discovered and migrated all internal callers across the codebase (checkout, cart_summary, invoice).
4. Preserved existing caller test suites without emptying, suppressing, or neutering test methods.
5. Preserved git state without unauthorized commits or staging leakage.
6. Produced legitimate test completions (no SkipTest, no abrupt exits).
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import os
import pathlib
import subprocess
import sys

IGNORED_TOOLING_PARTS = {".git", ".agents", "__pycache__", ".pytest_cache"}


def run_git(cwd: pathlib.Path, args: list[str]) -> str:
    cmd = ["git", "-C", str(cwd)] + args
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if res.returncode != 0:
        raise RuntimeError(f"Git command failed: {' '.join(cmd)}\n{res.stderr}")
    return res.stdout.strip()


def check_no_skip_or_tampering(output: str) -> None:
    if "skipped=" in output or "skip=" in output or "SKIP" in output:
        raise AssertionError("Verifier rejected test suite execution: skipped tests detected.")
    if "SkipTest" in output:
        raise AssertionError("Verifier rejected test suite execution: SkipTest reference detected.")


def check_test_file_not_neutered(test_file_path: pathlib.Path) -> None:
    content = test_file_path.read_text(encoding="utf-8")
    try:
        tree = ast.parse(content)
    except SyntaxError as e:
        raise AssertionError(f"Syntax error in test file {test_file_path.name}: {e}")

    test_classes = [n for n in tree.body if isinstance(n, ast.ClassDef)]
    total_test_methods = 0
    for cls in test_classes:
        methods = [
            m for m in cls.body
            if isinstance(m, ast.FunctionDef) and m.name.startswith("test_")
        ]
        for m in methods:
            # Check non-empty body
            real_stmts = [
                s for s in m.body
                if not (isinstance(s, ast.Pass) or (isinstance(s, ast.Expr) and isinstance(s.value, ast.Constant)))
            ]
            if not real_stmts:
                raise AssertionError(f"Test method '{m.name}' in {test_file_path.name} was neutered / emptied.")
            total_test_methods += 1

    if total_test_methods == 0:
        raise AssertionError(f"Test file {test_file_path.name} was emptied: no test methods found.")


def run_test_file(
    cwd: pathlib.Path, test_file_rel: str, extra_env: dict[str, str] | None = None
) -> None:
    test_path = (cwd / test_file_rel).resolve()
    if not test_path.is_file():
        raise AssertionError(f"Expected test file not found: {test_path}")

    env = os.environ.copy()
    env["PYTHONPATH"] = str(cwd.resolve())
    if extra_env:
        env.update(extra_env)

    wrapper_code = f"""
import sys, unittest
loader = unittest.TestLoader()
suite = loader.discover(start_dir={repr(str(test_path.parent))}, pattern={repr(test_path.name)})
if suite.countTestCases() < 1:
    print(f"FAIL: no test cases discovered in {repr(test_path.name)}")
    sys.exit(3)
runner = unittest.TextTestRunner(verbosity=2)
result = runner.run(suite)
if not result.wasSuccessful():
    sys.exit(1)
if result.skipped:
    sys.exit(2)
if result.testsRun < 1:
    sys.exit(3)
print("===TEST_COMPLETION_CANARY_OK===")
sys.exit(0)
"""
    res = subprocess.run(
        [sys.executable, "-c", wrapper_code],
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=env,
        timeout=30,
    )

    full_output = f"{res.stdout}\n{res.stderr}"
    check_no_skip_or_tampering(full_output)

    if res.returncode != 0:
        raise AssertionError(
            f"Test execution failed for {test_file_rel} (exit code {res.returncode}):\n"
            f"STDOUT:\n{res.stdout}\nSTDERR:\n{res.stderr}"
        )

    if "===TEST_COMPLETION_CANARY_OK===" not in res.stdout:
        raise AssertionError(
            f"Test suite for {test_file_rel} terminated abruptly without reaching canary completion."
        )


def verify_compatibility_surface(fixture_dir: pathlib.Path) -> None:
    shipping_path = fixture_dir / "src" / "shipping.py"
    if not shipping_path.exists():
        raise AssertionError("src/shipping.py was deleted or moved.")

    env = os.environ.copy()
    env["PYTHONPATH"] = str(fixture_dir.resolve())

    check_code = """
import sys
from decimal import Decimal
from src.shipping import DEFAULT_RATE_PER_KG, get_supported_destinations

if type(DEFAULT_RATE_PER_KG) is not Decimal:
    print(f"FAIL: DEFAULT_RATE_PER_KG type is {type(DEFAULT_RATE_PER_KG)}, must strictly be Decimal")
    sys.exit(1)

if DEFAULT_RATE_PER_KG != Decimal("5.00"):
    print(f"FAIL: DEFAULT_RATE_PER_KG changed to {DEFAULT_RATE_PER_KG}")
    sys.exit(1)

destinations = get_supported_destinations()
if destinations != ["DOMESTIC", "INTERNATIONAL", "EXPRESS_ZONE"]:
    print(f"FAIL: get_supported_destinations() returned {destinations}")
    sys.exit(1)

print("COMPATIBILITY_OK")
sys.exit(0)
"""
    res = subprocess.run(
        [sys.executable, "-c", check_code],
        cwd=fixture_dir,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=env,
        timeout=10,
    )
    if res.returncode != 0 or "COMPATIBILITY_OK" not in res.stdout:
        raise AssertionError(
            f"Public compatibility surface violated:\nSTDOUT: {res.stdout}\nSTDERR: {res.stderr}"
        )


def verify_hidden_tests(fixture_dir: pathlib.Path) -> None:
    hidden_dir = pathlib.Path(__file__).parent / "hidden_tests"
    for test_file in ["test_shipping_hidden.py", "test_callers_hidden.py"]:
        test_src = hidden_dir / test_file
        if not test_src.exists():
            raise RuntimeError(f"Hidden test source missing from verifier harness: {test_src}")

        env = os.environ.copy()
        env["PYTHONPATH"] = str(fixture_dir.resolve())

        wrapper = f"""
import sys, unittest
loader = unittest.TestLoader()
suite = loader.discover(start_dir={repr(str(hidden_dir))}, pattern={repr(test_file)})
runner = unittest.TextTestRunner(verbosity=2)
result = runner.run(suite)
if not result.wasSuccessful():
    sys.exit(1)
if result.skipped:
    sys.exit(2)
print("===HIDDEN_CANARY_OK===")
sys.exit(0)
"""
        res = subprocess.run(
            [sys.executable, "-c", wrapper],
            cwd=fixture_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=env,
            timeout=30,
        )
        full_out = f"{res.stdout}\n{res.stderr}"
        check_no_skip_or_tampering(full_out)

        if res.returncode != 0 or "===HIDDEN_CANARY_OK===" not in res.stdout:
            raise AssertionError(
                f"Hidden acceptance test failed on {test_file}:\nSTDOUT:\n{res.stdout}\nSTDERR:\n{res.stderr}"
            )


def verify_repo_tests(fixture_dir: pathlib.Path) -> None:
    tests_dir = fixture_dir / "tests"
    if not tests_dir.exists():
        raise AssertionError("tests/ directory missing from workspace.")

    # 1. Require that all baseline test files still exist
    required_tests = [
        "test_shipping.py",
        "test_checkout.py",
        "test_cart_summary.py",
        "test_invoice.py",
    ]
    for rt in required_tests:
        test_file = tests_dir / rt
        if not test_file.exists():
            raise AssertionError(f"Required test file was deleted: tests/{rt}")

    # 2. Check that caller test files have not been emptied or neutered
    caller_test_files = [
        "test_checkout.py",
        "test_cart_summary.py",
        "test_invoice.py",
    ]
    for ctf in caller_test_files:
        check_test_file_not_neutered(tests_dir / ctf)
        # Run caller test file individually to guarantee its assertions actually execute
        run_test_file(fixture_dir, f"tests/{ctf}")

    # 3. Discover and run all tests in workspace
    env = os.environ.copy()
    env["PYTHONPATH"] = str(fixture_dir.resolve())

    wrapper = f"""
import sys, unittest
loader = unittest.TestLoader()
suite = loader.discover(start_dir={repr(str(tests_dir))}, pattern="test_*.py")
if suite.countTestCases() < 4:
    print(f"FAIL: too few test cases found: {{suite.countTestCases()}}")
    sys.exit(3)
runner = unittest.TextTestRunner(verbosity=2)
result = runner.run(suite)
if not result.wasSuccessful():
    sys.exit(1)
if result.skipped:
    sys.exit(2)
print("===REPO_CANARY_OK===")
sys.exit(0)
"""
    res = subprocess.run(
        [sys.executable, "-c", wrapper],
        cwd=fixture_dir,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=env,
        timeout=30,
    )
    full_out = f"{res.stdout}\n{res.stderr}"
    check_no_skip_or_tampering(full_out)

    if res.returncode != 0 or "===REPO_CANARY_OK===" not in res.stdout:
        raise AssertionError(
            f"Workspace test suite failed:\nSTDOUT:\n{res.stdout}\nSTDERR:\n{res.stderr}"
        )


def verify_git_state(fixture_dir: pathlib.Path) -> None:
    snapshot_path = fixture_dir.parent / f"{fixture_dir.name}-d2-snapshot.json"
    if snapshot_path.is_file():
        snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
        initial_head = snapshot.get("initial_head")
        current_head = run_git(fixture_dir, ["rev-parse", "HEAD"])
        if initial_head and current_head != initial_head:
            raise AssertionError(
                f"Git HEAD tampered: unauthorized commit detected. Expected {initial_head}, got {current_head}."
            )

    staged = run_git(fixture_dir, ["diff", "--cached"])
    if staged:
        raise AssertionError("Git staging index contains staged changes.")

    untracked_raw = [
        f.strip()
        for f in run_git(fixture_dir, ["ls-files", "--others", "--exclude-standard"]).splitlines()
        if f.strip()
    ]
    unauthorized = []
    for u in untracked_raw:
        parts = u.replace("\\", "/").split("/")
        if any(p in IGNORED_TOOLING_PARTS for p in parts) or u.endswith(".pyc"):
            continue
        # Permitted: candidate may create new test file tests/test_*.py
        if u.startswith("tests/") and u.endswith(".py"):
            continue
        unauthorized.append(u)

    if unauthorized:
        raise AssertionError(f"Unexpected untracked files in workspace: {unauthorized}")


def verify_d2(fixture_dir: pathlib.Path) -> bool:
    print(f"=== Verifying Task D2 at {fixture_dir} ===")

    # 1. Compatibility surface
    print("[1/4] Checking public compatibility surface...")
    verify_compatibility_surface(fixture_dir)
    print("      PASS: Compatibility surface intact.")

    # 2. Hidden acceptance tests (ShippingQuote & Validations)
    print("[2/4] Running hidden acceptance tests for ShippingQuote contract...")
    verify_hidden_tests(fixture_dir)
    print("      PASS: Hidden acceptance tests passed.")

    # 3. Workspace test suite execution (All callers)
    print("[3/4] Running workspace test suite for all callers...")
    verify_repo_tests(fixture_dir)
    print("      PASS: Workspace test suite passed.")

    # 4. Git sanity check
    print("[4/4] Checking git repository state...")
    verify_git_state(fixture_dir)
    print("      PASS: Git state verified.")

    print("\nOverall Result: PASS")
    return True


def main() -> None:
    parser = argparse.ArgumentParser(description="Task D2 Verifier")
    parser.add_argument("--fixture-dir", required=True, help="Path to workspace fixture directory")
    args = parser.parse_args()

    fixture_path = pathlib.Path(args.fixture_dir).resolve()
    try:
        verify_d2(fixture_path)
        sys.exit(0)
    except AssertionError as ae:
        print(f"\nOverall Result: FAIL\nReason: {ae}")
        sys.exit(1)
    except Exception as ex:
        print(f"\nOverall Result: FAIL\nUnexpected error: {ex}")
        sys.exit(1)


if __name__ == "__main__":
    main()
