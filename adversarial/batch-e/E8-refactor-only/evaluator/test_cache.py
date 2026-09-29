# Copyright (c) 2026 Example Fixture. MIT License.
"""Evaluator for E8. BRANCH_DIR selects variant; separate process each run.

The stamp assertion is white-box on purpose: this oracle belongs to the fixture
author, never to candidates (evaluator/ is excluded from run dirs). It proves the
double clock read has an observable consequence: a later expiry stamp.
"""
import os
import pathlib
import sys
import unittest

BRANCH = pathlib.Path(
    os.environ.get("BRANCH_DIR", pathlib.Path(__file__).parent.parent / "branch-defect")
).resolve()
sys.path.insert(0, str(BRANCH))

import cache  # noqa: E402


def scripted(times):
    it = iter(times)

    def tick():
        return next(it)

    return tick


class CacheTest(unittest.TestCase):
    def setUp(self):
        cache.reset()

    def tearDown(self):
        cache.reset()

    def test_single_capture_stamp(self):
        # Prime an expired entry, then measure ONE refresh: a correct
        # implementation reads the clock once, so the stamp is check-time + ttl.
        cache.get("k", lambda: "v", 10, clock=scripted([0.0]))
        cache.get("k", lambda: "v2", 10, clock=scripted([100.0, 200.0]))
        stamp = cache._STORE["k"]["expires"]
        self.assertEqual(
            stamp, 110.0, f"expected stamp 110.0 (one clock read), got {stamp}"
        )

    def test_hit_does_not_reload(self):
        calls = []
        cache.get("k", lambda: calls.append(1) or "v", 60, clock=scripted([1.0]))
        cache.get("k", lambda: calls.append(1) or "v", 60, clock=scripted([2.0]))
        self.assertEqual(calls, [1], f"hit must not reload, loader ran {len(calls)}x")

    def test_miss_then_hit_value(self):
        self.assertEqual(cache.get("k", lambda: "v", 60, clock=scripted([1.0])), "v")
        self.assertEqual(cache.get("k", lambda: "WRONG", 60, clock=scripted([2.0])), "v")


if __name__ == "__main__":
    unittest.main()
