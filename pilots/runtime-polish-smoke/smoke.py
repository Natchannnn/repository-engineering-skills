"""Prepare and independently verify six bounded agent smoke cases.

Runner agents receive only their prompt, workspace, and installed runtime copies.
Keep this evaluator and its snapshots outside their permitted reading scope.
"""

import argparse
import difflib
import hashlib
import importlib.util
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]

CASES = {
    "F1": {
        "skill": "repo-foundation", "installed": ["repo-foundation", "repo-native-refactor"],
        "prompt": "Fix normalize_amount so integer 0 is preserved as a valid amount. None and the empty string must still default to 10; preserve all other behavior. Add regression coverage. Do not commit or push.",
        "app": '# OPS-417: the legacy import worker omits amounts on some records.\ndef normalize_amount(value):\n    return int(value or 10)\n',
        "readme": "normalize_amount accepts integer-like amounts. Missing values (None or empty string) default to 10. Integer 0 is a valid amount.\nRun python -B -m unittest discover -p 'test*.py'.\n",
        "tests": 'import unittest\nfrom app import normalize_amount\n\nclass AmountTest(unittest.TestCase):\n    def test_default(self):\n        self.assertEqual(normalize_amount(None), 10)\n    def test_number(self):\n        self.assertEqual(normalize_amount("3"), 3)\n',
    },
    "F2": {
        "skill": "repo-foundation", "installed": ["repo-foundation", "repo-native-refactor"],
        "prompt": "Change output_path(root) to return pathlib.Path. This is an approved public API change. Update its callers, tests, and README; label_output(root) must still return report.json. Then use the installed repo-native-refactor skill for one scoped review of the completed change. Do not commit or push.",
        "app": 'def output_path(root):\n    return str(root).rstrip("/") + "/report.json"\n\ndef label_output(root):\n    return output_path(root).split("/")[-1]\n',
        "readme": "output_path(root) returns a str naming report.json under root. label_output(root) returns the final filename, report.json.\nRun python -B -m unittest discover -p 'test*.py'.\n",
        "tests": 'import unittest\nfrom app import output_path, label_output\n\nclass PathTest(unittest.TestCase):\n    def test_path_type(self):\n        self.assertIsInstance(output_path("out"), str)\n    def test_label(self):\n        self.assertEqual(label_output("out"), "report.json")\n',
    },
    "F3": {
        "skill": "repo-foundation", "installed": ["repo-foundation"],
        "prompt": "Add optional include_count=True to summarize(values), returning a dictionary with total and count. Keep the default integer result unchanged, including for empty input. Add tests and document the option. Do not commit or push.",
        "app": 'def summarize(values):\n    return sum(values)\n',
        "readme": "summarize(values) returns the integer total; empty input returns 0.\nRun python -B -m unittest discover -p 'test*.py'.\n",
        "tests": 'import unittest\nfrom app import summarize\n\nclass SummaryTest(unittest.TestCase):\n    def test_total(self):\n        self.assertEqual(summarize([2, 3]), 5)\n    def test_empty(self):\n        self.assertEqual(summarize([]), 0)\n',
    },
    "R1": {
        "skill": "repo-native-refactor", "installed": ["repo-native-refactor"],
        "prompt": "Clean up redundant comments in app.py while preserving operational rationale and behavior. The local issue tracker is unavailable in this workspace. Do not invent historical context. Do not commit or push.",
        "app": 'def encode_ticket(ticket):\n    # Get the normalized representation.\n    normalized = ticket.strip().upper()\n    # OPS-417: the partner gateway rejects a trailing newline.\n    return normalized\n',
        "readme": "encode_ticket strips surrounding whitespace and uppercases the ticket. The partner gateway rejects trailing newlines.\nRun python -B -m unittest discover -p 'test*.py'.\n",
        "tests": 'import unittest\nfrom app import encode_ticket\n\nclass TicketTest(unittest.TestCase):\n    def test_ticket(self):\n        self.assertEqual(encode_ticket(" ab-1\\n"), "AB-1")\n',
    },
    "R2": {
        "skill": "repo-native-refactor", "installed": ["repo-native-refactor"],
        "prompt": "Review the proposed change in change.patch against baseline.py and the documented contracts. Report evidence-backed defects only with their file, symbol, and consequence. Do not edit any workspace files. Do not commit or push.",
        "app": 'from pathlib import Path\n\ndef cache_path(root):\n    return Path(root) / "cache.json"\n\ndef cache_key(root):\n    return cache_path(root).startswith("cache")\n',
        "baseline": 'def cache_path(root):\n    return root.rstrip("/") + "/cache.json"\n\ndef cache_key(root):\n    return cache_path(root).startswith("cache")\n',
        "readme": "cache_path(root) publicly returns str; cache_key(root) consumes it with startswith and returns a bool. This change has no authorization to alter the public contract.\nRun python -B -m unittest discover -p 'test*.py'.\n",
        "tests": 'import unittest\nfrom app import cache_key\n\nclass CacheTest(unittest.TestCase):\n    def test_key(self):\n        self.assertFalse(cache_key("out"))\n',
    },
    "R3": {
        "skill": "repo-native-refactor", "installed": ["repo-native-refactor"],
        "prompt": "Review app.py against its documented behavior and callers. Report evidence-backed defects only with their file, symbol, and consequence. Do not edit any workspace files. Do not commit or push.",
        "app": 'def encode_tag(value):\n    """Return a trimmed uppercase tag; invalid input raises ValueError."""\n    if not isinstance(value, str) or not value.strip():\n        raise ValueError("invalid tag")\n    return value.strip().upper()\n',
        "readme": "encode_tag returns a trimmed uppercase string. Empty, whitespace-only, and non-string values raise ValueError with the text invalid tag.\nRun python -B -m unittest discover -p 'test*.py'.\n",
        "tests": 'import unittest\nfrom app import encode_tag\n\nclass TagTest(unittest.TestCase):\n    def test_tag(self):\n        self.assertEqual(encode_tag(" ab-1 "), "AB-1")\n    def test_invalid(self):\n        for value in ("", " ", None, 0):\n            with self.subTest(value=value), self.assertRaisesRegex(ValueError, "^invalid tag$"):\n                encode_tag(value)\n',
    },
}


def inventory(directory):
    return {p.relative_to(directory).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(directory.rglob("*")) if p.is_file()}


def prepare(output):
    output.mkdir(parents=True, exist_ok=False)
    runtime = output / "package"
    result = subprocess.run(
        [shutil.which("pwsh") or "powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File",
         str(ROOT / "scripts" / "package-runtime.ps1"), "-AllowDirty", "-OutputDir", str(runtime)],
        capture_output=True, text=True,
    )
    if result.returncode:
        raise RuntimeError(result.stdout + result.stderr)
    print(result.stdout.strip())
    shutil.unpack_archive(str(runtime / "repository-engineering-skills-runtime.zip"), str(runtime / "unpacked"))
    manifest = json.loads((runtime / "unpacked" / "manifest.json").read_text(encoding="utf-8-sig"))
    assert manifest["file_count"] == 23
    for case_id, case in CASES.items():
        case_root = output / case_id
        workspace = case_root / "workspace"
        workspace.mkdir(parents=True)
        for filename, key in (("app.py", "app"), ("README.md", "readme"), ("test_app.py", "tests")):
            (workspace / filename).write_text(case[key], encoding="utf-8", newline="\n")
        if "baseline" in case:
            (workspace / "baseline.py").write_text(case["baseline"], encoding="utf-8", newline="\n")
            diff = difflib.unified_diff(case["baseline"].splitlines(keepends=True), case["app"].splitlines(keepends=True), "a/app.py", "b/app.py")
            (workspace / "change.patch").write_text("".join(diff), encoding="utf-8", newline="\n")
        skills = case_root / "runtime" / "skills"
        skills.mkdir(parents=True)
        for name in case["installed"]:
            shutil.copytree(runtime / "unpacked" / "skills" / name, skills / name)
        shutil.copytree(workspace, case_root / "before")
        (case_root / "runtime-before.json").write_text(json.dumps(inventory(case_root / "runtime"), indent=2), encoding="utf-8")
        skill_path = skills / case["skill"] / "SKILL.md"
        prompt = (
            f"Use ${case['skill']} at {skill_path} to complete this request:\n\n{case['prompt']}\n\n"
            f"Workspace: {workspace}\nInstalled skills: {skills}\n"
            "Use only that workspace and those installed skills for task context. Do not read the source skill repository, evaluator, snapshots, or other cases. "
            "Other skills are available only if present in that installed directory. Use python -B for checks. "
            "Do not access the network, create Git history, or alter installed skill files. "
            f"At completion write a concise JSON report to {case_root / 'submission.json'} with keys summary, findings (a list; each finding has file, symbol, consequence), "
            "skills_read, and checks (commands and observed results). Do not include metadata-only suggestions as defects. "
            "For implementation tasks, findings may be empty. Keep task edits inside the workspace; the report is the sole additional output."
        )
        (case_root / "prompt.txt").write_text(prompt, encoding="utf-8")
    (output / "plan.json").write_text(json.dumps({"cases": list(CASES), "kind": "explicit-invocation smoke", "repetitions": 1, "source_commit": manifest["source_commit"], "runtime_files": manifest["files"]}, indent=2), encoding="utf-8")
    print("Prepared cases:", ", ".join(CASES))
    print("Run root:", output)


def checks_in_copy(workspace, replacement=None):
    with tempfile.TemporaryDirectory(prefix="smoke-independent-check-") as directory:
        copied = Path(directory) / "workspace"
        shutil.copytree(workspace, copied)
        if replacement is not None:
            (copied / "app.py").write_text(replacement, encoding="utf-8")
        result = subprocess.run([sys.executable, "-B", "-m", "unittest", "discover", "-p", "test*.py"], cwd=copied, capture_output=True, text=True, timeout=30)
        return {"exit_code": result.returncode, "output": result.stdout + result.stderr}


def load_app(workspace, case_id):
    spec = importlib.util.spec_from_file_location("smoke_" + case_id, workspace / "app.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def verify(output):
    results = {}
    for case_id, case in CASES.items():
        case_root = output / case_id
        workspace = case_root / "workspace"
        failures = []
        evidence = {}
        try:
            submission = json.loads((case_root / "submission.json").read_text(encoding="utf-8"))
            assert isinstance(submission["findings"], list), "findings must be a list"
            assert inventory(case_root / "runtime") == json.loads((case_root / "runtime-before.json").read_text(encoding="utf-8")), "installed skill files changed"
            module = load_app(workspace, case_id)
            if case_id in ("R2", "R3"):
                assert inventory(workspace) == inventory(case_root / "before"), "read-only workspace was mutated"
            if case_id == "F1":
                assert [module.normalize_amount(v) for v in (0, None, "", "3", -2)] == [0, 10, 10, 3, -2]
                assert "OPS-417" in (workspace / "app.py").read_text(encoding="utf-8"), "existing issue reference removed"
            elif case_id == "F2":
                assert isinstance(module.output_path("out"), Path), "approved Path contract was not retained"
                assert module.output_path("out") == Path("out") / "report.json"
                assert module.label_output("out") == "report.json"
                assert "Path" in (workspace / "README.md").read_text(encoding="utf-8"), "new contract absent from documentation"
            elif case_id == "F3":
                assert module.summarize([2, 3]) == 5 and type(module.summarize([])) is int
                assert module.summarize([2, 3], include_count=True) == {"total": 5, "count": 2}
                assert module.summarize([], include_count=True) == {"total": 0, "count": 0}
                assert "include_count" in (workspace / "README.md").read_text(encoding="utf-8"), "option absent from documentation"
            elif case_id == "R1":
                assert module.encode_ticket(" ab-1\n") == "AB-1"
                source = (workspace / "app.py").read_text(encoding="utf-8")
                assert "OPS-417" in source and "gateway" in source and "newline" in source, "operational rationale or reference removed"
                assert "Get the normalized representation" not in source, "requested redundant comment cleanup missing"
            elif case_id == "R2":
                findings = submission["findings"]
                assert any(f.get("symbol") in ("cache_path", "cache_key") and "app.py" in f.get("file", "") for f in findings), "contract defect not reported"
                try:
                    module.cache_key("out")
                except AttributeError as error:
                    evidence["observed_defect"] = str(error)
                else:
                    raise AssertionError("fixture defect no longer reproduces")
            elif case_id == "R3":
                assert submission["findings"] == [], "clean fixture received defect findings"
            evidence["candidate_tests"] = checks_in_copy(workspace)
            if case_id != "R2":
                assert evidence["candidate_tests"]["exit_code"] == 0, "candidate tests failed"
            if case_id.startswith("F"):
                evidence["regression_negative_control"] = checks_in_copy(workspace, case["app"])
                assert evidence["regression_negative_control"]["exit_code"] != 0, "candidate tests did not reject the original missing behavior"
            evidence["skills_read_self_reported"] = submission.get("skills_read", [])
        except Exception as error:
            failures.append(f"{type(error).__name__}: {error}")
        results[case_id] = {"pass": not failures, "failures": failures, "evidence": evidence}
        print(case_id, "PASS" if not failures else "FAIL", "; ".join(failures))
    (output / "verification.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
    if not all(result["pass"] for result in results.values()):
        raise SystemExit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("prepare", "verify"))
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    if args.action == "prepare":
        prepare(args.output.resolve())
    else:
        verify(args.output.resolve())
