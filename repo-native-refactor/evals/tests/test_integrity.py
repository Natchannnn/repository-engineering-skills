"""Regression tests use temporary repos and synthetic judgments, not AI ratings."""
from __future__ import annotations

import copy
import json
import os
import subprocess
import sys
import unittest
from pathlib import Path

import test_harness as fixture

harness = fixture.harness
write_json = fixture.write_json
run_git = fixture.run_git


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


class IntegrityTest(unittest.TestCase):
    tearDown = fixture.HarnessTest.tearDown
    run_cli = fixture.HarnessTest.run_cli

    def setUp(self):
        fixture.HarnessTest.setUp(self)
        self.suite["variants"] = [self.suite["variants"][1]]
        self.run_root = self.root / "run"

    def prepare(self, *extra):
        write_json(self.suite_path, self.suite)
        write_json(self.bars_path, self.bars)
        self.run_cli("prepare", "--suite", str(self.suite_path), "--out", str(self.run_root), *extra)
        self.manifest = read(self.run_root / "control/prepared/manifest.json")
        self.packet = Path(self.manifest["packets"][0]["path"])
        self.workspace = self.packet / "workspace"
        self.bundle = self.run_root / "control/collections" / self.packet.name

    def collect(self):
        self.run_cli("collect", "--run", str(self.run_root))
        return read(self.bundle / "collection.json")

    def judge(self):
        self.run_cli("judge", "--run", str(self.run_root))
        return read(self.run_root / "control/judge-index.json")

    def judgment(self, item):
        return {
            "$schema": harness.JUDGMENT_SCHEMA, "artifact_id": item["artifact_id"], "verdict": "pass",
            "bar_evidence": [{"id": key, "claim": claim, "verdict": "pass", "evidence": "Synthetic scorer input."}
                             for key, claim in harness.required_bars(self.bars["cases"][0], self.bars).items()],
            "hard_failures": [],
            "dimensions": [{"id": d["id"], "score": 4, "evidence": ["Synthetic scorer input."]} for d in self.bars["dimensions"]],
            "confidence": "high", "notes": "Not a real AI review.",
        }

    def judge_all(self):
        index = self.judge()
        for item in index["artifacts"]:
            write_json(Path(item["path"]) / "judgment.json", self.judgment(item))
        return index

    def score(self):
        self.run_cli("score", "--run", str(self.run_root))
        return read(self.run_root / "scorecard.json")

    def rejected(self, command, expected, *extra):
        result = subprocess.run([sys.executable, "-B", str(fixture.HARNESS_PATH), command,
                                 "--run", str(self.run_root), *extra], capture_output=True, text=True)
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertIn(expected, result.stderr)
        self.assertNotIn("Traceback", result.stderr)

    def gate_status(self, collection, key):
        return next(g["status"] for g in collection["gates"] if g["id"] == key)

    def commit_source(self):
        run_git(self.repo, "add", "--all")
        run_git(self.repo, "commit", "--quiet", "-m", "extended fixture")

    def test_committed_protected_change_in_both_history_modes(self):
        for mode in ("none", "ancestors"):
            with self.subTest(mode=mode):
                self.run_root = self.root / mode
                self.suite["cases"][0]["history"] = mode
                self.prepare()
                (self.workspace / "generated/client.py").write_text("GENERATED = False\n")
                run_git(self.workspace, "add", "--all")
                run_git(self.workspace, "commit", "--quiet", "-m", "candidate commit")
                result = self.collect()
                self.assertIn("generated/client.py", result["changed_paths"])
                self.assertEqual(self.gate_status(result, "protected_paths"), "fail")
                self.assertEqual(self.gate_status(result, "allowed_scope"), "fail")
                self.assertGreater((self.bundle / "artifact.patch").stat().st_size, 0)

    def test_mixed_changes_preserve_runner_index(self):
        self.prepare()
        (self.workspace / "committed.txt").write_text("committed")
        run_git(self.workspace, "add", "committed.txt")
        run_git(self.workspace, "commit", "--quiet", "-m", "add file")
        (self.workspace / "staged.txt").write_text("staged")
        run_git(self.workspace, "add", "staged.txt")
        (self.workspace / "untracked.txt").write_text("untracked")
        (self.workspace / "app.py").write_text("VALUE = 1\n# local\n")
        index_before = (self.workspace / ".git/index").read_bytes()
        result = self.collect()
        self.assertEqual(set(result["changed_paths"]), {"app.py", "committed.txt", "staged.txt", "untracked.txt"})
        self.assertEqual((self.workspace / ".git/index").read_bytes(), index_before)

    def test_tracked_ignored_and_export_ignored_files_survive(self):
        (self.repo / ".gitignore").write_text("generated/\n")
        (self.repo / ".gitattributes").write_text("generated/client.py export-ignore\n")
        self.commit_source()
        self.prepare()
        self.assertIn("generated/client.py", harness.git(self.workspace, "ls-files").stdout)
        (self.workspace / "generated/client.py").write_text("GENERATED = False\n")
        result = self.collect()
        self.assertEqual(self.gate_status(result, "protected_paths"), "fail")
        packet = Path(self.judge()["artifacts"][0]["path"])
        self.assertEqual((packet / "repository/generated/client.py").read_text(), "GENERATED = False\n")

    def test_post_collection_workspace_and_report_drift_do_not_change_judged_code(self):
        self.prepare()
        (self.packet / "runner-report.md").write_text("Original report.")
        self.collect()
        (self.workspace / "app.py").write_text("VALUE = 999\n")
        (self.packet / "runner-report.md").write_text("New report.")
        packet = Path(self.judge()["artifacts"][0]["path"])
        self.assertEqual((packet / "repository/app.py").read_text(), "VALUE = 1\n")
        self.assertEqual((packet / "runner-report.md").read_text(), "Original report.")
        self.assertEqual((packet / "artifact.patch").read_bytes(), b"")

    def test_verification_mutation_is_invalid_and_does_not_touch_runner(self):
        self.suite["cases"][0]["verification"].append({"id": "mutate", "argv": [sys.executable, "-c",
            "from pathlib import Path; Path('generated/client.py').write_text('GENERATED = False\\n')"]})
        self.prepare()
        result = self.collect()
        self.assertEqual(self.gate_status(result, "verification_immutable"), "invalid")
        self.assertEqual((self.workspace / "generated/client.py").read_text(), "GENERATED = True\n")
        self.assertEqual((self.bundle / "repository/generated/client.py").read_text(), "GENERATED = True\n")
        self.judge_all()
        self.assertFalse(self.score()["variants"][0]["certified"])

    def test_modified_collected_patch_is_rejected(self):
        self.prepare()
        self.collect()
        (self.bundle / "artifact.patch").write_text("replaced")
        self.rejected("judge", "Collected evidence was modified")

    def test_modified_collected_result_is_rejected_after_judging(self):
        self.prepare()
        self.collect()
        self.judge_all()
        data = read(self.bundle / "collection.json")
        data["gates"] = []
        write_json(self.bundle / "collection.json", data)
        self.rejected("score", "Collected evidence was modified")

    def test_duplicate_judgment_cannot_replace_three_samples(self):
        self.suite["repetitions"] = 3
        self.bars["certification"]["required_repetitions"] = 3
        self.prepare()
        self.collect()
        index = self.judge_all()
        index["artifacts"] = [index["artifacts"][0]] * 3
        write_json(self.run_root / "control/judge-index.json", index)
        self.rejected("score", "duplicate, missing, or extra")

    def test_missing_and_wrong_identity_samples_rejected(self):
        self.prepare()
        self.collect()
        index = self.judge_all()
        wrong = copy.deepcopy(index)
        wrong["artifacts"][0]["repeat"] = 2
        write_json(self.run_root / "control/judge-index.json", wrong)
        self.rejected("score", "identity differs")
        index["artifacts"] = []
        write_json(self.run_root / "control/judge-index.json", index)
        self.rejected("score", "duplicate, missing, or extra")

    def test_contradictory_and_incomplete_judgments_rejected(self):
        item = {"artifact_id": "0123456789abcdef"}
        base = self.judgment(item)
        variants = []
        failed_bar = copy.deepcopy(base)
        failed_bar["bar_evidence"][0]["verdict"] = "fail"
        variants.append(failed_bar)
        hard_failure = copy.deepcopy(base)
        hard_failure["hard_failures"] = ["Known regression"]
        variants.append(hard_failure)
        zero = copy.deepcopy(base)
        zero["dimensions"][0]["score"] = 0
        variants.append(zero)
        missing = copy.deepcopy(base)
        missing["bar_evidence"].pop()
        variants.append(missing)
        duplicate = copy.deepcopy(base)
        duplicate["bar_evidence"].append(duplicate["bar_evidence"][0])
        variants.append(duplicate)
        for data in variants:
            with self.subTest(data=data):
                with self.assertRaises(harness.HarnessError):
                    harness.validate_judgment(data, item["artifact_id"], {"semantic", "native"},
                                              set(harness.required_bars(self.bars["cases"][0], self.bars)))

    def test_live_suite_edits_cannot_change_task_or_expected_count(self):
        self.prepare()
        self.collect()
        old_task = self.suite["cases"][0]["task"]
        self.suite["cases"][0]["task"] = "A different task"
        self.suite["repetitions"] = 20
        write_json(self.suite_path, self.suite)
        index = self.judge_all()
        task = read(Path(index["artifacts"][0]["path"]) / "task.json")
        self.assertEqual(task["task"], old_task)
        result = self.score()
        self.assertEqual(result["variants"][0]["expected_artifacts"], 1)

    def test_changed_bars_are_rejected_when_supplied(self):
        self.prepare()
        self.collect()
        self.bars["certification"]["min_rating"] = 0
        write_json(self.bars_path, self.bars)
        self.rejected("judge", "differ from the pre-registered", "--bars", str(self.bars_path))

    def test_prepared_configuration_tampering_rejected(self):
        self.prepare()
        (self.run_root / "control/prepared/bars.json").write_text("{}")
        self.rejected("collect", "incomplete or modified")

    def test_recollection_cannot_replace_failed_evidence(self):
        self.prepare()
        (self.workspace / "app.py").write_text("VALUE = 999\n")
        self.collect()
        self.judge_all()
        (self.workspace / "app.py").write_text("VALUE = 1\n")
        self.rejected("collect", "cannot be overwritten")
        self.assertFalse(self.score()["variants"][0]["certified"])

    def test_judge_logs_self_contained_and_known_identity_redacted(self):
        self.suite["cases"][0]["verification"].append({"id": "log", "argv": [sys.executable, "-c",
            "from pathlib import Path; print(Path.cwd()); print('fixture-skill')"]})
        self.prepare()
        self.collect()
        packet = Path(self.judge()["artifacts"][0]["path"])
        evidence = read(packet / "evidence.json")
        self.assertNotIn("skill_unchanged", {g["id"] for g in evidence["gates"]})
        for result in evidence["verification"]:
            path = packet / result["log"]
            self.assertFalse(Path(result["log"]).is_absolute())
            self.assertTrue(path.is_file())
            log = path.read_text()
            for private in (str(self.packet), str(self.repo), str(self.skill), "fixture-skill"):
                self.assertNotIn(private, log)
        self.assertTrue((packet / "scoring.md").is_file())

    def test_patch_roundtrip_binary_non_utf8_crlf_and_empty_files(self):
        samples = {"crlf.txt": b"one\r\ntwo\r\n", "latin.txt": b"caf\xe9\nold\n",
                   "binary.dat": b"\x00\xffold", "empty.txt": b"", "gone.txt": b"remove me"}
        for name, data in samples.items():
            (self.repo / name).write_bytes(data)
        (self.repo / ".gitattributes").write_text("* -text\n")
        self.commit_source()
        self.prepare()
        changed = {"crlf.txt": b"one\r\nnew\r\n", "latin.txt": b"caf\xe9\nnew\n",
                   "binary.dat": b"\x00\xffnew", "new-empty.txt": b"", "renamed.txt": b"remove me"}
        for name, data in changed.items():
            (self.workspace / name).write_bytes(data)
        (self.workspace / "gone.txt").unlink()
        result = self.collect()
        self.assertEqual(set(result["changed_paths"]), set(changed) | {"gone.txt"})
        replay = self.root / "replay"
        baseline = self.run_root / "control/prepared/baseline/case-one/repository"
        modes = self.manifest["cases"][0]["baseline_modes"]
        harness.materialize_workspace(baseline, modes, None, replay)
        patch = (self.bundle / "artifact.patch").read_bytes()
        harness.git_bytes(replay, "apply", "--binary", "-", data=patch)
        for name, data in changed.items():
            self.assertEqual((replay / name).read_bytes(), data)
        self.assertFalse((replay / "gone.txt").exists())

    def test_file_directory_transitions(self):
        (self.repo / "old-file").write_text("file")
        (self.repo / "old-dir").mkdir()
        (self.repo / "old-dir/child").write_text("child")
        self.commit_source()
        self.prepare()
        (self.workspace / "old-file").unlink()
        (self.workspace / "old-file").mkdir()
        (self.workspace / "old-file/child").write_text("child")
        (self.workspace / "old-dir/child").unlink()
        (self.workspace / "old-dir").rmdir()
        (self.workspace / "old-dir").write_text("file")
        result = self.collect()
        self.assertEqual(set(result["changed_paths"]), {"old-file", "old-file/child", "old-dir", "old-dir/child"})

    def test_judge_evidence_and_existing_outputs_not_overwritten(self):
        self.prepare()
        self.collect()
        index = self.judge_all()
        self.rejected("judge", "already exist")
        packet = Path(index["artifacts"][0]["path"])
        original = (packet / "repository/app.py").read_bytes()
        (packet / "repository/app.py").write_bytes(b"replacement")
        self.rejected("score", "evidence or its path was modified")
        (packet / "repository/app.py").write_bytes(original)
        self.score()
        self.rejected("score", "Scorecard already exists")

    def test_valid_three_sample_score_and_partial_usage_coverage(self):
        self.suite["repetitions"] = 3
        self.bars["certification"]["required_repetitions"] = 3
        self.prepare()
        write_json(self.packet / "run-metadata.json", {"tokens_input": 100, "tokens_output": 20})
        self.collect()
        self.judge_all()
        variant = self.score()["variants"][0]
        self.assertTrue(variant["certified"])
        self.assertEqual(variant["tokens_input_observed_artifacts"], 1)
        self.assertEqual(variant["tokens_input_total"], 100)

    def test_skipped_baseline_cannot_certify(self):
        self.prepare("--skip-baseline")
        self.collect()
        self.judge_all()
        self.assertFalse(self.score()["variants"][0]["certified"])

    def test_typo_protection_and_invalid_json_rejected(self):
        case = self.suite["cases"][0]
        case["protected_path"] = case.pop("protected_paths")
        with self.assertRaises(harness.HarnessError):
            harness.validate_suite(self.suite)
        for raw in ('{"x":1,"x":2}', '{"x":NaN}', '{"x":Infinity}'):
            self.suite_path.write_text(raw)
            with self.assertRaises(harness.HarnessError):
                harness.load_json(self.suite_path)

    def test_nonfinite_weights_and_unknown_fields_rejected(self):
        for value in (float("inf"), float("nan"), -1, True):
            bars = copy.deepcopy(self.bars)
            bars["dimensions"][0]["weight"] = value
            with self.assertRaises(harness.HarnessError):
                harness.validate_bars(bars)
        self.bars["dimensions"][0]["typo"] = True
        with self.assertRaises(harness.HarnessError):
            harness.validate_bars(self.bars)

    def test_near_perfect_float_rounding_does_not_certify(self):
        self.bars["dimensions"][0]["weight"] = 1e100
        self.bars["dimensions"][1]["weight"] = 1
        self.prepare()
        self.collect()
        index = self.judge_all()
        path = Path(index["artifacts"][0]["path"]) / "judgment.json"
        data = read(path)
        data["dimensions"][1]["score"] = 3
        write_json(path, data)
        result = self.score()["variants"][0]
        self.assertFalse(result["certified"])
        self.assertFalse(result["perfect_on_current_suite"])

    def test_prepare_freezes_runtime_skill_before_runner_dispatch(self):
        self.prepare()
        frozen = self.run_root / "control/prepared/skills/candidate/SKILL.md"
        original = frozen.read_bytes()
        (self.skill / "SKILL.md").write_text("changed original skill")
        self.assertEqual((self.packet / "skill/SKILL.md").read_bytes(), original)
        self.collect()
        self.judge_all()
        self.assertTrue(self.score()["variants"][0]["certified"])

    def test_unsupported_git_symlink_is_explicitly_rejected(self):
        blob = harness.git_bytes(self.repo, "hash-object", "-w", "--stdin", data=b"app.py").stdout.strip().decode()
        run_git(self.repo, "update-index", "--add", "--cacheinfo", f"120000,{blob},link")
        run_git(self.repo, "commit", "--quiet", "-m", "symlink fixture")
        with self.assertRaisesRegex(harness.HarnessError, "Unsupported tree entry"):
            harness.export_commit(self.repo, "HEAD", self.root / "export")

    def test_executable_mode_preserved_and_mode_change_measured(self):
        run_git(self.repo, "update-index", "--chmod=+x", "app.py")
        run_git(self.repo, "commit", "--quiet", "-m", "executable fixture")
        self.prepare()
        self.assertIn("100755", harness.git(self.workspace, "ls-files", "--stage", "app.py").stdout)
        if os.name == "nt":
            run_git(self.workspace, "update-index", "--chmod=-x", "app.py")
        else:
            (self.workspace / "app.py").chmod(0o644)
        result = self.collect()
        self.assertEqual(result["changed_paths"], ["app.py"])
        self.assertIn(b"old mode 100755", (self.bundle / "artifact.patch").read_bytes())


if __name__ == "__main__":
    unittest.main()
