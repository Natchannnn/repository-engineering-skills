"""Behavioral checks for the executable migration example shipped with the skill."""

import os
import re
import tempfile
import unittest
from pathlib import Path
from unittest import mock


EXAMPLE_PATH = Path(__file__).resolve().parents[2] / "references" / "migration-examples.md"


def replace_from_example(dest, new_bytes):
    text = EXAMPLE_PATH.read_text(encoding="utf-8")
    section = text.split("## Atomic replacement", 1)[1].split("\n## ", 1)[0]
    code = re.search(r"```python\n(.*?)```", section, re.DOTALL).group(1)
    namespace = {"os": os, "dest": dest, "new_bytes": new_bytes}
    exec(compile(code, str(EXAMPLE_PATH), "exec"), namespace)
    if "replace_file" in namespace:
        namespace["replace_file"](dest, new_bytes)


class MigrationExampleTest(unittest.TestCase):
    def test_replacement_writes_complete_content(self):
        for initial in (None, b"previous valid state"):
            with self.subTest(initial=initial), tempfile.TemporaryDirectory() as directory:
                dest = Path(directory) / "state.json"
                if initial is not None:
                    dest.write_bytes(initial)

                replace_from_example(dest, b'{"version": 2}\n')

                self.assertEqual(dest.read_bytes(), b'{"version": 2}\n')
                self.assertEqual(set(dest.parent.iterdir()), {dest})

    def test_io_failure_preserves_old_state_and_cleans_temporary_file(self):
        for operation in ("fsync", "replace"):
            with self.subTest(operation=operation), tempfile.TemporaryDirectory() as directory:
                dest = Path(directory) / "state.json"
                dest.write_bytes(b"previous valid state")

                with mock.patch.object(os, operation, side_effect=OSError("injected failure")):
                    with self.assertRaisesRegex(OSError, "injected failure"):
                        replace_from_example(dest, b"replacement")

                self.assertEqual(dest.read_bytes(), b"previous valid state")
                self.assertEqual(set(dest.parent.iterdir()), {dest})

    def test_write_failure_preserves_old_state_and_cleans_temporary_file(self):
        create_file = tempfile.NamedTemporaryFile

        def failing_writer(*args, **kwargs):
            file = create_file(*args, **kwargs)
            file.write = mock.Mock(side_effect=OSError("injected write failure"))
            return file

        with tempfile.TemporaryDirectory() as directory:
            dest = Path(directory) / "state.json"
            dest.write_bytes(b"previous valid state")

            with mock.patch.object(tempfile, "NamedTemporaryFile", side_effect=failing_writer):
                with self.assertRaisesRegex(OSError, "injected write failure"):
                    replace_from_example(dest, b"replacement")

            self.assertEqual(dest.read_bytes(), b"previous valid state")
            self.assertEqual(set(dest.parent.iterdir()), {dest})

    def test_existing_temporary_file_is_preserved(self):
        with tempfile.TemporaryDirectory() as directory:
            dest = Path(directory) / "state.json"
            unrelated = dest.with_suffix(".tmp")
            unrelated.write_bytes(b"unrelated user data")

            replace_from_example(dest, b"replacement")

            self.assertEqual(dest.read_bytes(), b"replacement")
            self.assertEqual(unrelated.read_bytes(), b"unrelated user data")
            self.assertEqual(set(dest.parent.iterdir()), {dest, unrelated})


if __name__ == "__main__":
    unittest.main()
