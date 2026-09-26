from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


HARNESS_PATH = Path(__file__).resolve().parents[1] / "harness.py"
SPEC = importlib.util.spec_from_file_location("repo_native_harness", HARNESS_PATH)
assert SPEC and SPEC.loader
harness = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(harness)


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def run_git(repo: Path, *args: str) -> None:
    result = subprocess.run(
        ["git", "-C", str(repo), *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    if result.returncode:
        raise AssertionError(result.stderr)


class HarnessTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(prefix="harness-test-")
        self.root = Path(self.temp.name)
        self.repo = self.root / "repo"
        self.repo.mkdir()
        (self.repo / "app.py").write_text("VALUE = 1\n", encoding="utf-8")
        (self.repo / "generated").mkdir()
        (self.repo / "generated" / "client.py").write_text("GENERATED = True\n", encoding="utf-8")
        run_git(self.repo, "init", "--quiet")
        run_git(self.repo, "config", "user.name", "Harness Test")
        run_git(self.repo, "config", "user.email", "harness-test.invalid")
        run_git(self.repo, "add", "--all")
        run_git(self.repo, "commit", "--quiet", "-m", "fixture")

        self.skill = self.root / "skill"
        (self.skill / "evals").mkdir(parents=True)
        (self.skill / "SKILL.md").write_text(
            "---\nname: fixture-skill\ndescription: Test skill.\n---\n\n# Fixture\n",
            encoding="utf-8",
        )
        (self.skill / "evals" / "secret.txt").write_text("EXPECTED PATCH", encoding="utf-8")

        check = [sys.executable, "-c", "from pathlib import Path; assert Path('app.py').read_text() == 'VALUE = 1\\n'"]
        self.suite = {
            "$schema": harness.SUITE_SCHEMA,
            "name": "integration",
            "repetitions": 1,
            "variants": [
                {"id": "baseline", "skill": None},
                {"id": "candidate", "skill": str(self.skill)},
            ],
            "cases": [
                {
                    "id": "case-one",
                    "repository": str(self.repo),
                    "revision": "HEAD",
                    "task": "Make the completed change repository-native without changing behavior.",
                    "verification": [{"id": "tests", "argv": check, "timeout_seconds": 30}],
                    "protected_paths": ["generated/**"],
                    "allowed_paths": ["app.py"],
                }
            ],
        }
        self.bars = {
            "$schema": harness.BARS_SCHEMA,
            "first_principles": ["Preserve behavior."],
            "dimensions": [
                {"id": "semantic", "weight": 2, "bar": "Behavior is preserved."},
                {"id": "native", "weight": 1, "bar": "The result fits the repository."},
            ],
            "cases": [{"id": "case-one", "outcome": "A bounded behavior-preserving result.", "smells": ["Speculative churn."]}],
            "certification": {"required_repetitions": 1, "min_pass_rate": 1.0, "min_rating": 10.0},
        }
        self.suite_path = self.root / "suite.json"
        self.bars_path = self.root / "bars.json"
        write_json(self.suite_path, self.suite)
        write_json(self.bars_path, self.bars)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def run_cli(self, *args: str) -> None:
        if args[0] == "prepare" and "--bars" not in args:
            args = (*args, "--bars", str(self.bars_path))
        result = subprocess.run(
            [sys.executable, str(HARNESS_PATH), *args],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)

    def test_end_to_end_blind_protocol(self) -> None:
        run_root = self.root / "run"
        self.run_cli("validate", "--suite", str(self.suite_path), "--bars", str(self.bars_path))
        self.run_cli("prepare", "--suite", str(self.suite_path), "--out", str(run_root))

        manifest = json.loads((run_root / "control/prepared/manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(len(manifest["packets"]), 2)
        for packet_info in manifest["packets"]:
            packet = Path(packet_info["path"])
            prompt = (packet / "prompt.md").read_text(encoding="utf-8")
            self.assertNotIn("Speculative churn", prompt)
            self.assertNotIn("A bounded behavior-preserving result", prompt)
            (packet / "runner-report.md").write_text("No change was necessary; verification passed.\n", encoding="utf-8")
            if packet_info["variant_id"] == "candidate":
                self.assertTrue((packet / "skill" / "SKILL.md").is_file())
                self.assertFalse((packet / "skill" / "evals").exists())

        self.run_cli("collect", "--run", str(run_root))
        self.run_cli("judge", "--run", str(run_root), "--bars", str(self.bars_path))
        index = json.loads((run_root / "control" / "judge-index.json").read_text(encoding="utf-8"))
        for artifact in index["artifacts"]:
            self.assertTrue((Path(artifact["path"]) / "repository" / "app.py").is_file())
            judgment = {
                "$schema": harness.JUDGMENT_SCHEMA,
                "artifact_id": artifact["artifact_id"],
                "verdict": "pass",
                "bar_evidence": [{"id": key, "claim": claim, "verdict": "pass", "evidence": "Synthetic self-test judgment."}
                                 for key, claim in harness.required_bars(self.bars["cases"][0], self.bars).items()],
                "hard_failures": [],
                "dimensions": [
                    {"id": "semantic", "score": 4, "evidence": ["All checks passed."]},
                    {"id": "native", "score": 4, "evidence": ["No unsupported change was introduced."]},
                ],
                "confidence": "high",
                "notes": "",
            }
            write_json(Path(artifact["path"]) / "judgment.json", judgment)

        self.run_cli("score", "--run", str(run_root), "--bars", str(self.bars_path))
        scorecard = json.loads((run_root / "scorecard.json").read_text(encoding="utf-8"))
        self.assertEqual({item["id"] for item in scorecard["variants"]}, {"baseline", "candidate"})
        self.assertTrue(all(item["perfect_on_current_suite"] for item in scorecard["variants"]))
        self.assertTrue(all(item["certified"] for item in scorecard["variants"]))

    def test_collect_flags_protected_path_change(self) -> None:
        self.suite["variants"] = [{"id": "candidate", "skill": str(self.skill)}]
        write_json(self.suite_path, self.suite)
        run_root = self.root / "protected-run"
        self.run_cli("prepare", "--suite", str(self.suite_path), "--out", str(run_root))
        manifest = json.loads((run_root / "control/prepared/manifest.json").read_text(encoding="utf-8"))
        packet = Path(manifest["packets"][0]["path"])
        (packet / "workspace" / "generated" / "client.py").write_text("GENERATED = False\n", encoding="utf-8")
        (packet / "runner-report.md").write_text("Changed generated output.\n", encoding="utf-8")
        self.run_cli("collect", "--run", str(run_root))
        collection = json.loads((run_root / "control/collections" / packet.name / "collection.json").read_text(encoding="utf-8"))
        gates = {item["id"]: item["status"] for item in collection["gates"]}
        self.assertEqual(gates["protected_paths"], "fail")
        self.assertEqual(gates["allowed_scope"], "fail")

    def test_validation_rejects_shell_command_strings(self) -> None:
        bad = json.loads(json.dumps(self.suite))
        bad["cases"][0]["verification"][0]["argv"] = "python -m pytest"
        with self.assertRaises(harness.HarnessError):
            harness.validate_suite(bad)

    def test_real_skill_runtime_copy_excludes_author_evals(self) -> None:
        destination = self.root / "sealed-real-skill"
        digest = harness.copy_runtime_skill(HARNESS_PATH.parents[1], destination)
        self.assertRegex(digest, r"^[a-f0-9]{64}$")
        self.assertTrue((destination / "SKILL.md").is_file())
        self.assertTrue((destination / "references" / "repository-prose.md").is_file())
        self.assertFalse((destination / "evals").exists())

    def test_source_guard_detects_content_change_with_same_dirty_status(self) -> None:
        (self.repo / "app.py").write_text("VALUE = 3\n", encoding="utf-8")
        before = harness.git_source_state(self.repo)
        (self.repo / "app.py").write_text("VALUE = 4\n", encoding="utf-8")
        after = harness.git_source_state(self.repo)
        self.assertEqual(before["status_sha256"], after["status_sha256"])
        self.assertNotEqual(before["visible_tree_sha256"], after["visible_tree_sha256"])

    def test_git_source_state_with_noncanonical_repo_path(self) -> None:
        non_canonical = self.repo.parent / "." / self.repo.name
        state = harness.git_source_state(non_canonical)
        self.assertRegex(state["visible_tree_sha256"], r"^[a-f0-9]{64}$")

    def test_ancestor_history_excludes_future_commits(self) -> None:
        original = subprocess.run(
            ["git", "-C", str(self.repo), "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
        (self.repo / "app.py").write_text("VALUE = 2\n", encoding="utf-8")
        run_git(self.repo, "add", "app.py")
        run_git(self.repo, "commit", "--quiet", "-m", "future answer")
        self.suite["variants"] = [{"id": "candidate", "skill": str(self.skill)}]
        self.suite["cases"][0]["revision"] = original
        self.suite["cases"][0]["history"] = "ancestors"
        write_json(self.suite_path, self.suite)

        run_root = self.root / "history-run"
        self.run_cli("prepare", "--suite", str(self.suite_path), "--out", str(run_root))
        manifest = json.loads((run_root / "control/prepared/manifest.json").read_text(encoding="utf-8"))
        workspace = Path(manifest["packets"][0]["path"]) / "workspace"
        count = subprocess.run(
            ["git", "-C", str(workspace), "rev-list", "--count", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
        log = subprocess.run(
            ["git", "-C", str(workspace), "log", "--format=%s"],
            capture_output=True,
            text=True,
            check=True,
        ).stdout
        self.assertEqual(count, "1")
        self.assertNotIn("future answer", log)
        self.assertEqual((workspace / "app.py").read_text(encoding="utf-8"), "VALUE = 1\n")


if __name__ == "__main__":
    unittest.main()
