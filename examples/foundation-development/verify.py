#!/usr/bin/env python3
"""
Independent Verification Runner for Foundation Development Demo.

Executes author-provided verification independent of agent-written code:
1. Scope boundary verification (allowed edits strictly confined to src/metric_hub/, tests/, and exact README.md;
   checks working tree, staged index, and untracked files using NUL-delimited Git output).
2. Author regression test suite (existing summary CLI & core contracts).
3. Author acceptance test suite for new export-json capability (all categories, dynamic datasets, precision, error handling).
4. Documentation synchronization check (README.md updated for export-json).
5. Workspace unit test execution with diff inspection for test changes.
"""

import argparse
import pathlib
import subprocess
import sys

ALLOWED_EXACT_FILES = {
    "README.md",
}

ALLOWED_DIRECTORY_PREFIXES = (
    "src/metric_hub/",
    "tests/",
)

IGNORED_TOOLING_PARTS = {
    ".agents",
    "__pycache__",
    ".pytest_cache",
}

def run_git_bytes(cwd: pathlib.Path, args: list[str]) -> bytes:
    cmd = ["git", "-C", str(cwd)] + args
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if res.returncode != 0:
        err = res.stderr.decode("utf-8", errors="replace").strip()
        raise RuntimeError(f"Git command failed: {' '.join(cmd)}\n{err}")
    return res.stdout

def get_git_paths(cwd: pathlib.Path, args: list[str]) -> list[str]:
    raw = run_git_bytes(cwd, args)
    # NUL-delimited entries: do not strip whitespace from paths
    return [p.decode("utf-8", errors="replace") for p in raw.split(b"\0") if len(p) > 0]

def is_path_allowed(path_str: str) -> bool:
    p = path_str.replace("\\", "/")

    # 1. Ignore tooling directories (.agents/) and ephemeral test caches
    parts = p.split("/")
    if any(part in IGNORED_TOOLING_PARTS for part in parts):
        return True

    # 2. Exact match for specific allowed root files
    if p in ALLOWED_EXACT_FILES:
        return True

    # 3. Directory prefixes (strictly ending in /)
    for prefix in ALLOWED_DIRECTORY_PREFIXES:
        if p.startswith(prefix):
            return True

    return False

def check_scope_boundaries(fixture_dir: pathlib.Path) -> list[str]:
    fixture_dir = fixture_dir.resolve()
    meta_dir = fixture_dir.parent
    head_file = meta_dir / f"{fixture_dir.name}-INITIAL_HEAD"

    if not head_file.is_file():
        raise FileNotFoundError(f"Missing INITIAL_HEAD reference file at: {head_file}. Cannot verify scope boundary.")

    initial_head = head_file.read_text(encoding="utf-8").strip()
    if not initial_head or len(initial_head) != 40:
        raise ValueError(f"Invalid INITIAL_HEAD commit SHA in {head_file}: {initial_head!r}")

    # Inspect all changes across working tree, staged index, and untracked files
    # Use --no-renames so that moves/renames outside allowed scope are not masked by destination paths
    wt_diff = get_git_paths(fixture_dir, ["diff", "-z", "--no-renames", "--name-only", initial_head])
    cached_diff = get_git_paths(fixture_dir, ["diff", "-z", "--no-renames", "--cached", "--name-only", initial_head])
    untracked = get_git_paths(fixture_dir, ["ls-files", "-z", "--others", "--exclude-standard"])

    all_changed_paths = sorted(set(wt_diff) | set(cached_diff) | set(untracked))

    disallowed = []
    for f in all_changed_paths:
        if not is_path_allowed(f):
            disallowed.append(f)

    if disallowed:
        raise AssertionError(
            "Scope boundary violated: modifications detected outside authorized paths:\n"
            + "\n".join(f"  - DISALLOWED: {d}" for d in disallowed)
        )

    # Filter out tooling for reporting
    return [f for f in all_changed_paths if not any(part in IGNORED_TOOLING_PARTS for part in f.replace("\\", "/").split("/"))]

def run_author_test_suite(test_script: pathlib.Path, fixture_dir: pathlib.Path) -> str:
    cmd = [sys.executable, str(test_script)]
    res = subprocess.run(cmd, cwd=str(fixture_dir), stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if res.returncode != 0:
        raise AssertionError(f"Author test suite '{test_script.name}' failed:\n{res.stderr}\n{res.stdout}")
    return res.stdout.strip()

def check_docs_sync(fixture_dir: pathlib.Path):
    readme = fixture_dir / "README.md"
    if not readme.is_file():
        raise FileNotFoundError(f"README.md missing at: {readme}")
    content = readme.read_text(encoding="utf-8")
    if "export-json" not in content:
        raise AssertionError("Documentation drift: README.md does not document the new 'export-json' command.")

def run_agent_tests(fixture_dir: pathlib.Path, initial_head_file: pathlib.Path):
    # Check if tests exist and run them
    cmd = [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"]
    res = subprocess.run(cmd, cwd=str(fixture_dir), stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if res.returncode != 0:
        raise AssertionError(f"Workspace unit test execution failed:\n{res.stderr}\n{res.stdout}")

    # Inspect diff for tests authored or modified by the agent
    test_changes = []
    if initial_head_file.is_file():
        initial_head = initial_head_file.read_text(encoding="utf-8").strip()
        diff_files = get_git_paths(fixture_dir, ["diff", "-z", "--no-renames", "--name-only", initial_head, "--", "tests/"])
        untracked_tests = get_git_paths(fixture_dir, ["ls-files", "-z", "--others", "--exclude-standard", "--", "tests/"])
        test_changes = sorted(set(diff_files) | set(untracked_tests))

    return test_changes

def main():
    parser = argparse.ArgumentParser(description="Verify Foundation Development Demo")
    parser.add_argument("--fixture-dir", required=True, help="Path to fixture workspace")
    args = parser.parse_args()

    fixture_dir = pathlib.Path(args.fixture_dir).resolve()
    script_dir = pathlib.Path(__file__).parent.resolve()
    checks_dir = script_dir / "independent_checks"
    meta_dir = fixture_dir.parent
    initial_head_file = meta_dir / f"{fixture_dir.name}-INITIAL_HEAD"

    print("=== Verifying Foundation Development Demo ===")
    print(f"Workspace: {fixture_dir}\n")

    # 1. Scope Boundary Check
    print("--> Check 1: Verifying change set scope boundaries...")
    try:
        modified = check_scope_boundaries(fixture_dir)
        print(f"    [PASS] Scope preserved: {len(modified)} files changed strictly within authorized boundaries.")
        for m in modified:
            print(f"           - {m}")
    except Exception as e:
        print(f"    [FAIL] {e}", file=sys.stderr)
        sys.exit(1)

    # 2. Existing Public Contract Regressions
    print("\n--> Check 2: Running author independent regression test suite...")
    regress_test = checks_dir / "test_regression.py"
    try:
        run_author_test_suite(regress_test, fixture_dir)
        print("    [PASS] Existing contracts preserved: baseline core functions & summary CLI verified.")
    except Exception as e:
        print(f"    [FAIL] {e}", file=sys.stderr)
        sys.exit(1)

    # 3. New Feature Acceptance Verification
    print("\n--> Check 3: Running author independent acceptance test suite for new feature...")
    feature_test = checks_dir / "test_feature.py"
    try:
        run_author_test_suite(feature_test, fixture_dir)
        print("    [PASS] New feature verified: export-json categories, dynamic dataset, and error exits pass.")
    except Exception as e:
        print(f"    [FAIL] {e}", file=sys.stderr)
        sys.exit(1)

    # 4. Documentation Synchronization
    print("\n--> Check 4: Verifying documentation synchronization...")
    try:
        check_docs_sync(fixture_dir)
        print("    [PASS] Documentation synchronized: README.md documents export-json usage.")
    except Exception as e:
        print(f"    [FAIL] {e}", file=sys.stderr)
        sys.exit(1)

    # 5. Workspace Unit Tests Execution
    print("\n--> Check 5: Running workspace unit test suite...")
    try:
        test_changes = run_agent_tests(fixture_dir, initial_head_file)
        if test_changes:
            print(f"    [PASS] Workspace unit tests pass cleanly. Test file changes detected: {', '.join(test_changes)}")
        else:
            print("    [PASS] Workspace unit tests pass cleanly.")
            print("    [NOTE] No modified or added test files were detected under tests/ relative to baseline.")
    except Exception as e:
        print(f"    [FAIL] {e}", file=sys.stderr)
        sys.exit(1)

    print("\nOVERALL VERIFICATION: PASSED (Independent contracts, scope, docs, and feature tests verified)")
    sys.exit(0)

if __name__ == "__main__":
    main()
