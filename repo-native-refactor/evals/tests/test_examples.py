"""Behavioral checks for the retry example shipped with the skill."""

import re
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock


EXAMPLE_PATH = Path(__file__).resolve().parents[2] / "references" / "refactor-examples.md"


class TransientError(Exception):
    pass


class PermanentError(Exception):
    pass


def retry_from_example(publish):
    text = EXAMPLE_PATH.read_text(encoding="utf-8")
    section = text.split("## R3 -", 1)[1].split("\n## ", 1)[0]
    code = re.findall(r"```python\n(.*?)```", section, re.DOTALL)[1]
    namespace = {
        "publish": publish,
        "ev": SimpleNamespace(id="event-1"),
        "TransientError": TransientError,
        "PermanentError": PermanentError,
        "log": mock.Mock(),
    }
    function = "def documented_retry():\n" + "\n".join(
        "    " + line for line in code.splitlines()
    )
    exec(compile(function, str(EXAMPLE_PATH), "exec"), namespace)
    return namespace["documented_retry"]()


class RetryExampleTest(unittest.TestCase):
    def test_publish_succeeds_after_transient_errors(self):
        publish = mock.Mock(side_effect=[TransientError("busy"), TransientError("busy"), "published"])

        self.assertEqual(retry_from_example(publish), "published")
        self.assertEqual(publish.call_count, 3)
        for call in publish.call_args_list:
            self.assertEqual(call.kwargs["idempotency_key"], "event-1")

    def test_exhaustion_propagates_final_transient_error(self):
        final_error = TransientError("service unavailable")
        publish = mock.Mock(side_effect=[TransientError("busy"), TransientError("busy"), final_error])

        with self.assertRaises(TransientError) as caught:
            retry_from_example(publish)

        self.assertIs(caught.exception, final_error)
        self.assertEqual(publish.call_count, 3)

    def test_permanent_error_is_not_retried(self):
        error = PermanentError("invalid event")
        publish = mock.Mock(side_effect=error)

        with self.assertRaises(PermanentError) as caught:
            retry_from_example(publish)

        self.assertIs(caught.exception, error)
        self.assertEqual(publish.call_count, 1)


if __name__ == "__main__":
    unittest.main()
