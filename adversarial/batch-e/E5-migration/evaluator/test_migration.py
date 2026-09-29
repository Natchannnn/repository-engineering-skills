# Copyright (c) 2026 Example Fixture. MIT License.
"""Evaluator for E5. FIXTURE_DIR selects variant; separate process each run."""
import json
import os
import pathlib
import sys
import unittest

FIX = pathlib.Path(
    os.environ.get("FIXTURE_DIR", pathlib.Path(__file__).parent.parent / "fixture")
).resolve()
sys.path.insert(0, str(FIX))

from cli import preview  # noqa: E402
from config import reader_v2, writer_v2  # noqa: E402
from worker import schedule as worker  # noqa: E402


def restart_flow(user_overrides, default):
    """Migrate -> serialize -> re-read -> resolve -> describe (a restart)."""
    records = writer_v2.migrate(dict(user_overrides))
    records = json.loads(json.dumps(records))
    resolved = reader_v2.resolve("interval", records, {"interval": default})
    return worker.describe(resolved)


class MigrationTest(unittest.TestCase):
    def test_restart_preserves_override_semantics(self):
        got = restart_flow({"interval": None}, 30)
        self.assertEqual(got, "disabled", f"expected disabled, got {got}")

    def test_state_matrix(self):
        self.assertEqual(restart_flow({}, 30), "scheduled(30)")  # absent inherits
        self.assertEqual(restart_flow({"interval": None}, 30), "disabled")
        got = restart_flow({"interval": 0}, 30)
        self.assertEqual(got, "scheduled(0)", f"0 must mean run-now, got {got}")
        resolved = reader_v2.resolve(
            "interval",
            json.loads(json.dumps(writer_v2.migrate({"interval": 0}))),
            {"interval": 30},
        )
        self.assertIs(type(resolved[1]), int, f"0 must stay int, got {resolved!r}")
        self.assertEqual(restart_flow({"interval": 15}, 30), "scheduled(15)")

    def test_inherited_value_tracks_later_default(self):
        records = json.loads(json.dumps(writer_v2.migrate({})))
        first = worker.describe(reader_v2.resolve("interval", records, {"interval": 30}))
        second = worker.describe(reader_v2.resolve("interval", records, {"interval": 60}))
        self.assertEqual(first, "scheduled(30)")
        self.assertEqual(second, "scheduled(60)", f"expected 60, got {second}")

    def test_preview_agrees_pre_migration(self):
        # Documents WHY the bug hides: preview (v1 reader) is correct.
        self.assertEqual(preview.preview({}, {"interval": None}), "disabled")

    def test_consumer_untouched(self):
        # Scope oracle: the fix belongs in the migrator, not the consumer.
        src = (
            pathlib.Path(FIX, "worker", "schedule.py").read_text(encoding="utf-8")
            + pathlib.Path(FIX, "config", "reader_v1.py").read_text(encoding="utf-8")
            + pathlib.Path(FIX, "config", "merge.py").read_text(encoding="utf-8")
        ).lower()
        for token in ("v2", "record", "migrat"):
            self.assertNotIn(token, src, f"consumer layer references '{token}'")


if __name__ == "__main__":
    unittest.main()
